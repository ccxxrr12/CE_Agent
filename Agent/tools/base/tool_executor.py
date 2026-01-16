"""
Cheat Engine AI Agent 的工具执行器。

该模块实现了已注册工具的执行逻辑，
包括参数验证、权限检查和错误处理。
"""
import asyncio
import time
import concurrent.futures
from typing import Dict, Any, List, Optional, Callable
from ..models.base import ToolResult, ToolCall, ToolMetadata
from ...utils.logger import get_logger
from .tool_registry import ToolRegistry


class ToolExecutor:
    """用于运行已注册工具的执行器。"""
    
    def __init__(self, registry: ToolRegistry, mcp_client=None, max_workers: int = 5):
        """
        初始化工具执行器。
        
        Args:
            registry: 要使用的工具注册表
            mcp_client: 用于执行工具的 MCP 客户端
            max_workers: 线程池的最大工作线程数
        """
        self.registry = registry
        self.mcp_client = mcp_client
        self.logger = get_logger(__name__)
        # 创建线程池，避免每次创建新线程
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    def execute(self, tool_name: str, timeout: Optional[float] = None, **kwargs) -> ToolResult:
        """
        使用提供的参数执行单个工具。
        
        Args:
            tool_name: 要执行的工具名称
            timeout: 超时时间（秒），None 表示无限等待
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
            
            # 执行工具（带超时）
            self.logger.info(f"开始执行工具: {tool_name}, 超时: {timeout}秒")
            result = self._execute_with_timeout(tool_func, timeout, **kwargs)
            self.logger.info(f"工具执行完成: {tool_name}, 耗时: {time.time() - start_time:.2f}秒")
            
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
    
    def _execute_with_timeout(self, func: callable, timeout: Optional[float], **kwargs) -> Any:
        """
        带超时的执行函数。
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒），None 表示无限等待
            **kwargs: 函数的参数
            
        Returns:
            函数执行的结果
            
        Raises:
            TimeoutError: 如果执行超时
        """
        if timeout is None:
            return func(mcp_client=self.mcp_client, **kwargs)
        
        # 使用线程池执行函数，避免每次创建新线程
        try:
            future = self.executor.submit(func, mcp_client=self.mcp_client, **kwargs)
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            self.logger.warning(f"工具执行超时（{timeout}秒）")
            raise TimeoutError(f"工具执行超时（{timeout}秒）")
    
    async def execute_async(self, tool_name: str, timeout: Optional[float] = None, **kwargs) -> ToolResult:
        """
        异步执行单个工具。
        
        Args:
            tool_name: 要执行的工具名称
            timeout: 超时时间（秒），None 表示无限等待
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
            
            # 执行工具（带超时）
            self.logger.info(f"开始执行工具（异步）: {tool_name}, 超时: {timeout}秒")
            result = await self._execute_async_impl(tool_func, timeout, **kwargs)
            self.logger.info(f"工具执行完成（异步）: {tool_name}, 耗时: {time.time() - start_time:.2f}秒")
            
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
            error_msg = f"Error executing tool '{tool_name}' (async): {str(e)}"
            self.logger.error(error_msg)
            
            return ToolResult(
                success=False,
                tool_name=tool_name,
                parameters=kwargs,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def _execute_async_impl(self, func: callable, timeout: Optional[float], **kwargs) -> Any:
        """
        异步执行函数的实现。
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒），None 表示无限等待
            **kwargs: 函数的参数
            
        Returns:
            函数执行的结果
        """
        if asyncio.iscoroutinefunction(func):
            if timeout is None:
                return await func(mcp_client=self.mcp_client, **kwargs)
            else:
                # 为协程添加超时
                return await asyncio.wait_for(
                    func(mcp_client=self.mcp_client, **kwargs),
                    timeout=timeout
                )
        else:
            # 如果不是协程，在线程池中运行它
            loop = asyncio.get_event_loop()
            if timeout is None:
                return await loop.run_in_executor(
                    self.executor, func, mcp_client=self.mcp_client, **kwargs
                )
            else:
                # 为线程池任务添加超时
                future = loop.run_in_executor(
                    self.executor, func, mcp_client=self.mcp_client, **kwargs
                )
                return await asyncio.wait_for(future, timeout=timeout)
    
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
    
    async def execute_batch_async(self, calls: List[ToolCall], max_concurrency: int = 5) -> List[ToolResult]:
        """
        异步执行多个工具（并发）。
        
        Args:
            calls: 要执行的工具调用列表
            max_concurrency: 最大并发数
            
        Returns:
            每个工具调用的结果列表
        """
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def execute_single_call(call: ToolCall) -> ToolResult:
            async with semaphore:
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
    
    def shutdown(self):
        """
        关闭执行器，释放资源。
        """
        self.executor.shutdown(wait=True)
        self.logger.info("ToolExecutor 已关闭")
    
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
