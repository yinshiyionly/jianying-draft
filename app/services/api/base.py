from typing import Optional, Dict, Any
from ...utils.http import HTTPClient
from ...config import settings
from ...utils.logger import api_logger


class BaseAPIService:
    """API服务基类
    
    提供基础的API调用功能，所有具体的API服务类都应该继承这个类。
    """
    
    def __init__(self):
        """初始化API服务
        
        创建HTTP客户端并设置基础URL
        """
        self.client = HTTPClient(
            base_url=settings.API_BASE_URL,
            timeout=settings.API_TIMEOUT
        )
        self.logger = api_logger

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """统一的错误处理方法
        
        Args:
            error: 异常对象
            context: 错误发生的上下文描述
        """
        error_msg = f"{context} - Error: {str(error)}"
        self.logger.error(error_msg)
        if settings.SHOW_DETAILED_ERRORS:
            raise error
        raise Exception(error_msg)

    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送API请求的通用方法
        
        Args:
            method: HTTP方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            **kwargs: 其他请求参数
            
        Returns:
            Dict[str, Any]: API响应数据
        """
        try:
            return self.client.request(
                method=method,
                endpoint=endpoint,
                params=params,
                data=data,
                **kwargs
            )
        except Exception as e:
            self._handle_error(e, f"Failed to {method} {endpoint}") 