#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全管理数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class FirewallRuleAction(enum.Enum):
    """防火墙规则动作枚举"""
    ALLOW = "allow"
    DENY = "deny"
    REJECT = "reject"


class FirewallRuleProtocol(enum.Enum):
    """防火墙规则协议枚举"""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "all"


class SSLCertStatus(enum.Enum):
    """SSL证书状态枚举"""
    VALID = "valid"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"
    INVALID = "invalid"


class SecurityEventLevel(enum.Enum):
    """安全事件级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FirewallRule(Base):
    """防火墙规则模型"""
    __tablename__ = "firewall_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    action = Column(Enum(FirewallRuleAction), nullable=False)
    protocol = Column(Enum(FirewallRuleProtocol), default=FirewallRuleProtocol.TCP)
    port = Column(String(100))  # 端口或端口范围
    source_ip = Column(String(100))  # 源IP或IP段
    destination_ip = Column(String(100))  # 目标IP或IP段
    
    # 规则配置
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 是否为系统规则
    priority = Column(Integer, default=100)
    description = Column(Text)
    
    # 统计信息
    hit_count = Column(Integer, default=0)
    last_hit = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SSLCertificate(Base):
    """SSL证书模型"""
    __tablename__ = "ssl_certificates"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False)
    cert_path = Column(String(500), nullable=False)
    key_path = Column(String(500), nullable=False)
    ca_path = Column(String(500))  # CA证书路径
    
    # 证书信息
    issuer = Column(String(500))  # 颁发者
    subject = Column(String(500))  # 主题
    serial_number = Column(String(100))  # 序列号
    fingerprint = Column(String(200))  # 指纹
    
    # 有效期
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    status = Column(Enum(SSLCertStatus), default=SSLCertStatus.VALID)
    
    # 配置信息
    auto_renew = Column(Boolean, default=True)
    cert_type = Column(String(50))  # lets_encrypt, self_signed, custom
    key_size = Column(Integer, default=2048)
    
    # 关联信息
    website_id = Column(Integer, ForeignKey("websites.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SecurityEvent(Base):
    """安全事件模型"""
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)  # login_failed, port_scan, etc.
    level = Column(Enum(SecurityEventLevel), default=SecurityEventLevel.LOW)
    source_ip = Column(String(45))
    target_ip = Column(String(45))
    port = Column(Integer)
    
    # 事件详情
    title = Column(String(500), nullable=False)
    description = Column(Text)
    details = Column(JSON)  # 详细信息JSON
    
    # 处理状态
    is_handled = Column(Boolean, default=False)
    handled_by = Column(Integer, ForeignKey("users.id"))
    handled_at = Column(DateTime)
    handling_note = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())


class IPBlacklist(Base):
    """IP黑名单模型"""
    __tablename__ = "ip_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, unique=True)
    ip_range = Column(String(100))  # IP段
    reason = Column(String(500))
    
    # 封禁配置
    is_active = Column(Boolean, default=True)
    is_permanent = Column(Boolean, default=False)
    expires_at = Column(DateTime)  # 过期时间
    
    # 统计信息
    block_count = Column(Integer, default=0)
    last_block = Column(DateTime)
    
    # 来源信息
    added_by = Column(Integer, ForeignKey("users.id"))
    auto_added = Column(Boolean, default=False)  # 是否自动添加
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class IPWhitelist(Base):
    """IP白名单模型"""
    __tablename__ = "ip_whitelist"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), nullable=False, unique=True)
    ip_range = Column(String(100))  # IP段
    description = Column(String(500))
    
    # 配置信息
    is_active = Column(Boolean, default=True)
    services = Column(JSON)  # 允许访问的服务列表
    
    # 来源信息
    added_by = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SSHConfig(Base):
    """SSH配置模型"""
    __tablename__ = "ssh_configs"

    id = Column(Integer, primary_key=True, index=True)
    port = Column(Integer, default=22)
    permit_root_login = Column(Boolean, default=False)
    password_authentication = Column(Boolean, default=True)
    pubkey_authentication = Column(Boolean, default=True)
    
    # 安全配置
    max_auth_tries = Column(Integer, default=3)
    login_grace_time = Column(Integer, default=120)
    client_alive_interval = Column(Integer, default=0)
    client_alive_count_max = Column(Integer, default=3)
    
    # 访问控制
    allow_users = Column(Text)  # 允许的用户列表
    deny_users = Column(Text)   # 禁止的用户列表
    allow_groups = Column(Text) # 允许的组列表
    deny_groups = Column(Text)  # 禁止的组列表
    
    # 其他配置
    banner_file = Column(String(500))  # 登录横幅文件
    log_level = Column(String(20), default="INFO")
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SecurityScan(Base):
    """安全扫描模型"""
    __tablename__ = "security_scans"

    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(50), nullable=False)  # port, vulnerability, malware
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    
    # 扫描配置
    target = Column(String(500))  # 扫描目标
    options = Column(JSON)  # 扫描选项
    
    # 扫描结果
    total_items = Column(Integer, default=0)
    scanned_items = Column(Integer, default=0)
    vulnerabilities_found = Column(Integer, default=0)
    threats_found = Column(Integer, default=0)
    
    # 时间信息
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration = Column(Integer)  # 扫描耗时(秒)
    
    # 结果文件
    report_file = Column(String(500))
    
    created_at = Column(DateTime, server_default=func.now())


class SecurityScanResult(Base):
    """安全扫描结果模型"""
    __tablename__ = "security_scan_results"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("security_scans.id"), nullable=False)
    item_type = Column(String(50), nullable=False)  # port, file, service
    item_name = Column(String(500), nullable=False)
    
    # 风险信息
    risk_level = Column(Enum(SecurityEventLevel), default=SecurityEventLevel.LOW)
    vulnerability_type = Column(String(100))
    description = Column(Text)
    recommendation = Column(Text)
    
    # 详细信息
    details = Column(JSON)
    
    # 处理状态
    is_fixed = Column(Boolean, default=False)
    fixed_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    scan = relationship("SecurityScan")
