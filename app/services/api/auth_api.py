from typing import Dict, Any, Optional
from .base import BaseAPIService


class AuthAPIService(BaseAPIService):
    """认证相关的API服务
    
    提供登录、获取验证码等认证相关的API调用
    """
    
    async def request_verification_code(self, phone: str) -> Dict[str, Any]:
        """请求手机验证码
        
        Args:
            phone: 手机号码
            
        Returns:
            Dict[str, Any]: 包含请求结果的字典
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        try:
            endpoint = "/auth/verification-code"
            data = {"phone": phone}
            
            self.logger.info(f"Requesting verification code for phone: {phone[:3]}****{phone[-4:]}")
            
            response = await self.make_request(
                method="POST",
                endpoint=endpoint,
                data=data
            )
            
            self.logger.info("Verification code requested successfully")
            return response
        except Exception as e:
            self._handle_error(e, "Failed to request verification code")
    
    async def login_with_verification_code(self, phone: str, code: str) -> Dict[str, Any]:
        """使用验证码登录
        
        Args:
            phone: 手机号码
            code: 验证码
            
        Returns:
            Dict[str, Any]: 包含用户信息和认证令牌的字典
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        try:
            endpoint = "/auth/login"
            data = {
                "phone": phone,
                "code": code,
                "login_type": "verification_code"
            }
            
            self.logger.info(f"Logging in with phone: {phone[:3]}****{phone[-4:]}")
            
            response = await self.make_request(
                method="POST",
                endpoint=endpoint,
                data=data
            )
            
            self.logger.info("Login successful")
            return response
        except Exception as e:
            self._handle_error(e, "Failed to login with verification code")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """验证token是否有效
        
        Args:
            token: 认证令牌
            
        Returns:
            Dict[str, Any]: 包含验证结果的字典
            
        Raises:
            Exception: 当API调用失败时抛出异常
        """
        try:
            endpoint = "/auth/validate-token"
            headers = {"Authorization": f"Bearer {token}"}
            
            self.logger.info("Validating authentication token")
            
            response = await self.make_request(
                method="GET",
                endpoint=endpoint,
                headers=headers
            )
            
            self.logger.info("Token validation successful")
            return response
        except Exception as e:
            self._handle_error(e, "Failed to validate token") 