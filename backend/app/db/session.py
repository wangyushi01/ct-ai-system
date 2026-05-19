"""数据库会话管理"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from app.core.config import settings
from app.core.logger import logger

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基类
Base = declarative_base()


async def get_db() -> Generator:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"数据库错误: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        # 导入所有模型
        from app.models import user, study, report, analysis

        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建成功")


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("数据库连接已关闭")
