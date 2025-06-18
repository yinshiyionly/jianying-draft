from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用程序配置类

    用于管理应用程序的所有配置项，包括基础设置、数据库配置、API配置、
    下载配置、同步配置、界面配置以及异常处理配置等。
    继承自pydantic.BaseSettings，支持从环境变量和.env文件加载配置。
    """
    
    # 应用配置
    APP_NAME: str = "草稿箱管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_DATABASE: str = "draft_box"

    # API配置
    API_TOKEN: Optional[str] = None
    API_BASE_URL: str = "https://api.example.com"
    API_TIMEOUT: int = 30
    API_RETRY_COUNT: int = 3

    # 下载配置
    DOWNLOAD_CONCURRENT_COUNT: int = 5
    DOWNLOAD_CHUNK_SIZE: int = 8192
    DOWNLOAD_TIMEOUT: int = 300

    # 同步配置
    SYNC_INTERVAL_SECONDS: int = 10
    SYNC_RETRY_COUNT: int = 3

    # 界面配置
    WINDOW_WIDTH: int = 1200
    WINDOW_HEIGHT: int = 800
    WINDOW_MIN_WIDTH: int = 800
    WINDOW_MIN_HEIGHT: int = 600
    THEME: str = "light"
    AUTO_SAVE_WINDOW_STATE: bool = True

    # 日志配置
    LOG_DIR: str = os.path.join(os.path.expanduser("~"), ".jy_draft", "logs")
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    LOG_FILE_PREFIX: str = "app"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5

    # 异常处理配置
    SHOW_DETAILED_ERRORS: bool = True
    AUTO_REPORT_ERRORS: bool = False
    ERROR_LOG_MAX_SIZE: str = "10MB"
    ERROR_LOG_BACKUP_COUNT: int = 5

    class Config:
        """配置类设置

        case_sensitive: 区分大小写
        env_file: 环境变量文件路径
        """
        case_sensitive = True
        env_file = ".env"


settings = Settings()  # 创建全局配置实例