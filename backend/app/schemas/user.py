"""用户相关Schema"""
from pydantic import BaseModel, EmailStr, Field, field_serializer
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    department: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """创建用户Schema"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """更新用户Schema"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: Any
    is_active: bool
    is_superuser: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime

    @field_serializer('id')
    def serialize_id(self, value: Any) -> str:
        """将UUID转换为字符串"""
        return str(value)

    class Config:
        from_attributes = True


class User(UserInDB):
    """用户响应Schema"""
    pass


class UserLogin(BaseModel):
    """用户登录Schema"""
    username: str
    password: str


class Token(BaseModel):
    """令牌Schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User


class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: str  # user_id
    exp: Optional[int] = None
