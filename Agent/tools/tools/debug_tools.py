"""
Cheat Engine AI Agent 的调试工具。

该模块包含调试相关的工具，如disassemble、get_instruction_info和analyze_function等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ...utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="disassemble",
    category=ToolCategory.DEBUG,
    description="Disassemble a memory region into assembly instructions.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to start disassembling from"
        ),
        Parameter(
            name="count",
            type="integer",
            required=False,
            default=20,
            description="The number of instructions to disassemble"
        )
    ],
    examples=["disassemble(address=0x77190000, count=10)"]
)
def disassemble_impl(mcp_client, address: int, count: int = 20) -> Dict[str, Any]:
    """
    将内存区域反汇编为汇编指令。
    
    Args:
        mcp_client: MCP客户端实例
        address: 起始内存地址
        count: 要反汇编的指令数量
        
    Returns:
        反汇编结果
    """
    try:
        response = mcp_client.send_command("disassemble", {
            "address": address,
            "count": count
        })
        return response
    except Exception as e:
        logger.error(f"disassemble 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_instruction_info",
    category=ToolCategory.DEBUG,
    description="Get detailed information about a specific instruction.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The address of the instruction to analyze"
        )
    ],
    examples=["get_instruction_info(address=0x77190000)"]
)
def get_instruction_info_impl(mcp_client, address: int) -> Dict[str, Any]:
    """
    获取特定指令的详细信息。
    
    Args:
        mcp_client: MCP客户端实例
        address: 指令地址
        
    Returns:
        指令信息
    """
    try:
        response = mcp_client.send_command("get_instruction_info", {
            "address": address
        })
        return response
    except Exception as e:
        logger.error(f"get_instruction_info 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="find_function_boundaries",
    category=ToolCategory.DEBUG,
    description="Find the boundaries of a function at a given address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The address within the function to analyze"
        ),
        Parameter(
            name="max_search",
            type="integer",
            required=False,
            default=4096,
            description="The maximum number of bytes to search for function boundaries"
        )
    ],
    examples=["find_function_boundaries(address=0x77190000, max_search=2048)"]
)
def find_function_boundaries_impl(mcp_client, address: int, max_search: int = 4096) -> Dict[str, Any]:
    """
    查找给定地址处函数的边界。
    
    Args:
        mcp_client: MCP客户端实例
        address: 函数内的地址
        max_search: 查找函数边界的最大字节数
        
    Returns:
        函数边界信息
    """
    try:
        response = mcp_client.send_command("find_function_boundaries", {
            "address": address,
            "max_search": max_search
        })
        return response
    except Exception as e:
        logger.error(f"find_function_boundaries 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="analyze_function",
    category=ToolCategory.DEBUG,
    description="Analyze a function to extract its signature, parameters, and other information.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The address of the function to analyze"
        )
    ],
    examples=["analyze_function(address=0x77190000)"]
)
def analyze_function_impl(mcp_client, address: int) -> Dict[str, Any]:
    """
    分析函数以提取其签名、参数和其他信息。
    
    Args:
        mcp_client: MCP客户端实例
        address: 函数地址
        
    Returns:
        函数分析结果
    """
    try:
        response = mcp_client.send_command("analyze_function", {
            "address": address
        })
        return response
    except Exception as e:
        logger.error(f"analyze_function 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="find_references",
    category=ToolCategory.DEBUG,
    description="Find all references to a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to find references to"
        ),
        Parameter(
            name="limit",
            type="integer",
            required=False,
            default=50,
            description="Maximum number of results to return"
        )
    ],
    examples=["find_references(address=0x77190000, limit=20)"]
)
def find_references_impl(mcp_client, address: int, limit: int = 50) -> Dict[str, Any]:
    """
    查找对特定内存地址的所有引用。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        limit: 返回结果的最大数量
        
    Returns:
        引用查找结果
    """
    try:
        response = mcp_client.send_command("find_references", {
            "address": address,
            "limit": limit
        })
        return response
    except Exception as e:
        logger.error(f"find_references 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="find_call_references",
    category=ToolCategory.DEBUG,
    description="Find all call references to a specific function.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The address of the function to find call references to"
        ),
        Parameter(
            name="limit",
            type="integer",
            required=False,
            default=100,
            description="Maximum number of results to return"
        )
    ],
    examples=["find_call_references(address=0x77190000, limit=50)"]
)
def find_call_references_impl(mcp_client, address: int, limit: int = 100) -> Dict[str, Any]:
    """
    查找对特定函数的所有调用引用。
    
    Args:
        mcp_client: MCP客户端实例
        address: 函数地址
        limit: 返回结果的最大数量
        
    Returns:
        调用引用查找结果
    """
    try:
        response = mcp_client.send_command("find_call_references", {
            "address": address,
            "limit": limit
        })
        return response
    except Exception as e:
        logger.error(f"find_call_references 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="dissect_structure",
    category=ToolCategory.DEBUG,
    description="Attempt to dissect a memory structure at a given address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to start dissecting from"
        ),
        Parameter(
            name="size",
            type="integer",
            required=True,
            description="The size of the memory region to analyze"
        )
    ],
    examples=["dissect_structure(address=0x77190000, size=128)"]
)
def dissect_structure_impl(mcp_client, address: int, size: int) -> Dict[str, Any]:
    """
    尝试分析给定地址处的内存结构。
    
    Args:
        mcp_client: MCP客户端实例
        address: 起始内存地址
        size: 要分析的内存区域大小
        
    Returns:
        结构分析结果
    """
    try:
        response = mcp_client.send_command("dissect_structure", {
            "address": address,
            "size": size
        })
        return response
    except Exception as e:
        logger.error(f"dissect_structure 命令执行失败: {e}")
        return {"error": str(e)}
