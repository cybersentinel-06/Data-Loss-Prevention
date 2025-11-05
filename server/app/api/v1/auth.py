"""
Authentication API Endpoints
User login, registration, token refresh
"""

from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import structlog

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
    decode_token,
)
from app.core.config import settings

logger = structlog.get_logger()
router = APIRouter()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register a new user
    """
    # Validate password strength
    if not validate_password_strength(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters "
                   "and contain uppercase, lowercase, digit, and special character",
        )

    # TODO: Check if user already exists
    # TODO: Create user in database

    logger.info("User registered", email=user_data.email)

    return {
        "message": "User registered successfully",
        "email": user_data.email,
    }


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    User login with email and password
    Returns access and refresh tokens
    """
    # TODO: Fetch user from database
    # Mock authentication for now
    if form_data.username != "admin@cybersentinel.local" or form_data.password != "ChangeMe123!":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": "user-123",
            "email": form_data.username,
            "role": "admin",
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": "user-123",
            "email": form_data.username,
        }
    )

    logger.info("User logged in", email=form_data.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    """
    try:
        payload = decode_token(request.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Create new tokens
        access_token = create_access_token(
            data={
                "sub": payload["sub"],
                "email": payload["email"],
                "role": payload.get("role", "viewer"),
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": payload["sub"],
                "email": payload["email"],
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout")
async def logout():
    """
    User logout
    """
    # TODO: Invalidate token (add to blacklist in Redis)
    return {"message": "Logged out successfully"}
