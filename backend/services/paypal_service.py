import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        self.client_id = os.environ.get('PAYPAL_CLIENT_ID')
        self.client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
        self.mode = os.environ.get('PAYPAL_MODE', 'sandbox') # 'sandbox' or 'live'
        
        if self.mode == 'live':
            self.base_url = "https://api-m.paypal.com"
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"

    def get_access_token(self):
        """Get OAuth2 access token from PayPal."""
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                auth=(self.client_id, self.client_secret), 
                data=data
            )
            response.raise_for_status()
            return response.json().get('access_token')
        except Exception as e:
            logger.error(f"PayPal Auth Error: {e}")
            return None

    def get_subscription_details(self, subscription_id):
        """Fetch subscription details from PayPal."""
        token = self.get_access_token()
        if not token:
            return None
            
        url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PayPal Get Subscription Error: {e}")
            return None

    def cancel_subscription(self, subscription_id, reason="User cancelled"):
        """Cancel a subscription in PayPal."""
        token = self.get_access_token()
        if not token:
            return False
            
        url = f"{self.base_url}/v1/billing/subscriptions/{subscription_id}/cancel"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = {"reason": reason}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.status_code == 204
        except Exception as e:
            logger.error(f"PayPal Cancel Subscription Error: {e}")
            return False

    def create_order(self, amount, currency="USD", description="Credit Recharge"):
        """Create a PayPal order for one-time payment."""
        token = self.get_access_token()
        if not token:
            return None
            
        url = f"{self.base_url}/v2/checkout/orders"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "description": description
            }]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PayPal Create Order Error: {e}")
            return None

    def capture_order(self, order_id):
        """Capture a previously created PayPal order."""
        token = self.get_access_token()
        if not token:
            return None
            
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PayPal Capture Order Error: {e}")
            return None

    def verify_webhook_signature(self, headers, body):
        """
        Verify the signature of a PayPal webhook.
        NOTE: This requires a full implementation of PayPal's signature verification.
        For now, we will log and process, but in production this should be strictly verified.
        """
        # TODO: Implement full signature verification logic
        return True
