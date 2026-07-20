"""应用配置

使用 pydantic-settings 管理配置，支持环境变量和 .env 文件
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本信息
    app_name: str = "{app_title}"
    app_version: str = "0.1.0"
    debug: bool = True

    # 网络配置（如有）
    api_base_url: str = "https://api.example.com"
    api_timeout: int = 30

    # 存储
    storage_type: str = "json"  # json | sqlite

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
