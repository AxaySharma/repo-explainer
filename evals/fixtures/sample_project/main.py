"""Main FastAPI application module for the User Management API.

Defines all HTTP endpoints, request/response models, startup/shutdown database hooks,
and dependency-injected bearer validation requirements.
"""

from fastapi import FastAPI, Depends, HTTPException
from database import get_db, Database
from auth import create_token, require_auth
from models import User, UserCreate, LoginRequest, TokenResponse, UserResponse

# Instantiate FastAPI application
app = FastAPI(title="User Management API", version="1.0.0")

@app.on_event("startup")
def startup_event() -> None:
    """Establish connection with the database when the application starts."""
    db: Database = get_db()
    db.connect()

@app.on_event("shutdown")
def shutdown_event() -> None:
    """Safely terminate database connections when the application stops."""
    db: Database = get_db()
    db.disconnect()

@app.get("/health")
def health_check() -> dict:
    """Perform health checks to confirm container statuses and api run states."""
    return {"status": "ok", "version": "1.0.0"}

@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Accept credential details, verify password match, and return active JWT bearer token."""
    db: Database = get_db()
    user = db.get_user_by_email(body.email)
    
    # Simple password equality check as specified
    if not user or getattr(user, "password", None) != body.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    return create_token(user.id)

@app.get("/users", response_model=list[UserResponse])
def get_users(token: dict = Depends(require_auth)) -> list[User]:
    """Retrieve all user accounts from the database."""
    db: Database = get_db()
    return db.get_all_users()

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, token: dict = Depends(require_auth)) -> User:
    """Retrieve details for a single user by ID."""
    db: Database = get_db()
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users", response_model=UserResponse)
def create_user(body: UserCreate, token: dict = Depends(require_auth)) -> User:
    """Register a new user inside the database."""
    db: Database = get_db()
    
    # Check if email is already taken
    existing_user = db.get_user_by_email(body.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    return db.insert_user(body)
