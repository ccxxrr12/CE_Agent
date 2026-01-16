"""
Cheat Engine AI Agent 的工具模型。

该模块包含工具相关的基础模型类，如ToolMetadata、ToolCategory、ToolCall和Parameter等。
"""
from typing import List, Dict, Any, Optional
from enum import Enum


class ToolCategory(Enum):
    """工具类别枚举。"""
    BASIC = "basic"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    PATTERN_SCAN = "pattern_scan"
    DEBUG = "debug"
    BREAKPOINT = "breakpoint"
    DBVM = "dbvm"
    PROCESS = "process"
    OTHER = "other"


class Parameter:
    """
    工具参数模型。
    
    表示工具的单个参数，包括名称、类型、是否必填、描述和默认值等。
    """
    def __init__(
        self,
        name: str,
        type: str,
        required: bool,
        description: str,
        default: Any = None
    ):
        """
        初始化参数。
        
        Args:
            name: 参数名称
            type: 参数类型
            required: 是否为必填参数
            description: 参数描述
            default: 默认值，仅对非必填参数有效
        """
        self.name = name
        self.type = type
        self.required = required
        self.description = description
        self.default = default

    def to_dict(self) -> Dict[str, Any]:
        """
        将参数转换为字典格式。
        
        Returns:
            包含参数信息的字典
        """
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "default": self.default
        }


class ToolMetadata:
    """
    工具元数据模型。
    
    表示工具的元数据信息，包括名称、类别、描述、参数列表和示例等。
    """
    def __init__(
        self,
        name: str,
        category: ToolCategory,
        description: str,
        parameters: List[Parameter] = None,
        examples: List[str] = None,
        timeout: Optional[float] = None,
        destructive: bool = False,
        requires_approval: bool = False
    ):
        """
        初始化工具元数据。
        
        Args:
            name: 工具名称
            category: 工具类别
            description: 工具描述
            parameters: 参数列表
            examples: 使用示例列表
            timeout: 执行超时时间（秒）
            destructive: 是否为破坏性工具
            requires_approval: 是否需要批准才能执行
        """
        self.name = name
        self.category = category
        self.description = description
        self.parameters = parameters or []
        self.examples = examples or []
        self.timeout = timeout
        self.destructive = destructive
        self.requires_approval = requires_approval

    def to_dict(self) -> Dict[str, Any]:
        """
        将工具元数据转换为字典格式。
        
        Returns:
            包含工具元数据的字典
        """
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "parameters": [param.to_dict() for param in self.parameters],
            "examples": self.examples,
            "timeout": self.timeout,
            "destructive": self.destructive,
            "requires_approval": self.requires_approval
        }


class ToolCall:
    """
    工具调用模型。
    
    表示对工具的一次调用，包括工具名称和参数等。
    """
    def __init__(
        self,
        name: str,
        arguments: Dict[str, Any] = None
    ):
        """
        初始化工具调用。
        
        Args:
            name: 工具名称
            arguments: 工具参数
        """
        self.name = name
        self.arguments = arguments or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        将工具调用转换为字典格式。
        
        Returns:
            包含工具调用信息的字典
        """
        return {
            "name": self.name,
            "arguments": self.arguments
        }


class ToolResult:
    """
    工具执行结果模型。
    
    表示工具执行后的结果，包括成功状态、工具名称、参数、结果和错误信息等。
    """
    def __init__(
        self,
        success: bool,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any = None,
        error: str = None,
        execution_time: float = 0.0
    ):
        """
        初始化工具结果。
        
        Args:
            success: 执行是否成功
            tool_name: 工具名称
            parameters: 执行时使用的参数
            result: 执行结果（仅当成功时有效）
            error: 错误信息（仅当失败时有效）
            execution_time: 执行耗时（秒）
        """
        self.success = success
        self.tool_name = tool_name
        self.parameters = parameters
        self.result = result
        self.error = error
        self.execution_time = execution_time

    def to_dict(self) -> Dict[str, Any]:
        """
        将工具结果转换为字典格式。
        
        Returns:
            包含工具结果信息的字典
        """
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time
        }
