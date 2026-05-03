"""
Herbalife Distributor SaaS Platform - Application Factory
Main Flask application entry point.

Copyright © 2026 WEBLIFETECH (Jonnathan Peña). All Rights Reserved.
Migration Path: App factory will become an HTTP gateway for a P2P mesh of agents.
"""
import os
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import get_config
from extensions import db, jwt, migrate, limiter
import models # Ensure models are registered for migrations

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # CORS (configurable origins for production security)
    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS(app, resources={
        r"/api/*": {"origins": cors_origins},
        r"/webhooks/*": {"origins": cors_origins}
    })

    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)

    # -------------------------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.distributors import distributors_bp
    from routes.leads import leads_bp
    from routes.customers import customers_bp
    from routes.wellness import wellness_bp
    from routes.agents import agents_bp
    from routes.channels import channels_bp
    from routes.webhooks import webhooks_bp
    from routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(distributors_bp, url_prefix='/api/distributors')
    app.register_blueprint(leads_bp, url_prefix='/api/leads')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(wellness_bp, url_prefix='/api/wellness')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(channels_bp, url_prefix='/api/channels')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    from routes.google_auth import google_auth_bp
    app.register_blueprint(google_auth_bp, url_prefix='/api/auth/google')

    from routes.payments import payments_bp
    app.register_blueprint(payments_bp, url_prefix='/api/payments')

    # Phase 13: dLocal Go Subscription Billing
    from routes.billing import billing_bp
    app.register_blueprint(billing_bp)

    from routes.rag import rag_bp
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    
    from routes.openai_compat import openai_bp
    app.register_blueprint(openai_bp)

    # Phase 11: Super Admin Panel
    from routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Phase 12: Unified Identity
    from routes.contacts import contacts_bp
    app.register_blueprint(contacts_bp, url_prefix='/api/contacts')


    # -------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'app': 'EnpiAI - Herbalife SaaS'}), 200

    # Serve Wellness Reports (Publicly but with long random filenames)
    @app.route('/api/wellness/reports/<path:filename>')
    def serve_wellness_report(filename):
        reports_dir = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads'), 'reports')
        return send_from_directory(reports_dir, filename)

    # -------------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    # -------------------------------------------------------------------
    # JWT Error Handlers
    # -------------------------------------------------------------------
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Authorization required'}), 401

    logger.info("EnpiAI application created successfully")
    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
