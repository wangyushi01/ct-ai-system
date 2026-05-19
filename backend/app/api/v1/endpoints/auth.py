"""认证相关API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.schemas.user import UserCreate, UserLogin, Token, User
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册

    创建新用户账号
    """
    try:
        user = await AuthService.register(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录

    使用用户名和密码登录，返回访问令牌
    """
    try:
        token = await AuthService.login(db, login_data)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=User)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户信息

    返回当前登录用户的详细信息
    """
    return current_user
