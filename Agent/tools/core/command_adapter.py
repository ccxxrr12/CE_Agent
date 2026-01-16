"""
Cheat Engine AI Agent 的命令适配层。

该模块负责将客户端工具调用参数转换为 MCP_Server 期望的格式，
确保参数名称、类型和结构的一致性。
"""
from typing import Dict, Any, Callable


class MCPCommandAdapter:
    """MCP命令适配器，负责将客户端参数转换为MCP_Server期望的格式。"""
    
    def __init__(self):
        """初始化命令适配器。"""
        self.adaptors: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "read_memory": self._adapt_read_memory,
            "read_integer": self._adapt_read_integer,
            "read_string": self._adapt_read_string,
            "read_pointer": self._adapt_read_pointer,
            "read_pointer_chain": self._adapt_read_pointer_chain,
            "checksum_memory": self._adapt_checksum_memory,
            "scan_all": self._adapt_scan_all,
            "get_scan_results": self._adapt_get_scan_results,
            "aob_scan": self._adapt_aob_scan,
            "search_string": self._adapt_search_string,
            "generate_signature": self._adapt_generate_signature,
            "get_memory_regions": self._adapt_get_memory_regions,
            "enum_memory_regions_full": self._adapt_enum_memory_regions_full,
            "disassemble": self._adapt_disassemble,
            "get_instruction_info": self._adapt_get_instruction_info,
            "find_function_boundaries": self._adapt_find_function_boundaries,
            "analyze_function": self._adapt_analyze_function,
            "find_references": self._adapt_find_references,
            "find_call_references": self._adapt_find_call_references,
            "dissect_structure": self._adapt_dissect_structure,
            "set_breakpoint": self._adapt_set_breakpoint,
            "set_data_breakpoint": self._adapt_set_data_breakpoint,
            "remove_breakpoint": self._adapt_remove_breakpoint,
            "list_breakpoints": self._adapt_list_breakpoints,
            "clear_all_breakpoints": self._adapt_clear_all_breakpoints,
            "get_breakpoint_hits": self._adapt_get_breakpoint_hits,
            "get_physical_address": self._adapt_get_physical_address,
            "start_dbvm_watch": self._adapt_start_dbvm_watch,
            "stop_dbvm_watch": self._adapt_stop_dbvm_watch,
            "poll_dbvm_watch": self._adapt_poll_dbvm_watch,
            "enum_modules": self._adapt_enum_modules,
            "get_thread_list": self._adapt_get_thread_list,
            "get_symbol_address": self._adapt_get_symbol_address,
            "get_address_info": self._adapt_get_address_info,
            "get_process_info": self._adapt_get_process_info,
            "ping": self._adapt_ping,
            "evaluate_lua": self._adapt_evaluate_lua,
            "auto_assemble": self._adapt_auto_assemble,
        }
    
    def adapt_command(self, command_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据命令名称适配参数格式。
        
        Args:
            command_name: 命令名称
            params: 命令参数
            
        Returns:
            适配后的命令参数
        """
        if command_name in self.adaptors:
            return self.adaptors[command_name](params)
        return params
    
    def _adapt_read_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 read_memory 命令参数。"""
        return {
            "address": params.get("address"),
            "size": params.get("size", 256)
        }
    
    def _adapt_read_integer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 read_integer 命令参数。"""
        return {
            "address": params.get("address"),
            "type": params.get("type", "dword")
        }
    
    def _adapt_read_string(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 read_string 命令参数。"""
        return {
            "address": params.get("address"),
            "max_length": params.get("max_length", 256),
            "wide": params.get("wide", False)
        }
    
    def _adapt_read_pointer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 read_pointer 命令参数。"""
        return {
            "address": params.get("address"),
            "offsets": params.get("offsets", [])
        }
    
    def _adapt_read_pointer_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 read_pointer_chain 命令参数。"""
        return {
            "base": params.get("base"),
            "offsets": params.get("offsets", [])
        }
    
    def _adapt_checksum_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 checksum_memory 命令参数。"""
        return {
            "address": params.get("address"),
            "size": params.get("size")
        }
    
    def _adapt_scan_all(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 scan_all 命令参数。"""
        return {
            "value": params.get("value"),
            "type": params.get("type", "exact"),
            "protection": params.get("protection", "+W-C")
        }
    
    def _adapt_get_scan_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_scan_results 命令参数。"""
        return {
            "max": params.get("max", 100)
        }
    
    def _adapt_aob_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 aob_scan 命令参数。"""
        return {
            "pattern": params.get("pattern"),
            "protection": params.get("protection", "+X"),
            "limit": params.get("limit", 100)
        }
    
    def _adapt_search_string(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 search_string 命令参数。"""
        return {
            "string": params.get("string"),
            "wide": params.get("wide", False),
            "limit": params.get("limit", 100)
        }
    
    def _adapt_generate_signature(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 generate_signature 命令参数。"""
        return {
            "address": params.get("address"),
            "size": params.get("size", 256)
        }
    
    def _adapt_get_memory_regions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_memory_regions 命令参数。"""
        return {
            "max": params.get("max", 100)
        }
    
    def _adapt_enum_memory_regions_full(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 enum_memory_regions_full 命令参数。"""
        return {
            "max": params.get("max", 500)
        }
    
    def _adapt_disassemble(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 disassemble 命令参数。"""
        return {
            "address": params.get("address"),
            "count": params.get("count", 20)
        }
    
    def _adapt_get_instruction_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_instruction_info 命令参数。"""
        return {
            "address": params.get("address")
        }
    
    def _adapt_find_function_boundaries(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 find_function_boundaries 命令参数。"""
        return {
            "address": params.get("address"),
            "max_search": params.get("max_search", 4096)
        }
    
    def _adapt_analyze_function(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 analyze_function 命令参数。"""
        return {
            "address": params.get("address")
        }
    
    def _adapt_find_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 find_references 命令参数。"""
        return {
            "address": params.get("address"),
            "limit": params.get("limit", 50)
        }
    
    def _adapt_find_call_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 find_call_references 命令参数。"""
        return {
            "address": params.get("address"),
            "limit": params.get("limit", 100)
        }
    
    def _adapt_dissect_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 dissect_structure 命令参数。"""
        return {
            "address": params.get("address"),
            "size": params.get("size", 256)
        }
    
    def _adapt_set_breakpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 set_breakpoint 命令参数。"""
        return {
            "address": params.get("address"),
            "id": params.get("id"),
            "capture_registers": params.get("capture_registers", True),
            "capture_stack": params.get("capture_stack", False),
            "stack_depth": params.get("stack_depth", 16)
        }
    
    def _adapt_set_data_breakpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 set_data_breakpoint 命令参数。"""
        return {
            "address": params.get("address"),
            "id": params.get("id"),
            "access_type": params.get("access_type", "w"),
            "size": params.get("size", 4)
        }
    
    def _adapt_remove_breakpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 remove_breakpoint 命令参数。"""
        return {
            "id": params.get("id")
        }
    
    def _adapt_list_breakpoints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 list_breakpoints 命令参数。"""
        return {}
    
    def _adapt_clear_all_breakpoints(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 clear_all_breakpoints 命令参数。"""
        return {}
    
    def _adapt_get_breakpoint_hits(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_breakpoint_hits 命令参数。"""
        return {
            "id": params.get("id"),
            "clear": params.get("clear", False)
        }
    
    def _adapt_get_physical_address(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_physical_address 命令参数。"""
        return {
            "address": params.get("address")
        }
    
    def _adapt_start_dbvm_watch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 start_dbvm_watch 命令参数。"""
        return {
            "address": params.get("address"),
            "mode": params.get("mode", "w"),
            "max_entries": params.get("max_entries", 1000)
        }
    
    def _adapt_stop_dbvm_watch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 stop_dbvm_watch 命令参数。"""
        return {
            "address": params.get("address")
        }
    
    def _adapt_poll_dbvm_watch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 poll_dbvm_watch 命令参数。"""
        return {
            "address": params.get("address"),
            "max_results": params.get("max_results", 1000)
        }
    
    def _adapt_enum_modules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 enum_modules 命令参数。"""
        return {}
    
    def _adapt_get_thread_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_thread_list 命令参数。"""
        return {}
    
    def _adapt_get_symbol_address(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_symbol_address 命令参数。"""
        return {
            "symbol": params.get("symbol")
        }
    
    def _adapt_get_address_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_address_info 命令参数。"""
        return {
            "address": params.get("address"),
            "include_modules": params.get("include_modules", True),
            "include_symbols": params.get("include_symbols", True),
            "include_sections": params.get("include_sections", False)
        }
    
    def _adapt_get_process_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 get_process_info 命令参数。"""
        return {}
    
    def _adapt_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 ping 命令参数。"""
        return {}
    
    def _adapt_evaluate_lua(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 evaluate_lua 命令参数。"""
        return {
            "code": params.get("code")
        }
    
    def _adapt_auto_assemble(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """适配 auto_assemble 命令参数。"""
        return {
            "script": params.get("script")
        }
