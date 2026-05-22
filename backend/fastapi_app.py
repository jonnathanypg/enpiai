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

        logger.info(f"Received WhatsApp webhook from api-whatsapp for distributor {distributor_id}")

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
        ])

        return {"status": "received", "async": True, "conversation_id": conv_id}
    except Exception as e:
        logger.error(f"Failed to dispatch task: {e}")
        return {"status": "error", "message": str(e)}

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
