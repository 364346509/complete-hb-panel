#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站管理数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class WebsiteStatus(enum.Enum):
    """网站状态枚举"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class SSLType(enum.Enum):
    """SSL证书类型枚举"""
    NONE = "none"
    LETS_ENCRYPT = "lets_encrypt"
    SELF_SIGNED = "self_signed"
    CUSTOM = "custom"


class BackupType(enum.Enum):
    """备份类型枚举"""
    FULL = "full"
    FILES = "files"
    DATABASE = "database"


class Website(Base):
    """网站模型"""
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(255), nullable=False)
    domains = Column(Text)  # JSON格式的域名列表
    path = Column(String(500), nullable=False)
    php_version = Column(String(10), default="7.4")
    status = Column(Enum(WebsiteStatus), default=WebsiteStatus.RUNNING)
    
    # SSL配置
    ssl_type = Column(Enum(SSLType), default=SSLType.NONE)
    ssl_cert = Column(Text)
    ssl_key = Column(Text)
    ssl_auto_renew = Column(Boolean, default=False)
    
    # 网站配置
    index_files = Column(String(200), default="index.html,index.htm,index.php")
    rewrite_rule = Column(Text)  # 伪静态规则
    proxy_cache = Column(Boolean, default=False)
    gzip_enable = Column(Boolean, default=True)
    
    # 访问控制
    password_protect = Column(Boolean, default=False)
    password_user = Column(String(50))
    password_hash = Column(String(255))
    ip_whitelist = Column(Text)  # JSON格式的IP白名单
    ip_blacklist = Column(Text)  # JSON格式的IP黑名单
    
    # 统计信息
    total_requests = Column(Integer, default=0)
    total_traffic = Column(Integer, default=0)  # 字节
    last_access = Column(DateTime)
    
    # 备份配置
    backup_enable = Column(Boolean, default=False)
    backup_keep_days = Column(Integer, default=7)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    databases = relationship("WebsiteDatabase", back_populates="website")
    backups = relationship("WebsiteBackup", back_populates="website")


class WebsiteDatabase(Base):
    """网站数据库关联模型"""
    __tablename__ = "website_databases"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    website = relationship("Website", back_populates="databases")
    database = relationship("Database", back_populates="websites")


class WebsiteBackup(Base):
    """网站备份模型"""
    __tablename__ = "website_backups"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(20), nullable=False)  # full, files, database
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    website = relationship("Website", back_populates="backups")


class WebsiteLog(Base):
    """网站访问日志模型"""
    __tablename__ = "website_logs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    request_method = Column(String(10))
    request_uri = Column(String(1000))
    status_code = Column(Integer)
    response_size = Column(Integer)
    referer = Column(String(1000))
    request_time = Column(DateTime, server_default=func.now())
    
    # 索引
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )


class SSLCertificate(Base):
    """SSL证书模型"""
    __tablename__ = "ssl_certificates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(255), nullable=False)
    domains = Column(Text)  # JSON格式的域名列表
    type = Column(Enum(SSLType), nullable=False)
    
    # 证书内容
    certificate = Column(Text, nullable=False)
    private_key = Column(Text, nullable=False)
    ca_bundle = Column(Text)
    
    # 证书信息
    issuer = Column(String(200))
    subject = Column(String(200))
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    
    # Let's Encrypt配置
    acme_account = Column(String(100))
    auto_renew = Column(Boolean, default=False)
    renew_days = Column(Integer, default=30)
    
    # 状态
    is_active = Column(Boolean, default=True)
    last_check = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class RewriteRule(Base):
    """伪静态规则模板模型"""
    __tablename__ = "rewrite_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(500))
    type = Column(String(50))  # wordpress, thinkphp, laravel, etc
    nginx_rule = Column(Text)
    apache_rule = Column(Text)
    is_builtin = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class PHPVersion(Base):
    """PHP版本管理模型"""
    __tablename__ = "php_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(10), unique=True, index=True, nullable=False)
    path = Column(String(200), nullable=False)
    config_path = Column(String(200))
    fpm_config_path = Column(String(200))
    is_installed = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    
    # 扩展配置
    extensions = Column(Text)  # JSON格式的已安装扩展列表
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
