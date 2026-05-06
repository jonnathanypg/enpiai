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
jwt = JWTManager()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",  # Use Redis in prod: "redis://localhost:6381/2"
)
