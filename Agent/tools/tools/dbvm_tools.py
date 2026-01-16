"""
Cheat Engine AI Agent 的 DBVM 工具。

该模块包含 DBVM (Driver-Level Virtual Machine) 相关的工具，如 get_physical_address、start_dbvm_watch 和 stop_dbvm_watch 等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ..utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="get_physical_address",
    category=ToolCategory.DBVM,
    description="Convert a virtual memory address to a physical memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The virtual memory address to convert"
        )
    ],
    examples=["get_physical_address(address=0x77190000)"]
)
def get_physical_address_impl(mcp_client, address: int) -> Dict[str, Any]:
    """
    将虚拟内存地址转换为物理内存地址。
    
    Args:
        mcp_client: MCP客户端实例
        address: 虚拟内存地址
        
    Returns:
        物理地址转换结果
    """
    try:
        response = mcp_client.send_command("get_physical_address", {
            "address": address
        })
        return response
    except Exception as e:
        logger.error(f"get_physical_address 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="start_dbvm_watch",
    category=ToolCategory.DBVM,
    description="Start watching a memory address using DBVM.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to watch"
        ),
        Parameter(
            name="mode",
            type="string",
            required=False,
            default="w",
            description="The watch mode (r, w, x)"
        ),
        Parameter(
            name="max_entries",
            type="integer",
            required=False,
            default=1000,
            description="Maximum number of entries to store"
        )
    ],
    examples=["start_dbvm_watch(address=0x77190000, mode='w', max_entries=500)"]
)
def start_dbvm_watch_impl(mcp_client, address: int, mode: str = "w", max_entries: int = 1000) -> Dict[str, Any]:
    """
    使用 DBVM 开始监视内存地址。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        mode: 监视模式 (r, w, x)
        max_entries: 要存储的最大条目数
        
    Returns:
        DBVM 监视启动结果
    """
    try:
        response = mcp_client.send_command("start_dbvm_watch", {
            "address": address,
            "mode": mode,
            "max_entries": max_entries
        })
        return response
    except Exception as e:
        logger.error(f"start_dbvm_watch 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="stop_dbvm_watch",
    category=ToolCategory.DBVM,
    description="Stop watching a memory address using DBVM.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to stop watching"
        )
    ],
    examples=["stop_dbvm_watch(address=0x77190000)"]
)
def stop_dbvm_watch_impl(mcp_client, address: int) -> Dict[str, Any]:
    """
    使用 DBVM 停止监视内存地址。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        
    Returns:
        DBVM 监视停止结果
    """
    try:
        response = mcp_client.send_command("stop_dbvm_watch", {
            "address": address
        })
        return response
    except Exception as e:
        logger.error(f"stop_dbvm_watch 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="poll_dbvm_watch",
    category=ToolCategory.DBVM,
    description="Poll for DBVM watch results.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address being watched"
        ),
        Parameter(
            name="max_results",
            type="integer",
            required=False,
            default=1000,
            description="Maximum number of results to return"
        )
    ],
    examples=["poll_dbvm_watch(address=0x77190000, max_results=200)"]
)
def poll_dbvm_watch_impl(mcp_client, address: int, max_results: int = 1000) -> Dict[str, Any]:
    """
    查询 DBVM 监视结果。
    
    Args:
        mcp_client: MCP客户端实例
        address: 被监视的内存地址
        max_results: 返回结果的最大数量
        
    Returns:
        DBVM 监视结果
    """
    try:
        response = mcp_client.send_command("poll_dbvm_watch", {
            "address": address,
            "max_results": max_results
        })
        return response
    except Exception as e:
        logger.error(f"poll_dbvm_watch 命令执行失败: {e}")
        return {"error": str(e)}
