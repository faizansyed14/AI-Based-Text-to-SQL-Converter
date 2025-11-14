"""Authentication schemas"""
from pydantic import BaseModel, EmailStr

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

