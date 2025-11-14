"""Schema endpoints"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, HTTPException
from services.schema_service import get_table_schema

router = APIRouter()

@router.get("/api/schema")
async def get_schema():
    """Get database schema"""
    try:
        schema = get_table_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

