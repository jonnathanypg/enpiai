"""
EnpiAI - FastAPI Unified Gateway
This application handles both high-concurrency async requests and legacy Flask routes.

Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
"""
import os
import time
import logging
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from a2wsgi import WSGIMiddleware

from config import get_config
from celery_app import celery
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()

# Initialize Flask App for migration
flask_app = create_app(config_class=config)

# FastAPI Initialization
app = FastAPI(
    title="EnpiAI Unified Gateway",
    description="Unified High-performance Gateway managing both Async and Legacy services.",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Engine Setup
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    **config.SQLALCHEMY_ENGINE_OPTIONS
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        # Mandatory rollback/ping to avoid stale connections
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()

@app.get("/health")
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "app": "EnpiAI FastAPI Bridge",
            "database": "connected",
            "timestamp": time.time(),
            "celery": "available" if celery else "unavailable"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# ---------------------------------------------------------------------------
# Webhook Proxy (Surgical Migration)
# ---------------------------------------------------------------------------

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook_async(request: Request):
    """
    Asynchronous receiver for WhatsApp Webhooks from api-whatsapp.
    Acknowledges receipt immediately and dispatches logic to Celery.
    """
    try:
        data = await request.json()
    except:
        # Fallback for form-data
        form_data = await request.form()
        data = dict(form_data)

    if not data:
        return {"status": "ignored", "reason": "empty_payload"}

    # Dispatch to Celery
    try:
        distributor_id = data.get('companyId')
        sender_phone = data.get('from', '').strip()
        message_text = data.get('message', '')
        attachment = data.get('attachment')

        is_audio = False
        if attachment and attachment.get('type') == 'audio' and attachment.get('local_path'):
            from services.voice_service import VoiceService
            audio_path = attachment.get('local_path')
            logger.info(f"Transcribing incoming WhatsApp audio: {audio_path}")
            transcription = VoiceService.transcribe(audio_path)
            if transcription:
                message_text = transcription
                is_audio = True
                logger.info(f"Audio transcribed successfully: '{message_text}'")
                # Remove temporary audio file
                try:
                    import os
                    os.remove(audio_path)
                except Exception as ex:
                    logger.warning(f"Could not remove temporary audio file: {ex}")
            else:
                message_text = "[Audio no transcribible]"

        logger.info(f"Received WhatsApp webhook from api-whatsapp for distributor {distributor_id} (is_audio={is_audio})")

        with SessionLocal() as db:
            from models.conversation import Conversation, ConversationChannel, ConversationStatus, Message, MessageRole
            from datetime import datetime

            # 1. Find/Create Conversation
            conversation = db.query(Conversation).filter_by(
                distributor_id=distributor_id,
                channel=ConversationChannel.WHATSAPP,
                participant_id=sender_phone,
                status=ConversationStatus.ACTIVE
            ).first()

            if not conversation:
                conversation = Conversation(
                    distributor_id=distributor_id,
                    channel=ConversationChannel.WHATSAPP,
                    participant_id=sender_phone,
                    participant_name=data.get('fromName', ''),
                )
                db.add(conversation)
                db.flush()

            # 2. Save User Message
            user_msg = Message(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content=message_text,
                message_metadata={
                    'messageId': data.get('messageId'),
                    'timestamp': data.get('timestamp')
                }
            )
            db.add(user_msg)
            conversation.last_message_at = datetime.utcnow()
            db.commit()

            conv_id = conversation.id

        # 3. Dispatch to Celery
        celery.send_task('tasks.process_webhook_message', args=[
            distributor_id,
            conv_id,
            message_text,
            'whatsapp',
            sender_phone
        ], kwargs={'is_audio': is_audio})

        return {"status": "received", "async": True, "conversation_id": conv_id}
    except Exception as e:
        logger.error(f"Failed to dispatch task: {e}")
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Voice Protocol Endpoints (FastAPI Bridge)
# ---------------------------------------------------------------------------
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uuid
import re

class SynthesizeRequest(BaseModel):
    text: str
    voice_name: Optional[str] = "es-EC-LuisNeural"

@app.get("/api/voice/voices")
def get_voices():
    """
    Get list of available voices.
    """
    from services.voice_service import VoiceService
    return VoiceService.get_voices()

@app.post("/api/voice/synthesize")
def voice_synthesize(req: SynthesizeRequest):
    """
    Synthesize text to speech on-demand.
    """
    from services.voice_service import VoiceService
    
    filename = f"synth_{uuid.uuid4().hex}.mp3"
    voice_dir = os.path.join(config.UPLOAD_FOLDER, 'voice')
    os.makedirs(voice_dir, exist_ok=True)
    output_path = os.path.join(voice_dir, filename)
    
    success = VoiceService.synthesize(req.text, req.voice_name, output_path)
    if not success:
        raise HTTPException(status_code=500, detail="Voice synthesis failed")
        
    return FileResponse(output_path, media_type="audio/mpeg", filename=filename)

@app.get("/api/voice/file/{filename}")
def get_voice_file(filename: str):
    """
    Retrieve and serve synthesized voice response files.
    """
    voice_dir = os.path.join(config.UPLOAD_FOLDER, 'voice')
    file_path = os.path.join(voice_dir, filename)
    
    # Path traversal security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(voice_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path, media_type="audio/mpeg")

@app.post("/api/voice/interact")
async def voice_interact(
    file: UploadFile = File(...),
    distributor_id: Optional[int] = Form(None),
    conversation_id: Optional[int] = Form(None),
    channel: Optional[str] = Form("webchat")
):
    """
    Receives user audio file, transcribes it, runs AgentOrchestrator to get response,
    synthesizes the response to audio, and returns text and audio path.
    """
    from services.voice_service import VoiceService
    from models.distributor import Distributor
    from models.conversation import Conversation, ConversationChannel, ConversationStatus, Message, MessageRole
    from services.agent_orchestrator import get_agent_orchestrator
    from datetime import datetime

    # Resolve distributor_id if not provided (Platform Support fallback)
    if not distributor_id:
        from models.platform_config import PlatformConfig
        platform_conf = PlatformConfig.get_config()
        distributor_id = platform_conf.platform_distributor_id
        if not distributor_id:
            raise HTTPException(status_code=503, detail="Platform agent not configured")

    # 1. Save uploaded file temporarily
    voice_dir = os.path.join(config.UPLOAD_FOLDER, 'voice')
    os.makedirs(voice_dir, exist_ok=True)
    
    temp_filename = f"upload_{uuid.uuid4().hex}_{file.filename}"
    temp_path = os.path.join(voice_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # 2. Transcribe using Whisper
        user_text = VoiceService.transcribe(temp_path)
        if not user_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio.")
    finally:
        # Delete the uploaded user file after transcription to save VPS disk space
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not delete temp uploaded voice note: {e}")

    # 3. Process with Agent Orchestrator
    with SessionLocal() as db:
        distributor = db.query(Distributor).get(distributor_id)
        if not distributor:
            raise HTTPException(status_code=404, detail="Distributor not found")

        # Get or create active conversation
        conversation = None
        if conversation_id:
            conversation = db.query(Conversation).get(conversation_id)
            
        if not conversation:
            # Try to find an existing active conversation for this channel
            conv_channel = ConversationChannel.WHATSAPP if channel == "whatsapp" else ConversationChannel.PLAYGROUND
            conversation = db.query(Conversation).filter_by(
                distributor_id=distributor.id,
                channel=conv_channel,
                status=ConversationStatus.ACTIVE
            ).first()
            
        if not conversation:
            conv_channel = ConversationChannel.WHATSAPP if channel == "whatsapp" else ConversationChannel.PLAYGROUND
            conversation = Conversation(
                distributor_id=distributor.id,
                channel=conv_channel,
                status=ConversationStatus.ACTIVE,
                participant_name="Usuario Web Voz"
            )
            db.add(conversation)
            db.flush()

        # Save User Message to conversation history
        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_text
        )
        db.add(user_msg)
        conversation.last_message_at = datetime.utcnow()
        db.commit()

        # Get response from Orchestrator
        orchestrator = get_agent_orchestrator(distributor)
        response_data = orchestrator.process_message(
            conversation=conversation,
            user_message=user_text,
            channel=channel or "webchat"
        )
        
        response_text = response_data.get('content', '')
        
        # Save Agent Message to conversation history
        ai_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_text,
            message_metadata={'agent_name': response_data.get('agent_name')}
        )
        db.add(ai_msg)
        conversation.last_message_at = datetime.utcnow()
        db.commit()

        conv_id = conversation.id

    # 4. Synthesize AI reply back to audio
    voice_name = VoiceService.resolve_voice(distributor)
    filename = f"reply_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(voice_dir, filename)
    
    # Strip markdown formatting
    clean_text = re.sub(r'[*_`#~-]', '', response_text)
    
    success = VoiceService.synthesize(clean_text, voice_name, output_path)
    audio_url = f"/api/voice/file/{filename}" if success else None

    return {
        "user_text": user_text,
        "response_text": response_text,
        "audio_url": audio_url,
        "conversation_id": conv_id
    }

@app.get("/api/v2/test")
def test_async():
    return {
        "message": "FastAPI is running for EnpiAI",
        "features": ["async_webhooks", "celery_bridge", "shared_db_pool", "flask_integrated"]
    }

# Mount Flask as a WSGI Middleware to handle all legacy routes
# This is placed after FastAPI routes to allow FastAPI to handle specific async routes first.
app.mount("/", WSGIMiddleware(flask_app))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
