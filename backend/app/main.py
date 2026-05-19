"""FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logger import logger
from app.api.v1.api import api_router
from app.db.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化数据库
    try:
        await init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 初始化MinIO
    try:
        from app.core.minio_client import init_minio
        await init_minio()
        logger.info("MinIO初始化成功")
    except Exception as e:
        logger.error(f"MinIO初始化失败: {e}")

    yield

    # 关闭
    logger.info("系统关闭中...")
    await close_db()
    logger.info("系统已关闭")


# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于AI Agent的CT影像智能分析系统",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
