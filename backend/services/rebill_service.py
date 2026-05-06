import requests
import os
from flask import current_app

class RebillService:
    def __init__(self):
        self.secret_key = os.getenv('REBILL_SECRET_KEY')
        self.base_url = os.getenv('REBILL_BASE_URL', 'https://api.rebill.com/v3')
        self.headers = {
            'x-api-key': self.secret_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def create_customer(self, first_name, last_name, email, phone=None):
        """
        Creates a customer in Rebill.
        """
        url = f"{self.base_url}/customers"
        payload = {
            "firstName": first_name,
            "lastName": last_name,
            "email": email
        }
        if phone:
            # Rebill expects an array of phone numbers
            payload["phoneNumbers"] = [{
                "number": phone,
                "countryCode": "593" # Default to Ecuador for now or extract from phone
            }]

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def create_payment_link(self, payment_link_data):
        """
        Creates a payment link (Hosted Checkout).
        """
        url = f"{self.base_url}/payment-links"
        response = requests.post(url, headers=self.headers, json=payment_link_data)
        response.raise_for_status()
        return response.json()

    def get_payment_link_for_plan(self, plan_id, user_email, user_id, user_name, plan_name):
        """
        Generates a simplified Single-Use Payment Link for a Plan.
        """
        payload = {
            "title": [{"language": "en", "text": f"Subscribe to {plan_name}"}],
            "description": [{"language": "en", "text": f"Subscription for {user_email}"}],
            "type": "plan",
            "status": "active",
            "isSingleUse": True, # One-time link for this specific checkout attempt
            "paymentMethods": [
                {"methods": ["card"], "currency": "USD"} # Adjust currency/methods as needed
            ],
            "plan": {
                 "id": plan_id
            },
            "showCoupon": True,
            "metadata": {
                "user_id": str(user_id),
                "email": user_email
            },
             "prefilledFields": {
                "customer": {
                    "email": user_email,
                    "fullName": user_name
                }
            },
            # Redirects
            "redirectUrls": {
                "approved": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/success",
                "rejected": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/cancel",
                "pending": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/payment/pending"
            }
        }
        return self.create_payment_link(payload)

    def get_subscription(self, subscription_id):
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def cancel_subscription(self, subscription_id):
        url = f"{self.base_url}/subscriptions/{subscription_id}"
        payload = {"status": "cancelled"}
        response = requests.patch(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
