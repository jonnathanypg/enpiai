"""
PayPal Service - Payment Processing
"""
import os
import paypalrestsdk

from flask import current_app

class PayPalService:
    """
    PayPal Integration Service
    Architecture: Multi-tenant (Company keys > Platform keys)
    Using `paypalrestsdk.Api` for isolated contexts.
    """
    
    def __init__(self, company=None):
        self.company = company
        self._api = None
    
    def _get_credential(self, key: str) -> str:
        """Resolve credential: Company > Env"""
        # 1. Check Company Keys (support both naming conventions)
        if self.company and self.company.api_keys:
            value = self.company.api_keys.get(key)
            if value:
                return value
            
            # Check alternate key names (paypal_id vs paypal_client_id)
            alt_keys = {
                'paypal_client_id': 'paypal_id',
                'paypal_client_secret': 'paypal_secret',
                'paypal_id': 'paypal_client_id',
                'paypal_secret': 'paypal_client_secret'
            }
            if key in alt_keys:
                value = self.company.api_keys.get(alt_keys[key])
                if value:
                    return value
        
        # 2. Check Environment Variables
        env_map = {
            'paypal_client_id': 'PAYPAL_CLIENT_ID',
            'paypal_client_secret': 'PAYPAL_CLIENT_SECRET',
            'paypal_mode': 'PAYPAL_MODE'
        }
        return os.getenv(env_map.get(key, ''), 'sandbox') # Default to sandbox if missing

    def _get_api(self):
        """Create isolated PayPal API context"""
        client_id = self._get_credential('paypal_client_id')
        client_secret = self._get_credential('paypal_client_secret')
        mode = self._get_credential('paypal_mode')
        
        if not client_id or not client_secret:
            raise ValueError("PayPal credentials not configured")
            
        return paypalrestsdk.Api({
            "mode": mode, # sandbox or live
            "client_id": client_id,
            "client_secret": client_secret
        })

    def create_payment(self, amount: float, currency: str = "USD", return_url: str = None, cancel_url: str = None, description: str = "OnePunch Service"):
        """
        Create a PayPal payment object
        """
        api = self._get_api()
        
        # Determine Return URLs
        try:
            base_url = current_app.config.get('API_BASE_URL', 'http://localhost:5001')
        except:
             base_url = 'http://localhost:5001' # Fallback if outside app context
             
        cid_param = f"?cid={self.company.id}" if self.company else ""
        default_return = f"{base_url}/api/payments/success{cid_param}"
        default_cancel = f"{base_url}/api/payments/cancel"
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url or default_return,
                "cancel_url": cancel_url or default_cancel
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": description,
                        "sku": "001",
                        "price": str(amount),
                        "currency": currency,
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(amount),
                    "currency": currency
                },
                "description": description
            }]
        }, api=api)
        
        if payment.create():
            # Extract approval URL
            approval_url = next((link.href for link in payment.links if link.rel == "approval_url"), None)
            return {
                'status': 'success',
                'payment_id': payment.id,
                'approval_url': approval_url
            }
        else:
            return {
                'status': 'error', 
                'error': payment.error
            }

    def execute_payment(self, payment_id: str, payer_id: str):
        """Execute approved payment"""
        api = self._get_api()
        payment = paypalrestsdk.Payment.find(payment_id, api=api)
        
        if payment.execute({"payer_id": payer_id}):
            return {'status': 'success', 'payment': payment.to_dict()}
        else:
            return {'status': 'error', 'error': payment.error}
