"""
Cheat Engine AI Agent 的工具模块。

这包括代理可以用来与 Cheat Engine 交互
和执行内存分析任务的各种工具。
"""
from .base.tool_registry import ToolRegistry
from .base.tool_executor import ToolExecutor
from .base.result_parser import ResultParser
from .base.decorators import tool, async_tool, set_global_registry, get_global_registry

# 初始化工具注册表
global_registry = ToolRegistry()
set_global_registry(global_registry)

# 导入工具实现，它们会自动注册到全局注册表
from .tools import basic_tools
from .tools import memory_tools
from .tools import scan_tools
from .tools import debug_tools
from .tools import breakpoint_tools
from .tools import dbvm_tools
from .tools import process_tools

__all__ = ['ToolRegistry', 'ToolExecutor', 'ResultParser', 'tool', 'async_tool', 'global_registry']