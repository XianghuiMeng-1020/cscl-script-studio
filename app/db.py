"""Database initialization and session management"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
import os

db = SQLAlchemy()


def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('PRAGMA busy_timeout=30000')
    cursor.close()


def init_db(app: Flask):
    """Initialize database connection"""
    database_url = app.config.get('DATABASE_URL', '')
    
    # Use psycopg3 dialect when postgresql:// is given (psycopg3 supports Python 3.13)
    if database_url and database_url.startswith('postgresql://') and 'postgresql+' not in database_url:
        try:
            import psycopg
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
        except ImportError:
            pass
    
    if not database_url:
        # No external DB configured: use a file-based SQLite so every thread/worker
        # shares the same database and demo users seeded at startup stay visible.
        import pathlib
        db_dir = pathlib.Path(app.root_path).parent / 'data'
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / 'app.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'check_same_thread': False, 'timeout': 30},
        }
        db.init_app(app)

        from sqlalchemy import event as sa_event
        with app.app_context():
            sa_event.listen(db.engine, 'connect', _set_sqlite_pragma)

        return False
    
    # Set SQLAlchemy config
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Initialize Flask-SQLAlchemy
    db.init_app(app)
    
    return True


def check_db_connection(app: Flask):
    """Check if database is connected and accessible"""
    try:
        database_url = app.config.get('DATABASE_URL', '')
        if not database_url:
            return False
        
        # Try to connect
        with app.app_context():
            # Check if db is initialized
            if not hasattr(db, 'engine') or db.engine is None:
                return False
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            return True
    except Exception:
        return False
