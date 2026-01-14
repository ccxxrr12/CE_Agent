"""
Cheat Engine AI Agent 的工具执行器。

该模块实现了已注册工具的执行逻辑，
包括参数验证、权限检查和错误处理。
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from ..models.base import ToolResult, ToolCall, ToolMetadata
from ..utils.logger import get_logger
from .registry import ToolRegistry


class ToolExecutor:
    """用于运行已注册工具的执行器。"""
    
    def __init__(self, registry: ToolRegistry, mcp_client=None):
        """
        初始化工具执行器。
        
        Args:
            registry: 要使用的工具注册表
            mcp_client: 用于执行工具的 MCP 客户端
        """
        self.registry = registry
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
    
    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """
        使用提供的参数执行单个工具。
        
        Args:
            tool_name: 要执行的工具名称
            **kwargs: 工具的参数
            
        Returns:
            工具执行的结果
        """
        start_time = time.time()
        
        try:
            # 验证参数
            if not self.validate_parameters(tool_name, kwargs):
                error_msg = f"工具 '{tool_name}' 的参数无效"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 检查权限
            if not self.check_permissions(tool_name):
                error_msg = f"Permission denied for tool '{tool_name}'"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 获取工具函数
            tool_func = self.registry.get_tool_function(tool_name)
            if not tool_func:
                error_msg = f"Tool '{tool_name}' not found"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 执行工具
            result = tool_func(mcp_client=self.mcp_client, **kwargs)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                tool_name=tool_name,
                parameters=kwargs,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                success=False,
                tool_name=tool_name,
                parameters=kwargs,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def execute_async(self, tool_name: str, **kwargs) -> ToolResult:
        """
        异步执行单个工具。
        
        Args:
            tool_name: 要执行的工具名称
            **kwargs: 工具的参数
            
        Returns:
            工具执行的结果
        """
        start_time = time.time()
        
        try:
            # 验证参数
            if not self.validate_parameters(tool_name, kwargs):
                error_msg = f"Invalid parameters for tool '{tool_name}'"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 检查权限
            if not self.check_permissions(tool_name):
                error_msg = f"Permission denied for tool '{tool_name}'"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 获取工具函数
            tool_func = self.registry.get_tool_function(tool_name)
            if not tool_func:
                error_msg = f"Tool '{tool_name}' not found"
                self.logger.error(error_msg)
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    parameters=kwargs,
                    error=error_msg
                )
            
            # 执行工具（应该是异步的）
            result = await tool_func(mcp_client=self.mcp_client, **kwargs)
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                tool_name=tool_name,
                parameters=kwargs,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                success=False,
                tool_name=tool_name,
                parameters=kwargs,
                error=error_msg,
                execution_time=execution_time
            )
    
    def execute_batch(self, calls: List[ToolCall]) -> List[ToolResult]:
        """
        按顺序执行多个工具。
        
        Args:
            calls: 要执行的工具调用列表
            
        Returns:
            每个工具调用的结果列表
        """
        results = []
        
        for call in calls:
            result = self.execute(call.name, **call.arguments)
            results.append(result)
            
            # 如果工具失败且是关键的，我们可能想要停止
            # 目前，无论单个失败如何，我们都继续执行
            if not result.success:
                self.logger.warning(f"Tool '{call.name}' failed: {result.error}")
        
        return results
    
    async def execute_batch_async(self, calls: List[ToolCall]) -> List[ToolResult]:
        """
        异步执行多个工具（并发）。
        
        Args:
            calls: 要执行的工具调用列表
            
        Returns:
            每个工具调用的结果列表
        """
        async def execute_single_call(call: ToolCall) -> ToolResult:
            return await self.execute_async(call.name, **call.arguments)
        
        tasks = [execute_single_call(call) for call in calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理执行期间发生的任何异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ToolResult(
                        success=False,
                        tool_name=calls[i].name,
                        parameters=calls[i].arguments,
                        error=str(result)
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    def validate_parameters(self, tool_name: str, params: Dict[str, Any]) -> bool:
        """
        验证工具的参数。
        
        Args:
            tool_name: 工具的名称
            params: 要验证的参数
            
        Returns:
            如果参数有效则返回 True，否则返回 False
        """
        return self.registry.validate_parameters(tool_name, params)
    
    def check_permissions(self, tool_name: str) -> bool:
        """
        根据权限检查是否可以执行工具。
        
        Args:
            tool_name: 工具的名称
            
        Returns:
            如果授予权限则返回 True，否则返回 False
        """
        metadata = self.registry.get_tool_metadata(tool_name)
        if not metadata:
            return False
        
        # 目前，我们允许所有非破坏性工具
        # 破坏性工具可能需要额外的确认
        return not metadata.destructive or metadata.requires_approval