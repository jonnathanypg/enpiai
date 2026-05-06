import os
from app import create_app
from extensions import db
from models.subscription import Plan, Subscription
from models.distributor import Distributor
from services.dlocal_service import DLocalGoService

app = create_app()

with app.app_context():
    print("Clearing old plans...")
    # First unlink plans from distributors just in case
    distributors = Distributor.query.all()
    for d in distributors:
        if d.subscription_plan_id:
            d.subscription_plan_id = None
    db.session.commit()

    # Now delete subscriptions
    print("Deleting old subscriptions...")
    Subscription.query.delete()
    db.session.commit()

    # Now delete old plans
    print("Deleting old plans...")
    Plan.query.delete()
    db.session.commit()

    print("Creating new plans with dLocal Go...")
    dlocal = DLocalGoService()

    plans_data = [
        {"name": "Starter", "desc": "Starter Plan", "price": 19.99},
        {"name": "Pro", "desc": "Pro Plan", "price": 29.99},
        {"name": "Enterprise", "desc": "Enterprise Plan", "price": 99.99},
    ]

    for p in plans_data:
        try:
            print(f"Syncing {p['name']} with dLocal...")
            resp = dlocal.create_plan(
                name=p["name"],
                description=p["desc"],
                amount=p["price"],
                currency="USD",
                frequency_type="MONTHLY",
                frequency_value=1
            )
            
            plan_token = resp.get('plan_token')
            plan_id = str(resp.get('id', ''))
            print(f"Success! Token: {plan_token}")
            
            new_plan = Plan(
                name=p["name"],
                description=p["desc"],
                price_monthly=p["price"],
                price_annual=0,
                currency="USD",
                dlocal_plan_id=plan_id,
                dlocal_plan_token=plan_token,
                is_active=True
            )
            db.session.add(new_plan)
        except Exception as e:
            print(f"Failed to create {p['name']}: {e}")

    db.session.commit()
    print("All plans successfully recreated and saved to the database!")
