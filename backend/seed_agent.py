import logging
from app import create_app
from extensions import db
from models.distributor import Distributor
from models.agent_config import AgentConfig, AgentFeature, DEFAULT_FEATURES, AgentTone, AgentObjective

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_agent_configs():
    app = create_app()
    with app.app_context():
        distributors = Distributor.query.all()
        for dist in distributors:
            # Check if agent config exists
            config = AgentConfig.query.filter_by(distributor_id=dist.id).first()
            if not config:
                logger.info(f"Creating default agent config for distributor {dist.name} (ID: {dist.id})")
                config = AgentConfig(
                    distributor_id=dist.id,
                    name=dist.agent_name or "Asistente Virtual",
                    description=f"Agente principal para {dist.name}",
                    agent_type='prospect',
                    tone=AgentTone.FRIENDLY,
                    objective=AgentObjective.GENERAL,
                    priority=1,
                    is_active=True
                )
                db.session.add(config)
                db.session.flush() # Get config ID

                # Add default features
                for feat_data in DEFAULT_FEATURES:
                    feature = AgentFeature(
                        agent_id=config.id,
                        category=feat_data['category'],
                        name=feat_data['name'],
                        label=feat_data['label'],
                        description=feat_data['description'],
                        order=feat_data['order'],
                        is_enabled=True # Enable all by default for test
                    )
                    db.session.add(feature)
                
                logger.info(f"Added {len(DEFAULT_FEATURES)} default features to agent {config.name}")
            else:
                logger.info(f"Agent config already exists for distributor {dist.name}")
        
        db.session.commit()
        logger.info("Agent configuration fix completed! 🚀")

if __name__ == "__main__":
    fix_agent_configs()
