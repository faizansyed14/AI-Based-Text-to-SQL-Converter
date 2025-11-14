"""Authentication routes"""
import sys
import os
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv
# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import APIRouter, HTTPException, Depends, Header
from models.schemas import LoginRequest, LoginResponse, AuthResponse
from database.postgres import get_db_connection

load_dotenv()

router = APIRouter()

# Get credentials from environment variables
AUTH_EMAIL = os.getenv("AUTH_EMAIL")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")

if not AUTH_EMAIL or not AUTH_PASSWORD:
    raise ValueError("AUTH_EMAIL and AUTH_PASSWORD must be set in environment variables")

# Build credentials dictionary from env
VALID_CREDENTIALS = {
    AUTH_EMAIL.lower().strip(): AUTH_PASSWORD
}

# In-memory token storage (in production, use Redis or database)
active_tokens = {}

def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def verify_token(token: str) -> bool:
    """Verify if token is valid and not expired"""
    if token not in active_tokens:
        return False
    
    token_data = active_tokens[token]
    if datetime.now() > token_data["expires_at"]:
        del active_tokens[token]
        return False
    
    return True

@router.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return token"""
    email = request.email.lower().strip()
    password = request.password
    
    # Validate credentials
    if email not in VALID_CREDENTIALS:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if VALID_CREDENTIALS[email] != password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate token
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=24)  # 24 hour expiry
    
    # Store token
    active_tokens[token] = {
        "email": email,
        "created_at": datetime.now(),
        "expires_at": expires_at
    }
    
    return LoginResponse(
        success=True,
        message="Login successful",
        token=token
    )

@router.post("/api/auth/logout")
async def logout(authorization: str = Header(None)):
    """Logout user by invalidating token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    if token in active_tokens:
        del active_tokens[token]
    
    return {"success": True, "message": "Logged out successfully"}

@router.get("/api/auth/verify", response_model=AuthResponse)
async def verify_auth(authorization: str = Header(None)):
    """Verify if user is authenticated"""
    if not authorization or not authorization.startswith("Bearer "):
        return AuthResponse(authenticated=False)
    
    token = authorization.replace("Bearer ", "")
    
    if verify_token(token):
        token_data = active_tokens[token]
        return AuthResponse(
            authenticated=True,
            email=token_data["email"]
        )
    
    return AuthResponse(authenticated=False)

def get_current_user(authorization: str = Header(None)) -> str:
    """Dependency to get current authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    
    return active_tokens[token]["email"]

