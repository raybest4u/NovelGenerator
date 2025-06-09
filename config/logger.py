# config/logging.py
"""
日志配置模块
"""

import os
import sys
if "" in sys.path:
    sys.path.remove("")  # Remove current directory from path
from pathlib import Path

from loguru import logger

from config.settings import get_settings


def setup_logging():
    """设置日志配置"""
    settings = get_settings()

    # 移除默认处理器
    logger.remove()

    # 控制台日志
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.mcp.log_level,
        colorize=True
    )

    # 文件日志
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 应用日志
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="zip"
    )

    # 错误日志
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 week",
        retention="1 month",
        compression="zip"
    )

    # API访问日志
    logger.add(
        log_dir / "access.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="7 days",
        filter=lambda record: record["extra"].get("type") == "access"
    )

    # 性能日志
    logger.add(
        log_dir / "performance.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="1 day",
        retention="7 days",
        filter=lambda record: record["extra"].get("type") == "performance"
    )


class LoggerMixin:
    """日志混入类"""

    @property
    def logger(self):
        return logger.bind(name=self.__class__.__name__)





