#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.service_service import ServiceService

router = APIRouter()


class ServiceResponse(BaseModel):
    """服务响应模型"""
    id: int
    name: str
    display_name: str
    description: str
    status: str
    enabled: bool
    pid: int = None
    memory_usage: int = None
    cpu_usage: float = None
    start_time: str = None
    
    class Config:
        from_attributes = True


class ServiceActionRequest(BaseModel):
    """服务操作请求模型"""
    action: str  # start, stop, restart, enable, disable


@router.get("/", response_model=List[ServiceResponse])
async def get_services(
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取系统服务列表"""
    service_service = ServiceService(db)
    services = await service_service.get_services(search=search, status=status)
    return services


@router.get("/{service_name}", response_model=ServiceResponse)
async def get_service(
    service_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单个服务详情"""
    service_service = ServiceService(db)
    service = await service_service.get_service(service_name)
    
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    return service


@router.post("/{service_name}/action")
async def service_action(
    service_name: str,
    request: ServiceActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行服务操作"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    service_service = ServiceService(db)
    
    try:
        result = await service_service.execute_action(service_name, request.action)
        return {
            "success": result,
            "message": f"服务 {service_name} {request.action} 操作{'成功' if result else '失败'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_name}/logs")
async def get_service_logs(
    service_name: str,
    lines: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取服务日志"""
    service_service = ServiceService(db)
    logs = await service_service.get_service_logs(service_name, lines)
    return {"logs": logs}


@router.post("/refresh")
async def refresh_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刷新服务列表"""
    service_service = ServiceService(db)
    await service_service.refresh_services()
    return {"message": "服务列表已刷新"}
