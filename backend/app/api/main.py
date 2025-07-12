#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API主路由
"""

from fastapi import APIRouter

from .endpoints import auth, system, packages, services, files, users, websites, databases

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(system.router, prefix="/system", tags=["系统监控"])
api_router.include_router(websites.router, prefix="/websites", tags=["网站管理"])
api_router.include_router(databases.router, prefix="/databases", tags=["数据库管理"])
api_router.include_router(packages.router, prefix="/packages", tags=["软件包管理"])
api_router.include_router(services.router, prefix="/services", tags=["系统服务"])
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
