#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
from typing import List, Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "HB-Panel"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 安全配置
    SECRET_KEY: str = "hb-panel-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./hb_panel.db"
    
    # CORS配置
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Redis配置
    REDIS_URL: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/hb-panel.log"
    
    # 系统配置
    SYSTEM_USER: str = "root"
    TEMP_DIR: str = "/tmp/hb-panel"
    
    # 软件包管理配置
    PACKAGE_CACHE_DIR: str = "/var/cache/hb-panel/packages"
    PACKAGE_INSTALL_TIMEOUT: int = 300  # 5分钟
    
    # Web环境配置
    WEB_ROOT: str = "/var/www/html"
    NGINX_CONF_DIR: str = "/etc/nginx"
    APACHE_CONF_DIR: str = "/etc/apache2"
    PHP_CONF_DIR: str = "/etc/php"
    MYSQL_CONF_DIR: str = "/etc/mysql"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_database_url() -> str:
    """获取数据库连接URL"""
    return settings.DATABASE_URL


def get_redis_url() -> Optional[str]:
    """获取Redis连接URL"""
    return settings.REDIS_URL


def is_production() -> bool:
    """判断是否为生产环境"""
    return not settings.DEBUG


def get_log_config() -> dict:
    """获取日志配置"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": settings.LOG_FILE,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["default", "file"],
        },
    }
