"""
Cheat Engine AI Agent 的数据模型。

该模块定义了在整个代理中使用的核心数据结构，
包括工具元数据、参数、类别和结果。
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ToolCategory(str, Enum):
    """工具类别枚举。"""
    BASIC = "basic"
    MEMORY_READ = "memory_read"
    PATTERN_SCAN = "pattern_scan"
    DISASSEMBLE = "disassemble"
    BREAKPOINT_DEBUG = "breakpoint_debug"
    DBVM = "dbvm"
    PROCESS_MODULE = "process_module"


class Parameter(BaseModel):
    """工具参数的模型。"""
    name: str
    type: str
    required: bool
    default: Any = None
    description: str


class ToolMetadata(BaseModel):
    """工具元数据的模型。"""
    name: str
    category: ToolCategory
    description: str
    parameters: List[Parameter]
    destructive: bool = False
    requires_approval: bool = False
    examples: List[str] = []


class ToolResult(BaseModel):
    """工具执行结果的模型。"""
    success: bool
    tool_name: str
    parameters: Dict[str, Any]
    result: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolCall(BaseModel):
    """工具调用的模型。"""
    name: str
    arguments: Dict[str, Any]


class ExecutionPlan(BaseModel):
    """执行计划的模型。"""
    task_id: str
    task_type: str
    description: str
    subtasks: List['SubTask']
    estimated_steps: int


class SubTask(BaseModel):
    """子任务的模型。"""
    id: int
    description: str
    tools: List[str]
    expected_output: str
    dependencies: List[int] = []


class ExecutionContext(BaseModel):
    """执行上下文的模型。"""
    task_id: str
    user_request: str
    execution_plan: ExecutionPlan
    current_step: int = 0
    results: List[ToolResult] = []
    context_data: Dict[str, Any] = {}