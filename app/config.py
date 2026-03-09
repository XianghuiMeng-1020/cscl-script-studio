"""Configuration management for the application"""
import os
import socket


class Config:
    """Base configuration class"""
    APP_ENV = os.getenv('APP_ENV', os.getenv('FLASK_ENV', 'development'))
    SECRET_KEY = os.getenv('SECRET_KEY', 'teaching-feedback-system-2025-dev-only')
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '')
    
    # Data directory
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    
    # File paths
    ASSIGNMENTS_FILE = os.path.join(DATA_DIR, 'assignments.json')
    SUBMISSIONS_FILE = os.path.join(DATA_DIR, 'submissions.json')
    RUBRICS_FILE = os.path.join(DATA_DIR, 'rubrics.json')
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    LOGS_FILE = os.path.join(DATA_DIR, 'activity_logs.json')
    CONFIG_FILE = os.path.join(DATA_DIR, 'system_config.json')
    ENGAGEMENT_FILE = os.path.join(DATA_DIR, 'engagement_metrics.json')
    
    # Web server port with auto-switching logic
    @staticmethod
    def get_web_port():
        """Get web port with auto-switching if port is in use"""
        base_port = int(os.getenv('WEB_PORT', '5001'))
        port = base_port
        
        # Try to find an available port (check up to 5 ports)
        for offset in range(5):
            test_port = base_port + offset
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', test_port))
            sock.close()
            if result != 0:  # Port is available
                port = test_port
                break
        
        return port
    
    WEB_PORT = get_web_port()
    
    # LLM Provider Configuration (S2.10: primary + fallback; default: OpenAI only)
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()
    LLM_PROVIDER_PRIMARY = os.getenv('LLM_PRIMARY', os.getenv('LLM_PROVIDER_PRIMARY', 'openai')).lower()
    LLM_PROVIDER_FALLBACK = os.getenv('LLM_FALLBACK', os.getenv('LLM_PROVIDER_FALLBACK', 'openai')).lower()
    LLM_STRATEGY = os.getenv('LLM_PROVIDER_STRATEGY', os.getenv('LLM_STRATEGY', 'primary_with_fallback')).lower()
    LLM_ALLOW_UNIMPLEMENTED_PRIMARY = os.getenv('LLM_ALLOW_UNIMPLEMENTED_PRIMARY', 'false').lower() == 'true'
    OPENAI_ENABLED = os.getenv('OPENAI_ENABLED', 'true').lower() == 'true'
    OPENAI_IMPLEMENTED = os.getenv('OPENAI_IMPLEMENTED', 'true').lower() == 'true'
    QWEN_ENABLED = os.getenv('QWEN_ENABLED', 'false').lower() == 'true'
    QWEN_IMPLEMENTED = os.getenv('QWEN_IMPLEMENTED', 'true').lower() == 'true'
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
    QWEN_BASE_URL = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-plus')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    MOCK_MODEL = os.getenv('MOCK_MODEL', 'mock-model-v1')
    
    # Database Configuration (for future use)
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    USE_DB_STORAGE = os.getenv('USE_DB_STORAGE', 'false').lower() == 'true'
    
    # Spec Validation Configuration
    SPEC_VALIDATE_PUBLIC = os.getenv('SPEC_VALIDATE_PUBLIC', 'false').lower() == 'true'

    # S2.14 static cache busting
    STATIC_VERSION = os.getenv('STATIC_VERSION', '3')

    # Pipeline: require critic success for overall success (default conservative)
    PIPELINE_REQUIRE_CRITIC_SUCCESS = os.getenv('PIPELINE_REQUIRE_CRITIC_SUCCESS', 'true').lower() == 'true'

    # C1: Idempotency cache (Redis for multi-instance; omit for in-memory fallback)
    REDIS_URL = os.getenv('REDIS_URL', '')
    IDEMPOTENCY_TTL_SECONDS = int(os.getenv('IDEMPOTENCY_TTL_SECONDS', '120'))

    # M1: Upload / extraction limits (configurable)
    UPLOAD_TIMEOUT_SECONDS = int(os.getenv('UPLOAD_TIMEOUT_SECONDS', '120'))
    PDF_EXTRACTION_TIMEOUT_SECONDS = int(os.getenv('PDF_EXTRACTION_TIMEOUT_SECONDS', '60'))
    DOCUMENT_MAX_FILE_SIZE_MB = float(os.getenv('DOCUMENT_MAX_FILE_SIZE_MB', '10'))
    PDF_MAX_PAGES = int(os.getenv('PDF_MAX_PAGES', '500'))

    # S2.12 Auth + Demo
    DEMO_MODE = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    QUICK_DEMO_PUBLIC = os.getenv('QUICK_DEMO_PUBLIC', 'true').lower() == 'true'
    REQUIRE_LOGIN_FOR_TEACHER = os.getenv('REQUIRE_LOGIN_FOR_TEACHER', 'true').lower() == 'true'
    REQUIRE_LOGIN_FOR_STUDENT = os.getenv('REQUIRE_LOGIN_FOR_STUDENT', 'true').lower() == 'true'
    
    @staticmethod
    def validate():
        """Validate configuration; fail fast in production for critical vars"""
        import warnings
        prod = Config.APP_ENV.lower() in ('production', 'prod')
        if Config.SECRET_KEY == 'teaching-feedback-system-2025-dev-only':
            if prod:
                raise ValueError("SECRET_KEY must be set in production. Generate: python -c \"import secrets; print(secrets.token_hex(32))\"")
            warnings.warn("Using default SECRET_KEY. Set SECRET_KEY in environment for production!")
        return True
