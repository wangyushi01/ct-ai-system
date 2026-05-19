"""日志配置模块"""
import logging
import sys
from pathlib import Path
from app.core.config import settings


def setup_logger() -> logging.Logger:
    """设置日志"""
    # 创建logger
    logger = logging.getLogger("ct-ai")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 清除现有handlers
    logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 错误日志handler
    error_handler = logging.FileHandler(
        log_dir / "error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# 创建全局logger
logger = setup_logger()
