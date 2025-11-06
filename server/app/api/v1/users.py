"""
Users API Endpoints
User management and profile operations
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.security import get_current_user, require_role, get_password_hash
from app.core.database import get_db
from app.services.user_service import UserService

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
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's profile
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(current_user["sub"])

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization": user.organization or "CyberSentinel",
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all users (admin only)
    """
    user_service = UserService(db)
    users = await user_service.get_all_users(
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    )

    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization": user.organization or "CyberSentinel",
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get specific user by ID
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization": user.organization or "CyberSentinel",
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user (admin only)
    """
    user_service = UserService(db)
    user = await user_service.update_user(
        user_id=user_id,
        full_name=user_update.full_name,
        role=user_update.role,
        is_active=user_update.is_active,
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        "User updated",
        user_id=user_id,
        updated_by=current_user["email"],
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization": user.organization or "CyberSentinel",
        "is_active": user.is_active,
        "created_at": user.created_at,
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete user (admin only - soft delete)
    """
    user_service = UserService(db)
    success = await user_service.delete_user(user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        "User deleted",
        user_id=user_id,
        deleted_by=current_user["email"],
    )

    return {"message": "User deleted successfully"}
