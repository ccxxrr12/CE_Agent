"""
Cheat Engine AI Agent 的基础工具。

该模块包含基础的MCP工具，如ping、evaluate_lua和auto_assemble等。
"""
from typing import Any, Dict
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ...utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="ping",
    category=ToolCategory.BASIC,
    description="Check if the MCP server is reachable.",
    examples=["ping()"]
)
def ping_impl(mcp_client) -> Dict[str, Any]:
    """
    检查MCP服务器是否可达。
    
    Args:
        mcp_client: MCP客户端实例
        
    Returns:
        服务器响应
    """
    try:
        response = mcp_client.send_command("ping", {})
        return response
    except Exception as e:
        logger.error(f"ping 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="evaluate_lua",
    category=ToolCategory.BASIC,
    description="Execute a Lua script in Cheat Engine.",
    parameters=[
        Parameter(
            name="code",
            type="string",
            required=True,
            description="The Lua script to execute"
        )
    ],
    examples=['evaluate_lua(code=\'print("Hello, Cheat Engine!")\')']
)
def evaluate_lua_impl(mcp_client, code: str) -> Dict[str, Any]:
    """
    在Cheat Engine中执行Lua脚本。
    
    Args:
        mcp_client: MCP客户端实例
        code: 要执行的Lua脚本
        
    Returns:
        脚本执行结果
    """
    try:
        response = mcp_client.send_command("execute_script", {"script": code})
        return response
    except Exception as e:
        logger.error(f"evaluate_lua 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="auto_assemble",
    category=ToolCategory.BASIC,
    description="Perform auto assembly in Cheat Engine.",
    parameters=[
        Parameter(
            name="script",
            type="string",
            required=True,
            description="The assembly code to assemble"
        )
    ],
    examples=['auto_assemble(script="globalalloc(mcp_test_region_v3,4)")']
)
def auto_assemble_impl(mcp_client, script: str) -> Dict[str, Any]:
    """
    在Cheat Engine中执行自动汇编。
    
    Args:
        mcp_client: MCP客户端实例
        script: 汇编代码
        
    Returns:
        汇编执行结果
    """
    try:
        response = mcp_client.send_command("auto_assemble", {"script": script})
        return response
    except Exception as e:
        logger.error(f"auto_assemble 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_process_info",
    category=ToolCategory.BASIC,
    description="Get information about the currently attached process.",
    examples=["get_process_info()"]
)
def get_process_info_impl(mcp_client) -> Dict[str, Any]:
    """
    获取当前附加进程的信息。
    
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


@tool(
    name="get_symbol_address",
    category=ToolCategory.BASIC,
    description="Get the address of a symbol in the attached process.",
    parameters=[
        Parameter(
            name="symbol",
            type="string",
            required=True,
            description="The symbol name to resolve"
        )
    ],
    examples=['get_symbol_address(symbol="kernel32.CreateProcessW")']
)
def get_symbol_address_impl(mcp_client, symbol: str) -> Dict[str, Any]:
    """
    获取附加进程中符号的地址。
    
    Args:
        mcp_client: MCP客户端实例
        symbol: 符号名称
        
    Returns:
        符号地址信息
    """
    try:
        response = mcp_client.send_command("get_symbol_address", {"symbol": symbol})
        return response
    except Exception as e:
        logger.error(f"get_symbol_address 命令执行失败: {e}")
        return {"error": str(e)}
