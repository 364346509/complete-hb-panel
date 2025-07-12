#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.file_service import FileService

router = APIRouter()


class FileInfo(BaseModel):
    """文件信息模型"""
    name: str
    path: str
    type: str  # file, directory
    size: int
    permissions: str
    owner: str
    group: str
    modified_time: str
    is_hidden: bool


class FileActionRequest(BaseModel):
    """文件操作请求模型"""
    action: str  # copy, move, delete, rename
    source: str
    target: str = None


@router.get("/list")
async def list_files(
    path: str = "/",
    show_hidden: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件列表"""
    file_service = FileService(db)
    
    try:
        files = await file_service.list_files(path, show_hidden)
        return {
            "path": path,
            "files": files
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="路径不存在")


@router.get("/info")
async def get_file_info(
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件详细信息"""
    file_service = FileService(db)
    
    try:
        info = await file_service.get_file_info(path)
        return info
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")


@router.get("/content")
async def get_file_content(
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取文件内容"""
    file_service = FileService(db)
    
    try:
        content = await file_service.get_file_content(path)
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件不是文本文件")


@router.post("/content")
async def save_file_content(
    path: str,
    content: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """保存文件内容"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    file_service = FileService(db)
    
    try:
        await file_service.save_file_content(path, content)
        return {"message": "文件保存成功"}
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")


@router.post("/upload")
async def upload_file(
    path: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传文件"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    file_service = FileService(db)
    
    try:
        file_path = await file_service.upload_file(path, file)
        return {
            "message": "文件上传成功",
            "file_path": file_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
async def download_file(
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """下载文件"""
    file_service = FileService(db)
    
    try:
        if not await file_service.file_exists(path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=path,
            filename=path.split('/')[-1]
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")


@router.post("/action")
async def file_action(
    request: FileActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行文件操作"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    file_service = FileService(db)
    
    try:
        result = await file_service.execute_action(
            action=request.action,
            source=request.source,
            target=request.target
        )
        
        return {
            "success": result,
            "message": f"文件{request.action}操作{'成功' if result else '失败'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mkdir")
async def create_directory(
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建目录"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    file_service = FileService(db)
    
    try:
        await file_service.create_directory(path)
        return {"message": "目录创建成功"}
    except FileExistsError:
        raise HTTPException(status_code=400, detail="目录已存在")
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")


@router.post("/chmod")
async def change_permissions(
    path: str,
    permissions: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改文件权限"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    file_service = FileService(db)
    
    try:
        await file_service.change_permissions(path, permissions)
        return {"message": "权限修改成功"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="文件不存在")
    except PermissionError:
        raise HTTPException(status_code=403, detail="权限不足")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
