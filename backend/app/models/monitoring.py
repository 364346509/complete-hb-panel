#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控告警数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AlertLevel(enum.Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(enum.Enum):
    """告警状态枚举"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class MonitorType(enum.Enum):
    """监控类型枚举"""
    SYSTEM = "system"
    WEBSITE = "website"
    DATABASE = "database"
    SERVICE = "service"
    CUSTOM = "custom"


class NotificationChannel(enum.Enum):
    """通知渠道枚举"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"
    SLACK = "slack"


class MonitorRule(Base):
    """监控规则模型"""
    __tablename__ = "monitor_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    monitor_type = Column(Enum(MonitorType), nullable=False)
    metric_name = Column(String(100), nullable=False)  # cpu_usage, memory_usage, etc.
    
    # 监控目标
    target_type = Column(String(50))  # system, website, database, service
    target_id = Column(Integer)  # 目标ID
    target_name = Column(String(200))  # 目标名称
    
    # 告警条件
    operator = Column(String(10), nullable=False)  # >, <, >=, <=, ==, !=
    threshold = Column(Float, nullable=False)
    duration = Column(Integer, default=300)  # 持续时间(秒)
    
    # 告警配置
    alert_level = Column(Enum(AlertLevel), default=AlertLevel.WARNING)
    is_active = Column(Boolean, default=True)
    
    # 通知配置
    notification_channels = Column(JSON)  # 通知渠道列表
    notification_interval = Column(Integer, default=3600)  # 通知间隔(秒)
    
    # 统计信息
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime)
    last_value = Column(Float)
    
    # 其他配置
    description = Column(Text)
    recovery_threshold = Column(Float)  # 恢复阈值
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Alert(Base):
    """告警记录模型"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("monitor_rules.id"), nullable=False)
    
    # 告警信息
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(Enum(AlertLevel), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    
    # 触发信息
    trigger_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    metric_name = Column(String(100), nullable=False)
    
    # 目标信息
    target_type = Column(String(50))
    target_id = Column(Integer)
    target_name = Column(String(200))
    
    # 时间信息
    triggered_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
    acknowledged_at = Column(DateTime)
    
    # 处理信息
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    resolution_note = Column(Text)
    
    # 通知状态
    notification_sent = Column(Boolean, default=False)
    notification_count = Column(Integer, default=0)
    last_notification = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    rule = relationship("MonitorRule")


class SystemMetric(Base):
    """系统指标模型"""
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # 时间信息
    timestamp = Column(DateTime, nullable=False)
    
    # CPU指标
    cpu_usage = Column(Float, default=0.0)
    cpu_load_1m = Column(Float, default=0.0)
    cpu_load_5m = Column(Float, default=0.0)
    cpu_load_15m = Column(Float, default=0.0)
    
    # 内存指标
    memory_usage = Column(Float, default=0.0)
    memory_total = Column(Integer, default=0)
    memory_used = Column(Integer, default=0)
    memory_free = Column(Integer, default=0)
    memory_cached = Column(Integer, default=0)
    
    # 磁盘指标
    disk_usage = Column(Float, default=0.0)
    disk_total = Column(Integer, default=0)
    disk_used = Column(Integer, default=0)
    disk_free = Column(Integer, default=0)
    disk_read_bytes = Column(Integer, default=0)
    disk_write_bytes = Column(Integer, default=0)
    
    # 网络指标
    network_in_bytes = Column(Integer, default=0)
    network_out_bytes = Column(Integer, default=0)
    network_in_packets = Column(Integer, default=0)
    network_out_packets = Column(Integer, default=0)
    
    # 进程指标
    process_count = Column(Integer, default=0)
    thread_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())


class WebsiteMetric(Base):
    """网站指标模型"""
    __tablename__ = "website_metrics"

    id = Column(Integer, primary_key=True, index=True)
    website_id = Column(Integer, ForeignKey("websites.id"), nullable=False)
    
    # 时间信息
    timestamp = Column(DateTime, nullable=False)
    
    # 访问指标
    requests_count = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    bounce_rate = Column(Float, default=0.0)
    
    # 性能指标
    avg_response_time = Column(Float, default=0.0)
    max_response_time = Column(Float, default=0.0)
    min_response_time = Column(Float, default=0.0)
    
    # 状态码统计
    status_2xx = Column(Integer, default=0)
    status_3xx = Column(Integer, default=0)
    status_4xx = Column(Integer, default=0)
    status_5xx = Column(Integer, default=0)
    
    # 流量指标
    bandwidth_in = Column(Integer, default=0)
    bandwidth_out = Column(Integer, default=0)
    
    # 错误指标
    error_count = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    website = relationship("Website")


class ServiceMetric(Base):
    """服务指标模型"""
    __tablename__ = "service_metrics"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), nullable=False)
    
    # 时间信息
    timestamp = Column(DateTime, nullable=False)
    
    # 服务状态
    is_running = Column(Boolean, default=True)
    status = Column(String(50))
    
    # 性能指标
    cpu_usage = Column(Float, default=0.0)
    memory_usage = Column(Float, default=0.0)
    memory_rss = Column(Integer, default=0)
    memory_vms = Column(Integer, default=0)
    
    # 连接指标
    connections = Column(Integer, default=0)
    active_connections = Column(Integer, default=0)
    
    # 请求指标
    requests_per_second = Column(Float, default=0.0)
    avg_response_time = Column(Float, default=0.0)
    
    # 错误指标
    error_count = Column(Integer, default=0)
    error_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, server_default=func.now())


class NotificationTemplate(Base):
    """通知模板模型"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    alert_level = Column(Enum(AlertLevel), nullable=False)
    
    # 模板内容
    subject_template = Column(String(500))
    body_template = Column(Text, nullable=False)
    
    # 配置信息
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NotificationConfig(Base):
    """通知配置模型"""
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    
    # 配置参数
    config = Column(JSON, nullable=False)  # 配置参数JSON
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_test = Column(DateTime)
    test_result = Column(String(20))  # success, failed
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    
    # 通知内容
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    recipient = Column(String(200), nullable=False)
    
    # 发送状态
    status = Column(String(20), default="pending")  # pending, sent, failed
    error_message = Column(Text)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    alert = relationship("Alert")
