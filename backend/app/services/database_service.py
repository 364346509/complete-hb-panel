#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理服务
"""

import os
import subprocess
import asyncio
import pymysql
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json
import hashlib

from app.models.database import Database, DatabaseUser, DatabaseBackup, DatabaseStatus, DatabaseOperation
from app.core.config import settings


class DatabaseService:
    """数据库管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mysql_host = "localhost"
        self.mysql_port = 3306
        self.mysql_root_user = "root"
        self.mysql_root_password = settings.MYSQL_ROOT_PASSWORD if hasattr(settings, 'MYSQL_ROOT_PASSWORD') else ""
        self.backup_path = "/www/backup/databases"
    
    async def get_database_stats(self) -> Dict:
        """获取数据库统计信息"""
        total = self.db.query(Database).count()
        total_size = self.db.query(Database).with_entities(Database.size).all()
        total_size = sum([size[0] or 0 for size in total_size])
        users = self.db.query(DatabaseUser).count()
        backups = self.db.query(DatabaseBackup).count()
        
        return {
            "total": total,
            "total_size": total_size,
            "users": users,
            "backups": backups
        }
    
    async def get_databases(self, search: Optional[str] = None, page: int = 1, size: int = 20) -> List[Database]:
        """获取数据库列表"""
        query = self.db.query(Database)
        
        if search:
            query = query.filter(Database.name.contains(search))
        
        # 更新数据库统计信息
        await self._update_database_stats()
        
        offset = (page - 1) * size
        return query.offset(offset).limit(size).all()
    
    async def database_exists(self, name: str) -> bool:
        """检查数据库名称是否存在"""
        # 检查本地记录
        local_exists = self.db.query(Database).filter(Database.name == name).first() is not None
        
        # 检查MySQL实际数据库
        mysql_exists = await self._check_mysql_database_exists(name)
        
        return local_exists or mysql_exists
    
    async def create_database(self, database_data: Dict) -> Database:
        """创建数据库"""
        try:
            # 在MySQL中创建数据库
            await self._create_mysql_database(
                database_data["name"],
                database_data.get("charset", "utf8mb4"),
                database_data.get("collation", "utf8mb4_unicode_ci")
            )
            
            # 创建数据库记录
            database = Database(
                name=database_data["name"],
                charset=database_data.get("charset", "utf8mb4"),
                collation=database_data.get("collation", "utf8mb4_unicode_ci"),
                description=database_data.get("description"),
                auto_backup=database_data.get("auto_backup", False),
                backup_keep_days=database_data.get("backup_keep_days", 7),
                status=DatabaseStatus.ACTIVE
            )
            
            self.db.add(database)
            self.db.commit()
            self.db.refresh(database)
            
            # 记录操作日志
            await self._log_database_operation(
                database.id,
                "create",
                f"CREATE DATABASE `{database.name}` CHARACTER SET {database.charset} COLLATE {database.collation}",
                "success"
            )
            
            return database
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                None,
                "create",
                f"CREATE DATABASE `{database_data['name']}`",
                "failed",
                str(e)
            )
            raise e
    
    async def get_database(self, database_id: int) -> Optional[Database]:
        """获取数据库详情"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        
        if database:
            # 更新数据库统计信息
            await self._update_single_database_stats(database)
        
        return database
    
    async def delete_database(self, database_id: int) -> bool:
        """删除数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            return False
        
        try:
            # 在MySQL中删除数据库
            await self._drop_mysql_database(database.name)
            
            # 删除相关用户
            users = self.db.query(DatabaseUser).filter(DatabaseUser.database_id == database_id).all()
            for user in users:
                await self._drop_mysql_user(user.username, user.host)
                self.db.delete(user)
            
            # 删除数据库记录
            self.db.delete(database)
            self.db.commit()
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "drop",
                f"DROP DATABASE `{database.name}`",
                "success"
            )
            
            return True
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                database_id,
                "drop",
                f"DROP DATABASE `{database.name}`",
                "failed",
                str(e)
            )
            return False
    
    async def backup_database(self, database_id: int, backup_type: str = "full", compression: str = "gzip"):
        """备份数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{database.name}_{backup_type}_{timestamp}"
            
            # 创建备份目录
            os.makedirs(self.backup_path, exist_ok=True)
            
            if compression == "gzip":
                backup_file = f"{self.backup_path}/{backup_name}.sql.gz"
                cmd = [
                    "mysqldump",
                    f"--host={self.mysql_host}",
                    f"--port={self.mysql_port}",
                    f"--user={self.mysql_root_user}",
                    f"--password={self.mysql_root_password}",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    database.name
                ]
                
                # 执行备份并压缩
                with open(backup_file, 'wb') as f:
                    mysqldump = subprocess.Popen(cmd, stdout=subprocess.PIPE)
                    gzip_proc = subprocess.Popen(['gzip'], stdin=mysqldump.stdout, stdout=f)
                    mysqldump.stdout.close()
                    gzip_proc.communicate()
            else:
                backup_file = f"{self.backup_path}/{backup_name}.sql"
                cmd = [
                    "mysqldump",
                    f"--host={self.mysql_host}",
                    f"--port={self.mysql_port}",
                    f"--user={self.mysql_root_user}",
                    f"--password={self.mysql_root_password}",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    database.name
                ]
                
                with open(backup_file, 'w') as f:
                    subprocess.run(cmd, stdout=f, check=True)
            
            # 记录备份信息
            backup = DatabaseBackup(
                database_id=database_id,
                name=backup_name,
                file_path=backup_file,
                file_size=os.path.getsize(backup_file) if os.path.exists(backup_file) else 0,
                backup_type=backup_type,
                compression=compression,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            self.db.add(backup)
            
            # 更新数据库最后备份时间
            database.last_backup = datetime.utcnow()
            self.db.commit()
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "backup",
                f"BACKUP DATABASE `{database.name}`",
                "success"
            )
            
        except Exception as e:
            # 记录失败的备份
            backup = DatabaseBackup(
                database_id=database_id,
                name=backup_name,
                file_path="",
                file_size=0,
                backup_type=backup_type,
                compression=compression,
                status="failed",
                error_message=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            self.db.add(backup)
            self.db.commit()
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "backup",
                f"BACKUP DATABASE `{database.name}`",
                "failed",
                str(e)
            )
    
    async def batch_backup_databases(self, database_ids: List[int], backup_type: str = "full", compression: str = "gzip"):
        """批量备份数据库"""
        for database_id in database_ids:
            await self.backup_database(database_id, backup_type, compression)
    
    async def optimize_database(self, database_id: int) -> Dict:
        """优化数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            raise ValueError("数据库不存在")
        
        try:
            # 获取数据库中的所有表
            tables = await self._get_database_tables(database.name)
            
            results = []
            for table in tables:
                # 优化表
                result = await self._execute_mysql_query(
                    f"OPTIMIZE TABLE `{database.name}`.`{table}`"
                )
                results.append({
                    "table": table,
                    "result": result
                })
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "optimize",
                f"OPTIMIZE DATABASE `{database.name}`",
                "success"
            )
            
            return {"tables": results}
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                database_id,
                "optimize",
                f"OPTIMIZE DATABASE `{database.name}`",
                "failed",
                str(e)
            )
            raise e
    
    async def repair_database(self, database_id: int) -> Dict:
        """修复数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            raise ValueError("数据库不存在")
        
        try:
            # 获取数据库中的所有表
            tables = await self._get_database_tables(database.name)
            
            results = []
            for table in tables:
                # 修复表
                result = await self._execute_mysql_query(
                    f"REPAIR TABLE `{database.name}`.`{table}`"
                )
                results.append({
                    "table": table,
                    "result": result
                })
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "repair",
                f"REPAIR DATABASE `{database.name}`",
                "success"
            )
            
            return {"tables": results}
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                database_id,
                "repair",
                f"REPAIR DATABASE `{database.name}`",
                "failed",
                str(e)
            )
            raise e
    
    async def database_user_exists(self, username: str) -> bool:
        """检查数据库用户是否存在"""
        return self.db.query(DatabaseUser).filter(DatabaseUser.username == username).first() is not None
    
    async def create_database_user(self, user_data: Dict) -> DatabaseUser:
        """创建数据库用户"""
        try:
            # 在MySQL中创建用户
            await self._create_mysql_user(
                user_data["username"],
                user_data["password"],
                user_data["host"]
            )
            
            # 授予权限
            database = self.db.query(Database).filter(Database.id == user_data["database_id"]).first()
            if database:
                await self._grant_mysql_privileges(
                    user_data["username"],
                    user_data["host"],
                    database.name,
                    user_data.get("privileges", ["ALL"])
                )
            
            # 创建用户记录
            password_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
            
            user = DatabaseUser(
                username=user_data["username"],
                password_hash=password_hash,
                database_id=user_data["database_id"],
                privileges=json.dumps(user_data.get("privileges", ["ALL"])),
                host=user_data.get("host", "%"),
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except Exception as e:
            raise e
    
    async def get_database_users(self, database_id: int) -> List[DatabaseUser]:
        """获取数据库用户列表"""
        return self.db.query(DatabaseUser).filter(DatabaseUser.database_id == database_id).all()
    
    async def delete_database_user(self, user_id: int) -> bool:
        """删除数据库用户"""
        user = self.db.query(DatabaseUser).filter(DatabaseUser.id == user_id).first()
        if not user:
            return False
        
        try:
            # 在MySQL中删除用户
            await self._drop_mysql_user(user.username, user.host)
            
            # 删除用户记录
            self.db.delete(user)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"删除数据库用户失败: {e}")
            return False
    
    async def get_database_backups(self, database_id: int) -> List[DatabaseBackup]:
        """获取数据库备份列表"""
        return self.db.query(DatabaseBackup).filter(
            DatabaseBackup.database_id == database_id
        ).order_by(DatabaseBackup.created_at.desc()).all()
    
    async def export_database(self, database_id: int, format: str = "sql"):
        """导出数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_name = f"{database.name}_export_{timestamp}"
            export_file = f"{self.backup_path}/{export_name}.{format}"
            
            # 创建导出目录
            os.makedirs(self.backup_path, exist_ok=True)
            
            if format == "sql":
                cmd = [
                    "mysqldump",
                    f"--host={self.mysql_host}",
                    f"--port={self.mysql_port}",
                    f"--user={self.mysql_root_user}",
                    f"--password={self.mysql_root_password}",
                    "--single-transaction",
                    "--routines",
                    "--triggers",
                    database.name
                ]
                
                with open(export_file, 'w') as f:
                    subprocess.run(cmd, stdout=f, check=True)
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "export",
                f"EXPORT DATABASE `{database.name}`",
                "success"
            )
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                database_id,
                "export",
                f"EXPORT DATABASE `{database.name}`",
                "failed",
                str(e)
            )
    
    async def import_database(self, database_id: int, sql_file: str):
        """导入数据库"""
        database = self.db.query(Database).filter(Database.id == database_id).first()
        if not database:
            return
        
        try:
            if not os.path.exists(sql_file):
                raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
            
            cmd = [
                "mysql",
                f"--host={self.mysql_host}",
                f"--port={self.mysql_port}",
                f"--user={self.mysql_root_user}",
                f"--password={self.mysql_root_password}",
                database.name
            ]
            
            with open(sql_file, 'r') as f:
                subprocess.run(cmd, stdin=f, check=True)
            
            # 记录操作日志
            await self._log_database_operation(
                database_id,
                "import",
                f"IMPORT DATABASE `{database.name}`",
                "success"
            )
            
        except Exception as e:
            # 记录失败日志
            await self._log_database_operation(
                database_id,
                "import",
                f"IMPORT DATABASE `{database.name}`",
                "failed",
                str(e)
            )

    async def _get_mysql_connection(self):
        """获取MySQL连接"""
        return pymysql.connect(
            host=self.mysql_host,
            port=self.mysql_port,
            user=self.mysql_root_user,
            password=self.mysql_root_password,
            charset='utf8mb4'
        )

    async def _check_mysql_database_exists(self, database_name: str) -> bool:
        """检查MySQL数据库是否存在"""
        try:
            connection = await self._get_mysql_connection()
            with connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES LIKE %s", (database_name,))
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            print(f"检查数据库存在性失败: {e}")
            return False
        finally:
            connection.close()

    async def _create_mysql_database(self, name: str, charset: str = "utf8mb4", collation: str = "utf8mb4_unicode_ci"):
        """在MySQL中创建数据库"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                sql = f"CREATE DATABASE `{name}` CHARACTER SET {charset} COLLATE {collation}"
                cursor.execute(sql)
                connection.commit()
        finally:
            connection.close()

    async def _drop_mysql_database(self, name: str):
        """在MySQL中删除数据库"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP DATABASE `{name}`")
                connection.commit()
        finally:
            connection.close()

    async def _create_mysql_user(self, username: str, password: str, host: str = "%"):
        """在MySQL中创建用户"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE USER '{username}'@'{host}' IDENTIFIED BY %s", (password,))
                connection.commit()
        finally:
            connection.close()

    async def _drop_mysql_user(self, username: str, host: str = "%"):
        """在MySQL中删除用户"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP USER '{username}'@'{host}'")
                connection.commit()
        finally:
            connection.close()

    async def _grant_mysql_privileges(self, username: str, host: str, database: str, privileges: List[str]):
        """授予MySQL用户权限"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                if "ALL" in privileges:
                    privilege_str = "ALL PRIVILEGES"
                else:
                    privilege_str = ", ".join(privileges)

                cursor.execute(f"GRANT {privilege_str} ON `{database}`.* TO '{username}'@'{host}'")
                cursor.execute("FLUSH PRIVILEGES")
                connection.commit()
        finally:
            connection.close()

    async def _get_database_tables(self, database_name: str) -> List[str]:
        """获取数据库中的所有表"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"USE `{database_name}`")
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                return tables
        finally:
            connection.close()

    async def _execute_mysql_query(self, query: str) -> Dict:
        """执行MySQL查询"""
        connection = await self._get_mysql_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                connection.commit()
                return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            connection.close()

    async def _update_database_stats(self):
        """更新所有数据库统计信息"""
        databases = self.db.query(Database).all()
        for database in databases:
            await self._update_single_database_stats(database)
        self.db.commit()

    async def _update_single_database_stats(self, database: Database):
        """更新单个数据库统计信息"""
        try:
            connection = await self._get_mysql_connection()
            with connection.cursor() as cursor:
                # 获取数据库大小
                cursor.execute("""
                    SELECT
                        ROUND(SUM(data_length + index_length), 0) as size,
                        COUNT(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = %s
                """, (database.name,))

                result = cursor.fetchone()
                if result:
                    database.size = int(result[0] or 0)
                    database.table_count = int(result[1] or 0)
                    database.updated_at = datetime.utcnow()
        except Exception as e:
            print(f"更新数据库统计信息失败: {e}")
        finally:
            connection.close()

    async def _log_database_operation(self, database_id: Optional[int], operation_type: str,
                                    operation_sql: str, status: str, error_message: str = None):
        """记录数据库操作日志"""
        try:
            operation = DatabaseOperation(
                database_id=database_id,
                operation_type=operation_type,
                operation_sql=operation_sql,
                status=status,
                result_message=error_message,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )

            self.db.add(operation)
            self.db.commit()
        except Exception as e:
            print(f"记录操作日志失败: {e}")
