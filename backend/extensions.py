"""
Extensions module
Separates database and other extensions from app to avoid circular imports.
Migration Path: Extensions will be wrapped in a SkillAdapter for decentralized P2P state.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()

# Wrap db.session.rollback to be resilient to connection resets ("MySQL has gone away")
original_rollback = db.session.rollback

def resilient_rollback(*args, **kwargs):
    try:
        return original_rollback(*args, **kwargs)
    except Exception as e:
        import logging
        logging.getLogger("extensions").warning(
            f"Database rollback encountered operational error (likely MySQL gone away): {e}. "
            f"Removing session to force reconnection."
        )
        try:
            db.session.remove()
        except Exception:
            pass
        return None

db.session.rollback = resilient_rollback

jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",  # Use Redis in prod: "redis://localhost:6381/2"
)

import threading
ctx = threading.local()
