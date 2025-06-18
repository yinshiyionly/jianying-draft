import os
import json
import asyncio
from typing import Dict, Any, Optional, Callable, Tuple
from .api.auth_api import AuthAPIService
from ..utils.logger import service_logger
from ..models.user import User


class AuthService:
    """认证服务
    
    处理用户认证相关的业务逻辑，如登录、注销、验证码请求等
    """
    
    def __init__(self):
        """初始化认证服务"""
        self.api_service = AuthAPIService()
        self.logger = service_logger
        self._verification_callbacks = []
        self._login_callbacks = []
        self._logout_callbacks = []
        self._current_user = None
    
    def register_verification_callback(self, callback: Callable[[bool, str], None]) -> None:
        """注册验证码发送结果回调
        
        Args:
            callback: 回调函数，接收成功状态和消息
        """
        self._verification_callbacks.append(callback)
    
    def register_login_callback(self, callback: Callable[[bool, Dict[str, Any], str], None]) -> None:
        """注册登录状态变更回调
        
        Args:
            callback: 回调函数，接收成功状态、用户信息和消息
        """
        self._login_callbacks.append(callback)
    
    def register_logout_callback(self, callback: Callable[[], None]) -> None:
        """注册登出回调
        
        Args:
            callback: 回调函数
        """
        self._logout_callbacks.append(callback)
    
    def _notify_verification_callbacks(self, success: bool, message: str) -> None:
        """通知验证码回调

        Args:
            success: 是否成功
            message: 消息
        """
        for callback in self._verification_callbacks:
            try:
                callback(success, message)
            except Exception as e:
                self.logger.error(f"Error in verification callback: {str(e)}")
    
    def _notify_login_callbacks(self, success: bool, user_info: Dict[str, Any], message: str) -> None:
        """通知登录回调

        Args:
            success: 是否成功
            user_info: 用户信息
            message: 消息
        """
        for callback in self._login_callbacks:
            try:
                callback(success, user_info, message)
            except Exception as e:
                self.logger.error(f"Error in login callback: {str(e)}")
    
    def _notify_logout_callbacks(self) -> None:
        """通知登出回调"""
        for callback in self._logout_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in logout callback: {str(e)}")
    
    async def request_verification_code(self, phone: str) -> Tuple[bool, str]:
        """请求验证码
        
        Args:
            phone: 手机号码
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证手机号格式
            if not self._validate_phone(phone):
                message = "手机号格式不正确"
                self._notify_verification_callbacks(False, message)
                return False, message
            
            # 调用API获取验证码
            response = await self.api_service.request_verification_code(phone)
            
            # 检查响应
            if response.get("success", False):
                message = "验证码已发送"
                self._notify_verification_callbacks(True, message)
                return True, message
            else:
                message = response.get("message", "获取验证码失败")
                self._notify_verification_callbacks(False, message)
                return False, message
                
        except Exception as e:
            message = f"获取验证码出错: {str(e)}"
            self.logger.error(message)
            self._notify_verification_callbacks(False, message)
            return False, message
    
    async def login(self, phone: str, code: str) -> Tuple[bool, Dict[str, Any], str]:
        """使用验证码登录
        
        Args:
            phone: 手机号码
            code: 验证码
            
        Returns:
            Tuple[bool, Dict[str, Any], str]: (是否成功, 用户信息, 消息)
        """
        try:
            # 验证手机号和验证码
            if not self._validate_phone(phone):
                message = "手机号格式不正确"
                self._notify_login_callbacks(False, {}, message)
                return False, {}, message
                
            if not code or len(code.strip()) != 6:
                message = "验证码必须是6位数字"
                self._notify_login_callbacks(False, {}, message)
                return False, {}, message
            
            # 调用API登录
            response = await self.api_service.login_with_verification_code(phone, code)
            
            # 检查响应
            if response.get("success", False):
                # 提取用户信息和令牌
                user_info = response.get("data", {}).get("user_info", {})
                token = response.get("data", {}).get("token", "")
                
                # 保存到数据库
                user = User.save_from_api_response(user_info, token)
                self._current_user = user
                
                message = "登录成功"
                self._notify_login_callbacks(True, user.to_dict(), message)
                return True, user.to_dict(), message
            else:
                message = response.get("message", "登录失败")
                self._notify_login_callbacks(False, {}, message)
                return False, {}, message
                
        except Exception as e:
            message = f"登录出错: {str(e)}"
            self.logger.error(message)
            self._notify_login_callbacks(False, {}, message)
            return False, {}, message
    
    def logout(self) -> None:
        """退出登录"""
        if self._current_user:
            self._current_user = None
            self._notify_logout_callbacks()
            self.logger.info("User logged out")
    
    def is_logged_in(self) -> bool:
        """检查用户是否已登录
        
        Returns:
            bool: 是否已登录
        """
        return self._current_user is not None
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息
        
        Returns:
            Dict[str, Any]: 用户信息
        """
        if self._current_user:
            return self._current_user.to_dict()
        return {}
    
    def get_token(self) -> Optional[str]:
        """获取认证令牌
        
        Returns:
            Optional[str]: 认证令牌
        """
        if self._current_user:
            return self._current_user.token
        return None
    
    def get_current_user(self) -> Optional[User]:
        """获取当前用户对象
        
        Returns:
            Optional[User]: 用户对象
        """
        return self._current_user
    
    def get_current_user_id(self) -> Optional[int]:
        """获取当前用户ID
        
        Returns:
            Optional[int]: 用户ID
        """
        if self._current_user:
            return self._current_user.id
        return None
    
    async def validate_current_token(self) -> bool:
        """验证当前存储的令牌是否有效
        
        Returns:
            bool: 令牌是否有效
        """
        token = self.get_token()
        if not token:
            return False
            
        try:
            response = await self.api_service.validate_token(token)
            return response.get("success", False)
        except:
            return False
    
    def _validate_phone(self, phone: str) -> bool:
        """验证手机号格式
        
        Args:
            phone: 手机号码
            
        Returns:
            bool: 是否为有效手机号
        """
        # 简单验证手机号格式（中国大陆11位手机号）
        if not phone or not phone.isdigit() or len(phone) != 11:
            return False
        return True
    
    def load_last_logged_in_user(self) -> None:
        """加载最后登录的用户"""
        try:
            # 查询最近登录的用户
            users = User.get_all()
            if users:
                # 假设最近登录的用户在列表的第一个位置
                self._current_user = users[0]
                self.logger.info(f"加载最近登录用户: {self._current_user.username}")
        except Exception as e:
            self.logger.error(f"加载最近登录用户失败: {str(e)}")


# 创建单例实例
auth_service = AuthService() 