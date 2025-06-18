from typing import Dict, Any, List, Optional
from .base import BaseAPIService


class DraftService(BaseAPIService):
    """草稿箱API服务
    
    处理与草稿相关的所有API请求
    """
    
    def __init__(self):
        """初始化草稿箱服务"""
        super().__init__()
        self.base_endpoint = 'drafts'  # API端点前缀

    async def get_drafts(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取草稿列表
        
        Args:
            page: 页码
            page_size: 每页数量
            filters: 过滤条件
            
        Returns:
            Dict[str, Any]: 草稿列表数据
        """
        params = {
            'page': page,
            'page_size': page_size,
            **(filters or {})
        }
        
        return await self.make_request('GET', self.base_endpoint, params=params)

    async def get_draft(self, draft_id: str) -> Dict[str, Any]:
        """获取单个草稿详情
        
        Args:
            draft_id: 草稿ID
            
        Returns:
            Dict[str, Any]: 草稿详情数据
        """
        endpoint = f"{self.base_endpoint}/{draft_id}"
        return await self.make_request('GET', endpoint)

    async def create_draft(self, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建新草稿
        
        Args:
            draft_data: 草稿数据
            
        Returns:
            Dict[str, Any]: 创建的草稿数据
        """
        return await self.make_request('POST', self.base_endpoint, data=draft_data)

    async def update_draft(self, draft_id: str, draft_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新草稿
        
        Args:
            draft_id: 草稿ID
            draft_data: 更新的草稿数据
            
        Returns:
            Dict[str, Any]: 更新后的草稿数据
        """
        endpoint = f"{self.base_endpoint}/{draft_id}"
        return await self.make_request('PUT', endpoint, data=draft_data)

    async def delete_draft(self, draft_id: str) -> Dict[str, Any]:
        """删除草稿
        
        Args:
            draft_id: 草稿ID
            
        Returns:
            Dict[str, Any]: 删除操作的响应数据
        """
        endpoint = f"{self.base_endpoint}/{draft_id}"
        return await self.make_request('DELETE', endpoint)

    async def batch_delete_drafts(self, draft_ids: List[str]) -> Dict[str, Any]:
        """批量删除草稿
        
        Args:
            draft_ids: 草稿ID列表
            
        Returns:
            Dict[str, Any]: 批量删除操作的响应数据
        """
        return await self.make_request(
            'DELETE',
            f"{self.base_endpoint}/batch",
            data={'ids': draft_ids}
        ) 