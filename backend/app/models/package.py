#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件包管理数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PackageStatus(enum.Enum):
    """软件包状态枚举"""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    UPGRADABLE = "upgradable"
    BROKEN = "broken"


class InstallStatus(enum.Enum):
    """安装状态枚举"""
    PENDING = "pending"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Package(Base):
    """软件包模型"""
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    category = Column(String(50))
    version = Column(String(50))
    installed_version = Column(String(50))
    status = Column(Enum(PackageStatus), default=PackageStatus.NOT_INSTALLED)
    size = Column(Integer)          # 包大小 KB
    dependencies = Column(Text)     # JSON格式的依赖列表
    homepage = Column(String(500))
    maintainer = Column(String(200))
    architecture = Column(String(20))
    priority = Column(String(20))
    section = Column(String(50))
    is_essential = Column(Boolean, default=False)
    is_auto_installed = Column(Boolean, default=False)
    install_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PackageCategory(Base):
    """软件包分类模型"""
    __tablename__ = "package_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100))
    description = Column(Text)
    icon = Column(String(100))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class InstallTask(Base):
    """安装任务模型"""
    __tablename__ = "install_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    package_name = Column(String(100), nullable=False)
    action = Column(String(20))     # install, uninstall, upgrade
    status = Column(Enum(InstallStatus), default=InstallStatus.PENDING)
    progress = Column(Integer, default=0)  # 进度百分比
    log_output = Column(Text)
    error_message = Column(Text)
    user_id = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class PackageRepository(Base):
    """软件源模型"""
    __tablename__ = "package_repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    url = Column(String(500), nullable=False)
    distribution = Column(String(50))
    components = Column(String(200))
    architecture = Column(String(50))
    is_enabled = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)
    priority = Column(Integer, default=500)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
