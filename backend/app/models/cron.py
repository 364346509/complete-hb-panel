#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计划任务数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class CronStatus(enum.Enum):
    """计划任务状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class CronType(enum.Enum):
    """计划任务类型枚举"""
    SHELL = "shell"
    BACKUP = "backup"
    LOG_CLEAN = "log_clean"
    WEBSITE_BACKUP = "website_backup"
    DATABASE_BACKUP = "database_backup"
    SYSTEM_CLEAN = "system_clean"
    CUSTOM = "custom"


class CronTask(Base):
    """计划任务模型"""
    __tablename__ = "cron_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(CronType), default=CronType.SHELL)
    command = Column(Text, nullable=False)
    cron_expression = Column(String(100), nullable=False)  # cron表达式
    status = Column(Enum(CronStatus), default=CronStatus.ACTIVE)
    
    # 执行配置
    timeout = Column(Integer, default=3600)  # 超时时间(秒)
    retry_count = Column(Integer, default=0)  # 重试次数
    save_log = Column(Boolean, default=True)  # 是否保存日志
    
    # 统计信息
    total_runs = Column(Integer, default=0)
    success_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    
    # 其他信息
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    logs = relationship("CronLog", back_populates="task")


class CronLog(Base):
    """计划任务执行日志模型"""
    __tablename__ = "cron_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("cron_tasks.id"), nullable=False)
    status = Column(String(20), nullable=False)  # success, failed, timeout
    output = Column(Text)  # 执行输出
    error_output = Column(Text)  # 错误输出
    execution_time = Column(Integer)  # 执行时间(秒)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    task = relationship("CronTask", back_populates="logs")


class SystemCronTemplate(Base):
    """系统计划任务模板"""
    __tablename__ = "system_cron_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(CronType), nullable=False)
    command_template = Column(Text, nullable=False)
    default_cron = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 分类：备份、清理、监控等
    is_system = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class BackupTask(Base):
    """备份任务模型"""
    __tablename__ = "backup_tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # website, database, system
    target_id = Column(Integer)  # 目标ID（网站ID或数据库ID）
    backup_path = Column(String(500), nullable=False)
    compression = Column(String(20), default="gzip")
    keep_days = Column(Integer, default=7)
    
    # 备份配置
    include_files = Column(Boolean, default=True)
    include_database = Column(Boolean, default=True)
    exclude_patterns = Column(Text)  # 排除模式，JSON格式
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    last_backup = Column(DateTime)
    last_size = Column(Integer, default=0)
    total_backups = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BackupRecord(Base):
    """备份记录模型"""
    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("backup_tasks.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    status = Column(String(20), default="completed")  # running, completed, failed
    error_message = Column(Text)
    
    # 时间信息
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    task = relationship("BackupTask")
