#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.system_service import SystemService

router = APIRouter()


class SystemInfoResponse(BaseModel):
    """系统信息响应模型"""
    hostname: str
    os_name: str
    os_version: str
    kernel_version: str
    architecture: str
    cpu_model: str
    cpu_cores: int
    total_memory: int
    total_disk: int
    uptime: int
    load_average: str


class SystemStatsResponse(BaseModel):
    """系统统计响应模型"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: int
    network_out: int
    load_1min: float
    load_5min: float
    load_15min: float
    timestamp: datetime


class ProcessResponse(BaseModel):
    """进程响应模型"""
    pid: int
    name: str
    cmdline: str
    username: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_rss: int
    create_time: datetime
    num_threads: int


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统基本信息"""
    system_service = SystemService(db)
    info = await system_service.get_system_info()
    return info


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统实时统计信息"""
    system_service = SystemService(db)
    stats = await system_service.get_system_stats()
    return stats


@router.get("/stats/history")
async def get_system_stats_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统历史统计数据"""
    system_service = SystemService(db)
    history = await system_service.get_stats_history(hours)
    return history


@router.get("/processes", response_model=List[ProcessResponse])
async def get_processes(
    limit: int = 50,
    sort_by: str = "cpu_percent",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取进程列表"""
    system_service = SystemService(db)
    processes = await system_service.get_processes(limit, sort_by)
    return processes


@router.delete("/processes/{pid}")
async def kill_process(
    pid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """终止进程"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    system_service = SystemService(db)
    success = await system_service.kill_process(pid)
    
    if not success:
        raise HTTPException(status_code=404, detail="进程不存在或无法终止")
    
    return {"message": f"进程 {pid} 已终止"}


@router.get("/disk/usage")
async def get_disk_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取磁盘使用情况"""
    system_service = SystemService(db)
    disk_usage = await system_service.get_disk_usage()
    return disk_usage


@router.get("/network/interfaces")
async def get_network_interfaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取网络接口信息"""
    system_service = SystemService(db)
    interfaces = await system_service.get_network_interfaces()
    return interfaces


@router.get("/logs/system")
async def get_system_logs(
    lines: int = 100,
    level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统日志"""
    system_service = SystemService(db)
    logs = await system_service.get_system_logs(lines, level)
    return logs
