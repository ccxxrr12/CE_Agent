"""
Cheat Engine AI Agent 的高级 MCP 工具实现。

该模块包含与 Cheat Engine MCP 服务器交互的反汇编器、断点调试、
DBVM 和进程/模块工具的实现。
"""
from typing import Any, Dict, List, Optional
import json
from ..models.base import ToolMetadata, Parameter, ToolCategory


def register_advanced_mcp_tools(registry, mcp_client):
    """
    使用提供的注册表注册高级 MCP 工具。
    
    Args:
        registry: 用于注册工具的工具注册表
        mcp_client: 用于工具实现的 MCP 客户端
    """
    # 反汇编工具
    _register_disassemble_tools(registry, mcp_client)
    
    # 断点调试工具
    _register_breakpoint_debug_tools(registry, mcp_client)
    
    # DBVM 工具
    _register_dbvm_tools(registry, mcp_client)
    
    # 进程模块工具
    _register_process_module_tools(registry, mcp_client)


def _register_disassemble_tools(registry, mcp_client):
    """注册反汇编 MCP 工具。"""
    
    # disassemble
    disassemble_metadata = ToolMetadata(
        name="disassemble",
        category=ToolCategory.DISASSEMBLE,
        description="Disassemble instructions at a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to disassemble"
            ),
            Parameter(
                name="count",
                type="integer",
                required=False,
                default=10,
                description="The number of instructions to disassemble"
            )
        ],
        examples=["disassemble(address=0x77190000, count=20)"]
    )
    
    def disassemble_impl(mcp_client, address: int, count: int = 10):
        try:
            response = mcp_client.send_command("disassemble", {
                "address": address,
                "count": count
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(disassemble_metadata, disassemble_impl)
    
    # get_instruction_info
    get_instruction_info_metadata = ToolMetadata(
        name="get_instruction_info",
        category=ToolCategory.DISASSEMBLE,
        description="Get detailed information about an assembly instruction.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address of the instruction"
            )
        ],
        examples=["get_instruction_info(address=0x77190000)"]
    )
    
    def get_instruction_info_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("get_instruction_info", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_instruction_info_metadata, get_instruction_info_impl)
    
    # find_function_boundaries
    find_function_boundaries_metadata = ToolMetadata(
        name="find_function_boundaries",
        category=ToolCategory.DISASSEMBLE,
        description="Find the boundaries of a function starting at the given address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The starting address of the function"
            )
        ],
        examples=["find_function_boundaries(address=0x77190000)"]
    )
    
    def find_function_boundaries_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("find_function_boundaries", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(find_function_boundaries_metadata, find_function_boundaries_impl)
    
    # analyze_function
    analyze_function_metadata = ToolMetadata(
        name="analyze_function",
        category=ToolCategory.DISASSEMBLE,
        description="Perform static analysis on a function.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The starting address of the function"
            )
        ],
        examples=["analyze_function(address=0x77190000)"]
    )
    
    def analyze_function_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("analyze_function", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(analyze_function_metadata, analyze_function_impl)
    
    # find_references
    find_references_metadata = ToolMetadata(
        name="find_references",
        category=ToolCategory.DISASSEMBLE,
        description="Find all references to a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to find references to"
            )
        ],
        examples=["find_references(address=0x77190000)"]
    )
    
    def find_references_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("find_references", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(find_references_metadata, find_references_impl)
    
    # find_call_references
    find_call_references_metadata = ToolMetadata(
        name="find_call_references",
        category=ToolCategory.DISASSEMBLE,
        description="Find all call references to a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to find call references to"
            )
        ],
        examples=["find_call_references(address=0x77190000)"]
    )
    
    def find_call_references_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("find_call_references", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(find_call_references_metadata, find_call_references_impl)
    
    # dissect_structure
    dissect_structure_metadata = ToolMetadata(
        name="dissect_structure",
        category=ToolCategory.DISASSEMBLE,
        description="Dissect a data structure in memory.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address of the structure"
            ),
            Parameter(
                name="size",
                type="integer",
                required=True,
                description="The size of the structure"
            )
        ],
        examples=["dissect_structure(address=0x77190000, size=256)"]
    )
    
    def dissect_structure_impl(mcp_client, address: int, size: int):
        try:
            response = mcp_client.send_command("dissect_structure", {
                "address": address,
                "size": size
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(dissect_structure_metadata, dissect_structure_impl)


def _register_breakpoint_debug_tools(registry, mcp_client):
    """注册断点调试 MCP 工具。"""
    
    # set_breakpoint
    set_breakpoint_metadata = ToolMetadata(
        name="set_breakpoint",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="Set a breakpoint at a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to set the breakpoint at"
            ),
            Parameter(
                name="condition",
                type="string",
                required=False,
                default="",
                description="Optional condition for the breakpoint"
            )
        ],
        examples=["set_breakpoint(address=0x77190000)", 'set_breakpoint(address=0x77190000, condition="eax == 0")']
    )
    
    def set_breakpoint_impl(mcp_client, address: int, condition: str = ""):
        try:
            params = {"address": address}
            if condition:
                params["condition"] = condition
            response = mcp_client.send_command("set_breakpoint", params)
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(set_breakpoint_metadata, set_breakpoint_impl)
    
    # set_data_breakpoint
    set_data_breakpoint_metadata = ToolMetadata(
        name="set_data_breakpoint",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="Set a data breakpoint at a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to set the data breakpoint at"
            ),
            Parameter(
                name="size",
                type="integer",
                required=True,
                description="The size of the memory region to watch"
            ),
            Parameter(
                name="access_type",
                type="string",
                required=False,
                default="rw",
                description="The type of access to break on (r=read, w=write, rw=read/write)"
            )
        ],
        examples=["set_data_breakpoint(address=0x77190000, size=4, access_type=\"rw\")"]
    )
    
    def set_data_breakpoint_impl(mcp_client, address: int, size: int, access_type: str = "rw"):
        try:
            response = mcp_client.send_command("set_data_breakpoint", {
                "address": address,
                "size": size,
                "access_type": access_type
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(set_data_breakpoint_metadata, set_data_breakpoint_impl)
    
    # remove_breakpoint
    remove_breakpoint_metadata = ToolMetadata(
        name="remove_breakpoint",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="Remove a breakpoint at a specific address.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address of the breakpoint to remove"
            )
        ],
        examples=["remove_breakpoint(address=0x77190000)"]
    )
    
    def remove_breakpoint_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("remove_breakpoint", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(remove_breakpoint_metadata, remove_breakpoint_impl)
    
    # list_breakpoints
    list_breakpoints_metadata = ToolMetadata(
        name="list_breakpoints",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="List all active breakpoints.",
        parameters=[],
        examples=["list_breakpoints()"]
    )
    
    def list_breakpoints_impl(mcp_client):
        try:
            response = mcp_client.send_command("list_breakpoints", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(list_breakpoints_metadata, list_breakpoints_impl)
    
    # clear_all_breakpoints
    clear_all_breakpoints_metadata = ToolMetadata(
        name="clear_all_breakpoints",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="Clear all active breakpoints.",
        parameters=[],
        examples=["clear_all_breakpoints()"]
    )
    
    def clear_all_breakpoints_impl(mcp_client):
        try:
            response = mcp_client.send_command("clear_all_breakpoints", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(clear_all_breakpoints_metadata, clear_all_breakpoints_impl)
    
    # get_breakpoint_hits
    get_breakpoint_hits_metadata = ToolMetadata(
        name="get_breakpoint_hits",
        category=ToolCategory.BREAKPOINT_DEBUG,
        description="Get information about breakpoint hits.",
        parameters=[
            Parameter(
                name="timeout",
                type="integer",
                required=False,
                default=5000,
                description="Timeout in milliseconds to wait for hits"
            )
        ],
        examples=["get_breakpoint_hits(timeout=10000)"]
    )
    
    def get_breakpoint_hits_impl(mcp_client, timeout: int = 5000):
        try:
            response = mcp_client.send_command("get_breakpoint_hits", {
                "timeout": timeout
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_breakpoint_hits_metadata, get_breakpoint_hits_impl)


def _register_dbvm_tools(registry, mcp_client):
    """注册 DBVM MCP 工具。"""
    
    # get_physical_address
    get_physical_address_metadata = ToolMetadata(
        name="get_physical_address",
        category=ToolCategory.DBVM,
        description="Get the physical address for a virtual address.",
        parameters=[
            Parameter(
                name="virtual_address",
                type="integer",
                required=True,
                description="The virtual address to translate"
            )
        ],
        examples=["get_physical_address(virtual_address=0x77190000)"]
    )
    
    def get_physical_address_impl(mcp_client, virtual_address: int):
        try:
            response = mcp_client.send_command("get_physical_address", {
                "virtual_address": virtual_address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_physical_address_metadata, get_physical_address_impl)
    
    # start_dbvm_watch
    start_dbvm_watch_metadata = ToolMetadata(
        name="start_dbvm_watch",
        category=ToolCategory.DBVM,
        description="Start watching a memory region with DBVM.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to watch"
            ),
            Parameter(
                name="size",
                type="integer",
                required=True,
                description="The size of the region to watch"
            ),
            Parameter(
                name="access_type",
                type="string",
                required=False,
                default="rw",
                description="The type of access to monitor (r=read, w=write, rw=read/write)"
            )
        ],
        examples=["start_dbvm_watch(address=0x77190000, size=256, access_type=\"rw\")"]
    )
    
    def start_dbvm_watch_impl(mcp_client, address: int, size: int, access_type: str = "rw"):
        try:
            response = mcp_client.send_command("start_dbvm_watch", {
                "address": address,
                "size": size,
                "access_type": access_type
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(start_dbvm_watch_metadata, start_dbvm_watch_impl)
    
    # stop_dbvm_watch
    stop_dbvm_watch_metadata = ToolMetadata(
        name="stop_dbvm_watch",
        category=ToolCategory.DBVM,
        description="Stop watching a memory region with DBVM.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address of the watched region"
            )
        ],
        examples=["stop_dbvm_watch(address=0x77190000)"]
    )
    
    def stop_dbvm_watch_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("stop_dbvm_watch", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(stop_dbvm_watch_metadata, stop_dbvm_watch_impl)
    
    # poll_dbvm_watch
    poll_dbvm_watch_metadata = ToolMetadata(
        name="poll_dbvm_watch",
        category=ToolCategory.DBVM,
        description="Poll for changes detected by DBVM watch.",
        parameters=[
            Parameter(
                name="timeout",
                type="integer",
                required=False,
                default=1000,
                description="Timeout in milliseconds to wait for changes"
            )
        ],
        examples=["poll_dbvm_watch(timeout=2000)"]
    )
    
    def poll_dbvm_watch_impl(mcp_client, timeout: int = 1000):
        try:
            response = mcp_client.send_command("poll_dbvm_watch", {
                "timeout": timeout
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(poll_dbvm_watch_metadata, poll_dbvm_watch_impl)


def _register_process_module_tools(registry, mcp_client):
    """注册进程/模块 MCP 工具。"""
    
    # enum_modules
    enum_modules_metadata = ToolMetadata(
        name="enum_modules",
        category=ToolCategory.PROCESS_MODULE,
        description="Enumerate all loaded modules in the process.",
        parameters=[],
        examples=["enum_modules()"]
    )
    
    def enum_modules_impl(mcp_client):
        try:
            response = mcp_client.send_command("enum_modules", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(enum_modules_metadata, enum_modules_impl)
    
    # get_thread_list
    get_thread_list_metadata = ToolMetadata(
        name="get_thread_list",
        category=ToolCategory.PROCESS_MODULE,
        description="Get a list of all threads in the process.",
        parameters=[],
        examples=["get_thread_list()"]
    )
    
    def get_thread_list_impl(mcp_client):
        try:
            response = mcp_client.send_command("get_thread_list", {})
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_thread_list_metadata, get_thread_list_impl)
    
    # get_symbol_address
    get_symbol_address_metadata = ToolMetadata(
        name="get_symbol_address",
        category=ToolCategory.PROCESS_MODULE,
        description="Get the address of a symbol in the process.",
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
            response = mcp_client.send_command("get_symbol_address", {
                "symbol": symbol
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_symbol_address_metadata, get_symbol_address_impl)
    
    # get_address_info
    get_address_info_metadata = ToolMetadata(
        name="get_address_info",
        category=ToolCategory.PROCESS_MODULE,
        description="Get information about an address in the process.",
        parameters=[
            Parameter(
                name="address",
                type="integer",
                required=True,
                description="The address to get information for"
            )
        ],
        examples=["get_address_info(address=0x77190000)"]
    )
    
    def get_address_info_impl(mcp_client, address: int):
        try:
            response = mcp_client.send_command("get_address_info", {
                "address": address
            })
            return response
        except Exception as e:
            return {"error": str(e)}
    
    registry.register_tool(get_address_info_metadata, get_address_info_impl)
    
    # get_process_info
    get_process_info_metadata = ToolMetadata(
        name="get_process_info",
        category=ToolCategory.PROCESS_MODULE,
        description="Get detailed information about the current process.",
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