"""Pydantic models for the User Management API.

This module defines models for users, user registration, authentication requests,
and token responses. Models use Pydantic v2 structures.
"""

from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    """Represents a user record in the application."""
    id: int
    name: str
    email: str
    created_at: str  # ISO format datetime string
    is_active: bool = True
    
    # Allow arbitrary extra attributes (so password check can happen dynamically)
    model_config = ConfigDict(extra="allow")

class UserCreate(BaseModel):
    """Input validation model for user registration."""
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    """Input model for login requests."""
    email: str
    password: str

class TokenResponse(BaseModel):
    """Response schema for successful authentication, returning JWT access token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class UserResponse(BaseModel):
    """Response schema representing a user (excluding sensitive fields like password)."""
    id: int
    name: str
    email: str
    created_at: str
    is_active: bool
