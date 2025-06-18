from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import os
import time
import math

from ..utils.database import db


class DownloadTask:
    """下载任务模型类"""
    
    # 任务状态常量
    STATUS_PENDING = 'pending'     # 等待下载
    STATUS_DOWNLOADING = 'downloading'  # 下载中
    STATUS_COMPLETED = 'completed'  # 下载完成
    STATUS_FAILED = 'failed'        # 下载失败
    STATUS_PAUSED = 'paused'        # 暂停下载
    STATUS_CANCELED = 'canceled'    # 取消下载
    
    def __init__(self, task_data: Dict[str, Any] = None):
        """初始化下载任务模型
        
        Args:
            task_data: 任务数据字典
        """
        self.id = None
        self.user_id = None
        self.task_name = None
        self.file_url = None
        self.file_path = None
        self.file_size = 0
        self.downloaded_size = 0
        self.status = self.STATUS_PENDING
        self.error_message = None
        self.created_at = None
        self.updated_at = None
        self.completed_at = None
        
        if task_data:
            self._populate_from_dict(task_data)
    
    def _populate_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典填充任务数据
        
        Args:
            data: 数据字典
        """
        self.id = data.get('id')
        self.user_id = data.get('user_id')
        self.task_name = data.get('task_name')
        self.file_url = data.get('file_url')
        self.file_path = data.get('file_path')
        self.file_size = data.get('file_size', 0)
        self.downloaded_size = data.get('downloaded_size', 0)
        self.status = data.get('status', self.STATUS_PENDING)
        self.error_message = data.get('error_message')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
        self.completed_at = data.get('completed_at')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 任务数据字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_name': self.task_name,
            'file_url': self.file_url,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'downloaded_size': self.downloaded_size,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at
        }
    
    @property
    def progress(self) -> float:
        """下载进度
        
        Returns:
            float: 进度百分比 (0-100)
        """
        if self.file_size <= 0:
            return 0
        return min(100, (self.downloaded_size / self.file_size) * 100)
    
    @property
    def progress_text(self) -> str:
        """格式化的进度文本
        
        Returns:
            str: 格式化的进度
        """
        return f"{self.progress:.1f}%"
    
    @property
    def is_completed(self) -> bool:
        """是否已完成
        
        Returns:
            bool: 是否已完成
        """
        return self.status == self.STATUS_COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """是否失败
        
        Returns:
            bool: 是否失败
        """
        return self.status == self.STATUS_FAILED
    
    @property
    def is_paused(self) -> bool:
        """是否暂停
        
        Returns:
            bool: 是否暂停
        """
        return self.status == self.STATUS_PAUSED
    
    @property
    def is_active(self) -> bool:
        """是否处于活动状态
        
        Returns:
            bool: 是否活动中
        """
        return self.status in [self.STATUS_DOWNLOADING, self.STATUS_PENDING]
    
    @property
    def can_resume(self) -> bool:
        """是否可以恢复下载
        
        Returns:
            bool: 是否可以恢复
        """
        return self.status in [self.STATUS_PAUSED, self.STATUS_FAILED]
    
    @property
    def can_restart(self) -> bool:
        """是否可以重新开始
        
        Returns:
            bool: 是否可以重新开始
        """
        return self.status in [self.STATUS_COMPLETED, self.STATUS_FAILED, self.STATUS_CANCELED]
    
    @property
    def filename(self) -> str:
        """获取文件名
        
        Returns:
            str: 文件名
        """
        if self.file_path:
            return os.path.basename(self.file_path)
        return ""
    
    @property
    def file_extension(self) -> str:
        """获取文件扩展名
        
        Returns:
            str: 文件扩展名
        """
        if self.filename:
            _, ext = os.path.splitext(self.filename)
            return ext.lower()
        return ""
    
    @property
    def formatted_size(self) -> str:
        """格式化文件大小
        
        Returns:
            str: 格式化后的大小字符串
        """
        return self._format_size(self.file_size)
    
    @property
    def formatted_downloaded(self) -> str:
        """格式化已下载大小
        
        Returns:
            str: 格式化后的大小字符串
        """
        return self._format_size(self.downloaded_size)
    
    @property
    def status_text(self) -> str:
        """获取状态文本
        
        Returns:
            str: 状态描述
        """
        status_map = {
            self.STATUS_PENDING: "等待下载",
            self.STATUS_DOWNLOADING: "下载中",
            self.STATUS_COMPLETED: "已完成",
            self.STATUS_FAILED: "下载失败",
            self.STATUS_PAUSED: "已暂停",
            self.STATUS_CANCELED: "已取消"
        }
        return status_map.get(self.status, self.status)
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化字节大小为易读字符串
        
        Args:
            size_bytes: 字节大小
            
        Returns:
            str: 格式化后的大小字符串
        """
        if size_bytes <= 0:
            return "0 B"
            
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024
            i += 1
            
        return f"{size_bytes:.2f} {units[i]}"
    
    def save(self) -> bool:
        """保存任务数据
        
        Returns:
            bool: 是否成功
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.id:
            # 更新现有任务
            query = """
                UPDATE download_tasks SET
                    user_id = ?,
                    task_name = ?,
                    file_url = ?,
                    file_path = ?,
                    file_size = ?,
                    downloaded_size = ?,
                    status = ?,
                    error_message = ?,
                    updated_at = ?,
                    completed_at = ?
                WHERE id = ?
            """
            params = (
                self.user_id,
                self.task_name,
                self.file_url,
                self.file_path,
                self.file_size,
                self.downloaded_size,
                self.status,
                self.error_message,
                current_time,
                self.completed_at,
                self.id
            )
            db.execute(query, params)
            return True
        else:
            # 创建新任务
            query = """
                INSERT INTO download_tasks (
                    user_id, task_name, file_url, file_path, file_size,
                    downloaded_size, status, error_message, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                self.user_id,
                self.task_name,
                self.file_url,
                self.file_path,
                self.file_size,
                self.downloaded_size,
                self.status,
                self.error_message,
                current_time,
                current_time
            )
            cursor = db.execute(query, params)
            self.id = cursor.lastrowid
            return True
    
    def update_progress(self, downloaded_size: int, file_size: Optional[int] = None) -> None:
        """更新下载进度
        
        Args:
            downloaded_size: 已下载大小
            file_size: 文件总大小，如果提供则更新
        """
        self.downloaded_size = downloaded_size
        if file_size is not None:
            self.file_size = file_size
        
        # 更新状态为下载中
        if self.status != self.STATUS_DOWNLOADING:
            self.status = self.STATUS_DOWNLOADING
        
        # 检查是否下载完成
        if self.file_size > 0 and self.downloaded_size >= self.file_size:
            self.mark_as_completed()
        else:
            # 只更新进度，不更新状态
            self._update_progress_only()
    
    def _update_progress_only(self) -> None:
        """仅更新下载进度信息，不修改其他字段"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if self.id:
            query = """
                UPDATE download_tasks SET
                    downloaded_size = ?,
                    file_size = ?,
                    updated_at = ?
                WHERE id = ?
            """
            params = (
                self.downloaded_size,
                self.file_size,
                current_time,
                self.id
            )
            db.execute(query, params)
    
    def mark_as_completed(self) -> None:
        """标记任务为已完成"""
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save()
    
    def mark_as_failed(self, error_message: str) -> None:
        """标记任务为失败
        
        Args:
            error_message: 错误信息
        """
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.save()
    
    def mark_as_paused(self) -> None:
        """标记任务为暂停"""
        self.status = self.STATUS_PAUSED
        self.save()
    
    def mark_as_canceled(self) -> None:
        """标记任务为取消"""
        self.status = self.STATUS_CANCELED
        self.save()
    
    def resume(self) -> None:
        """恢复下载任务"""
        if self.can_resume:
            self.status = self.STATUS_DOWNLOADING
            self.error_message = None
            self.save()
    
    def restart(self) -> None:
        """重新开始下载任务"""
        self.status = self.STATUS_PENDING
        self.downloaded_size = 0
        self.error_message = None
        self.completed_at = None
        self.save()
    
    def delete(self) -> bool:
        """删除任务
        
        Returns:
            bool: 是否成功
        """
        if not self.id:
            return False
            
        query = "DELETE FROM download_tasks WHERE id = ?"
        db.execute(query, (self.id,))
        return True
    
    @classmethod
    def get_by_id(cls, task_id: int) -> Optional['DownloadTask']:
        """通过ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[DownloadTask]: 任务对象，不存在时返回None
        """
        query = "SELECT * FROM download_tasks WHERE id = ?"
        result = db.query_one(query, (task_id,))
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_by_url(cls, file_url: str, user_id: Optional[int] = None) -> Optional['DownloadTask']:
        """通过URL获取任务
        
        Args:
            file_url: 文件URL
            user_id: 用户ID
            
        Returns:
            Optional[DownloadTask]: 任务对象，不存在时返回None
        """
        if user_id:
            query = "SELECT * FROM download_tasks WHERE file_url = ? AND user_id = ?"
            result = db.query_one(query, (file_url, user_id))
        else:
            query = "SELECT * FROM download_tasks WHERE file_url = ?"
            result = db.query_one(query, (file_url,))
            
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_by_file_path(cls, file_path: str) -> Optional['DownloadTask']:
        """通过文件路径获取任务
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[DownloadTask]: 任务对象，不存在时返回None
        """
        query = "SELECT * FROM download_tasks WHERE file_path = ?"
        result = db.query_one(query, (file_path,))
        if result:
            return cls(result)
        return None
    
    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List['DownloadTask']:
        """获取所有任务
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[DownloadTask]: 任务对象列表
        """
        query = "SELECT * FROM download_tasks ORDER BY id DESC LIMIT ? OFFSET ?"
        results = db.query_all(query, (limit, offset))
        return [cls(result) for result in results]
    
    @classmethod
    def get_by_user(cls, user_id: int, limit: int = 100, offset: int = 0) -> List['DownloadTask']:
        """获取用户的任务
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[DownloadTask]: 任务对象列表
        """
        query = """
            SELECT * FROM download_tasks 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT ? OFFSET ?
        """
        results = db.query_all(query, (user_id, limit, offset))
        return [cls(result) for result in results]
    
    @classmethod
    def get_by_status(cls, status: str, user_id: Optional[int] = None) -> List['DownloadTask']:
        """获取指定状态的任务
        
        Args:
            status: 任务状态
            user_id: 用户ID
            
        Returns:
            List[DownloadTask]: 任务对象列表
        """
        if user_id:
            query = """
                SELECT * FROM download_tasks 
                WHERE status = ? AND user_id = ? 
                ORDER BY id DESC
            """
            results = db.query_all(query, (status, user_id))
        else:
            query = """
                SELECT * FROM download_tasks 
                WHERE status = ? 
                ORDER BY id DESC
            """
            results = db.query_all(query, (status,))
            
        return [cls(result) for result in results]
    
    @classmethod
    def get_active_tasks(cls) -> List['DownloadTask']:
        """获取所有活动中的任务（下载中或暂停）
        
        Returns:
            List[DownloadTask]: 任务对象列表
        """
        query = """
            SELECT * FROM download_tasks 
            WHERE status IN (?, ?) 
            ORDER BY updated_at DESC
        """
        results = db.query_all(query, (cls.STATUS_DOWNLOADING, cls.STATUS_PAUSED))
        return [cls(result) for result in results]
    
    @classmethod
    def count_by_status(cls, status: str, user_id: Optional[int] = None) -> int:
        """统计指定状态的任务数量
        
        Args:
            status: 任务状态
            user_id: 用户ID
            
        Returns:
            int: 任务数量
        """
        if user_id:
            query = """
                SELECT COUNT(*) as count FROM download_tasks 
                WHERE status = ? AND user_id = ?
            """
            result = db.query_one(query, (status, user_id))
        else:
            query = """
                SELECT COUNT(*) as count FROM download_tasks 
                WHERE status = ?
            """
            result = db.query_one(query, (status,))
            
        return result.get('count', 0) if result else 0 