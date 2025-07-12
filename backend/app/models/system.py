#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统相关数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class SystemInfo(Base):
    """系统信息模型"""
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(100))
    os_name = Column(String(50))
    os_version = Column(String(50))
    kernel_version = Column(String(100))
    architecture = Column(String(20))
    cpu_model = Column(String(200))
    cpu_cores = Column(Integer)
    total_memory = Column(Integer)  # MB
    total_disk = Column(Integer)    # GB
    uptime = Column(Integer)        # 秒
    load_average = Column(String(50))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemMonitor(Base):
    """系统监控数据模型"""
    __tablename__ = "system_monitor"

    id = Column(Integer, primary_key=True, index=True)
    cpu_usage = Column(Float)       # CPU使用率
    memory_usage = Column(Float)    # 内存使用率
    disk_usage = Column(Float)      # 磁盘使用率
    network_in = Column(Integer)    # 网络入流量 bytes/s
    network_out = Column(Integer)   # 网络出流量 bytes/s
    load_1min = Column(Float)       # 1分钟负载
    load_5min = Column(Float)       # 5分钟负载
    load_15min = Column(Float)      # 15分钟负载
    timestamp = Column(DateTime, server_default=func.now())


class Service(Base):
    """系统服务模型"""
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    status = Column(String(20))     # active, inactive, failed
    enabled = Column(Boolean)       # 是否开机自启
    service_type = Column(String(50))  # systemd, sysv, etc
    pid = Column(Integer)
    memory_usage = Column(Integer)  # KB
    cpu_usage = Column(Float)
    start_time = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Process(Base):
    """进程信息模型"""
    __tablename__ = "processes"

    id = Column(Integer, primary_key=True, index=True)
    pid = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(200))
    cmdline = Column(Text)
    username = Column(String(50))
    status = Column(String(20))
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    memory_rss = Column(Integer)    # KB
    memory_vms = Column(Integer)    # KB
    create_time = Column(DateTime)
    num_threads = Column(Integer)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
