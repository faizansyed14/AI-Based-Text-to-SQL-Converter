"""SQL Server database connection for business data (VikasAI)"""
import pymssql
from fastapi import HTTPException
import os

# SQL Server configuration (for business data: VikasAI database)
SQLSERVER_CONFIG = {
    "server": os.getenv("SQLSERVER_HOST", "localhost"),
    "port": int(os.getenv("SQLSERVER_PORT", "1433")),
    "database": os.getenv("SQLSERVER_DB", "VikasAI"),
    "user": os.getenv("SQLSERVER_USER", "sa"),
    "password": os.getenv("SQLSERVER_PASSWORD", "YourStrong@Passw0rd"),
}

def get_sqlserver_connection():
    """Create and return a SQL Server connection (for business data)"""
    try:
        conn = pymssql.connect(
            server=SQLSERVER_CONFIG["server"],
            port=SQLSERVER_CONFIG["port"],
            user=SQLSERVER_CONFIG["user"],
            password=SQLSERVER_CONFIG["password"],
            database=SQLSERVER_CONFIG["database"],
            timeout=10
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL Server connection error: {str(e)}")

def check_sqlserver_connection():
    """Check if SQL Server connection is available"""
    try:
        # Try to connect directly without raising HTTPException
        conn = pymssql.connect(
            server=SQLSERVER_CONFIG["server"],
            port=SQLSERVER_CONFIG["port"],
            user=SQLSERVER_CONFIG["user"],
            password=SQLSERVER_CONFIG["password"],
            database=SQLSERVER_CONFIG["database"],
            timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return True, "Connected to VikasAI Database"
    except Exception as e:
        error_msg = str(e)
        # Make error message more user-friendly
        if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
            return False, "Connection timeout - SQL Server may be unreachable"
        return False, f"Connection failed: {error_msg[:100]}"

