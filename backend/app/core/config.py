"""配置管理模块"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "CT影像AI分析系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ct_ai_db"
    DATABASE_TEST_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ct_ai_test"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "ct-images"
    MINIO_SECURE: bool = False

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".dcm", ".zip"}

    # AI模型配置
    MODEL_PATH: str = "./models"
    DEVICE: str = "cuda"  # cuda or cpu
    BATCH_SIZE: int = 4

    # Agent配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    ANTHROPIC_API_KEY: Optional[str] = None

    # DeepSeek配置（兼容OpenAI接口）
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    USE_MOCK_AI: bool = True  # 开发环境使用模拟AI

    # Celery配置
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # WebSocket配置
    WS_MESSAGE_QUEUE: str = "ws_messages"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# 创建全局配置实例
settings = Settings()
