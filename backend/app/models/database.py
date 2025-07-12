#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DatabaseStatus(enum.Enum):
    """数据库状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Database(Base):
    """数据库模型"""
    __tablename__ = "databases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    charset = Column(String(32), default="utf8mb4")
    collation = Column(String(64), default="utf8mb4_unicode_ci")
    status = Column(Enum(DatabaseStatus), default=DatabaseStatus.ACTIVE)
    
    # 统计信息
    size = Column(Integer, default=0)  # 字节
    table_count = Column(Integer, default=0)
    last_backup = Column(DateTime)
    
    # 配置信息
    description = Column(Text)
    auto_backup = Column(Boolean, default=False)
    backup_keep_days = Column(Integer, default=7)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    users = relationship("DatabaseUser", back_populates="database")
    backups = relationship("DatabaseBackup", back_populates="database")
    websites = relationship("WebsiteDatabase", back_populates="database")


class DatabaseUser(Base):
    """数据库用户模型"""
    __tablename__ = "database_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    
    # 权限配置
    privileges = Column(Text)  # JSON格式的权限列表
    host = Column(String(255), default="%")
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    database = relationship("Database", back_populates="users")


class DatabaseBackup(Base):
    """数据库备份模型"""
    __tablename__ = "database_backups"

    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id"), nullable=False)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    
    # 备份信息
    backup_type = Column(String(20), default="full")  # full, incremental
    compression = Column(String(20), default="gzip")  # gzip, none
    
    # 状态信息
    status = Column(String(20), default="completed")  # pending, running, completed, failed
    error_message = Column(Text)
    
    # 时间信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    database = relationship("Database", back_populates="backups")


class DatabaseConnection(Base):
    """数据库连接配置模型"""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    host = Column(String(255), default="localhost")
    port = Column(Integer, default=3306)
    username = Column(String(64), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 连接配置
    max_connections = Column(Integer, default=100)
    timeout = Column(Integer, default=30)
    charset = Column(String(32), default="utf8mb4")
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    last_test = Column(DateTime)
    test_result = Column(String(20))  # success, failed
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DatabaseOperation(Base):
    """数据库操作日志模型"""
    __tablename__ = "database_operations"

    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id"))
    operation_type = Column(String(50), nullable=False)  # create, drop, backup, restore, optimize
    operation_sql = Column(Text)
    
    # 执行信息
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")  # pending, running, success, failed
    result_message = Column(Text)
    execution_time = Column(Float)  # 执行时间(秒)
    
    # 时间信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    database = relationship("Database")


class MySQLConfig(Base):
    """MySQL配置模型"""
    __tablename__ = "mysql_configs"

    id = Column(Integer, primary_key=True, index=True)
    config_name = Column(String(100), unique=True, index=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(50), nullable=False)  # server, client, mysql, mysqldump
    
    # 配置信息
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    requires_restart = Column(Boolean, default=False)
    
    # 版本信息
    mysql_version = Column(String(20))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class DatabaseMonitor(Base):
    """数据库监控数据模型"""
    __tablename__ = "database_monitors"

    id = Column(Integer, primary_key=True, index=True)
    database_id = Column(Integer, ForeignKey("databases.id"))
    
    # 性能指标
    connections = Column(Integer, default=0)
    queries_per_second = Column(Float, default=0.0)
    slow_queries = Column(Integer, default=0)
    
    # 存储指标
    data_size = Column(Integer, default=0)
    index_size = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    
    # 缓存指标
    buffer_pool_hit_rate = Column(Float, default=0.0)
    query_cache_hit_rate = Column(Float, default=0.0)
    
    # 锁定指标
    table_locks_waited = Column(Integer, default=0)
    innodb_row_lock_waits = Column(Integer, default=0)
    
    # 时间信息
    recorded_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    database = relationship("Database")


# 导入到主模块
from app.models.website import WebsiteDatabase
