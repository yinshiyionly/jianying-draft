import os
import sqlite3
import threading
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
import json
import logging

# 获取logger
from .logger import get_logger
db_logger = get_logger("database")

# 数据库文件路径
DB_PATH = os.path.join(os.path.expanduser("~"), ".jy_draft", "database.sqlite")


class Database:
    """SQLite数据库管理类"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """初始化数据库连接"""
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = db_logger
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        # 创建数据库连接
        self.conn = None
        self.connect()
        
        # 初始化数据库表
        self.init_database()
    
    def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 配置返回行为字典
            self.conn.row_factory = sqlite3.Row
            self.logger.info(f"数据库连接成功: {DB_PATH}")
        except Exception as e:
            self.logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("数据库连接已关闭")
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if not self.conn:
            self.connect()
        return self.conn
    
    def execute(self, query: str, params: Tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            sqlite3.Cursor: 游标对象
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            self.logger.error(f"SQL执行错误: {query}, 参数: {params}, 错误: {str(e)}")
            conn.rollback()
            raise
    
    def executemany(self, query: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        """批量执行SQL语句
        
        Args:
            query: SQL查询语句
            params_list: 参数列表
            
        Returns:
            sqlite3.Cursor: 游标对象
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor
        except Exception as e:
            self.logger.error(f"批量SQL执行错误: {query}, 错误: {str(e)}")
            conn.rollback()
            raise
    
    def query_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """查询单条记录
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果，无结果时返回None
        """
        try:
            cursor = self.execute(query, params)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            self.logger.error(f"查询错误: {query}, 参数: {params}, 错误: {str(e)}")
            raise
    
    def query_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """查询多条记录
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            cursor = self.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"查询错误: {query}, 参数: {params}, 错误: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 表是否存在
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.query_one(query, (table_name,))
        return result is not None
    
    def init_database(self) -> None:
        """初始化数据库表结构"""
        try:
            # 创建用户表
            self.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT UNIQUE,
                    username TEXT,
                    nickname TEXT,
                    avatar TEXT,
                    token TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建下载任务表
            self.execute("""
                CREATE TABLE IF NOT EXISTS download_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_name TEXT,
                    file_url TEXT,
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    downloaded_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            self.logger.info("数据库表初始化完成")
        except Exception as e:
            self.logger.error(f"数据库表初始化失败: {str(e)}")
            raise
    
    def add_column_if_not_exists(self, table: str, column: str, definition: str) -> None:
        """添加列如果不存在
        
        Args:
            table: 表名
            column: 列名
            definition: 列定义
        """
        try:
            # 检查列是否存在
            query = f"PRAGMA table_info({table})"
            columns = self.query_all(query)
            column_exists = any(col['name'] == column for col in columns)
            
            if not column_exists:
                # 添加列
                alter_query = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                self.execute(alter_query)
                self.logger.info(f"表 {table} 添加列 {column} 成功")
        except Exception as e:
            self.logger.error(f"添加列失败: {str(e)}")
            raise


# 创建单例实例
db = Database() 