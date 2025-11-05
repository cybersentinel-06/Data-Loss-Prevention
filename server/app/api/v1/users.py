"""
Users API Endpoints
User management and profile operations
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
import structlog

from app.core.security import get_current_user, require_role, get_password_hash

logger = structlog.get_logger()
router = APIRouter()


class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    role: str
    organization: str
    is_active: bool = True
    created_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's profile
    """
    # TODO: Fetch full user details from database
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": "Admin User",
        "role": current_user["role"],
        "organization": "CyberSentinel",
        "is_active": True,
        "created_at": datetime.now(),
    }


@router.get("/", response_model=List[User])
async def get_users(
    current_user: dict = Depends(require_role("admin")),
):
    """
    Get all users (admin only)
    """
    # TODO: Fetch from database
    return []


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Get specific user by ID
    """
    # TODO: Fetch from database
    raise HTTPException(status_code=404, detail="User not found")


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Update user (admin only)
    """
    # TODO: Update in database

    logger.info(
        "User updated",
        user_id=user_id,
        updated_by=current_user["email"],
    )

    raise HTTPException(status_code=404, detail="User not found")


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete user (admin only)
    """
    # TODO: Delete from database

    logger.info(
        "User deleted",
        user_id=user_id,
        deleted_by=current_user["email"],
    )

    return {"message": "User deleted successfully"}
