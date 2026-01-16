"""
Cheat Engine AI Agent 的内存工具。

该模块包含内存读取相关的工具，如read_memory、read_integer、read_string等。
"""
from typing import Any, Dict, List
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ..base.decorators import tool
from ..utils.logger import get_logger


logger = get_logger(__name__)


@tool(
    name="read_memory",
    category=ToolCategory.MEMORY_READ,
    description="Read raw bytes from a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to read from"
        ),
        Parameter(
            name="size",
            type="integer",
            required=True,
            description="The number of bytes to read"
        )
    ],
    examples=["read_memory(address=0x77190000, size=16)"]
)
def read_memory_impl(mcp_client, address: int, size: int) -> Dict[str, Any]:
    """
    从特定内存地址读取原始字节。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        size: 要读取的字节数
        
    Returns:
        内存读取结果
    """
    try:
        response = mcp_client.send_command("read_memory", {
            "address": address,
            "size": size
        })
        return response
    except Exception as e:
        logger.error(f"read_memory 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="read_integer",
    category=ToolCategory.MEMORY_READ,
    description="Read an integer value from a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to read from"
        ),
        Parameter(
            name="type",
            type="string",
            required=False,
            default="dword",
            description="The type of integer to read (byte, word, dword, qword, float, double)"
        )
    ],
    examples=["read_integer(address=0x77190000)"]
)
def read_integer_impl(mcp_client, address: int, type: str = "dword") -> Dict[str, Any]:
    """
    从特定内存地址读取整数值。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        type: 整数类型
        
    Returns:
        内存读取结果
    """
    try:
        response = mcp_client.send_command("read_integer", {
            "address": address,
            "type": type
        })
        return response
    except Exception as e:
        logger.error(f"read_integer 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="read_string",
    category=ToolCategory.MEMORY_READ,
    description="Read a string from a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to read from"
        ),
        Parameter(
            name="max_length",
            type="integer",
            required=False,
            default=256,
            description="The maximum length of the string to read"
        ),
        Parameter(
            name="wide",
            type="boolean",
            required=False,
            default=False,
            description="Whether to read a wide (UTF-16) string"
        )
    ],
    examples=["read_string(address=0x77190000, max_length=100)"]
)
def read_string_impl(mcp_client, address: int, max_length: int = 256, wide: bool = False) -> Dict[str, Any]:
    """
    从特定内存地址读取字符串。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        max_length: 要读取的最大长度
        wide: 是否读取宽字符串
        
    Returns:
        内存读取结果
    """
    try:
        response = mcp_client.send_command("read_string", {
            "address": address,
            "max_length": max_length,
            "wide": wide
        })
        return response
    except Exception as e:
        logger.error(f"read_string 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="read_pointer",
    category=ToolCategory.MEMORY_READ,
    description="Read a pointer value from a specific memory address.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The memory address to read from"
        )
    ],
    examples=["read_pointer(address=0x77190000)"]
)
def read_pointer_impl(mcp_client, address: int) -> Dict[str, Any]:
    """
    从特定内存地址读取指针值。
    
    Args:
        mcp_client: MCP客户端实例
        address: 内存地址
        
    Returns:
        指针读取结果
    """
    try:
        response = mcp_client.send_command("read_pointer", {
            "address": address
        })
        return response
    except Exception as e:
        logger.error(f"read_pointer 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="read_pointer_chain",
    category=ToolCategory.MEMORY_READ,
    description="Read a value through a chain of pointers.",
    parameters=[
        Parameter(
            name="base",
            type="integer",
            required=True,
            description="The base address to start the pointer chain"
        ),
        Parameter(
            name="offsets",
            type="list",
            required=True,
            description="A list of offsets to follow in the pointer chain"
        )
    ],
    examples=["read_pointer_chain(base=0x77190000, offsets=[0x10, 0x20])"]
)
def read_pointer_chain_impl(mcp_client, base: int, offsets: List[int]) -> Dict[str, Any]:
    """
    通过指针链读取值。
    
    Args:
        mcp_client: MCP客户端实例
        base: 指针链的基地址
        offsets: 指针链的偏移列表
        
    Returns:
        指针链读取结果
    """
    try:
        response = mcp_client.send_command("read_pointer_chain", {
            "base": base,
            "offsets": offsets
        })
        return response
    except Exception as e:
        logger.error(f"read_pointer_chain 命令执行失败: {e}")
        return {"error": str(e)}


@tool(
    name="checksum_memory",
    category=ToolCategory.MEMORY_READ,
    description="Calculate a checksum for a region of memory.",
    parameters=[
        Parameter(
            name="address",
            type="integer",
            required=True,
            description="The starting memory address"
        ),
        Parameter(
            name="size",
            type="integer",
            required=True,
            description="The size of the memory region"
        )
    ],
    examples=["checksum_memory(address=0x77190000, size=4096)"]
)
def checksum_memory_impl(mcp_client, address: int, size: int) -> Dict[str, Any]:
    """
    计算内存区域的校验和。
    
    Args:
        mcp_client: MCP客户端实例
        address: 起始内存地址
        size: 内存区域大小
        
    Returns:
        校验和计算结果
    """
    try:
        response = mcp_client.send_command("checksum_memory", {
            "address": address,
            "size": size
        })
        return response
    except Exception as e:
        logger.error(f"checksum_memory 命令执行失败: {e}")
        return {"error": str(e)}
