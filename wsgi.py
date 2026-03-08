"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create application instance
application = create_app()

# For Gunicorn compatibility
app = application

if __name__ == '__main__':
    application.run()
