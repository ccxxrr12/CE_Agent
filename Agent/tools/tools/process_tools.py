"""
Cheat Engine AI Agent 的进程工具。

该模块包含进程和模块相关的工具，如enum_modules、get_thread_list、get_address_info和get_process_info等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ..utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="enum_modules",
    category=ToolCategory.PROCESS,
    description="Enumerate all modules loaded in the process.",
    examples=["enum_modules()"]
)
def enum_modules_impl(mcp_client) -> Dict[str, Any]:
    """
    枚举进程中加载的所有模块。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        模块列表
    """
    try:
        response = mcp_client.send_command("enum_modules", {})
        return response
    except Exception as e:
        logger.error(f"enum_modules 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_thread_list",
    category=ToolCategory.PROCESS,
    description="Get a list of all threads in the process.",
    examples=["get_thread_list()"]
)
def get_thread_list_impl(mcp_client) -> Dict[str, Any]:
    """
    获取进程中所有线程的列表。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        线程列表
    """
    try:
        response = mcp_client.send_command("get_thread_list", {})
        return response
    except Exception as e:
        logger.error(f"get_thread_list 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_symbol_address",
    category=ToolCategory.PROCESS,
    description="Get the address of a symbol in the process.",
    parameters=[
        Parameter(
            name="symbol",
            type="string",
            required=True,
            description="The symbol name to resolve (e.g., 'kernel32.dll!CreateProcessW')"
        )
    ],
    examples=['get_symbol_address(symbol="kernel32.dll!CreateProcessW")']
)
def get_symbol_address_impl(mcp_client, symbol: str) -> Dict[str, Any]:
    """
    获取进程中符号的地址。
    
    Args:
        mcp_client: MCP客户端实例
        symbol: 符号名称
        
    Returns:
        符号地址信息
    """
    try:
        response = mcp_client.send_command("get_symbol_address", {
            "symbol": symbol
        })
        return response
    except Exception as e:
        logger.error(f"get_symbol_address 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_address_info",
    category=ToolCategory.PROCESS,
    description="Get information about a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to get information about"
        ),
        Parameter(
            name="include_modules",
            type="boolean",
            required=False,
            default=True,
            description="Whether to include module information"
        ),
        Parameter(
            name="include_symbols",
            type="boolean",
            required=False,
            default=True,
            description="Whether to include symbol information"
        ),
        Parameter(
            name="include_sections",
            type="boolean",
            required=False,
            default=False,
            description="Whether to include section information"
        )
    ],
    examples=["get_address_info(address=0x77190000, include_modules=True, include_symbols=True)"]
)
def get_address_info_impl(mcp_client, address: int, include_modules: bool = True, include_symbols: bool = True, include_sections: bool = False) -> Dict[str, Any]:
    """
    获取特定内存地址的信息。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        include_modules: 是否包含模块信息
        include_symbols: 是否包含符号信息
        include_sections: 是否包含节信息
        
    Returns:
        地址信息
    """
    try:
        response = mcp_client.send_command("get_address_info", {
            "address": address,
            "include_modules": include_modules,
            "include_symbols": include_symbols,
            "include_sections": include_sections
        })
        return response
    except Exception as e:
        logger.error(f"get_address_info 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_process_info",
    category=ToolCategory.PROCESS,
    description="Get information about the current process.",
    examples=["get_process_info()"]
)
def get_process_info_impl(mcp_client) -> Dict[str, Any]:
    """
    获取当前进程的信息。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        进程信息
    """
    try:
        response = mcp_client.send_command("get_process_info", {})
        return response
    except Exception as e:
        logger.error(f"get_process_info 命令执行失败: {e}")
        return {"error": str(e)}
