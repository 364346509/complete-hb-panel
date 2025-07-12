#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计划任务管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.models.cron import CronTask, CronLog, CronStatus, CronType, BackupTask
from app.services.cron_service import CronService

router = APIRouter()


class CronTaskCreateRequest(BaseModel):
    """计划任务创建请求模型"""
    name: str
    type: CronType = CronType.SHELL
    command: str
    cron_expression: str
    timeout: int = 3600
    retry_count: int = 0
    save_log: bool = True
    description: Optional[str] = None


class CronTaskUpdateRequest(BaseModel):
    """计划任务更新请求模型"""
    name: Optional[str] = None
    command: Optional[str] = None
    cron_expression: Optional[str] = None
    status: Optional[CronStatus] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None
    save_log: Optional[bool] = None
    description: Optional[str] = None


class CronTaskResponse(BaseModel):
    """计划任务响应模型"""
    id: int
    name: str
    type: str
    command: str
    cron_expression: str
    status: str
    timeout: int
    retry_count: int
    save_log: bool
    total_runs: int
    success_runs: int
    failed_runs: int
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class BackupTaskCreateRequest(BaseModel):
    """备份任务创建请求模型"""
    name: str
    type: str  # website, database, system
    target_id: Optional[int] = None
    backup_path: str
    compression: str = "gzip"
    keep_days: int = 7
    include_files: bool = True
    include_database: bool = True
    exclude_patterns: Optional[List[str]] = None


class BackupTaskResponse(BaseModel):
    """备份任务响应模型"""
    id: int
    name: str
    type: str
    target_id: Optional[int] = None
    backup_path: str
    compression: str
    keep_days: int
    include_files: bool
    include_database: bool
    is_active: bool
    last_backup: Optional[str] = None
    last_size: int
    total_backups: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/tasks", response_model=List[CronTaskResponse])
async def get_cron_tasks(
    search: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取计划任务列表"""
    cron_service = CronService(db)
    tasks = await cron_service.get_cron_tasks(
        search=search,
        task_type=type,
        status=status,
        page=page,
        size=size
    )
    return tasks


@router.post("/tasks", response_model=CronTaskResponse)
async def create_cron_task(
    task_data: CronTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建计划任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    try:
        task = await cron_service.create_cron_task(task_data.dict(), current_user.id)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建计划任务失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=CronTaskResponse)
async def get_cron_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取计划任务详情"""
    cron_service = CronService(db)
    task = await cron_service.get_cron_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="计划任务不存在")
    
    return task


@router.put("/tasks/{task_id}", response_model=CronTaskResponse)
async def update_cron_task(
    task_id: int,
    task_data: CronTaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新计划任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    try:
        task = await cron_service.update_cron_task(
            task_id, 
            task_data.dict(exclude_unset=True)
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新计划任务失败: {str(e)}")


@router.delete("/tasks/{task_id}")
async def delete_cron_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除计划任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    try:
        await cron_service.delete_cron_task(task_id)
        return {"message": "计划任务删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除计划任务失败: {str(e)}")


@router.post("/tasks/{task_id}/run")
async def run_cron_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动执行计划任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    # 检查任务是否存在
    task = await cron_service.get_cron_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="计划任务不存在")
    
    # 在后台执行任务
    background_tasks.add_task(
        cron_service.execute_task,
        task_id
    )
    
    return {"message": "任务已启动执行"}


@router.post("/tasks/{task_id}/toggle")
async def toggle_cron_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启用/禁用计划任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    try:
        task = await cron_service.toggle_cron_task(task_id)
        return {"message": f"任务已{'启用' if task.status == CronStatus.ACTIVE else '禁用'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")


@router.get("/tasks/{task_id}/logs")
async def get_cron_task_logs(
    task_id: int,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取计划任务执行日志"""
    cron_service = CronService(db)
    logs = await cron_service.get_task_logs(task_id, page, size)
    return logs


@router.get("/templates")
async def get_cron_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取计划任务模板"""
    cron_service = CronService(db)
    templates = await cron_service.get_cron_templates()
    return templates


@router.get("/backups", response_model=List[BackupTaskResponse])
async def get_backup_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取备份任务列表"""
    cron_service = CronService(db)
    tasks = await cron_service.get_backup_tasks()
    return tasks


@router.post("/backups", response_model=BackupTaskResponse)
async def create_backup_task(
    task_data: BackupTaskCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建备份任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    try:
        task = await cron_service.create_backup_task(task_data.dict())
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份任务失败: {str(e)}")


@router.post("/backups/{task_id}/run")
async def run_backup_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动执行备份任务"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    cron_service = CronService(db)
    
    # 在后台执行备份
    background_tasks.add_task(
        cron_service.execute_backup,
        task_id
    )
    
    return {"message": "备份任务已启动"}


@router.get("/system/status")
async def get_cron_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取计划任务系统状态"""
    cron_service = CronService(db)
    status = await cron_service.get_system_status()
    return status
