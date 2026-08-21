import os
import requests
import logging
from app import create_app
from extensions import db
from models.subscription import Plan
from services.paypal_service import PayPalService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_paypal_plans")

app = create_app()
paypal = PayPalService()

def create_product(token):
    """Create the EnpiAI product in PayPal catalogs."""
    url = f"{paypal.base_url}/v1/catalogs/products"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "name": "EnpiAI Platform",
        "description": "EnpiAI SaaS Platform Subscriptions",
        "type": "SERVICE",
        "category": "SOFTWARE"
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    product_id = response.json().get("id")
    logger.info(f"Successfully created PayPal Product: {product_id}")
    return product_id

def create_billing_plan(token, product_id, plan_name, price, currency="USD"):
    """Create a subscription plan in PayPal for a product."""
    url = f"{paypal.base_url}/v1/billing/plans"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = {
        "product_id": product_id,
        "name": f"EnpiAI {plan_name} Plan",
        "description": f"Subscription plan for EnpiAI {plan_name}",
        "status": "ACTIVE",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0, # Infinite cycles until cancelled
                "pricing_scheme": {
                    "fixed_price": {
                        "value": f"{price:.2f}",
                        "currency_code": currency
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": "0.00",
                "currency_code": currency
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    plan_id = response.json().get("id")
    logger.info(f"Successfully created PayPal Plan for {plan_name}: {plan_id}")
    return plan_id

if __name__ == "__main__":
    with app.app_context():
        # 1. Authenticate with PayPal
        token = paypal.get_access_token()
        if not token:
            logger.error("Could not obtain PayPal access token. Verify credentials in .env.")
            exit(1)
            
        logger.info("Authenticated successfully with PayPal Sandbox API.")
        
        # 2. Get active plans from DB
        db_plans = Plan.query.filter_by(is_active=True).all()
        if not db_plans:
            logger.warn("No active plans found in the database. Run recreate_plans.py first.")
            exit(0)
            
        logger.info(f"Found {len(db_plans)} active plans in the database.")
        
        # 3. Create Product
        try:
            product_id = create_product(token)
        except Exception as e:
            logger.error(f"Failed to create PayPal Product: {e}")
            exit(1)
            
        # 4. Create Plans and link them
        updated_count = 0
        for plan in db_plans:
            # We skip if it is a credit block since one-time charges do not need a PayPal billing plan ID
            if getattr(plan, "is_credit_block", False):
                logger.info(f"Skipping plan '{plan.name}' (is a credit block, uses standard PayPal orders).")
                continue
                
            logger.info(f"Registering PayPal plan for '{plan.name}' ($ {plan.price_monthly})...")
            try:
                paypal_plan_id = create_billing_plan(
                    token=token,
                    product_id=product_id,
                    plan_name=plan.name,
                    price=plan.price_monthly,
                    currency=plan.currency or "USD"
                )
                plan.paypal_plan_id = paypal_plan_id
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to create plan '{plan.name}' on PayPal: {e}")
                
        if updated_count > 0:
            db.session.commit()
            logger.info(f"Successfully updated {updated_count} plans in the database with their PayPal Plan IDs!")
        else:
            logger.warn("No plan IDs were updated.")
