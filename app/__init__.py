"""Application factory"""
import time
import uuid
import logging
from flask import Flask, g, request
from flask_cors import CORS
from flask_login import LoginManager
from app.config import Config
from app.db import init_db

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Create and configure Flask application"""
    import os
    # Get the root directory (parent of app/)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load configuration
    app.config.from_object(config_class)
    if os.environ.get('TESTING') == 'true':
        app.config['SPEC_VALIDATE_PUBLIC'] = True  # Allow spec/validate without auth in tests
    config_class.validate()
    
    # Enable CORS (restrict origins in production if CORS_ALLOWED_ORIGINS set)
    origins_str = getattr(config_class, 'CORS_ALLOWED_ORIGINS', '') or ''
    if origins_str and isinstance(origins_str, str):
        origins = [o.strip() for o in origins_str.split(',') if o and o.strip()]
        if origins:
            CORS(app, origins=origins)
        else:
            CORS(app)
    else:
        CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = None  # We handle login via API, not redirect
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(user_id)
    
    # Initialize database (non-blocking, won't fail if DB not configured)
    init_db(app)
    
    # S2.14: inject static_version for cache busting in templates
    @app.context_processor
    def inject_static_version():
        return {'static_version': app.config.get('STATIC_VERSION', '1')}

    # Register blueprints
    from app.routes import teacher_bp, student_bp, api_bp, auth_bp
    from app.routes.cscl import cscl_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(cscl_bp)

    # C2: trace_id for all /api/* requests + structured request log
    @app.before_request
    def before_api_request():
        if request.path.startswith('/api/'):
            g.request_id = getattr(g, 'request_id', None) or str(uuid.uuid4())[:16]
            g.request_start_time = time.time()

    @app.after_request
    def after_api_request(response):
        if not request.path.startswith('/api/'):
            return response
        req_id = getattr(g, 'request_id', None)
        if req_id and response:
            response.headers['X-Request-Id'] = req_id
        start = getattr(g, 'request_start_time', None)
        latency_ms = round((time.time() - start) * 1000) if start else None
        user_id = None
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                user_id = getattr(current_user, 'id', None)
        except Exception:
            pass
        err_code = getattr(g, 'error_code', None) if (response and response.status_code >= 400) else None
        logger.info(
            "api_request trace_id=%s user_id=%s endpoint=%s method=%s path=%s status_code=%s latency_ms=%s error_code=%s",
            req_id or '-', user_id or '-', request.endpoint or request.path, request.method, request.path,
            response.status_code if response else '-', latency_ms or '-', err_code or '-'
        )
        return response

    # B3: API routes must return JSON only (no HTML error pages)
    @app.errorhandler(404)
    def handle_404(e):
        from flask import request
        if request.path.startswith('/api/'):
            from app.utils.api_errors import api_error_response
            return api_error_response('NOT_FOUND', 'Resource not found.', 404)
        return e

    @app.errorhandler(500)
    def handle_500(e):
        from flask import request
        if request.path.startswith('/api/'):
            import traceback
            req_id = getattr(g, 'request_id', None) or str(uuid.uuid4())[:16]
            logger.error(
                "api_500 trace_id=%s path=%s error=%s",
                req_id, getattr(request, 'path', ''), str(e),
                exc_info=True,
                extra={'trace_id': req_id, 'traceback': traceback.format_exc()}
            )
            from app.utils.api_errors import api_error_response
            return api_error_response(
                'INTERNAL_ERROR',
                'An internal error occurred.',
                500,
                details={'trace_id': req_id},
                trace_id=req_id
            )
        from flask import jsonify
        return jsonify({'error': 'Internal Server Error'}), 500

    return app
