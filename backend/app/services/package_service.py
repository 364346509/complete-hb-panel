#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件包管理服务
"""

import subprocess
import asyncio
import uuid
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.package import Package, PackageCategory, InstallTask, PackageStatus, InstallStatus
from app.core.config import settings


class PackageService:
    """软件包管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_categories(self) -> List[Dict]:
        """获取软件包分类"""
        categories = self.db.query(PackageCategory).filter(
            PackageCategory.is_active == True
        ).order_by(PackageCategory.sort_order).all()
        
        return [
            {
                "id": cat.id,
                "name": cat.name,
                "display_name": cat.display_name,
                "description": cat.description,
                "icon": cat.icon
            }
            for cat in categories
        ]
    
    async def get_packages(self, category: Optional[str] = None, search: Optional[str] = None,
                          status: Optional[str] = None, page: int = 1, size: int = 20) -> List[Dict]:
        """获取软件包列表"""
        query = self.db.query(Package)
        
        if category:
            query = query.filter(Package.category == category)
        
        if search:
            query = query.filter(Package.name.contains(search) | 
                               Package.display_name.contains(search) |
                               Package.description.contains(search))
        
        if status:
            query = query.filter(Package.status == status)
        
        offset = (page - 1) * size
        packages = query.offset(offset).limit(size).all()
        
        return [self._package_to_dict(pkg) for pkg in packages]
    
    async def get_installed_packages(self) -> List[Dict]:
        """获取已安装软件包列表"""
        packages = self.db.query(Package).filter(
            Package.status == PackageStatus.INSTALLED
        ).all()
        
        return [self._package_to_dict(pkg) for pkg in packages]
    
    async def search_packages(self, query: str) -> List[Dict]:
        """搜索软件包"""
        try:
            # 使用apt search搜索软件包
            result = subprocess.run(
                ["apt", "search", query],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            packages = []
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '/' in line and '-' in line:
                        parts = line.split(' - ', 1)
                        if len(parts) == 2:
                            name = parts[0].split('/')[0]
                            description = parts[1]
                            packages.append({
                                "name": name,
                                "description": description,
                                "status": "not_installed"
                            })
            
            return packages[:50]  # 限制返回数量
        except Exception as e:
            print(f"搜索软件包失败: {e}")
            return []
    
    async def create_install_task(self, package_name: str, action: str, user_id: int) -> InstallTask:
        """创建安装任务"""
        task_id = str(uuid.uuid4())
        
        task = InstallTask(
            task_id=task_id,
            package_name=package_name,
            action=action,
            status=InstallStatus.PENDING,
            user_id=user_id
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    async def get_install_task(self, task_id: str) -> Optional[InstallTask]:
        """获取安装任务"""
        return self.db.query(InstallTask).filter(InstallTask.task_id == task_id).first()
    
    async def execute_install_task(self, task_id: str):
        """执行安装任务"""
        task = await self.get_install_task(task_id)
        if not task:
            return
        
        try:
            # 更新任务状态
            task.status = InstallStatus.INSTALLING
            task.started_at = datetime.utcnow()
            task.progress = 0
            self.db.commit()
            
            # 执行安装命令
            if task.action == "install":
                cmd = ["apt", "install", "-y", task.package_name]
            elif task.action == "uninstall":
                cmd = ["apt", "remove", "-y", task.package_name]
            elif task.action == "upgrade":
                cmd = ["apt", "upgrade", "-y", task.package_name]
            else:
                raise ValueError(f"不支持的操作: {task.action}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            output = ""
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                
                line_text = line.decode('utf-8', errors='ignore')
                output += line_text
                
                # 更新任务日志
                task.log_output = output
                task.progress = min(90, task.progress + 5)  # 模拟进度
                self.db.commit()
            
            await process.wait()
            
            if process.returncode == 0:
                task.status = InstallStatus.SUCCESS
                task.progress = 100
                
                # 更新软件包状态
                await self._update_package_status(task.package_name, task.action)
            else:
                task.status = InstallStatus.FAILED
                task.error_message = "安装失败"
            
        except Exception as e:
            task.status = InstallStatus.FAILED
            task.error_message = str(e)
        
        finally:
            task.completed_at = datetime.utcnow()
            self.db.commit()
    
    async def refresh_package_list(self):
        """刷新软件包列表"""
        try:
            # 更新软件包列表
            subprocess.run(["apt", "update"], check=True, timeout=300)
            
            # 获取已安装软件包
            result = subprocess.run(
                ["dpkg", "-l"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                await self._parse_installed_packages(result.stdout)
            
        except Exception as e:
            print(f"刷新软件包列表失败: {e}")
    
    async def get_lamp_status(self) -> Dict:
        """获取LAMP环境状态"""
        services = ["apache2", "nginx", "mysql", "php-fpm"]
        status = {}
        
        for service in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", service],
                    capture_output=True,
                    text=True
                )
                status[service] = result.stdout.strip() == "active"
            except:
                status[service] = False
        
        return {
            "apache": status.get("apache2", False),
            "nginx": status.get("nginx", False),
            "mysql": status.get("mysql", False),
            "php": status.get("php-fpm", False)
        }
    
    async def install_lamp_environment(self, environment_type: str, user_id: int) -> InstallTask:
        """安装LAMP/LEMP环境"""
        task_id = str(uuid.uuid4())
        
        task = InstallTask(
            task_id=task_id,
            package_name=f"{environment_type}_environment",
            action="install",
            status=InstallStatus.PENDING,
            user_id=user_id
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    async def execute_lamp_install(self, task_id: str):
        """执行LAMP环境安装"""
        task = await self.get_install_task(task_id)
        if not task:
            return
        
        try:
            task.status = InstallStatus.INSTALLING
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            environment_type = task.package_name.replace("_environment", "")
            
            if environment_type == "lamp":
                packages = ["apache2", "mysql-server", "php", "libapache2-mod-php", "php-mysql"]
            elif environment_type == "lemp":
                packages = ["nginx", "mysql-server", "php-fpm", "php-mysql"]
            elif environment_type == "mixed":
                packages = ["apache2", "nginx", "mysql-server", "php", "php-fpm", 
                           "libapache2-mod-php", "php-mysql", "redis-server"]
            else:
                raise ValueError(f"不支持的环境类型: {environment_type}")
            
            # 安装软件包
            for i, package in enumerate(packages):
                task.log_output = f"正在安装 {package}...\n"
                task.progress = int((i / len(packages)) * 90)
                self.db.commit()
                
                process = await asyncio.create_subprocess_exec(
                    "apt", "install", "-y", package,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )
                
                await process.wait()
                
                if process.returncode != 0:
                    raise Exception(f"安装 {package} 失败")
            
            # 配置服务
            await self._configure_lamp_services(environment_type)
            
            task.status = InstallStatus.SUCCESS
            task.progress = 100
            task.log_output += f"\n{environment_type.upper()}环境安装完成！"
            
        except Exception as e:
            task.status = InstallStatus.FAILED
            task.error_message = str(e)
            task.log_output += f"\n安装失败: {str(e)}"
        
        finally:
            task.completed_at = datetime.utcnow()
            self.db.commit()
    
    def _package_to_dict(self, package: Package) -> Dict:
        """将Package对象转换为字典"""
        return {
            "id": package.id,
            "name": package.name,
            "display_name": package.display_name,
            "description": package.description,
            "category": package.category,
            "version": package.version,
            "installed_version": package.installed_version,
            "status": package.status.value if package.status else "unknown",
            "size": package.size,
            "homepage": package.homepage
        }
    
    async def _update_package_status(self, package_name: str, action: str):
        """更新软件包状态"""
        package = self.db.query(Package).filter(Package.name == package_name).first()
        
        if not package:
            # 创建新的软件包记录
            package = Package(
                name=package_name,
                display_name=package_name,
                description="",
                category="other"
            )
            self.db.add(package)
        
        if action == "install":
            package.status = PackageStatus.INSTALLED
            package.install_date = datetime.utcnow()
        elif action == "uninstall":
            package.status = PackageStatus.NOT_INSTALLED
            package.install_date = None
        
        self.db.commit()
    
    async def _parse_installed_packages(self, dpkg_output: str):
        """解析已安装软件包"""
        lines = dpkg_output.split('\n')
        
        for line in lines:
            if line.startswith('ii '):  # 已安装的软件包
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[1]
                    version = parts[2]
                    
                    package = self.db.query(Package).filter(Package.name == name).first()
                    if not package:
                        package = Package(
                            name=name,
                            display_name=name,
                            description="",
                            category="system"
                        )
                        self.db.add(package)
                    
                    package.status = PackageStatus.INSTALLED
                    package.installed_version = version
        
        self.db.commit()
    
    async def _configure_lamp_services(self, environment_type: str):
        """配置LAMP服务"""
        try:
            if environment_type in ["lamp", "mixed"]:
                # 启用Apache模块
                subprocess.run(["a2enmod", "rewrite"], check=True)
                subprocess.run(["a2enmod", "ssl"], check=True)
                
                # 启动Apache
                subprocess.run(["systemctl", "enable", "apache2"], check=True)
                subprocess.run(["systemctl", "start", "apache2"], check=True)
            
            if environment_type in ["lemp", "mixed"]:
                # 启动Nginx
                subprocess.run(["systemctl", "enable", "nginx"], check=True)
                subprocess.run(["systemctl", "start", "nginx"], check=True)
            
            # 启动MySQL
            subprocess.run(["systemctl", "enable", "mysql"], check=True)
            subprocess.run(["systemctl", "start", "mysql"], check=True)
            
            # 启动PHP-FPM
            if environment_type in ["lemp", "mixed"]:
                subprocess.run(["systemctl", "enable", "php8.1-fpm"], check=True)
                subprocess.run(["systemctl", "start", "php8.1-fpm"], check=True)
            
            if environment_type == "mixed":
                # 启动Redis
                subprocess.run(["systemctl", "enable", "redis-server"], check=True)
                subprocess.run(["systemctl", "start", "redis-server"], check=True)
                
        except Exception as e:
            print(f"配置服务失败: {e}")
