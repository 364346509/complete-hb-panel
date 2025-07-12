#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务管理服务
"""

import subprocess
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.system import Service
from app.core.config import settings


class ServiceService:
    """系统服务管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_services(self, search: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """获取系统服务列表"""
        try:
            # 获取systemd服务
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--all", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            services = []
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '.service' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            name = parts[0].replace('.service', '')
                            load_state = parts[1]
                            active_state = parts[2]
                            sub_state = parts[3]
                            
                            # 过滤条件
                            if search and search.lower() not in name.lower():
                                continue
                            
                            if status and status != active_state:
                                continue
                            
                            service_info = {
                                "name": name,
                                "display_name": name.replace('-', ' ').title(),
                                "status": active_state,
                                "enabled": await self._is_service_enabled(name),
                                "description": await self._get_service_description(name)
                            }
                            
                            services.append(service_info)
            
            return services[:100]  # 限制返回数量
            
        except Exception as e:
            print(f"获取服务列表失败: {e}")
            return []
    
    async def get_service(self, service_name: str) -> Optional[Dict]:
        """获取单个服务详情"""
        try:
            # 获取服务状态
            status_result = subprocess.run(
                ["systemctl", "status", service_name],
                capture_output=True,
                text=True
            )
            
            # 获取服务是否启用
            enabled = await self._is_service_enabled(service_name)
            
            # 解析状态信息
            status_info = self._parse_service_status(status_result.stdout)
            
            return {
                "name": service_name,
                "display_name": service_name.replace('-', ' ').title(),
                "description": status_info.get("description", ""),
                "status": status_info.get("status", "unknown"),
                "enabled": enabled,
                "pid": status_info.get("pid"),
                "memory_usage": status_info.get("memory"),
                "start_time": status_info.get("start_time")
            }
            
        except Exception as e:
            print(f"获取服务详情失败: {e}")
            return None
    
    async def execute_action(self, service_name: str, action: str) -> bool:
        """执行服务操作"""
        try:
            if action in ["start", "stop", "restart"]:
                cmd = ["systemctl", action, service_name]
            elif action == "enable":
                cmd = ["systemctl", "enable", service_name]
            elif action == "disable":
                cmd = ["systemctl", "disable", service_name]
            else:
                return False
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
            
        except Exception as e:
            print(f"执行服务操作失败: {e}")
            return False
    
    async def get_service_logs(self, service_name: str, lines: int = 100) -> List[str]:
        """获取服务日志"""
        try:
            result = subprocess.run(
                ["journalctl", "-u", service_name, "-n", str(lines), "--no-pager"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.split('\n')
            else:
                return ["无法获取服务日志"]
                
        except Exception as e:
            return [f"获取日志时出错: {str(e)}"]
    
    async def refresh_services(self):
        """刷新服务列表"""
        try:
            # 重新加载systemd配置
            subprocess.run(["systemctl", "daemon-reload"], timeout=30)
            
            # 更新数据库中的服务信息
            services = await self.get_services()
            
            for service_info in services:
                service = self.db.query(Service).filter(Service.name == service_info["name"]).first()
                
                if not service:
                    service = Service(
                        name=service_info["name"],
                        display_name=service_info["display_name"],
                        description=service_info["description"]
                    )
                    self.db.add(service)
                
                service.status = service_info["status"]
                service.enabled = service_info["enabled"]
            
            self.db.commit()
            
        except Exception as e:
            print(f"刷新服务列表失败: {e}")
    
    async def _is_service_enabled(self, service_name: str) -> bool:
        """检查服务是否启用"""
        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", service_name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == "enabled"
        except:
            return False
    
    async def _get_service_description(self, service_name: str) -> str:
        """获取服务描述"""
        try:
            result = subprocess.run(
                ["systemctl", "show", service_name, "--property=Description"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Description='):
                        return line.split('=', 1)[1]
            
            return ""
        except:
            return ""
    
    def _parse_service_status(self, status_output: str) -> Dict:
        """解析服务状态输出"""
        info = {}
        
        lines = status_output.split('\n')
        for line in lines:
            line = line.strip()
            
            if 'Active:' in line:
                # 解析状态
                if 'active (running)' in line:
                    info['status'] = 'active'
                elif 'inactive' in line:
                    info['status'] = 'inactive'
                elif 'failed' in line:
                    info['status'] = 'failed'
                else:
                    info['status'] = 'unknown'
            
            elif 'Main PID:' in line:
                # 解析PID
                try:
                    pid_part = line.split('Main PID:')[1].split()[0]
                    info['pid'] = int(pid_part)
                except:
                    pass
            
            elif 'Memory:' in line:
                # 解析内存使用
                try:
                    memory_part = line.split('Memory:')[1].strip()
                    if 'M' in memory_part:
                        memory_mb = float(memory_part.replace('M', ''))
                        info['memory'] = int(memory_mb * 1024)  # 转换为KB
                except:
                    pass
            
            elif 'since' in line and 'ago' in line:
                # 解析启动时间
                try:
                    # 这里可以进一步解析启动时间
                    info['start_time'] = line
                except:
                    pass
        
        return info
