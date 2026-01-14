"""
Cheat Engine AI Agent 的基础 MCP 工具实现。

该模块包含与 Cheat Engine MCP 服务器交互的基础 MCP 工具实现。
"""
from typing import Any, Dict, List, Optional
import json
from ..models.base import ToolMetadata, Parameter, ToolCategory


def register_mcp_tools(registry, mcp_client):
    """
    使用提供的注册表注册所有 MCP 工具。
    
    Args:
        registry: 用于注册工具的工具注册表
        mcp_client: 用于工具实现的 MCP 客户端
    """
    # 基础工具
    _register_basic_tools(registry, mcp_client)
    
    # 内存读取工具
    _register_memory_read_tools(registry, mcp_client)
    
    # 模式扫描工具
    _register_pattern_scan_tools(registry, mcp_client)
    
    # 反汇编工具
    _register_disassemble_tools(registry, mcp_client)
    
    # 断点调试工具
    _register_breakpoint_debug_tools(registry, mcp_client)
    
    # DBVM 工具
    _register_dbvm_tools(registry, mcp_client)
    
    # 进程模块工具
    _register_process_module_tools(registry, mcp_client)


def _register_basic_tools(registry, mcp_client):
    """注册基础 MCP 工具。"""
    
    # ping
    ping_metadata = ToolMetadata(
        name="ping",
        category=ToolCategory.BASIC,
        description="Check if the MCP server is reachable.",
        parameters=[],
        examples=["ping()"]
    )
    
    def ping_impl(mcp_client):
        try:
            response = mcp_client.send_command("ping", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(ping_metadata, ping_impl)
    
    # get_process_info
    get_process_info_metadata = ToolMetadata(
        name="get_process_info",
        category=ToolCategory.BASIC,
        description="Get information about the currently attached process.",
        parameters=[],
        examples=["get_process_info()"]
    )
    
    def get_process_info_impl(mcp_client):
        try:
            response = mcp_client.send_command("get_process_info", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_process_info_metadata, get_process_info_impl)
    
    # evaluate_lua
    evaluate_lua_metadata = ToolMetadata(
        name="evaluate_lua",
        category=ToolCategory.BASIC,
        description="Execute a Lua script in Cheat Engine.",
        parameters=[
            Parameter(
                name="script",
                type="string",
                required=True,
                description="The Lua script to execute"
            )
        ],
        examples=['evaluate_lua(script="return getAddressSafe(\"kernel32.dll\")")']
    )
    
    def evaluate_lua_impl(mcp_client, script: str):
        try:
            response = mcp_client.send_command("execute_script", {"script": script})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(evaluate_lua_metadata, evaluate_lua_impl)
    
    # auto_assemble
    auto_assemble_metadata = ToolMetadata(
        name="auto_assemble",
        category=ToolCategory.BASIC,
        description="Perform auto assembly in Cheat Engine.",
        parameters=[
            Parameter(
                name="assembly",
                type="string",
                required=True,
                description="The assembly code to assemble"
            ),
            Parameter(
                name="address",
                type="string",
                required=False,
                default="",
                description="The address to assemble at (optional)"
            )
        ],
        examples=['auto_assemble(assembly="mov eax, ebx", address="00400000")']
    )
    
    def auto_assemble_impl(mcp_client, assembly: str, address: str = ""):
        try:
            params = {"assembly": assembly}
            if address:
                params["address"] = address
            response = mcp_client.send_command("auto_assemble", params)
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(auto_assemble_metadata, auto_assemble_impl)
    
    # get_symbol_address
    get_symbol_address_metadata = ToolMetadata(
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
    
    def get_symbol_address_impl(mcp_client, symbol: str):
        try:
            response = mcp_client.send_command("get_symbol_address", {"symbol": symbol})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_symbol_address_metadata, get_symbol_address_impl)


def _register_memory_read_tools(registry, mcp_client):
    """注册内存读取 MCP 工具。"""
    
    # read_memory
    read_memory_metadata = ToolMetadata(
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
    
    def read_memory_impl(mcp_client, address: int, size: int):
        try:
            response = mcp_client.send_command("read_memory", {"address": address, "size": size})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(read_memory_metadata, read_memory_impl)
    
    # read_integer
    read_integer_metadata = ToolMetadata(
        name="read_integer",
        category=ToolCategory.MEMORY_READ,
        description="Read an integer value from a specific memory address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The memory address to read from"
            )
        ],
        examples=["read_integer(address=0x77190000)"]
    )
    
    def read_integer_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("read_integer", {"address": address})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(read_integer_metadata, read_integer_impl)
    
    # read_string
    read_string_metadata = ToolMetadata(
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
                name="length",
                type="integer",
                required=False,
                default=256,
                description="The maximum length of the string to read"
            )
        ],
        examples=["read_string(address=0x77190000, length=100)"]
    )
    
    def read_string_impl(mcp_client, address: int, length: int = 256):
        try:
            response = mcp_client.send_command("read_string", {"address": address, "length": length})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(read_string_metadata, read_string_impl)
    
    # read_pointer
    read_pointer_metadata = ToolMetadata(
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
    
    def read_pointer_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("read_pointer", {"address": address})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(read_pointer_metadata, read_pointer_impl)
    
    # read_pointer_chain
    read_pointer_chain_metadata = ToolMetadata(
        name="read_pointer_chain",
        category=ToolCategory.MEMORY_READ,
        description="Read a value through a chain of pointers.",
        parameters=[
            Parameter(
                name="base_address",
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
        examples=["read_pointer_chain(base_address=0x77190000, offsets=[0x10, 0x20])"]
    )
    
    def read_pointer_chain_impl(mcp_client, base_address: int, offsets: List[int]):
        try:
            response = mcp_client.send_command("read_pointer_chain", {
                "base_address": base_address,
                "offsets": offsets
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(read_pointer_chain_metadata, read_pointer_chain_impl)
    
    # checksum_memory
    checksum_memory_metadata = ToolMetadata(
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
    
    def checksum_memory_impl(mcp_client, address: int, size: int):
        try:
            response = mcp_client.send_command("checksum_memory", {
                "address": address,
                "size": size
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(checksum_memory_metadata, checksum_memory_impl)


def _register_pattern_scan_tools(registry, mcp_client):
    """注册模式扫描 MCP 工具。"""
    
    # scan_all
    scan_all_metadata = ToolMetadata(
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
                name="scan_type",
                type="string",
                required=False,
                default="Auto Assembler",
                description="The type of scan to perform"
            )
        ],
        examples=['scan_all(value="55 8B EC", scan_type="Array of byte")']
    )
    
    def scan_all_impl(mcp_client, value: str, scan_type: str = "Auto Assembler"):
        try:
            response = mcp_client.send_command("scan_all", {
                "value": value,
                "scan_type": scan_type
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(scan_all_metadata, scan_all_impl)
    
    # get_scan_results
    get_scan_results_metadata = ToolMetadata(
        name="get_scan_results",
        category=ToolCategory.PATTERN_SCAN,
        description="Retrieve the results from the last scan operation.",
        parameters=[
            Parameter(
                name="max_results",
                type="integer",
                required=False,
                default=100,
                description="Maximum number of results to return"
            )
        ],
        examples=["get_scan_results(max_results=50)"]
    )
    
    def get_scan_results_impl(mcp_client, max_results: int = 100):
        try:
            response = mcp_client.send_command("get_scan_results", {
                "max_results": max_results
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_scan_results_metadata, get_scan_results_impl)
    
    # aob_scan
    aob_scan_metadata = ToolMetadata(
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
                name="writable",
                type="boolean",
                required=False,
                default=False,
                description="Whether to search in writable memory only"
            ),
            Parameter(
                name="executable",
                type="boolean",
                required=False,
                default=False,
                description="Whether to search in executable memory only"
            )
        ],
        examples=['aob_scan(pattern="48 8B ? ? 8B C1 E8 02 83 F8 01", writable=False, executable=True)']
    )
    
    def aob_scan_impl(mcp_client, pattern: str, writable: bool = False, executable: bool = False):
        try:
            response = mcp_client.send_command("aob_scan", {
                "pattern": pattern,
                "writable": writable,
                "executable": executable
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(aob_scan_metadata, aob_scan_impl)
    
    # search_string
    search_string_metadata = ToolMetadata(
        name="search_string",
        category=ToolCategory.PATTERN_SCAN,
        description="Search for a string in memory.",
        parameters=[
            Parameter(
                name="search_string",
                type="string",
                required=True,
                description="The string to search for"
            ),
            Parameter(
                name="case_sensitive",
                type="boolean",
                required=False,
                default=True,
                description="Whether the search is case sensitive"
            )
        ],
        examples=['search_string(search_string="Hello World", case_sensitive=False)']
    )
    
    def search_string_impl(mcp_client, search_string: str, case_sensitive: bool = True):
        try:
            response = mcp_client.send_command("search_string", {
                "search_string": search_string,
                "case_sensitive": case_sensitive
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(search_string_metadata, search_string_impl)
    
    # generate_signature
    generate_signature_metadata = ToolMetadata(
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
    
    def generate_signature_impl(mcp_client, address: int, size: int):
        try:
            response = mcp_client.send_command("generate_signature", {
                "address": address,
                "size": size
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(generate_signature_metadata, generate_signature_impl)
    
    # get_memory_regions
    get_memory_regions_metadata = ToolMetadata(
        name="get_memory_regions",
        category=ToolCategory.PATTERN_SCAN,
        description="Get information about all memory regions in the process.",
        parameters=[],
        examples=["get_memory_regions()"]
    )
    
    def get_memory_regions_impl(mcp_client):
        try:
            response = mcp_client.send_command("get_memory_regions", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_memory_regions_metadata, get_memory_regions_impl)
    
    # enum_memory_regions_full
    enum_memory_regions_full_metadata = ToolMetadata(
        name="enum_memory_regions_full",
        category=ToolCategory.PATTERN_SCAN,
        description="Enumerate all memory regions with detailed information.",
        parameters=[],
        examples=["enum_memory_regions_full()"]
    )
    
    def enum_memory_regions_full_impl(mcp_client):
        try:
            response = mcp_client.send_command("enum_memory_regions_full", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(enum_memory_regions_full_metadata, enum_memory_regions_full_impl)