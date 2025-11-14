"""PostgreSQL database connection for app metadata"""
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException
import os

# PostgreSQL configuration (for app metadata: chat_sessions, chat_messages)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

def get_db_connection():
    """Create and return a PostgreSQL connection (for app metadata)"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

