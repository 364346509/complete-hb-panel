#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理服务
"""

import os
import shutil
import stat
import mimetypes
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.core.config import settings


class FileService:
    """文件管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def list_files(self, path: str, show_hidden: bool = False) -> List[Dict]:
        """获取文件列表"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"路径不存在: {path}")
            
            if not path_obj.is_dir():
                raise NotADirectoryError(f"不是目录: {path}")
            
            files = []
            
            for item in path_obj.iterdir():
                # 跳过隐藏文件（除非明确要求显示）
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    stat_info = item.stat()
                    
                    file_info = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat_info.st_size if item.is_file() else 0,
                        "permissions": oct(stat_info.st_mode)[-3:],
                        "owner": self._get_owner_name(stat_info.st_uid),
                        "group": self._get_group_name(stat_info.st_gid),
                        "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "is_hidden": item.name.startswith('.'),
                        "mime_type": mimetypes.guess_type(str(item))[0] if item.is_file() else None
                    }
                    
                    files.append(file_info)
                    
                except (OSError, PermissionError):
                    # 跳过无法访问的文件
                    continue
            
            # 排序：目录在前，然后按名称排序
            files.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return files
            
        except Exception as e:
            raise Exception(f"获取文件列表失败: {str(e)}")
    
    async def get_file_info(self, path: str) -> Dict:
        """获取文件详细信息"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            stat_info = path_obj.stat()
            
            info = {
                "name": path_obj.name,
                "path": str(path_obj),
                "absolute_path": str(path_obj.absolute()),
                "type": "directory" if path_obj.is_dir() else "file",
                "size": stat_info.st_size,
                "permissions": oct(stat_info.st_mode)[-3:],
                "owner": self._get_owner_name(stat_info.st_uid),
                "group": self._get_group_name(stat_info.st_gid),
                "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
                "is_hidden": path_obj.name.startswith('.'),
                "is_symlink": path_obj.is_symlink(),
                "mime_type": mimetypes.guess_type(str(path_obj))[0] if path_obj.is_file() else None
            }
            
            if path_obj.is_symlink():
                info["link_target"] = str(path_obj.readlink())
            
            if path_obj.is_dir():
                try:
                    info["item_count"] = len(list(path_obj.iterdir()))
                except PermissionError:
                    info["item_count"] = 0
            
            return info
            
        except Exception as e:
            raise Exception(f"获取文件信息失败: {str(e)}")
    
    async def get_file_content(self, path: str) -> str:
        """获取文件内容"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            if not path_obj.is_file():
                raise IsADirectoryError(f"不是文件: {path}")
            
            # 检查文件大小（限制为10MB）
            if path_obj.stat().st_size > 10 * 1024 * 1024:
                raise ValueError("文件太大，无法在编辑器中打开")
            
            # 尝试以文本模式读取
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                for encoding in ['gbk', 'gb2312', 'latin1']:
                    try:
                        with open(path_obj, 'r', encoding=encoding) as f:
                            return f.read()
                    except UnicodeDecodeError:
                        continue
                
                raise UnicodeDecodeError("无法解码文件内容")
                
        except Exception as e:
            raise Exception(f"读取文件内容失败: {str(e)}")
    
    async def save_file_content(self, path: str, content: str):
        """保存文件内容"""
        try:
            path_obj = Path(path)
            
            # 创建目录（如果不存在）
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # 备份原文件（如果存在）
            if path_obj.exists():
                backup_path = path_obj.with_suffix(path_obj.suffix + '.bak')
                shutil.copy2(path_obj, backup_path)
            
            # 保存文件
            with open(path_obj, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            raise Exception(f"保存文件失败: {str(e)}")
    
    async def upload_file(self, directory: str, file: UploadFile) -> str:
        """上传文件"""
        try:
            dir_path = Path(directory)
            
            # 确保目录存在
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # 生成文件路径
            file_path = dir_path / file.filename
            
            # 如果文件已存在，生成新名称
            counter = 1
            original_path = file_path
            while file_path.exists():
                stem = original_path.stem
                suffix = original_path.suffix
                file_path = dir_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # 保存文件
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            return str(file_path)
            
        except Exception as e:
            raise Exception(f"上传文件失败: {str(e)}")
    
    async def execute_action(self, action: str, source: str, target: str = None) -> bool:
        """执行文件操作"""
        try:
            source_path = Path(source)
            
            if not source_path.exists():
                raise FileNotFoundError(f"源文件不存在: {source}")
            
            if action == "delete":
                if source_path.is_dir():
                    shutil.rmtree(source_path)
                else:
                    source_path.unlink()
                return True
            
            elif action in ["copy", "move"]:
                if not target:
                    raise ValueError("目标路径不能为空")
                
                target_path = Path(target)
                
                if action == "copy":
                    if source_path.is_dir():
                        shutil.copytree(source_path, target_path)
                    else:
                        shutil.copy2(source_path, target_path)
                else:  # move
                    shutil.move(str(source_path), str(target_path))
                
                return True
            
            elif action == "rename":
                if not target:
                    raise ValueError("新名称不能为空")
                
                target_path = source_path.parent / target
                source_path.rename(target_path)
                return True
            
            else:
                raise ValueError(f"不支持的操作: {action}")
                
        except Exception as e:
            raise Exception(f"文件操作失败: {str(e)}")
    
    async def create_directory(self, path: str):
        """创建目录"""
        try:
            path_obj = Path(path)
            path_obj.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            raise FileExistsError(f"目录已存在: {path}")
        except Exception as e:
            raise Exception(f"创建目录失败: {str(e)}")
    
    async def change_permissions(self, path: str, permissions: str):
        """修改文件权限"""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"文件不存在: {path}")
            
            # 验证权限格式（三位八进制数）
            if not permissions.isdigit() or len(permissions) != 3:
                raise ValueError("权限格式错误，应为三位数字（如755）")
            
            # 转换为八进制
            mode = int(permissions, 8)
            path_obj.chmod(mode)
            
        except Exception as e:
            raise Exception(f"修改权限失败: {str(e)}")
    
    async def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return Path(path).exists()
    
    def _get_owner_name(self, uid: int) -> str:
        """获取用户名"""
        try:
            import pwd
            return pwd.getpwuid(uid).pw_name
        except:
            return str(uid)
    
    def _get_group_name(self, gid: int) -> str:
        """获取组名"""
        try:
            import grp
            return grp.getgrgid(gid).gr_name
        except:
            return str(gid)
