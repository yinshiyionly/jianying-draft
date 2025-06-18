from typing import Optional, Dict, Any, List
from datetime import datetime
import time

from ..utils.database import db


class User:
    """用户模型类"""
    
    def __init__(self, user_data: Dict[str, Any] = None):
        """初始化用户模型
        
        Args:
            user_data: 用户数据字典
        """
        self.id = None
        self.phone = None
        self.username = None
        self.nickname = None
        self.avatar = None
        self.token = None
        self.created_at = None
        self.updated_at = None
        
        if user_data:
            self._populate_from_dict(user_data)
    
    def _populate_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典填充用户数据
        
        Args:
            data: 数据字典
        """
        self.id = data.get('id')
        self.phone = data.get('phone')
        self.username = data.get('username')
        self.nickname = data.get('nickname')
        self.avatar = data.get('avatar')
        self.token = data.get('token')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 用户数据字典
        """
        return {
            'id': self.id,
            'phone': self.phone,
            'username': self.username,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'token': self.token,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def save(self) -> bool:
        """保存用户数据
        
        Returns:
            bool: 是否成功
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.id:
            # 更新现有用户
            query = """
                UPDATE users SET
                    phone = ?,
                    username = ?,
                    nickname = ?,
                    avatar = ?,
                    token = ?,
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                self.phone,
                self.username,
                self.nickname,
                self.avatar,
                self.token,
                current_time,
                self.id
            )
            db.execute(query, params)
            return True
        else:
            # 创建新用户
            query = """
                INSERT INTO users (
                    phone, username, nickname, avatar, token, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.phone,
                self.username,
                self.nickname,
                self.avatar,
                self.token,
                current_time,
                current_time
            )
            cursor = db.execute(query, params)
            self.id = cursor.lastrowid
            return True
    
    def delete(self) -> bool:
        """删除用户
        
        Returns:
            bool: 是否成功
        """
        if not self.id:
            return False
            
        query = "DELETE FROM users WHERE id = ?"
        db.execute(query, (self.id,))
        return True
    
    @classmethod
    def get_by_id(cls, user_id: int) -> Optional['User']:
        """通过ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户对象，不存在时返回None
        """
        query = "SELECT * FROM users WHERE id = ?"
        result = db.query_one(query, (user_id,))
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_by_phone(cls, phone: str) -> Optional['User']:
        """通过手机号获取用户
        
        Args:
            phone: 手机号
            
        Returns:
            Optional[User]: 用户对象，不存在时返回None
        """
        query = "SELECT * FROM users WHERE phone = ?"
        result = db.query_one(query, (phone,))
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_by_token(cls, token: str) -> Optional['User']:
        """通过令牌获取用户
        
        Args:
            token: 认证令牌
            
        Returns:
            Optional[User]: 用户对象，不存在时返回None
        """
        query = "SELECT * FROM users WHERE token = ?"
        result = db.query_one(query, (token,))
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_all(cls) -> List['User']:
        """获取所有用户
        
        Returns:
            List[User]: 用户对象列表
        """
        query = "SELECT * FROM users ORDER BY id DESC"
        results = db.query_all(query)
        return [cls(result) for result in results]
    
    @classmethod
    def save_from_api_response(cls, user_info: Dict[str, Any], token: str) -> 'User':
        """从API响应保存用户
        
        Args:
            user_info: API返回的用户信息
            token: 认证令牌
            
        Returns:
            User: 保存后的用户对象
        """
        phone = user_info.get('phone')
        
        # 检查用户是否已存在
        user = cls.get_by_phone(phone) if phone else None
        
        if not user:
            user = cls()
        
        # 更新用户信息
        user.phone = phone
        user.username = user_info.get('username')
        user.nickname = user_info.get('nickname') or user_info.get('username')
        user.avatar = user_info.get('avatar')
        user.token = token
        
        # 保存到数据库
        user.save()
        
        return user 