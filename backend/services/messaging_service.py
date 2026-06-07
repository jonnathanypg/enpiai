"""
Messaging Service
Handles sending messages to external channels (WhatsApp, Telegram).
Abstracts the HTTP calls to the api-whatsapp microservice and Telegram API.
"""
import os
import requests
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class MessagingService:
    def __init__(self):
        # We'll get these from current_app.config within the methods to stay synchronized
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')

    def send_whatsapp(self, to_phone: str, message: str, distributor_id: int):
        """
        Send WhatsApp message via api-whatsapp microservice.
        Includes automatic splitting of long messages for a more human experience.
        """
        if not to_phone:
            logger.error("No phone number provided for WhatsApp")
            return False

        # Split message into parts if it's too long or has multiple paragraphs
        parts = self._split_message(message)
        
        # Get URL from config or env
        try:
            whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001').rstrip('/')
        except RuntimeError:
            whatsapp_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:3001').rstrip('/')
        url = f"{whatsapp_url}/lead"
        success = True

        for i, part in enumerate(parts):
            payload = {
                "message": part,
                "phone": to_phone,
                "companyId": str(distributor_id)
            }

            try:
                # Add a small delay between parts to simulate human typing
                if i > 0:
                    import time
                    time.sleep(1.5)
                
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"WhatsApp message part {i+1}/{len(parts)} sent to {to_phone}")
            except Exception as e:
                logger.error(f"Failed to send WhatsApp message part to {to_phone}: {e}")
                success = False
        
        return success

    def _split_message(self, message: str, max_length: int = 400) -> list:
        """
        Splits a message into logical parts (by paragraphs or sentences) 
        if it exceeds max_length or contains double newlines.
        """
        if not message: return []
        if len(message) <= max_length and "\n\n" not in message:
            return [message]

        # 1. Split by double newlines (paragraphs)
        raw_parts = message.split("\n\n")
        final_parts = []
        
        current_part = ""
        for p in raw_parts:
            p = p.strip()
            if not p: continue
            
            # If a single paragraph is still too long, we might need to split by sentences
            # but for now, let's keep it simple: if adding this paragraph exceeds limit, 
            # push current and start new.
            if len(current_part) + len(p) > max_length and current_part:
                final_parts.append(current_part.strip())
                current_part = p
            else:
                if current_part:
                    current_part += "\n\n" + p
                else:
                    current_part = p
                    
        if current_part:
            final_parts.append(current_part.strip())
            
        return final_parts

    def send_whatsapp_media(self, to_phone: str, media_url: str, media_type: str, distributor_id: int, caption: str = None, file_name: str = None):
        """
        Send WhatsApp media via api-whatsapp microservice.
        """
        try:
            whatsapp_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001').rstrip('/')
        except RuntimeError:
            whatsapp_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:3001').rstrip('/')
        url = f"{whatsapp_url}/lead/media"
        payload = {
            "phone": to_phone,
            "mediaUrl": media_url,
            "mediaType": media_type,
            "companyId": str(distributor_id),
            "caption": caption,
            "fileName": file_name
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"WhatsApp Media ({media_type}) sent to {to_phone}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp Media to {to_phone}: {e}")
            return False

    def send_telegram(self, chat_id: str, message: str, bot_token: str = None):
        """
        Send Telegram message via official API.
        """
        token = bot_token or self.telegram_token
        if not token:
            logger.error("No Telegram token provided")
            return False

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Telegram sent to {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send Telegram to {chat_id}: {e}")
            return False

messaging_service = MessagingService()
