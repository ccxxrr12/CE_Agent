"""
Cheat Engine AI Agent 的工具注册表。

该模块实现了一个用于管理所有 MCP 工具的注册表，
提供注册、查找和分类的方法。
"""
import asyncio
import inspect
from typing import Callable, Dict, List, Optional, Any
from ..models.base import ToolMetadata, ToolCategory, ToolCall


class ToolRegistry:
    """用于管理 MCP 工具的注册表。"""
    
    def __init__(self):
        """初始化工具注册表。"""
        self._tools: Dict[str, Dict[str, Any]] = {}  # 将工具名称映射到元数据和函数
        self._categories: Dict[ToolCategory, List[str]] = {}
        
    def register_tool(self, metadata: ToolMetadata, func: Callable):
        """
        注册工具及其元数据。
        
        Args:
            metadata: 工具的元数据
            func: 实现工具的可调用函数
        """
        # 存储工具
        self._tools[metadata.name] = {
            'metadata': metadata,
            'function': func
        }
        
        # 添加到类别映射
        if metadata.category not in self._categories:
            self._categories[metadata.category] = []
        self._categories[metadata.category].append(metadata.name)
        
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """
        按名称获取工具。
        
        Args:
            name: 工具的名称
            
        Returns:
            工具元数据和函数，如果未找到则返回 None
        """
        return self._tools.get(name)
    
    def get_tool_metadata(self, name: str) -> Optional[ToolMetadata]:
        """
        仅获取工具的元数据。
        
        Args:
            name: 工具的名称
            
        Returns:
            工具元数据，如果未找到则返回 None
        """
        tool = self.get_tool(name)
        return tool['metadata'] if tool else None
    
    def get_tool_function(self, name: str) -> Optional[Callable]:
        """
        仅获取工具的函数。
        
        Args:
            name: 工具的名称
            
        Returns:
            工具函数，如果未找到则返回 None
        """
        tool = self.get_tool(name)
        return tool['function'] if tool else None
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """
        获取特定类别中的所有工具。
        
        Args:
            category: 要搜索的类别
            
        Returns:
            该类别的工具元数据列表
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name]['metadata'] for name in tool_names]
    
    def search_tools(self, query: str) -> List[ToolMetadata]:
        """
        按名称或描述搜索工具。
        
        Args:
            query: 搜索查询
            
        Returns:
            匹配的工具元数据列表
        """
        query_lower = query.lower()
        matching_tools = []
        
        for tool_name, tool_data in self._tools.items():
            metadata = tool_data['metadata']
            if (query_lower in tool_name.lower() or 
                query_lower in metadata.description.lower()):
                matching_tools.append(metadata)
        
        return matching_tools
    
    def list_all_tools(self) -> List[ToolMetadata]:
        """
        获取所有已注册的工具。
        
        Returns:
            所有工具元数据的列表
        """
        return [data['metadata'] for data in self._tools.values()]
    
    def get_categories(self) -> List[ToolCategory]:
        """
        获取所有可用的工具类别。
        
        Returns:
            所有工具类别的列表
        """
        return list(self._categories.keys())
    
    def get_tools_in_category(self, category: ToolCategory) -> List[str]:
        """
        获取特定类别中的所有工具名称。
        
        Args:
            category: 要搜索的类别
            
        Returns:
            类别中的工具名称列表
        """
        return self._categories.get(category, [])
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """
        异步执行工具。
        
        Args:
            name: 要执行的工具名称
            **kwargs: 传递给工具的参数
            
        Returns:
            工具执行的结果
        """
        tool_data = self.get_tool(name)
        if not tool_data:
            raise ValueError(f"Tool '{name}' not found in registry")
        
        func = tool_data['function']
        
        # 检查函数是否是协程
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            # 如果不是协程，在线程池中运行它
            return func(**kwargs)
    
    def validate_parameters(self, name: str, params: Dict[str, Any]) -> bool:
        """
        验证工具的参数。
        
        Args:
            name: 工具的名称
            params: 要验证的参数
            
        Returns:
            如果参数有效则返回 True，否则返回 False
        """
        metadata = self.get_tool_metadata(name)
        if not metadata:
            return False
        
        # 检查必需参数
        for param in metadata.parameters:
            if param.required and param.name not in params:
                return False
        
        # 检查意外参数
        param_names = {param.name for param in metadata.parameters}
        for param_name in params:
            if param_name not in param_names:
                return False
        
        return True
    
    def get_required_parameters(self, name: str) -> List[str]:
        """
        获取工具的必需参数名称。
        
        Args:
            name: 工具的名称
            
        Returns:
            必需参数名称的列表
        """
        metadata = self.get_tool_metadata(name)
        if not metadata:
            return []
        
        return [param.name for param in metadata.parameters if param.required]
    
    def get_optional_parameters(self, name: str) -> List[str]:
        """
        获取工具的可选参数名称。
        
        Args:
            name: 工具的名称
            
        Returns:
            可选参数名称的列表
        """
        metadata = self.get_tool_metadata(name)
        if not metadata:
            return []
        
        return [param.name for param in metadata.parameters if not param.required]