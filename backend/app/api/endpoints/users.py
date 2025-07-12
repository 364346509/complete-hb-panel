#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter()


class UserCreateRequest(BaseModel):
    """用户创建请求模型"""
    username: str
    email: str
    password: str
    full_name: str = None
    is_superuser: bool = False


class UserUpdateRequest(BaseModel):
    """用户更新请求模型"""
    email: str = None
    full_name: str = None
    is_active: bool = None
    is_superuser: bool = None


class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: str = None
    is_active: bool
    is_superuser: bool
    avatar: str = None
    created_at: str
    last_login: str = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponse])
async def get_users(
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_service = UserService(db)
    users = user_service.get_users(page=page, size=size, search=search)
    return users


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    if user_service.get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if user_service.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    user = user_service.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        is_superuser=user_data.is_superuser
    )
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 非超级用户不能修改权限相关字段
    if not current_user.is_superuser:
        user_data.is_superuser = None
        user_data.is_active = None
    
    user_service = UserService(db)
    
    # 检查邮箱是否已被其他用户使用
    if user_data.email:
        existing_user = user_service.get_user_by_email(user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    update_data = {k: v for k, v in user_data.dict().items() if v is not None}
    user = user_service.update_user(user_id, **update_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "用户删除成功"}


@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_service = UserService(db)
    
    # 验证旧密码（仅当修改自己的密码时）
    if current_user.id == user_id:
        if not user_service.authenticate_user(current_user.username, password_data.old_password):
            raise HTTPException(status_code=400, detail="旧密码错误")
    
    success = user_service.change_password(user_id, password_data.new_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {"message": "密码修改成功"}


@router.post("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换用户状态（启用/禁用）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能禁用自己")
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.is_active:
        user_service.deactivate_user(user_id)
        message = "用户已禁用"
    else:
        user_service.activate_user(user_id)
        message = "用户已启用"
    
    return {"message": message}


@router.get("/{user_id}/login-logs")
async def get_user_login_logs(
    user_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户登录日志"""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    
    user_service = UserService(db)
    logs = user_service.get_login_logs(user_id=user_id, limit=limit)
    
    return [
        {
            "id": log.id,
            "login_type": log.login_type,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "login_time": log.login_time.isoformat() if log.login_time else None,
            "logout_time": log.logout_time.isoformat() if log.logout_time else None,
            "session_duration": log.session_duration
        }
        for log in logs
    ]
