#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class LogLevel(enum.Enum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogType(enum.Enum):
    """日志类型枚举"""
    SYSTEM = "system"
    ACCESS = "access"
    ERROR = "error"
    SECURITY = "security"
    APPLICATION = "application"
    AUDIT = "audit"


class SystemLog(Base):
    """系统日志模型"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(Enum(LogType), nullable=False)
    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    source = Column(String(100), nullable=False)  # 日志来源
    message = Column(Text, nullable=False)
    
    # 详细信息
    details = Column(JSON)  # 详细信息JSON
    stack_trace = Column(Text)  # 堆栈跟踪
    
    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # 处理状态
    is_read = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())


class AccessLog(Base):
    """访问日志模型"""
    __tablename__ = "access_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    
    # 请求信息
    ip_address = Column(String(45), nullable=False)
    method = Column(String(10), nullable=False)
    url = Column(Text, nullable=False)
    protocol = Column(String(20))
    
    # 响应信息
    status_code = Column(Integer, nullable=False)
    response_size = Column(BigInteger, default=0)
    response_time = Column(Integer)  # 响应时间(毫秒)
    
    # 客户端信息
    user_agent = Column(Text)
    referer = Column(Text)
    
    # 地理位置信息
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    
    # 时间信息
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    website = relationship("Website")


class ErrorLog(Base):
    """错误日志模型"""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"))
    
    # 错误信息
    error_type = Column(String(100), nullable=False)
    error_message = Column(Text, nullable=False)
    file_path = Column(String(500))
    line_number = Column(Integer)
    
    # 请求信息
    request_url = Column(Text)
    request_method = Column(String(10))
    ip_address = Column(String(45))
    
    # 详细信息
    stack_trace = Column(Text)
    context = Column(JSON)  # 错误上下文
    
    # 统计信息
    occurrence_count = Column(Integer, default=1)
    first_occurrence = Column(DateTime, nullable=False)
    last_occurrence = Column(DateTime, nullable=False)
    
    # 处理状态
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    resolution_note = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    website = relationship("Website")


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 操作信息
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))  # website, database, user, etc.
    resource_id = Column(Integer)
    resource_name = Column(String(200))
    
    # 操作详情
    operation = Column(String(50), nullable=False)  # create, update, delete, etc.
    old_values = Column(JSON)  # 操作前的值
    new_values = Column(JSON)  # 操作后的值
    
    # 请求信息
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    request_id = Column(String(100))  # 请求ID
    
    # 结果信息
    status = Column(String(20), default="success")  # success, failed
    error_message = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    user = relationship("User")


class LogFile(Base):
    """日志文件模型"""
    __tablename__ = "log_files"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    log_type = Column(Enum(LogType), nullable=False)
    
    # 文件信息
    file_size = Column(BigInteger, default=0)
    line_count = Column(Integer, default=0)
    encoding = Column(String(20), default="utf-8")
    
    # 配置信息
    is_monitored = Column(Boolean, default=True)
    auto_rotate = Column(Boolean, default=True)
    max_size = Column(Integer, default=100)  # MB
    keep_days = Column(Integer, default=30)
    
    # 统计信息
    last_read = Column(DateTime)
    last_modified = Column(DateTime)
    read_position = Column(BigInteger, default=0)  # 读取位置
    
    # 关联信息
    website_id = Column(Integer, ForeignKey("websites.id"))
    service_name = Column(String(100))  # 服务名称
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LogAlert(Base):
    """日志告警模型"""
    __tablename__ = "log_alerts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    log_type = Column(Enum(LogType), nullable=False)
    
    # 告警条件
    pattern = Column(Text, nullable=False)  # 匹配模式
    threshold = Column(Integer, default=1)  # 阈值
    time_window = Column(Integer, default=300)  # 时间窗口(秒)
    
    # 告警配置
    is_active = Column(Boolean, default=True)
    severity = Column(Enum(LogLevel), default=LogLevel.WARNING)
    
    # 通知配置
    email_notify = Column(Boolean, default=False)
    webhook_notify = Column(Boolean, default=False)
    webhook_url = Column(String(500))
    
    # 统计信息
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class LogStatistics(Base):
    """日志统计模型"""
    __tablename__ = "log_statistics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False)  # 统计日期
    log_type = Column(Enum(LogType), nullable=False)
    
    # 统计数据
    total_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    
    # 访问统计（针对访问日志）
    unique_visitors = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    bandwidth = Column(BigInteger, default=0)  # 字节
    
    # 错误统计（针对错误日志）
    error_types = Column(JSON)  # 错误类型统计
    top_errors = Column(JSON)   # 热门错误
    
    # 关联信息
    website_id = Column(Integer, ForeignKey("websites.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 索引
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )
