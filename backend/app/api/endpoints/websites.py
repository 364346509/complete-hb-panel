#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.models.website import Website, WebsiteStatus, SSLType
from app.services.website_service import WebsiteService

router = APIRouter()


class WebsiteCreateRequest(BaseModel):
    """网站创建请求模型"""
    name: str
    domain: str
    domains: List[str] = []
    php_version: str = "8.1"
    path: Optional[str] = None
    index_files: str = "index.html,index.htm,index.php"
    ssl_type: SSLType = SSLType.NONE
    ssl_auto_renew: bool = True
    gzip_enable: bool = True
    proxy_cache: bool = False
    backup_enable: bool = False
    backup_keep_days: int = 7
    # 数据库配置
    create_database: bool = False
    database_name: Optional[str] = None
    database_user: Optional[str] = None
    database_password: Optional[str] = None


class WebsiteUpdateRequest(BaseModel):
    """网站更新请求模型"""
    domain: Optional[str] = None
    domains: Optional[List[str]] = None
    php_version: Optional[str] = None
    index_files: Optional[str] = None
    ssl_type: Optional[SSLType] = None
    ssl_auto_renew: Optional[bool] = None
    gzip_enable: Optional[bool] = None
    proxy_cache: Optional[bool] = None
    backup_enable: Optional[bool] = None
    backup_keep_days: Optional[int] = None
    rewrite_rule: Optional[str] = None


class WebsiteResponse(BaseModel):
    """网站响应模型"""
    id: int
    name: str
    domain: str
    domains: List[str] = []
    path: str
    php_version: str
    status: str
    ssl_type: str
    ssl_auto_renew: bool
    gzip_enable: bool
    proxy_cache: bool
    backup_enable: bool
    backup_keep_days: int
    total_requests: int
    total_traffic: int
    last_access: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class WebsiteStatsResponse(BaseModel):
    """网站统计响应模型"""
    total: int
    running: int
    stopped: int
    ssl: int


@router.get("/stats", response_model=WebsiteStatsResponse)
async def get_website_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取网站统计信息"""
    website_service = WebsiteService(db)
    stats = await website_service.get_website_stats()
    return stats


@router.get("/", response_model=List[WebsiteResponse])
async def get_websites(
    search: Optional[str] = None,
    status: Optional[str] = None,
    php_version: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取网站列表"""
    website_service = WebsiteService(db)
    websites = await website_service.get_websites(
        search=search,
        status=status,
        php_version=php_version,
        page=page,
        size=size
    )
    return websites


@router.post("/", response_model=WebsiteResponse)
async def create_website(
    website_data: WebsiteCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建网站"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    
    # 检查网站名称是否已存在
    if await website_service.website_exists(website_data.name):
        raise HTTPException(status_code=400, detail="网站名称已存在")
    
    # 检查域名是否已被使用
    if await website_service.domain_exists(website_data.domain):
        raise HTTPException(status_code=400, detail="域名已被使用")
    
    try:
        website = await website_service.create_website(website_data.dict())
        
        # 在后台配置网站
        background_tasks.add_task(
            website_service.configure_website,
            website.id
        )
        
        return website
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建网站失败: {str(e)}")


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取网站详情"""
    website_service = WebsiteService(db)
    website = await website_service.get_website(website_id)
    
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    return website


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: int,
    website_data: WebsiteUpdateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新网站配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    
    # 检查网站是否存在
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    try:
        updated_website = await website_service.update_website(
            website_id, 
            website_data.dict(exclude_unset=True)
        )
        
        # 在后台重新配置网站
        background_tasks.add_task(
            website_service.reconfigure_website,
            website_id
        )
        
        return updated_website
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新网站失败: {str(e)}")


@router.delete("/{website_id}")
async def delete_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除网站"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    
    # 检查网站是否存在
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    try:
        await website_service.delete_website(website_id)
        return {"message": "网站删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除网站失败: {str(e)}")


@router.post("/{website_id}/start")
async def start_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启动网站"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    success = await website_service.start_website(website_id)
    
    if success:
        return {"message": "网站启动成功"}
    else:
        raise HTTPException(status_code=500, detail="网站启动失败")


@router.post("/{website_id}/stop")
async def stop_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """停止网站"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    success = await website_service.stop_website(website_id)
    
    if success:
        return {"message": "网站停止成功"}
    else:
        raise HTTPException(status_code=500, detail="网站停止失败")


@router.post("/{website_id}/backup")
async def backup_website(
    website_id: int,
    backup_type: str = "full",
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """备份网站"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    
    # 检查网站是否存在
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    # 在后台执行备份
    background_tasks.add_task(
        website_service.backup_website,
        website_id,
        backup_type
    )
    
    return {"message": "备份任务已启动"}


@router.get("/{website_id}/logs")
async def get_website_logs(
    website_id: int,
    log_type: str = "access",
    lines: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取网站日志"""
    website_service = WebsiteService(db)
    
    # 检查网站是否存在
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    logs = await website_service.get_website_logs(website_id, log_type, lines)
    return {"logs": logs}


@router.get("/{website_id}/ssl")
async def get_ssl_info(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取SSL证书信息"""
    website_service = WebsiteService(db)
    ssl_info = await website_service.get_ssl_info(website_id)
    return ssl_info


@router.post("/{website_id}/ssl")
async def configure_ssl(
    website_id: int,
    ssl_type: SSLType,
    auto_renew: bool = True,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """配置SSL证书"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    website_service = WebsiteService(db)
    
    # 检查网站是否存在
    website = await website_service.get_website(website_id)
    if not website:
        raise HTTPException(status_code=404, detail="网站不存在")
    
    # 在后台配置SSL
    background_tasks.add_task(
        website_service.configure_ssl,
        website_id,
        ssl_type,
        auto_renew
    )
    
    return {"message": "SSL配置任务已启动"}
