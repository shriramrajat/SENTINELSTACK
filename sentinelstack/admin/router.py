from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from sentinelstack.database import get_db
from sentinelstack.auth.models import User
from sentinelstack.auth.schemas import UserResponse
from sentinelstack.auth.dependencies import get_admin_user
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])

class TierUpdate(BaseModel):
    tier: str

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0, limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all users (Admin only)."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.patch("/users/{user_id}/tier", response_model=UserResponse)
async def update_user_tier(
    user_id: str,
    tier_update: TierUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update a user's rate limit tier (Admin only)."""
    if tier_update.tier not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.tier = tier_update.tier
    await db.commit()
    await db.refresh(user)
    return user
