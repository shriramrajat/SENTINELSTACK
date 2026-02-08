from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from sentinelstack.database import get_db
from sentinelstack.auth.schemas import UserCreate, UserResponse, Token
from sentinelstack.auth.service import AuthService
from sentinelstack.auth.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.create_user(user_in)

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id, role=user.role)
    return {"access_token": access_token, "token_type": "bearer"}