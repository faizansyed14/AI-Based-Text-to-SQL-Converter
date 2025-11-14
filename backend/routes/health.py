"""Health check and status endpoints"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter
from models.schemas import HealthResponse
from database.postgres import get_db_connection
from database.sqlserver import check_sqlserver_connection

router = APIRouter()

@router.get("/api/health", response_model=HealthResponse)
async def health():
    """Check health status of all services"""
    # Check PostgreSQL
    postgres_connected = False
    try:
        conn = get_db_connection()
        conn.close()
        postgres_connected = True
    except:
        postgres_connected = False
    
    # Check SQL Server
    sqlserver_connected, sqlserver_message = check_sqlserver_connection()
    
    status = "healthy" if (postgres_connected and sqlserver_connected) else "degraded"
    
    return HealthResponse(
        status=status,
        sqlserver_connected=sqlserver_connected,
        sqlserver_message=sqlserver_message,
        postgres_connected=postgres_connected
    )

@router.get("/")
async def root():
    return {"message": "Text to SQL API is running", "database": "VikasAI SQL Server"}

