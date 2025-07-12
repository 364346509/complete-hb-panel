#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户服务
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User, LoginLog
from app.core.security import verify_password, get_password_hash


class UserService:
    """用户服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_user(self, username: str, email: str, password: str, 
                   full_name: str = None, is_superuser: bool = False) -> User:
        """创建用户"""
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_superuser=is_superuser,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """更新用户信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def change_password(self, user_id: int, new_password: str) -> bool:
        """修改密码"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return True
    
    def deactivate_user(self, user_id: int) -> bool:
        """禁用用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        return True
    
    def activate_user(self, user_id: int) -> bool:
        """激活用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.is_active = True
        self.db.commit()
        return True
    
    def log_login(self, user_id: int, login_type: str, ip_address: str = None, 
                  user_agent: str = None) -> LoginLog:
        """记录登录日志"""
        log = LoginLog(
            user_id=user_id,
            login_type=login_type,
            ip_address=ip_address,
            user_agent=user_agent,
            login_time=datetime.utcnow()
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_login_logs(self, user_id: int = None, limit: int = 50):
        """获取登录日志"""
        query = self.db.query(LoginLog)
        if user_id:
            query = query.filter(LoginLog.user_id == user_id)
        return query.order_by(LoginLog.login_time.desc()).limit(limit).all()

    def get_users(self, page: int = 1, size: int = 20, search: str = None):
        """获取用户列表"""
        query = self.db.query(User)

        if search:
            query = query.filter(
                User.username.contains(search) |
                User.email.contains(search) |
                User.full_name.contains(search)
            )

        offset = (page - 1) * size
        return query.offset(offset).limit(size).all()

    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True
