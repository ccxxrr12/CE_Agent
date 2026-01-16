"""
Cheat Engine AI Agent 的扫描工具。

该模块包含内存扫描相关的工具，如scan_all、aob_scan、search_string等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ...utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="scan_all",
    category=ToolCategory.PATTERN_SCAN,
    description="Scan all memory regions for a specific value.",
    parameters=[
        Parameter(
            name="value",
            type="string",
            required=True,
            description="The value to search for"
        ),
        Parameter(
            name="type",
            type="string",
            required=False,
            default="exact",
            description="The type of scan to perform (exact, string, array)"
        ),
        Parameter(
            name="protection",
            type="string",
            required=False,
            default="+W-C",
            description="Memory protection filter (e.g., +W-C for writable, non-copy-on-write)"
        )
    ],
    examples=['scan_all(value="55 8B EC", type="array")', 'scan_all(value="100", type="exact", protection="+W-C")']
)
def scan_all_impl(mcp_client, value: str, type: str = "exact", protection: str = "+W-C") -> Dict[str, Any]:
    """
    扫描所有内存区域寻找特定值。
    
    Args:
        mcp_client: MCP客户端实例
        value: 要搜索的值
        type: 扫描类型 (exact, string, array)
        protection: 内存保护过滤器
        
    Returns:
        扫描结果
    """
    try:
        response = mcp_client.send_command("scan_all", {
            "value": value,
            "type": type,
            "protection": protection
        }, timeout=300)  # 增加超时时间到300秒
        return response
    except Exception as e:
        logger.error(f"scan_all 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_scan_results",
    category=ToolCategory.PATTERN_SCAN,
    description="Retrieve the results from the last 'scan_all' operation.",
    parameters=[
        Parameter(
            name="max",
            type="integer",
            required=False,
            default=100,
            description="Maximum number of results to return"
        )
    ],
    examples=["get_scan_results(max=50)"]
)
def get_scan_results_impl(mcp_client, max: int = 100) -> Dict[str, Any]:
    """
    获取上次'scan_all'操作的结果。
    
    Args:
        mcp_client: MCP客户端实例
        max: 返回结果的最大数量
        
    Returns:
        扫描结果
    """
    try:
        response = mcp_client.send_command("get_scan_results", {
            "max": max
        })
        return response
    except Exception as e:
        logger.error(f"get_scan_results 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="aob_scan",
    category=ToolCategory.PATTERN_SCAN,
    description="Scan for an array of bytes pattern.",
    parameters=[
        Parameter(
            name="pattern",
            type="string",
            required=True,
            description="The array of bytes pattern to search for (e.g., '48 8B ? ? 8B')"
        ),
        Parameter(
            name="protection",
            type="string",
            required=False,
            default="+X",
            description="Memory protection filter (e.g., +X for executable)"
        ),
        Parameter(
            name="limit",
            type="integer",
            required=False,
            default=100,
            description="Maximum number of results to return"
        )
    ],
    examples=['aob_scan(pattern="48 8B ? ? 8B C1 E8 02 83 F8 01", protection="+X", limit=100)']
)
def aob_scan_impl(mcp_client, pattern: str, protection: str = "+X", limit: int = 100) -> Dict[str, Any]:
    """
    扫描字节数组(AOB)模式。
    
    Args:
        mcp_client: MCP客户端实例
        pattern: 字节数组模式
        protection: 内存保护过滤器
        limit: 返回结果的最大数量
        
    Returns:
        扫描结果
    """
    try:
        response = mcp_client.send_command("aob_scan", {
            "pattern": pattern,
            "protection": protection,
            "limit": limit
        })
        return response
    except Exception as e:
        logger.error(f"aob_scan 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="search_string",
    category=ToolCategory.PATTERN_SCAN,
    description="Search for a string in memory.",
    parameters=[
        Parameter(
            name="string",
            type="string",
            required=True,
            description="The string to search for"
        ),
        Parameter(
            name="wide",
            type="boolean",
            required=False,
            default=False,
            description="Whether to search for wide (UTF-16) strings"
        ),
        Parameter(
            name="limit",
            type="integer",
            required=False,
            default=100,
            description="Maximum number of results to return"
        )
    ],
    examples=['search_string(string="Hello World", wide=False, limit=50)']
)
def search_string_impl(mcp_client, string: str, wide: bool = False, limit: int = 100) -> Dict[str, Any]:
    """
    在内存中搜索字符串。
    
    Args:
        mcp_client: MCP客户端实例
        string: 要搜索的字符串
        wide: 是否搜索宽字符串
        limit: 返回结果的最大数量
        
    Returns:
        搜索结果
    """
    try:
        response = mcp_client.send_command("search_string", {
            "string": string,
            "wide": wide,
            "limit": limit
        })
        return response
    except Exception as e:
        logger.error(f"search_string 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="generate_signature",
    category=ToolCategory.PATTERN_SCAN,
    description="Generate a signature for a memory region.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The starting address of the region"
        ),
        Parameter(
            name="size",
            type="integer",
            required=True,
            description="The size of the region"
        )
    ],
    examples=["generate_signature(address=0x77190000, size=256)"]
)
def generate_signature_impl(mcp_client, address: int, size: int) -> Dict[str, Any]:
    """
    为内存区域生成签名。
    
    Args:
        mcp_client: MCP客户端实例
        address: 区域起始地址
        size: 区域大小
        
    Returns:
        生成的签名
    """
    try:
        response = mcp_client.send_command("generate_signature", {
            "address": address,
            "size": size
        })
        return response
    except Exception as e:
        logger.error(f"generate_signature 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="get_memory_regions",
    category=ToolCategory.PATTERN_SCAN,
    description="Get information about all memory regions in the process.",
    parameters=[
        Parameter(
            name="max",
            type="integer",
            required=False,
            default=100,
            description="Maximum number of regions to return"
        )
    ],
    examples=["get_memory_regions(max=50)"]
)
def get_memory_regions_impl(mcp_client, max: int = 100) -> Dict[str, Any]:
    """
    获取进程中所有内存区域的信息。
    
    Args:
        mcp_client: MCP客户端实例
        max: 返回区域的最大数量
        
    Returns:
        内存区域信息
    """
    try:
        response = mcp_client.send_command("get_memory_regions", {
            "max": max
        })
        return response
    except Exception as e:
        logger.error(f"get_memory_regions 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="enum_memory_regions_full",
    category=ToolCategory.PATTERN_SCAN,
    description="Enumerate all memory regions with detailed information.",
    parameters=[
        Parameter(
            name="max",
            type="integer",
            required=False,
            default=500,
            description="Maximum number of regions to return"
        )
    ],
    examples=["enum_memory_regions_full(max=100)"]
)
def enum_memory_regions_full_impl(mcp_client, max: int = 500) -> Dict[str, Any]:
    """
    枚举所有内存区域并提供详细信息。
    
    Args:
        mcp_client: MCP客户端实例
        max: 返回区域的最大数量
        
    Returns:
        详细的内存区域信息
    """
    try:
        response = mcp_client.send_command("enum_memory_regions_full", {
            "max": max
        })
        return response
    except Exception as e:
        logger.error(f"enum_memory_regions_full 命令执行失败: {e}")
        return {"error": str(e)}
