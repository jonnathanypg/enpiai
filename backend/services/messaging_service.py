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
        """
        try:
            whatsapp_api_url = current_app.config.get('WHATSAPP_API_URL', 'http://localhost:3001')
            url = f"{whatsapp_api_url}/lead"
            payload = {
                "phone": to_phone,
                "message": message,
                "companyId": distributor_id
            }
            # Add API key if needed by the microservice
            headers = {
                "Content-Type": "application/json",
                # "Authorization": f"Bearer {os.getenv('WHATSAPP_API_KEY')}" 
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"WhatsApp sent to {to_phone}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {to_phone}: {e}")
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
