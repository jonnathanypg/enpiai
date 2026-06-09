"""
EnpiAI - Voice Service (IAGS Protocol)
Handles Speech-to-Text (STT) via OpenAI Whisper and Text-to-Speech (TTS) via Edge-TTS.

Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
"""
import os
import logging
import asyncio
import concurrent.futures
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

class VoiceService:
    """
    VoiceService implements the IAGS Voice Protocol.
    Static methods:
        transcribe(audio_path) -> str
        synthesize(text, voice_name, output_path) -> bool
        get_voices() -> list
    """

    @staticmethod
    def transcribe(audio_path: str) -> str:
        """
        Transcribes an audio file using MediaSuite Custom API.
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return ""

        import requests
        
        url = os.getenv("WHISPER_API_URL", "https://media.weblifetech.com/api/external/transcribe")
        api_key = os.getenv("WHISPER_API_KEY")
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            logger.info(f"Starting Custom API transcription for: {audio_path}")
            with open(audio_path, "rb") as audio_file:
                # We specify the filename, the file object, and a generic audio mime type.
                files = {"file": (os.path.basename(audio_path), audio_file, "audio/mpeg")}
                response = requests.post(url, headers=headers, files=files, timeout=60)
            
            response.raise_for_status()
            data = response.json()
            
            text = data.get("text", "")
            logger.info(f"Transcription successful. Length: {len(text)}")
            return text.strip()
        except Exception as e:
            logger.error(f"Custom API transcription failed: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                logger.error(f"Response: {response.text}")
            return ""

    @staticmethod
    def transcribe_blob(audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """
        Helper to transcribe audio from an in-memory blob.
        """
        # Save temp file
        temp_dir = os.path.join(config.UPLOAD_FOLDER, "voice", "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename)
        
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_bytes)
            
            result = VoiceService.transcribe(temp_path)
            return result
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp audio file: {e}")

    @staticmethod
    def synthesize(text: str, voice_name: str, output_path: str) -> bool:
        """
        Synthesizes text into speech MP3 using Edge-TTS.
        This is thread-safe and event-loop aware.
        """
        if not text:
            logger.warning("Empty text passed for synthesis.")
            return False

        if not voice_name:
            voice_name = "es-EC-LuisNeural"  # Default Ecuadorian Voice

        # Make sure target directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            import edge_tts
        except ImportError:
            logger.error("edge-tts package is not installed.")
            return False

        async def _run_synthesis():
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(output_path)

        try:
            logger.info(f"Synthesizing voice response using voice '{voice_name}'...")
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # If we're inside a running loop (like FastAPI), run in thread
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _run_synthesis())
                    future.result()
            else:
                loop.run_until_complete(_run_synthesis())

            success = os.path.exists(output_path) and os.path.getsize(output_path) > 0
            if success:
                logger.info(f"Synthesis successful. Saved to {output_path}")
            else:
                logger.error("Synthesis failed: Output file empty or missing.")
            return success
        except Exception as e:
            logger.error(f"Edge-TTS synthesis error: {e}")
            return False

    @staticmethod
    def get_voices() -> list:
        """
        Returns list of primary local voices recommended for the IAGS system.
        """
        return [
            {"id": "es-EC-LuisNeural", "name": "Luis (Ecuador - Masculino)", "gender": "Male", "lang": "es-EC"},
            {"id": "es-EC-RamonaNeural", "name": "Ramona (Ecuador - Femenino)", "gender": "Female", "lang": "es-EC"},
            {"id": "es-MX-DaliaNeural", "name": "Dalia (México - Femenino)", "gender": "Female", "lang": "es-MX"},
            {"id": "es-MX-JorgeNeural", "name": "Jorge (México - Masculino)", "gender": "Male", "lang": "es-MX"},
            {"id": "es-US-PalomaNeural", "name": "Paloma (USA/Latam - Femenino)", "gender": "Female", "lang": "es-US"},
            {"id": "es-US-AlonsoNeural", "name": "Alonso (USA/Latam - Masculino)", "gender": "Male", "lang": "es-US"},
            {"id": "es-ES-ElviraNeural", "name": "Elvira (España - Femenino)", "gender": "Female", "lang": "es-ES"},
            {"id": "es-ES-AlvaroNeural", "name": "Alvaro (España - Masculino)", "gender": "Male", "lang": "es-ES"},
        ]

    @staticmethod
    def resolve_voice(distributor) -> str:
        """
        Dynamically selects the best voice neural model based on distributor country and agent gender.
        """
        if not distributor:
            return "es-EC-LuisNeural"

        # Check if distributor has set a preferred voice first
        preferred_voice = getattr(distributor, 'preferred_voice', None)
        if preferred_voice:
            return preferred_voice

        country = (distributor.country or "").lower()
        gender = getattr(distributor.agent_gender, 'value', str(distributor.agent_gender)).lower()

        if any(c in country for c in ['mexico', 'méxico', 'mx']):
            if gender == 'female':
                return "es-MX-DaliaNeural"
            return "es-MX-JorgeNeural"
        elif any(c in country for c in ['españa', 'spain', 'es']):
            if gender == 'female':
                return "es-ES-ElviraNeural"
            return "es-ES-AlvaroNeural"
        elif any(c in country for c in ['us', 'united states', 'eeuu', 'estados unidos']):
            if gender == 'female':
                return "es-US-PalomaNeural"
            return "es-US-AlonsoNeural"

        # Fallback to Ecuador defaults
        if gender == 'female':
            return "es-EC-RamonaNeural"
        return "es-EC-LuisNeural"
