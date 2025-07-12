#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全管理相关API端点
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth import get_current_user
from app.models.user import User
from app.services.security_service import SecurityService

router = APIRouter()


class FirewallRule(BaseModel):
    """防火墙规则模型"""
    port: str
    protocol: str  # tcp, udp
    action: str    # allow, deny
    source: str = "anywhere"
    description: str = ""


class SSHConfig(BaseModel):
    """SSH配置模型"""
    port: int = 22
    permit_root_login: bool = False
    password_authentication: bool = True
    pubkey_authentication: bool = True
    max_auth_tries: int = 3
    client_alive_interval: int = 300


class SecurityScanResult(BaseModel):
    """安全扫描结果模型"""
    category: str
    level: str  # low, medium, high, critical
    title: str
    description: str
    recommendation: str


@router.get("/firewall/status")
async def get_firewall_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取防火墙状态"""
    security_service = SecurityService(db)
    status = await security_service.get_firewall_status()
    return status


@router.get("/firewall/rules")
async def get_firewall_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取防火墙规则列表"""
    security_service = SecurityService(db)
    rules = await security_service.get_firewall_rules()
    return rules


@router.post("/firewall/rules")
async def add_firewall_rule(
    rule: FirewallRule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加防火墙规则"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.add_firewall_rule(
        port=rule.port,
        protocol=rule.protocol,
        action=rule.action,
        source=rule.source,
        description=rule.description
    )
    
    if success:
        return {"message": "防火墙规则添加成功"}
    else:
        raise HTTPException(status_code=500, detail="添加防火墙规则失败")


@router.delete("/firewall/rules/{rule_id}")
async def delete_firewall_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除防火墙规则"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.delete_firewall_rule(rule_id)
    
    if success:
        return {"message": "防火墙规则删除成功"}
    else:
        raise HTTPException(status_code=404, detail="规则不存在或删除失败")


@router.post("/firewall/enable")
async def enable_firewall(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """启用防火墙"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.enable_firewall()
    
    if success:
        return {"message": "防火墙已启用"}
    else:
        raise HTTPException(status_code=500, detail="启用防火墙失败")


@router.post("/firewall/disable")
async def disable_firewall(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """禁用防火墙"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.disable_firewall()
    
    if success:
        return {"message": "防火墙已禁用"}
    else:
        raise HTTPException(status_code=500, detail="禁用防火墙失败")


@router.get("/ssh/config")
async def get_ssh_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取SSH配置"""
    security_service = SecurityService(db)
    config = await security_service.get_ssh_config()
    return config


@router.post("/ssh/config")
async def update_ssh_config(
    config: SSHConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新SSH配置"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.update_ssh_config(config.dict())
    
    if success:
        return {"message": "SSH配置更新成功"}
    else:
        raise HTTPException(status_code=500, detail="SSH配置更新失败")


@router.get("/ssh/keys")
async def get_ssh_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取SSH密钥列表"""
    security_service = SecurityService(db)
    keys = await security_service.get_ssh_keys()
    return keys


@router.post("/ssh/keys")
async def add_ssh_key(
    key_name: str,
    public_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加SSH密钥"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.add_ssh_key(key_name, public_key)
    
    if success:
        return {"message": "SSH密钥添加成功"}
    else:
        raise HTTPException(status_code=500, detail="SSH密钥添加失败")


@router.delete("/ssh/keys/{key_name}")
async def delete_ssh_key(
    key_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除SSH密钥"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.delete_ssh_key(key_name)
    
    if success:
        return {"message": "SSH密钥删除成功"}
    else:
        raise HTTPException(status_code=404, detail="SSH密钥不存在或删除失败")


@router.get("/scan")
async def security_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行安全扫描"""
    security_service = SecurityService(db)
    results = await security_service.security_scan()
    return results


@router.get("/login-attempts")
async def get_failed_login_attempts(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取失败登录尝试"""
    security_service = SecurityService(db)
    attempts = await security_service.get_failed_login_attempts(hours)
    return attempts


@router.post("/ban-ip")
async def ban_ip_address(
    ip_address: str,
    duration: int = 3600,  # 默认1小时
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """封禁IP地址"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.ban_ip_address(ip_address, duration)
    
    if success:
        return {"message": f"IP地址 {ip_address} 已封禁 {duration} 秒"}
    else:
        raise HTTPException(status_code=500, detail="封禁IP地址失败")


@router.get("/banned-ips")
async def get_banned_ips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取被封禁的IP列表"""
    security_service = SecurityService(db)
    banned_ips = await security_service.get_banned_ips()
    return banned_ips


@router.delete("/banned-ips/{ip_address}")
async def unban_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解封IP地址"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    security_service = SecurityService(db)
    success = await security_service.unban_ip_address(ip_address)
    
    if success:
        return {"message": f"IP地址 {ip_address} 已解封"}
    else:
        raise HTTPException(status_code=404, detail="IP地址不在封禁列表中")
