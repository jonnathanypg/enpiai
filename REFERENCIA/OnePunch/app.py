"""
OnePunch - Multi-Agent System Application
Main Flask application entry point
"""
import os
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_migrate import Migrate

from config import get_config
from extensions import db, jwt, migrate, socketio


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
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/webhooks/*": {"origins": "*"}
    })
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Ensure upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.companies import companies_bp
    from routes.agents import agents_bp
    from routes.channels import channels_bp
    from routes.rag import rag_bp
    from routes.analytics import analytics_bp
    from routes.chat import chat_bp
    from routes.webhooks import webhooks_bp
    from routes.livekit_routes import livekit_bp
    from routes.voice_agent_api import voice_agent_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(companies_bp, url_prefix='/api/companies')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(channels_bp, url_prefix='/api/channels')
    app.register_blueprint(rag_bp, url_prefix='/api/rag')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(webhooks_bp, url_prefix='/webhooks')
    app.register_blueprint(livekit_bp) # url_prefix already defined in blueprint
    app.register_blueprint(voice_agent_bp) # Internal API
    
    from routes.employees import employees_bp
    app.register_blueprint(employees_bp, url_prefix='/api/employees')
    
    from routes.google_auth import google_auth_bp
    app.register_blueprint(google_auth_bp)

    from routes.hubspot_auth import hubspot_auth_bp
    app.register_blueprint(hubspot_auth_bp)
    
    from routes.payments import payments_bp
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    
    # Frontend routes

    @app.route('/')
    def index():
        return render_template('dashboard/index.html')
    
    @app.route('/login')
    def login_page():
        return render_template('auth/login.html')
    
    @app.route('/register')
    def register_page():
        return render_template('auth/register.html')
    
    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard/index.html')
    
    @app.route('/agents')
    def agents_page():
        return render_template('config/agents.html')
    
    @app.route('/channels')
    def channels_page():
        return render_template('config/channels.html')
    
    @app.route('/documents')
    def documents_page():
        return render_template('config/documents.html')
    
    @app.route('/employees')
    def employees_page():
        return render_template('config/employees.html')
    
    @app.route('/analytics')
    def analytics_page():
        return render_template('dashboard/analytics.html')
    
    @app.route('/chat')
    def chat_page():
        return render_template('dashboard/chat.html')
    
    @app.route('/settings')
    def settings_page():
        return render_template('config/settings.html')
        
    @app.route('/livekit-test')
    def livekit_test_page():
        return render_template('livekit/test_call.html')
    
    # Health check
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'app': 'OnePunch'})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Authorization required'}), 401
    
    return app


# Create app instance
app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
