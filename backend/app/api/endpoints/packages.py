#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件包管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.package_service import PackageService

router = APIRouter()


class PackageResponse(BaseModel):
    """软件包响应模型"""
    id: int
    name: str
    display_name: str
    description: str
    category: str
    version: str
    installed_version: str = None
    status: str
    size: int
    homepage: str = None
    
    class Config:
        from_attributes = True


class PackageInstallRequest(BaseModel):
    """软件包安装请求模型"""
    package_name: str
    action: str  # install, uninstall, upgrade


class InstallTaskResponse(BaseModel):
    """安装任务响应模型"""
    task_id: str
    package_name: str
    action: str
    status: str
    progress: int
    log_output: str = None
    error_message: str = None
    
    class Config:
        from_attributes = True


@router.get("/categories")
async def get_package_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取软件包分类"""
    package_service = PackageService(db)
    categories = await package_service.get_categories()
    return categories


@router.get("/", response_model=List[PackageResponse])
async def get_packages(
    category: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取软件包列表"""
    package_service = PackageService(db)
    packages = await package_service.get_packages(
        category=category,
        search=search,
        status=status,
        page=page,
        size=size
    )
    return packages


@router.get("/installed", response_model=List[PackageResponse])
async def get_installed_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取已安装软件包列表"""
    package_service = PackageService(db)
    packages = await package_service.get_installed_packages()
    return packages


@router.post("/install")
async def install_package(
    request: PackageInstallRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """安装/卸载/升级软件包"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    package_service = PackageService(db)
    task = await package_service.create_install_task(
        package_name=request.package_name,
        action=request.action,
        user_id=current_user.id
    )
    
    # 在后台执行安装任务
    background_tasks.add_task(
        package_service.execute_install_task,
        task.task_id
    )
    
    return {
        "task_id": task.task_id,
        "message": f"已开始{request.action}任务"
    }


@router.get("/tasks/{task_id}", response_model=InstallTaskResponse)
async def get_install_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取安装任务状态"""
    package_service = PackageService(db)
    task = await package_service.get_install_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task


@router.get("/search")
async def search_packages(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索软件包"""
    package_service = PackageService(db)
    packages = await package_service.search_packages(query)
    return packages


@router.post("/refresh")
async def refresh_package_list(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刷新软件包列表"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    package_service = PackageService(db)
    background_tasks.add_task(package_service.refresh_package_list)
    
    return {"message": "正在刷新软件包列表"}


@router.get("/lamp/status")
async def get_lamp_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取LAMP环境状态"""
    package_service = PackageService(db)
    status = await package_service.get_lamp_status()
    return status


@router.post("/lamp/install")
async def install_lamp(
    environment_type: str,  # lamp, lemp, mixed
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """安装LAMP/LEMP环境"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    package_service = PackageService(db)
    task = await package_service.install_lamp_environment(
        environment_type=environment_type,
        user_id=current_user.id
    )
    
    background_tasks.add_task(
        package_service.execute_lamp_install,
        task.task_id
    )
    
    return {
        "task_id": task.task_id,
        "message": f"已开始安装{environment_type.upper()}环境"
    }
