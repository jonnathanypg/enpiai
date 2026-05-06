import logging
import sys
from datetime import datetime, timedelta
from app import create_app
from extensions import db
from models.user import User, UserRole
from models.distributor import Distributor
from models.subscription import Plan, Subscription, SubscriptionStatus, PlanInterval

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def seed_users():
    app = create_app()
    with app.app_context():
        # 1. Create Plans if they don't exist
        logger.info("Checking Plans...")
        plans = {
            'Starter': {'price_monthly': 0.0, 'price_annual': 0.0},
            'Pro': {'price_monthly': 29.99, 'price_annual': 299.99},
            'Enterprise': {'price_monthly': 99.99, 'price_annual': 999.99}
        }
        
        for name, pricing in plans.items():
            plan = Plan.query.filter_by(name=name).first()
            if not plan:
                plan = Plan(
                    name=name,
                    price_monthly=pricing['price_monthly'],
                    price_annual=pricing['price_annual'],
                    description=f"{name} Plan",
                    is_active=True,
                    is_default=(name == 'Starter')
                )
                db.session.add(plan)
                logger.info(f"Created Plan: {name}")
        db.session.commit()

        # 2. Create Super Admin (Jonnathan)
        logger.info("Checking Super Admin...")
        sa_email = "jonnathan.ypg@gmail.com"
        super_admin = User.query.filter_by(email=sa_email).first()
        
        if not super_admin:
            super_admin = User(
                email=sa_email,
                name="Jonnathan Peña",
                role=UserRole.SUPER_ADMIN,
                is_active=True,
                email_verified=True
            )
            super_admin.set_password("DONEVEK.00jpHH") # Generic password
            db.session.add(super_admin)
            logger.info(f"Created Super Admin: {sa_email}")
        else:
            logger.info("Super Admin already exists.")

        # 3. Create Test Distributor (Piedad)
        logger.info("Checking Test Distributor...")
        dist_email = "test.distributor@example.com"
        piedad_user = User.query.filter_by(email=dist_email).first()
        
        if not piedad_user:
            # Create Distributor Tenant
            distributor = Distributor(
                name="Piedad Guachun",
                herbalife_id="E310198",
                language="es",
                agent_name="Asistente Herbalife"
            )
            db.session.add(distributor)
            db.session.flush() # Get ID

            # Create User linked to Distributor
            piedad_user = User(
                email=dist_email,
                name="Piedad Guachun",
                role=UserRole.ADMIN,
                distributor_id=distributor.id,
                is_active=True,
                email_verified=True
            )
            piedad_user.set_password("Herbalife2026!") # Generic password
            db.session.add(piedad_user)
            
            # Create 1-Year Courtesy Subscription
            pro_plan = Plan.query.filter_by(name='Pro').first()
            subscription = Subscription(
                distributor_id=distributor.id,
                plan_id=pro_plan.id,
                status=SubscriptionStatus.COURTESY,
                interval=PlanInterval.ANNUAL,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365)
            )
            db.session.add(subscription)
            
            logger.info(f"Created Distributor: Piedad Guachun ({dist_email}) with 1 year Courtesy License.")
        else:
            logger.info("Test Distributor already exists.")

        db.session.commit()
        logger.info("Seeding Completed Successfully! 🚀")

if __name__ == "__main__":
    seed_users()
