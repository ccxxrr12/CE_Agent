"""
Cheat Engine AI Agent 的断点工具。

该模块包含断点相关的工具，如set_breakpoint、list_breakpoints和remove_breakpoint等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ...utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="set_breakpoint",
    category=ToolCategory.BREAKPOINT,
    description="Set a breakpoint at a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to set the breakpoint at"
        ),
        Parameter(
            name="id",
            type="string",
            required=False,
            description="A custom ID for the breakpoint"
        ),
        Parameter(
            name="capture_registers",
            type="boolean",
            required=False,
            default=True,
            description="Whether to capture registers when the breakpoint is hit"
        ),
        Parameter(
            name="capture_stack",
            type="boolean",
            required=False,
            default=False,
            description="Whether to capture the stack when the breakpoint is hit"
        ),
        Parameter(
            name="stack_depth",
            type="integer",
            required=False,
            default=16,
            description="The stack depth to capture"
        )
    ],
    examples=["set_breakpoint(address=0x77190000, id='bp1')"]
)
def set_breakpoint_impl(mcp_client, address: int, id: str = None, capture_registers: bool = True, capture_stack: bool = False, stack_depth: int = 16) -> Dict[str, Any]:
    """
    在特定内存地址设置断点。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        id: 断点的自定义ID
        capture_registers: 断点命中时是否捕获寄存器
        capture_stack: 断点命中时是否捕获堆栈
        stack_depth: 要捕获的堆栈深度
        
    Returns:
        断点设置结果
    """
    try:
        response = mcp_client.send_command("set_breakpoint", {
            "address": address,
            "id": id,
            "capture_registers": capture_registers,
            "capture_stack": capture_stack,
            "stack_depth": stack_depth
        })
        return response
    except Exception as e:
        logger.error(f"set_breakpoint 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="set_data_breakpoint",
    category=ToolCategory.BREAKPOINT,
    description="Set a data breakpoint at a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to set the data breakpoint at"
        ),
        Parameter(
            name="id",
            type="string",
            required=False,
            description="A custom ID for the data breakpoint"
        ),
        Parameter(
            name="access_type",
            type="string",
            required=False,
            default="w",
            description="The access type to break on (r, w, rw)"
        ),
        Parameter(
            name="size",
            type="integer",
            required=False,
            default=4,
            description="The size of the memory to watch (1, 2, 4, 8)"
        )
    ],
    examples=["set_data_breakpoint(address=0x77190000, id='dbp1', access_type='w', size=4)"]
)
def set_data_breakpoint_impl(mcp_client, address: int, id: str = None, access_type: str = "w", size: int = 4) -> Dict[str, Any]:
    """
    在特定内存地址设置数据断点。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        id: 数据断点的自定义ID
        access_type: 要中断的访问类型 (r, w, rw)
        size: 要监视的内存大小 (1, 2, 4, 8)
        
    Returns:
        数据断点设置结果
    """
    try:
        response = mcp_client.send_command("set_data_breakpoint", {
            "address": address,
            "id": id,
            "access_type": access_type,
            "size": size
        })
        return response
    except Exception as e:
        logger.error(f"set_data_breakpoint 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="remove_breakpoint",
    category=ToolCategory.BREAKPOINT,
    description="Remove a breakpoint by its ID.",
    parameters=[
        Parameter(
            name="id",
            type="string",
            required=True,
            description="The ID of the breakpoint to remove"
        )
    ],
    examples=["remove_breakpoint(id='bp1')"]
)
def remove_breakpoint_impl(mcp_client, id: str) -> Dict[str, Any]:
    """
    通过ID移除断点。
    
    Args:
        mcp_client: MCP客户端实例
        id: 断点ID
        
    Returns:
        断点移除结果
    """
    try:
        response = mcp_client.send_command("remove_breakpoint", {
            "id": id
        })
        return response
    except Exception as e:
        logger.error(f"remove_breakpoint 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="list_breakpoints",
    category=ToolCategory.BREAKPOINT,
    description="List all currently set breakpoints.",
    examples=["list_breakpoints()"]
)
def list_breakpoints_impl(mcp_client) -> Dict[str, Any]:
    """
    列出所有当前设置的断点。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        断点列表
    """
    try:
        response = mcp_client.send_command("list_breakpoints", {})
        return response
    except Exception as e:
        logger.error(f"list_breakpoints 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="clear_all_breakpoints",
    category=ToolCategory.BREAKPOINT,
    description="Clear all currently set breakpoints.",
    examples=["clear_all_breakpoints()"]
)
def clear_all_breakpoints_impl(mcp_client) -> Dict[str, Any]:
    """
    清除所有当前设置的断点。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        清除结果
    """
    try:
        response = mcp_client.send_command("clear_all_breakpoints", {})
        return response
    except Exception as e:
        logger.error(f"clear_all_breakpoints 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_breakpoint_hits",
    category=ToolCategory.BREAKPOINT,
    description="Get the hits for a specific breakpoint.",
    parameters=[
        Parameter(
            name="id",
            type="string",
            required=True,
            description="The ID of the breakpoint to get hits for"
        ),
        Parameter(
            name="clear",
            type="boolean",
            required=False,
            default=False,
            description="Whether to clear the hits after retrieving them"
        )
    ],
    examples=["get_breakpoint_hits(id='bp1', clear=True)"]
)
def get_breakpoint_hits_impl(mcp_client, id: str, clear: bool = False) -> Dict[str, Any]:
    """
    获取特定断点的命中记录。
    
    Args:
        mcp_client: MCP客户端实例
        id: 断点ID
        clear: 获取后是否清除命中记录
        
    Returns:
        断点命中记录
    """
    try:
        response = mcp_client.send_command("get_breakpoint_hits", {
            "id": id,
            "clear": clear
        })
        return response
    except Exception as e:
        logger.error(f"get_breakpoint_hits 命令执行失败: {e}")
        return {"error": str(e)}
