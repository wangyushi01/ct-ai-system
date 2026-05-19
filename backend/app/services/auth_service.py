"""认证服务"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.core.logger import logger


class AuthService:
    """认证服务"""

    @staticmethod
    async def register(
        db: AsyncSession,
        user_data: UserCreate
    ) -> User:
        """用户注册"""
        # 检查用户名是否存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ValueError("用户名已存在")

        # 检查邮箱是否存在
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("邮箱已被注册")

        # 创建用户
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            department=user_data.department,
            phone=user_data.phone,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"新用户注册: {user.username}")
        return user

    @staticmethod
    async def login(
        db: AsyncSession,
        login_data: UserLogin
    ) -> Token:
        """用户登录"""
        # 查找用户
        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalar_one_or_none()

        # 验证密码
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise ValueError("用户名或密码错误")

        if not user.is_active:
            raise ValueError("用户已被禁用")

        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        await db.commit()

        # 创建令牌
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"用户登录: {user.username}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        user_id: str
    ) -> Optional[User]:
        """获取当前用户"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user: User,
        update_data: dict
    ) -> User:
        """更新用户信息"""
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        logger.info(f"更新用户信息: {user.username}")
        return user
