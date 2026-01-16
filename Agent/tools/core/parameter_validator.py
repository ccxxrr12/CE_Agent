"""
Cheat Engine AI Agent 的参数验证器。

该模块负责验证工具调用参数是否符合 MCP_Server 的要求，
确保参数的类型、范围和约束条件都正确。
"""
from typing import Dict, Any, Callable, List


class MCPParameterValidator:
    """MCP参数验证器，确保参数符合MCP_Server的要求。"""
    
    def __init__(self):
        """初始化参数验证器。"""
        self.validators: Dict[str, Callable[[Dict[str, Any]], bool]] = {
            "read_memory": self._validate_read_memory,
            "read_integer": self._validate_read_integer,
            "read_string": self._validate_read_string,
            "read_pointer": self._validate_read_pointer,
            "read_pointer_chain": self._validate_read_pointer_chain,
            "checksum_memory": self._validate_checksum_memory,
            "scan_all": self._validate_scan_all,
            "get_scan_results": self._validate_get_scan_results,
            "aob_scan": self._validate_aob_scan,
            "search_string": self._validate_search_string,
            "generate_signature": self._validate_generate_signature,
            "get_memory_regions": self._validate_get_memory_regions,
            "enum_memory_regions_full": self._validate_enum_memory_regions_full,
            "disassemble": self._validate_disassemble,
            "get_instruction_info": self._validate_get_instruction_info,
            "find_function_boundaries": self._validate_find_function_boundaries,
            "analyze_function": self._validate_analyze_function,
            "find_references": self._validate_find_references,
            "find_call_references": self._validate_find_call_references,
            "dissect_structure": self._validate_dissect_structure,
            "set_breakpoint": self._validate_set_breakpoint,
            "set_data_breakpoint": self._validate_set_data_breakpoint,
            "remove_breakpoint": self._validate_remove_breakpoint,
            "list_breakpoints": self._validate_list_breakpoints,
            "clear_all_breakpoints": self._validate_clear_all_breakpoints,
            "get_breakpoint_hits": self._validate_get_breakpoint_hits,
            "get_physical_address": self._validate_get_physical_address,
            "start_dbvm_watch": self._validate_start_dbvm_watch,
            "stop_dbvm_watch": self._validate_stop_dbvm_watch,
            "poll_dbvm_watch": self._validate_poll_dbvm_watch,
            "enum_modules": self._validate_enum_modules,
            "get_thread_list": self._validate_get_thread_list,
            "get_symbol_address": self._validate_get_symbol_address,
            "get_address_info": self._validate_get_address_info,
            "get_process_info": self._validate_get_process_info,
            "ping": self._validate_ping,
            "evaluate_lua": self._validate_evaluate_lua,
            "auto_assemble": self._validate_auto_assemble,
        }
    
    def validate(self, command_name: str, params: Dict[str, Any]) -> bool:
        """
        验证命令参数是否有效。
        
        Args:
            command_name: 命令名称
            params: 命令参数
            
        Returns:
            如果参数有效则返回 True，否则返回 False
        """
        if command_name in self.validators:
            return self.validators[command_name](params)
        return True
    
    def _validate_read_memory(self, params: Dict[str, Any]) -> bool:
        """验证 read_memory 命令参数。"""
        if "address" not in params:
            return False
        if "size" not in params:
            return False
        if not isinstance(params["size"], int) or params["size"] <= 0:
            return False
        return True
    
    def _validate_read_integer(self, params: Dict[str, Any]) -> bool:
        """验证 read_integer 命令参数。"""
        if "address" not in params:
            return False
        if "type" in params:
            valid_types = ["byte", "word", "dword", "qword", "float", "double"]
            if params["type"] not in valid_types:
                return False
        return True
    
    def _validate_read_string(self, params: Dict[str, Any]) -> bool:
        """验证 read_string 命令参数。"""
        if "address" not in params:
            return False
        if "max_length" in params:
            if not isinstance(params["max_length"], int) or params["max_length"] <= 0:
                return False
        return True
    
    def _validate_read_pointer(self, params: Dict[str, Any]) -> bool:
        """验证 read_pointer 命令参数。"""
        if "address" not in params:
            return False
        if "offsets" in params:
            if not isinstance(params["offsets"], list):
                return False
        return True
    
    def _validate_read_pointer_chain(self, params: Dict[str, Any]) -> bool:
        """验证 read_pointer_chain 命令参数。"""
        if "base" not in params:
            return False
        if "offsets" not in params:
            return False
        if not isinstance(params["offsets"], list):
            return False
        return True
    
    def _validate_checksum_memory(self, params: Dict[str, Any]) -> bool:
        """验证 checksum_memory 命令参数。"""
        if "address" not in params:
            return False
        if "size" not in params:
            return False
        if not isinstance(params["size"], int) or params["size"] <= 0:
            return False
        return True
    
    def _validate_scan_all(self, params: Dict[str, Any]) -> bool:
        """验证 scan_all 命令参数。"""
        if "value" not in params:
            return False
        if "type" in params:
            valid_types = ["exact", "string", "array"]
            if params["type"] not in valid_types:
                return False
        return True
    
    def _validate_get_scan_results(self, params: Dict[str, Any]) -> bool:
        """验证 get_scan_results 命令参数。"""
        if "max" in params:
            if not isinstance(params["max"], int) or params["max"] <= 0:
                return False
        return True
    
    def _validate_aob_scan(self, params: Dict[str, Any]) -> bool:
        """验证 aob_scan 命令参数。"""
        if "pattern" not in params:
            return False
        if "limit" in params:
            if not isinstance(params["limit"], int) or params["limit"] <= 0:
                return False
        return True
    
    def _validate_search_string(self, params: Dict[str, Any]) -> bool:
        """验证 search_string 命令参数。"""
        if "string" not in params:
            return False
        if "limit" in params:
            if not isinstance(params["limit"], int) or params["limit"] <= 0:
                return False
        return True
    
    def _validate_generate_signature(self, params: Dict[str, Any]) -> bool:
        """验证 generate_signature 命令参数。"""
        if "address" not in params:
            return False
        if "size" not in params:
            return False
        if not isinstance(params["size"], int) or params["size"] <= 0:
            return False
        return True
    
    def _validate_get_memory_regions(self, params: Dict[str, Any]) -> bool:
        """验证 get_memory_regions 命令参数。"""
        if "max" in params:
            if not isinstance(params["max"], int) or params["max"] <= 0:
                return False
        return True
    
    def _validate_enum_memory_regions_full(self, params: Dict[str, Any]) -> bool:
        """验证 enum_memory_regions_full 命令参数。"""
        if "max" in params:
            if not isinstance(params["max"], int) or params["max"] <= 0:
                return False
        return True
    
    def _validate_disassemble(self, params: Dict[str, Any]) -> bool:
        """验证 disassemble 命令参数。"""
        if "address" not in params:
            return False
        if "count" in params:
            if not isinstance(params["count"], int) or params["count"] <= 0:
                return False
        return True
    
    def _validate_get_instruction_info(self, params: Dict[str, Any]) -> bool:
        """验证 get_instruction_info 命令参数。"""
        if "address" not in params:
            return False
        return True
    
    def _validate_find_function_boundaries(self, params: Dict[str, Any]) -> bool:
        """验证 find_function_boundaries 命令参数。"""
        if "address" not in params:
            return False
        if "max_search" in params:
            if not isinstance(params["max_search"], int) or params["max_search"] <= 0:
                return False
        return True
    
    def _validate_analyze_function(self, params: Dict[str, Any]) -> bool:
        """验证 analyze_function 命令参数。"""
        if "address" not in params:
            return False
        return True
    
    def _validate_find_references(self, params: Dict[str, Any]) -> bool:
        """验证 find_references 命令参数。"""
        if "address" not in params:
            return False
        if "limit" in params:
            if not isinstance(params["limit"], int) or params["limit"] <= 0:
                return False
        return True
    
    def _validate_find_call_references(self, params: Dict[str, Any]) -> bool:
        """验证 find_call_references 命令参数。"""
        if "address" not in params:
            return False
        if "limit" in params:
            if not isinstance(params["limit"], int) or params["limit"] <= 0:
                return False
        return True
    
    def _validate_dissect_structure(self, params: Dict[str, Any]) -> bool:
        """验证 dissect_structure 命令参数。"""
        if "address" not in params:
            return False
        if "size" not in params:
            return False
        if not isinstance(params["size"], int) or params["size"] <= 0:
            return False
        return True
    
    def _validate_set_breakpoint(self, params: Dict[str, Any]) -> bool:
        """验证 set_breakpoint 命令参数。"""
        if "address" not in params:
            return False
        if "stack_depth" in params:
            if not isinstance(params["stack_depth"], int) or params["stack_depth"] <= 0:
                return False
        return True
    
    def _validate_set_data_breakpoint(self, params: Dict[str, Any]) -> bool:
        """验证 set_data_breakpoint 命令参数。"""
        if "address" not in params:
            return False
        if "access_type" in params:
            valid_types = ["r", "w", "rw"]
            if params["access_type"] not in valid_types:
                return False
        if "size" in params:
            valid_sizes = [1, 2, 4, 8]
            if params["size"] not in valid_sizes:
                return False
        return True
    
    def _validate_remove_breakpoint(self, params: Dict[str, Any]) -> bool:
        """验证 remove_breakpoint 命令参数。"""
        if "id" not in params:
            return False
        return True
    
    def _validate_list_breakpoints(self, params: Dict[str, Any]) -> bool:
        """验证 list_breakpoints 命令参数。"""
        return True
    
    def _validate_clear_all_breakpoints(self, params: Dict[str, Any]) -> bool:
        """验证 clear_all_breakpoints 命令参数。"""
        return True
    
    def _validate_get_breakpoint_hits(self, params: Dict[str, Any]) -> bool:
        """验证 get_breakpoint_hits 命令参数。"""
        return True
    
    def _validate_get_physical_address(self, params: Dict[str, Any]) -> bool:
        """验证 get_physical_address 命令参数。"""
        if "address" not in params:
            return False
        return True
    
    def _validate_start_dbvm_watch(self, params: Dict[str, Any]) -> bool:
        """验证 start_dbvm_watch 命令参数。"""
        if "address" not in params:
            return False
        if "mode" in params:
            valid_modes = ["r", "w", "x"]
            if params["mode"] not in valid_modes:
                return False
        if "max_entries" in params:
            if not isinstance(params["max_entries"], int) or params["max_entries"] <= 0:
                return False
        return True
    
    def _validate_stop_dbvm_watch(self, params: Dict[str, Any]) -> bool:
        """验证 stop_dbvm_watch 命令参数。"""
        if "address" not in params:
            return False
        return True
    
    def _validate_poll_dbvm_watch(self, params: Dict[str, Any]) -> bool:
        """验证 poll_dbvm_watch 命令参数。"""
        if "address" not in params:
            return False
        if "max_results" in params:
            if not isinstance(params["max_results"], int) or params["max_results"] <= 0:
                return False
        return True
    
    def _validate_enum_modules(self, params: Dict[str, Any]) -> bool:
        """验证 enum_modules 命令参数。"""
        return True
    
    def _validate_get_thread_list(self, params: Dict[str, Any]) -> bool:
        """验证 get_thread_list 命令参数。"""
        return True
    
    def _validate_get_symbol_address(self, params: Dict[str, Any]) -> bool:
        """验证 get_symbol_address 命令参数。"""
        if "symbol" not in params:
            return False
        return True
    
    def _validate_get_address_info(self, params: Dict[str, Any]) -> bool:
        """验证 get_address_info 命令参数。"""
        if "address" not in params:
            return False
        return True
    
    def _validate_get_process_info(self, params: Dict[str, Any]) -> bool:
        """验证 get_process_info 命令参数。"""
        return True
    
    def _validate_ping(self, params: Dict[str, Any]) -> bool:
        """验证 ping 命令参数。"""
        return True
    
    def _validate_evaluate_lua(self, params: Dict[str, Any]) -> bool:
        """验证 evaluate_lua 命令参数。"""
        if "code" not in params:
            return False
        return True
    
    def _validate_auto_assemble(self, params: Dict[str, Any]) -> bool:
        """验证 auto_assemble 命令参数。"""
        if "script" not in params:
            return False
        return True
