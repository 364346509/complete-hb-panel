#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.models.database import Database, DatabaseUser, DatabaseBackup, DatabaseStatus
from app.services.database_service import DatabaseService

router = APIRouter()


class DatabaseCreateRequest(BaseModel):
    """数据库创建请求模型"""
    name: str
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"
    description: Optional[str] = None
    auto_backup: bool = False
    backup_keep_days: int = 7


class DatabaseUserCreateRequest(BaseModel):
    """数据库用户创建请求模型"""
    username: str
    password: str
    database_id: int
    privileges: List[str] = ["SELECT", "INSERT", "UPDATE", "DELETE"]
    host: str = "%"


class DatabaseBackupRequest(BaseModel):
    """数据库备份请求模型"""
    database_ids: List[int]
    backup_type: str = "full"
    compression: str = "gzip"


class DatabaseResponse(BaseModel):
    """数据库响应模型"""
    id: int
    name: str
    charset: str
    collation: str
    status: str
    size: int
    table_count: int
    description: Optional[str] = None
    auto_backup: bool
    backup_keep_days: int
    last_backup: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DatabaseStatsResponse(BaseModel):
    """数据库统计响应模型"""
    total: int
    total_size: int
    users: int
    backups: int


class DatabaseUserResponse(BaseModel):
    """数据库用户响应模型"""
    id: int
    username: str
    database_id: int
    privileges: List[str]
    host: str
    is_active: bool
    last_login: Optional[str] = None
    login_count: int
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/stats", response_model=DatabaseStatsResponse)
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库统计信息"""
    database_service = DatabaseService(db)
    stats = await database_service.get_database_stats()
    return stats


@router.get("/", response_model=List[DatabaseResponse])
async def get_databases(
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库列表"""
    database_service = DatabaseService(db)
    databases = await database_service.get_databases(
        search=search,
        page=page,
        size=size
    )
    return databases


@router.post("/", response_model=DatabaseResponse)
async def create_database(
    database_data: DatabaseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库名称是否已存在
    if await database_service.database_exists(database_data.name):
        raise HTTPException(status_code=400, detail="数据库名称已存在")
    
    try:
        database = await database_service.create_database(database_data.dict())
        return database
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据库失败: {str(e)}")


@router.get("/{database_id}", response_model=DatabaseResponse)
async def get_database(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库详情"""
    database_service = DatabaseService(db)
    database = await database_service.get_database(database_id)
    
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    return database


@router.delete("/{database_id}")
async def delete_database(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    try:
        await database_service.delete_database(database_id)
        return {"message": "数据库删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据库失败: {str(e)}")


@router.post("/{database_id}/backup")
async def backup_database(
    database_id: int,
    backup_type: str = "full",
    compression: str = "gzip",
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """备份数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    # 在后台执行备份
    background_tasks.add_task(
        database_service.backup_database,
        database_id,
        backup_type,
        compression
    )
    
    return {"message": "备份任务已启动"}


@router.post("/batch-backup")
async def batch_backup_databases(
    backup_request: DatabaseBackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量备份数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 在后台执行批量备份
    background_tasks.add_task(
        database_service.batch_backup_databases,
        backup_request.database_ids,
        backup_request.backup_type,
        backup_request.compression
    )
    
    return {"message": "批量备份任务已启动"}


@router.post("/{database_id}/optimize")
async def optimize_database(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """优化数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    try:
        result = await database_service.optimize_database(database_id)
        return {"message": "数据库优化完成", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库优化失败: {str(e)}")


@router.post("/{database_id}/repair")
async def repair_database(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修复数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    try:
        result = await database_service.repair_database(database_id)
        return {"message": "数据库修复完成", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库修复失败: {str(e)}")


@router.get("/{database_id}/users", response_model=List[DatabaseUserResponse])
async def get_database_users(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库用户列表"""
    database_service = DatabaseService(db)
    users = await database_service.get_database_users(database_id)
    return users


@router.post("/{database_id}/users", response_model=DatabaseUserResponse)
async def create_database_user(
    database_id: int,
    user_data: DatabaseUserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建数据库用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    # 检查用户名是否已存在
    if await database_service.database_user_exists(user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    try:
        user_data.database_id = database_id
        user = await database_service.create_database_user(user_data.dict())
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建数据库用户失败: {str(e)}")


@router.delete("/{database_id}/users/{user_id}")
async def delete_database_user(
    database_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除数据库用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    try:
        await database_service.delete_database_user(user_id)
        return {"message": "数据库用户删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据库用户失败: {str(e)}")


@router.get("/{database_id}/backups")
async def get_database_backups(
    database_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取数据库备份列表"""
    database_service = DatabaseService(db)
    backups = await database_service.get_database_backups(database_id)
    return backups


@router.post("/{database_id}/export")
async def export_database(
    database_id: int,
    format: str = "sql",
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导出数据库"""
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    # 在后台执行导出
    background_tasks.add_task(
        database_service.export_database,
        database_id,
        format
    )
    
    return {"message": "导出任务已启动"}


@router.post("/{database_id}/import")
async def import_database(
    database_id: int,
    sql_file: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """导入数据库"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    database_service = DatabaseService(db)
    
    # 检查数据库是否存在
    database = await database_service.get_database(database_id)
    if not database:
        raise HTTPException(status_code=404, detail="数据库不存在")
    
    # 在后台执行导入
    background_tasks.add_task(
        database_service.import_database,
        database_id,
        sql_file
    )
    
    return {"message": "导入任务已启动"}
