from typing import Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from ..config import settings
from .logger import api_logger


class HTTPClient:
    """HTTP客户端工具类
    
    提供统一的HTTP请求处理，包括：
    - 自动重试机制
    - 超时控制
    - 错误处理
    - 日志记录
    """

    def __init__(self, base_url: str = "", timeout: int = None):
        """初始化HTTP客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or settings.API_TIMEOUT
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建配置好的requests会话
        
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=settings.API_RETRY_COUNT,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        
        # 配置适配器
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _build_url(self, endpoint: str) -> str:
        """构建完整的URL
        
        Args:
            endpoint: API端点路径
            
        Returns:
            str: 完整的URL
        """
        endpoint = endpoint.lstrip('/')
        return f"{self.base_url}/{endpoint}" if self.base_url else endpoint

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """获取请求头
        
        Args:
            additional_headers: 额外的请求头
            
        Returns:
            Dict[str, str]: 合并后的请求头
        """
        headers = {
            'Content-Type': 'application/json'
        }
        
        # 添加API Token（如果配置了的话）
        if settings.API_TOKEN:
            headers['Authorization'] = f'Bearer {settings.API_TOKEN}'
            
        # 合并额外的请求头
        if additional_headers:
            headers.update(additional_headers)
            
        return headers

    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求日志
        
        Args:
            method: 请求方法
            url: 请求URL
            **kwargs: 请求参数
        """
        api_logger.info(f"API Request: {method} {url}")
        if kwargs.get('params'):
            api_logger.debug(f"Query Params: {kwargs['params']}")
        if kwargs.get('json'):
            api_logger.debug(f"Request Body: {kwargs['json']}")

    def _log_response(self, response: requests.Response):
        """记录响应日志
        
        Args:
            response: 响应对象
        """
        api_logger.info(f"API Response: {response.status_code} {response.reason}")
        api_logger.debug(f"Response Body: {response.text}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """处理响应
        
        Args:
            response: 响应对象
            
        Returns:
            Dict[str, Any]: 响应数据
            
        Raises:
            requests.exceptions.HTTPError: 当响应状态码不是2xx时
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.JSONDecodeError:
            api_logger.error("Failed to decode JSON response")
            return {'text': response.text}
        except requests.exceptions.HTTPError as e:
            api_logger.error(f"HTTP Error: {str(e)}")
            raise

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            method: 请求方法
            endpoint: API端点
            params: URL参数
            data: 请求体数据
            headers: 额外的请求头
            **kwargs: 其他请求参数
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        url = self._build_url(endpoint)
        headers = self._get_headers(headers)
        
        kwargs.update({
            'timeout': self.timeout,
            'headers': headers,
            'params': params,
            'json': data
        })
        
        self._log_request(method, url, **kwargs)
        
        try:
            response = self.session.request(method, url, **kwargs)
            self._log_response(response)
            return self._handle_response(response)
        except Exception as e:
            api_logger.error(f"Request failed: {str(e)}")
            raise

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送GET请求"""
        return self.request('GET', endpoint, params=params, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送POST请求"""
        return self.request('POST', endpoint, data=data, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PUT请求"""
        return self.request('PUT', endpoint, data=data, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送DELETE请求"""
        return self.request('DELETE', endpoint, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """发送PATCH请求"""
        return self.request('PATCH', endpoint, data=data, **kwargs) 