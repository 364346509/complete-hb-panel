#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站管理服务
"""

import os
import subprocess
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.models.website import Website, WebsiteStatus, SSLType, WebsiteBackup
from app.models.database import Database, DatabaseUser
from app.core.config import settings


class WebsiteService:
    """网站管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.nginx_sites_path = "/etc/nginx/sites-available"
        self.nginx_enabled_path = "/etc/nginx/sites-enabled"
        self.apache_sites_path = "/etc/apache2/sites-available"
        self.apache_enabled_path = "/etc/apache2/sites-enabled"
        self.web_root = "/www/wwwroot"
    
    async def get_website_stats(self) -> Dict:
        """获取网站统计信息"""
        total = self.db.query(Website).count()
        running = self.db.query(Website).filter(Website.status == WebsiteStatus.RUNNING).count()
        stopped = self.db.query(Website).filter(Website.status == WebsiteStatus.STOPPED).count()
        ssl = self.db.query(Website).filter(Website.ssl_type != SSLType.NONE).count()
        
        return {
            "total": total,
            "running": running,
            "stopped": stopped,
            "ssl": ssl
        }
    
    async def get_websites(self, search: Optional[str] = None, status: Optional[str] = None,
                          php_version: Optional[str] = None, page: int = 1, size: int = 20) -> List[Website]:
        """获取网站列表"""
        query = self.db.query(Website)
        
        if search:
            query = query.filter(
                Website.name.contains(search) |
                Website.domain.contains(search)
            )
        
        if status:
            query = query.filter(Website.status == status)
        
        if php_version:
            query = query.filter(Website.php_version == php_version)
        
        offset = (page - 1) * size
        return query.offset(offset).limit(size).all()
    
    async def website_exists(self, name: str) -> bool:
        """检查网站名称是否存在"""
        return self.db.query(Website).filter(Website.name == name).first() is not None
    
    async def domain_exists(self, domain: str) -> bool:
        """检查域名是否已被使用"""
        websites = self.db.query(Website).all()
        for website in websites:
            if website.domain == domain:
                return True
            if website.domains:
                domains_list = json.loads(website.domains) if isinstance(website.domains, str) else website.domains
                if domain in domains_list:
                    return True
        return False
    
    async def create_website(self, website_data: Dict) -> Website:
        """创建网站"""
        # 设置默认路径
        if not website_data.get("path"):
            website_data["path"] = f"{self.web_root}/{website_data['name']}"
        
        # 创建网站记录
        website = Website(
            name=website_data["name"],
            domain=website_data["domain"],
            domains=json.dumps(website_data.get("domains", [])),
            path=website_data["path"],
            php_version=website_data.get("php_version", "8.1"),
            ssl_type=website_data.get("ssl_type", SSLType.NONE),
            ssl_auto_renew=website_data.get("ssl_auto_renew", True),
            index_files=website_data.get("index_files", "index.html,index.htm,index.php"),
            gzip_enable=website_data.get("gzip_enable", True),
            proxy_cache=website_data.get("proxy_cache", False),
            backup_enable=website_data.get("backup_enable", False),
            backup_keep_days=website_data.get("backup_keep_days", 7),
            status=WebsiteStatus.STOPPED
        )
        
        self.db.add(website)
        self.db.commit()
        self.db.refresh(website)
        
        # 创建关联数据库
        if website_data.get("create_database"):
            await self._create_website_database(website, website_data)
        
        return website
    
    async def get_website(self, website_id: int) -> Optional[Website]:
        """获取网站详情"""
        return self.db.query(Website).filter(Website.id == website_id).first()
    
    async def update_website(self, website_id: int, update_data: Dict) -> Website:
        """更新网站配置"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            raise ValueError("网站不存在")
        
        for key, value in update_data.items():
            if hasattr(website, key):
                if key == "domains" and isinstance(value, list):
                    setattr(website, key, json.dumps(value))
                else:
                    setattr(website, key, value)
        
        website.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(website)
        
        return website
    
    async def delete_website(self, website_id: int) -> bool:
        """删除网站"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return False
        
        try:
            # 停止网站
            await self.stop_website(website_id)
            
            # 删除配置文件
            await self._remove_nginx_config(website.name)
            await self._remove_apache_config(website.name)
            
            # 删除网站文件（可选，根据需求）
            # shutil.rmtree(website.path, ignore_errors=True)
            
            # 删除数据库记录
            self.db.delete(website)
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"删除网站失败: {e}")
            return False
    
    async def start_website(self, website_id: int) -> bool:
        """启动网站"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return False
        
        try:
            # 启用Nginx配置
            await self._enable_nginx_site(website.name)
            
            # 重载Nginx
            subprocess.run(["nginx", "-s", "reload"], check=True)
            
            # 更新状态
            website.status = WebsiteStatus.RUNNING
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"启动网站失败: {e}")
            return False
    
    async def stop_website(self, website_id: int) -> bool:
        """停止网站"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return False
        
        try:
            # 禁用Nginx配置
            await self._disable_nginx_site(website.name)
            
            # 重载Nginx
            subprocess.run(["nginx", "-s", "reload"], check=True)
            
            # 更新状态
            website.status = WebsiteStatus.STOPPED
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"停止网站失败: {e}")
            return False
    
    async def configure_website(self, website_id: int):
        """配置网站（创建目录、配置文件等）"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return
        
        try:
            # 创建网站目录
            os.makedirs(website.path, exist_ok=True)
            os.makedirs(f"{website.path}/logs", exist_ok=True)
            
            # 设置目录权限
            subprocess.run(["chown", "-R", "www-data:www-data", website.path])
            subprocess.run(["chmod", "-R", "755", website.path])
            
            # 创建默认首页
            if not os.path.exists(f"{website.path}/index.html"):
                with open(f"{website.path}/index.html", "w") as f:
                    f.write(self._get_default_index_content(website))
            
            # 生成Nginx配置
            await self._create_nginx_config(website)
            
            # 如果启用了SSL，配置SSL证书
            if website.ssl_type != SSLType.NONE:
                await self.configure_ssl(website_id, website.ssl_type, website.ssl_auto_renew)
            
        except Exception as e:
            print(f"配置网站失败: {e}")
    
    async def reconfigure_website(self, website_id: int):
        """重新配置网站"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return
        
        try:
            # 重新生成配置文件
            await self._create_nginx_config(website)
            
            # 如果网站正在运行，重载配置
            if website.status == WebsiteStatus.RUNNING:
                subprocess.run(["nginx", "-s", "reload"], check=True)
                
        except Exception as e:
            print(f"重新配置网站失败: {e}")
    
    async def backup_website(self, website_id: int, backup_type: str = "full"):
        """备份网站"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{website.name}_{backup_type}_{timestamp}"
            backup_path = f"/www/backup/{backup_name}.tar.gz"
            
            # 创建备份目录
            os.makedirs("/www/backup", exist_ok=True)
            
            # 执行备份
            if backup_type == "full":
                # 备份网站文件和数据库
                subprocess.run([
                    "tar", "-czf", backup_path,
                    "-C", os.path.dirname(website.path),
                    os.path.basename(website.path)
                ], check=True)
            elif backup_type == "files":
                # 仅备份文件
                subprocess.run([
                    "tar", "-czf", backup_path,
                    "-C", os.path.dirname(website.path),
                    os.path.basename(website.path)
                ], check=True)
            
            # 记录备份信息
            backup = WebsiteBackup(
                website_id=website_id,
                name=backup_name,
                type=backup_type,
                file_path=backup_path,
                file_size=os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
            )
            
            self.db.add(backup)
            self.db.commit()
            
        except Exception as e:
            print(f"备份网站失败: {e}")
    
    async def get_website_logs(self, website_id: int, log_type: str = "access", lines: int = 100) -> List[str]:
        """获取网站日志"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return []
        
        try:
            if log_type == "access":
                log_file = f"{website.path}/logs/access.log"
            elif log_type == "error":
                log_file = f"{website.path}/logs/error.log"
            else:
                return []
            
            if not os.path.exists(log_file):
                return []
            
            result = subprocess.run(
                ["tail", "-n", str(lines), log_file],
                capture_output=True,
                text=True
            )
            
            return result.stdout.split('\n') if result.returncode == 0 else []
            
        except Exception as e:
            print(f"获取日志失败: {e}")
            return []
    
    async def get_ssl_info(self, website_id: int) -> Dict:
        """获取SSL证书信息"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return {}
        
        ssl_info = {
            "ssl_type": website.ssl_type.value,
            "auto_renew": website.ssl_auto_renew,
            "certificate": None,
            "valid_from": None,
            "valid_to": None,
            "issuer": None
        }
        
        # 如果有SSL证书，获取证书信息
        if website.ssl_type != SSLType.NONE and website.ssl_cert:
            try:
                # 解析证书信息（这里需要实现证书解析逻辑）
                pass
            except Exception as e:
                print(f"解析SSL证书失败: {e}")
        
        return ssl_info
    
    async def configure_ssl(self, website_id: int, ssl_type: SSLType, auto_renew: bool = True):
        """配置SSL证书"""
        website = self.db.query(Website).filter(Website.id == website_id).first()
        if not website:
            return
        
        try:
            if ssl_type == SSLType.LETS_ENCRYPT:
                # 使用Let's Encrypt申请证书
                await self._setup_letsencrypt_ssl(website)
            elif ssl_type == SSLType.SELF_SIGNED:
                # 生成自签名证书
                await self._setup_selfsigned_ssl(website)
            
            # 更新网站SSL配置
            website.ssl_type = ssl_type
            website.ssl_auto_renew = auto_renew
            self.db.commit()
            
            # 重新生成Nginx配置
            await self._create_nginx_config(website)
            
            # 重载Nginx
            if website.status == WebsiteStatus.RUNNING:
                subprocess.run(["nginx", "-s", "reload"], check=True)
                
        except Exception as e:
            print(f"配置SSL失败: {e}")
    
    async def _create_website_database(self, website: Website, website_data: Dict):
        """创建网站关联数据库"""
        try:
            from app.services.database_service import DatabaseService
            db_service = DatabaseService(self.db)
            
            # 创建数据库
            database = await db_service.create_database({
                "name": website_data["database_name"],
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci"
            })
            
            # 创建数据库用户
            if website_data.get("database_user") and website_data.get("database_password"):
                await db_service.create_database_user({
                    "username": website_data["database_user"],
                    "password": website_data["database_password"],
                    "database_id": database.id,
                    "privileges": ["ALL"]
                })
            
        except Exception as e:
            print(f"创建网站数据库失败: {e}")
    
    def _get_default_index_content(self, website: Website) -> str:
        """获取默认首页内容"""
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>欢迎访问 {website.domain}</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 100px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>网站创建成功！</h1>
        <p>欢迎访问 {website.domain}</p>
        <p>您可以将网站文件上传到: {website.path}</p>
        <p>由 HB-Panel 强力驱动</p>
    </div>
</body>
</html>"""

    async def _create_nginx_config(self, website: Website):
        """创建Nginx配置文件"""
        config_content = self._generate_nginx_config(website)
        config_path = f"{self.nginx_sites_path}/{website.name}.conf"

        with open(config_path, "w") as f:
            f.write(config_content)

    def _generate_nginx_config(self, website: Website) -> str:
        """生成Nginx配置内容"""
        domains = [website.domain]
        if website.domains:
            domains_list = json.loads(website.domains) if isinstance(website.domains, str) else website.domains
            domains.extend(domains_list)

        server_names = " ".join(domains)

        config = f"""server {{
    listen 80;
    server_name {server_names};
    root {website.path};
    index {website.index_files};

    # 日志配置
    access_log {website.path}/logs/access.log;
    error_log {website.path}/logs/error.log;

    # PHP配置
    location ~ \\.php$ {{
        fastcgi_pass unix:/var/run/php/php{website.php_version}-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }}

    # 静态文件缓存
    location ~* \\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
"""

        # 添加Gzip配置
        if website.gzip_enable:
            config += """
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
"""

        # 添加SSL配置
        if website.ssl_type != SSLType.NONE:
            config += f"""
    # SSL重定向
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {server_names};
    root {website.path};
    index {website.index_files};

    # SSL证书配置
    ssl_certificate /etc/ssl/certs/{website.name}.crt;
    ssl_certificate_key /etc/ssl/private/{website.name}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # 日志配置
    access_log {website.path}/logs/access.log;
    error_log {website.path}/logs/error.log;

    # PHP配置
    location ~ \\.php$ {{
        fastcgi_pass unix:/var/run/php/php{website.php_version}-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }}

    # 静态文件缓存
    location ~* \\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {{
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
"""

            if website.gzip_enable:
                config += """
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
"""

        # 添加伪静态规则
        if website.rewrite_rule:
            config += f"""
    # 伪静态规则
{website.rewrite_rule}
"""

        config += "\n}"
        return config

    async def _enable_nginx_site(self, site_name: str):
        """启用Nginx站点"""
        source = f"{self.nginx_sites_path}/{site_name}.conf"
        target = f"{self.nginx_enabled_path}/{site_name}.conf"

        if os.path.exists(source) and not os.path.exists(target):
            os.symlink(source, target)

    async def _disable_nginx_site(self, site_name: str):
        """禁用Nginx站点"""
        target = f"{self.nginx_enabled_path}/{site_name}.conf"
        if os.path.exists(target):
            os.remove(target)

    async def _remove_nginx_config(self, site_name: str):
        """删除Nginx配置"""
        config_file = f"{self.nginx_sites_path}/{site_name}.conf"
        enabled_file = f"{self.nginx_enabled_path}/{site_name}.conf"

        if os.path.exists(enabled_file):
            os.remove(enabled_file)
        if os.path.exists(config_file):
            os.remove(config_file)

    async def _remove_apache_config(self, site_name: str):
        """删除Apache配置"""
        config_file = f"{self.apache_sites_path}/{site_name}.conf"
        if os.path.exists(config_file):
            os.remove(config_file)

    async def _setup_letsencrypt_ssl(self, website: Website):
        """设置Let's Encrypt SSL证书"""
        try:
            domains = [website.domain]
            if website.domains:
                domains_list = json.loads(website.domains) if isinstance(website.domains, str) else website.domains
                domains.extend(domains_list)

            domain_args = []
            for domain in domains:
                domain_args.extend(["-d", domain])

            # 使用certbot申请证书
            cmd = [
                "certbot", "certonly",
                "--nginx",
                "--non-interactive",
                "--agree-tos",
                "--email", "admin@example.com",  # 这里应该从配置中获取
            ] + domain_args

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 证书申请成功，更新网站配置
                cert_path = f"/etc/letsencrypt/live/{website.domain}/fullchain.pem"
                key_path = f"/etc/letsencrypt/live/{website.domain}/privkey.pem"

                # 复制证书到网站目录
                subprocess.run([
                    "cp", cert_path, f"/etc/ssl/certs/{website.name}.crt"
                ])
                subprocess.run([
                    "cp", key_path, f"/etc/ssl/private/{website.name}.key"
                ])

        except Exception as e:
            print(f"设置Let's Encrypt SSL失败: {e}")

    async def _setup_selfsigned_ssl(self, website: Website):
        """设置自签名SSL证书"""
        try:
            cert_path = f"/etc/ssl/certs/{website.name}.crt"
            key_path = f"/etc/ssl/private/{website.name}.key"

            # 生成自签名证书
            subprocess.run([
                "openssl", "req", "-x509", "-nodes", "-days", "365",
                "-newkey", "rsa:2048",
                "-keyout", key_path,
                "-out", cert_path,
                "-subj", f"/C=CN/ST=State/L=City/O=Organization/CN={website.domain}"
            ], check=True)

        except Exception as e:
            print(f"生成自签名证书失败: {e}")
