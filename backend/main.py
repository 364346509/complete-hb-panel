#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HB-Panel 主启动文件
HasBir Linux管理面板后端服务
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.main import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    print("🚀 HB-Panel 后端服务启动成功")
    yield
    # 关闭时清理资源
    print("🛑 HB-Panel 后端服务关闭")


def create_application() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="HB-Panel API",
        description="HasBir Linux管理面板后端API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册API路由
    app.include_router(api_router, prefix="/api/v1")

    # 静态文件服务
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # 静态目录不存在时忽略
        pass

    return app


app = create_application()


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "HB-Panel API服务运行正常",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "hb-panel-backend"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
