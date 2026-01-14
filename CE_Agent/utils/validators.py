"""
Cheat Engine AI Agent 的验证器模块。

该模块提供数据验证功能，确保输入和输出数据的有效性。
"""
from typing import Any, Dict, List, Optional, Tuple
from ..utils.logger import get_logger
from ..models.base import ToolMetadata, ToolCall, ToolResult
from ..models.core_models import ExecutionPlan, SubTask, ExecutionContext


class ValidationError(Exception):
    """验证错误异常。"""
    pass


class Validator:
    """数据验证器。"""
    
    def __init__(self):
        """初始化验证器。"""
        self.logger = get_logger(__name__)
    
    def validate_tool_call(self, tool_call: ToolCall, tool_metadata: ToolMetadata) -> Tuple[bool, Optional[str]]:
        """
        验证工具调用是否有效。
        
        Args:
            tool_call: 工具调用对象
            tool_metadata: 工具元数据
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if tool_call.name != tool_metadata.name:
            return False, f"Tool name mismatch: expected {tool_metadata.name}, got {tool_call.name}"
        
        for param in tool_metadata.parameters:
            if param.required and param.name not in tool_call.arguments:
                return False, f"Missing required parameter: {param.name}"
        
        for arg_name in tool_call.arguments:
            param_names = {p.name for p in tool_metadata.parameters}
            if arg_name not in param_names:
                return False, f"Unexpected parameter: {arg_name}"
        
        return True, None
    
    def validate_tool_result(self, result: ToolResult) -> Tuple[bool, Optional[str]]:
        """
        验证工具执行结果是否有效。
        
        Args:
            result: 工具执行结果
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not isinstance(result.success, bool):
            return False, "Result success must be a boolean"
        
        if result.success and result.result is None:
            return False, "Successful result must have a result value"
        
        if not result.success and not result.error:
            return False, "Failed result must have an error message"
        
        if result.tool_name and not isinstance(result.tool_name, str):
            return False, "Tool name must be a string"
        
        return True, None
    
    def validate_execution_plan(self, plan: ExecutionPlan) -> Tuple[bool, Optional[str]]:
        """
        验证执行计划是否有效。
        
        Args:
            plan: 执行计划
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not plan.task_id:
            return False, "Execution plan must have a task_id"
        
        if not plan.task_type:
            return False, "Execution plan must have a task_type"
        
        if not plan.description:
            return False, "Execution plan must have a description"
        
        if not plan.subtasks:
            return False, "Execution plan must have at least one subtask"
        
        for i, subtask in enumerate(plan.subtasks):
            is_valid, error = self.validate_subtask(subtask)
            if not is_valid:
                return False, f"Subtask {i} validation failed: {error}"
        
        return True, None
    
    def validate_subtask(self, subtask: SubTask) -> Tuple[bool, Optional[str]]:
        """
        验证子任务是否有效。
        
        Args:
            subtask: 子任务
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if subtask.id is None:
            return False, "Subtask must have an id"
        
        if not subtask.description:
            return False, "Subtask must have a description"
        
        if not subtask.tools:
            return False, "Subtask must have at least one tool"
        
        for dep_id in subtask.dependencies:
            if dep_id == subtask.id:
                return False, f"Subtask cannot depend on itself (id={subtask.id})"
        
        return True, None
    
    def validate_execution_context(self, context: ExecutionContext) -> Tuple[bool, Optional[str]]:
        """
        验证执行上下文是否有效。
        
        Args:
            context: 执行上下文
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not context.task_id:
            return False, "Execution context must have a task_id"
        
        if not context.user_request:
            return False, "Execution context must have a user_request"
        
        if not context.execution_plan:
            return False, "Execution context must have an execution_plan"
        
        if context.current_step < 0:
            return False, "Current step cannot be negative"
        
        if context.current_step > len(context.execution_plan.subtasks):
            return False, "Current step exceeds number of subtasks"
        
        return True, None
    
    def validate_memory_address(self, address: Any) -> Tuple[bool, Optional[str]]:
        """
        验证内存地址是否有效。
        
        Args:
            address: 要验证的地址
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if isinstance(address, str):
            try:
                address = int(address, 0)
            except ValueError:
                return False, f"Invalid address format: {address}"
        
        if not isinstance(address, int):
            return False, f"Address must be an integer, got {type(address)}"
        
        if address < 0:
            return False, f"Address cannot be negative: {address}"
        
        if address > 0xFFFFFFFFFFFFFFFF:
            return False, f"Address too large: {address}"
        
        return True, None
    
    def validate_hex_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """
        验证十六进制模式是否有效。
        
        Args:
            pattern: 十六进制模式字符串
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not pattern:
            return False, "Pattern cannot be empty"
        
        parts = pattern.split()
        for part in parts:
            if part == '?':
                continue
            
            try:
                int(part, 16)
            except ValueError:
                return False, f"Invalid hex byte: {part}"
        
        return True, None
    
    def validate_json(self, json_str: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        验证JSON字符串是否有效。
        
        Args:
            json_str: JSON字符串
            
        Returns:
            (是否有效, 错误消息, 解析后的字典)元组
        """
        try:
            import json
            parsed = json.loads(json_str)
            return True, None, parsed
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}", None
    
    def validate_parameter_type(self, value: Any, expected_type: str) -> Tuple[bool, Optional[str]]:
        """
        验证参数类型是否匹配。
        
        Args:
            value: 要验证的值
            expected_type: 期望的类型字符串
            
        Returns:
            (是否有效, 错误消息)元组
        """
        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict,
            'any': object
        }
        
        expected_python_type = type_map.get(expected_type, object)
        
        if not isinstance(value, expected_python_type):
            return False, f"Expected type {expected_type}, got {type(value).__name__}"
        
        return True, None
    
    def validate_range(self, value: Any, min_val: Optional[Any] = None, max_val: Optional[Any] = None) -> Tuple[bool, Optional[str]]:
        """
        验证值是否在指定范围内。
        
        Args:
            value: 要验证的值
            min_val: 最小值（可选）
            max_val: 最大值（可选）
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if min_val is not None and value < min_val:
            return False, f"Value {value} is less than minimum {min_val}"
        
        if max_val is not None and value > max_val:
            return False, f"Value {value} is greater than maximum {max_val}"
        
        return True, None
    
    def validate_length(self, value: Any, min_len: Optional[int] = None, max_len: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        验证值的长度是否在指定范围内。
        
        Args:
            value: 要验证的值（字符串、列表等）
            min_len: 最小长度（可选）
            max_len: 最大长度（可选）
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not hasattr(value, '__len__'):
            return False, f"Value of type {type(value).__name__} has no length"
        
        length = len(value)
        
        if min_len is not None and length < min_len:
            return False, f"Length {length} is less than minimum {min_len}"
        
        if max_len is not None and length > max_len:
            return False, f"Length {length} is greater than maximum {max_len}"
        
        return True, None
    
    def validate_regex(self, value: str, pattern: str) -> Tuple[bool, Optional[str]]:
        """
        验证字符串是否匹配正则表达式模式。
        
        Args:
            value: 要验证的字符串
            pattern: 正则表达式模式
            
        Returns:
            (是否有效, 错误消息)元组
        """
        import re
        try:
            if not re.match(pattern, value):
                return False, f"Value '{value}' does not match pattern '{pattern}'"
            return True, None
        except re.error as e:
            return False, f"Invalid regex pattern: {e}"
    
    def validate_file_path(self, path: str, must_exist: bool = False) -> Tuple[bool, Optional[str]]:
        """
        验证文件路径是否有效。
        
        Args:
            path: 文件路径
            must_exist: 文件是否必须存在
            
        Returns:
            (是否有效, 错误消息)元组
        """
        from pathlib import Path
        
        try:
            p = Path(path)
            
            if must_exist and not p.exists():
                return False, f"Path does not exist: {path}"
            
            if p.exists() and not (p.is_file() or p.is_dir()):
                return False, f"Path is neither a file nor a directory: {path}"
            
            return True, None
        except Exception as e:
            return False, f"Invalid path: {e}"
    
    def sanitize_input(self, value: str, max_length: int = 1000) -> str:
        """
        清理输入字符串，移除潜在的危险字符。
        
        Args:
            value: 输入字符串
            max_length: 最大长度
            
        Returns:
            清理后的字符串
        """
        if not isinstance(value, str):
            return str(value)
        
        value = value[:max_length]
        
        dangerous_chars = ['\x00', '\r']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    def validate_task_request(self, request: str) -> Tuple[bool, Optional[str]]:
        """
        验证任务请求是否有效。
        
        Args:
            request: 任务请求字符串
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not request or not request.strip():
            return False, "Request cannot be empty"
        
        if len(request) > 10000:
            return False, "Request is too long (max 10000 characters)"
        
        return True, None


class InputValidator(Validator):
    """专门用于输入验证的验证器。"""
    
    def validate_user_input(self, input_str: str) -> Tuple[bool, Optional[str]]:
        """
        验证用户输入。
        
        Args:
            input_str: 用户输入字符串
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if not input_str or not input_str.strip():
            return False, "Input cannot be empty"
        
        if len(input_str) > 5000:
            return False, "Input is too long (max 5000 characters)"
        
        return True, None
    
    def validate_command(self, command: str, valid_commands: List[str]) -> Tuple[bool, Optional[str]]:
        """
        验证命令是否有效。
        
        Args:
            command: 命令字符串
            valid_commands: 有效命令列表
            
        Returns:
            (是否有效, 错误消息)元组
        """
        if command not in valid_commands:
            return False, f"Invalid command: {command}. Valid commands: {', '.join(valid_commands)}"
        
        return True, None


class OutputValidator(Validator):
    """专门用于输出验证的验证器。"""
    
    def validate_report(self, report: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        验证报告是否有效。
        
        Args:
            report: 报告字典
            
        Returns:
            (是否有效, 错误消息)元组
        """
        required_fields = ['task_id', 'success', 'summary', 'details', 'insights', 'recommendations']
        
        for field in required_fields:
            if field not in report:
                return False, f"Missing required field in report: {field}"
        
        if not isinstance(report['success'], bool):
            return False, "Report 'success' field must be a boolean"
        
        if not isinstance(report['insights'], list):
            return False, "Report 'insights' field must be a list"
        
        if not isinstance(report['recommendations'], list):
            return False, "Report 'recommendations' field must be a list"
        
        return True, None
