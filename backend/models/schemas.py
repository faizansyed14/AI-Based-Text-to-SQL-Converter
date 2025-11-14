"""Pydantic models for API requests and responses"""
from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[int] = None
    model: Optional[str] = "gpt-4o-mini"  # Default to OpenAI

class ChatResponse(BaseModel):
    message: str
    sql_query: Optional[str] = None
    data: Optional[List[dict]] = None
    formatted_html: Optional[str] = None
    summary: Optional[dict] = None
    error: Optional[str] = None
    session_id: Optional[int] = None
    model_name: Optional[str] = None  # Track which model was actually used
    
    class Config:
        protected_namespaces = ()  # Allow model_name field

class ChatSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    updated_at: str

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sql_query: Optional[str] = None
    data: Optional[List[dict]] = None
    error: Optional[str] = None
    timestamp: str

class ExcelTableResponse(BaseModel):
    id: int
    table_name: str
    file_name: str
    columns: List[str]
    row_count: int
    created_at: str
    updated_at: str

class TableSelectionRequest(BaseModel):
    table_name: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    sqlserver_connected: bool
    sqlserver_message: str
    postgres_connected: bool

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

class AuthResponse(BaseModel):
    authenticated: bool
    email: Optional[str] = None

