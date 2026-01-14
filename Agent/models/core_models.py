from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TaskState(str, Enum):
    """任务状态枚举。"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubTask(BaseModel):
    """执行计划中子任务的模型。"""
    id: int
    description: str
    tools: List[str]
    expected_output: str
    dependencies: List[int] = []


class ExecutionStep(BaseModel):
    """执行步骤的模型。"""
    step_id: int
    tool_name: str
    tool_args: Dict[str, Any]
    result: Any
    timestamp: datetime
    success: bool
    error: Optional[str] = None


class ExecutionPlan(BaseModel):
    """执行计划的模型。"""
    task_id: str
    task_type: str
    description: str
    subtasks: List[SubTask]
    estimated_steps: int


class ExecutionContext(BaseModel):
    """执行上下文的模型。"""
    task_id: str
    user_request: str
    execution_plan: ExecutionPlan
    current_step: int
    history: List[ExecutionStep]
    intermediate_results: Dict[str, Any]
    state: TaskState


class AnalysisReport(BaseModel):
    """Model for analysis reports."""
    task_id: str
    success: bool
    summary: str
    details: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    execution_time: float
    error: Optional[str] = None


class Analysis(BaseModel):
    """Model for analysis results."""
    success: bool
    findings: List[Dict[str, Any]]
    conclusions: List[str]
    next_steps: List[str]
    confidence: float


class StateEvaluation(BaseModel):
    """Model for state evaluation."""
    current_state: TaskState
    progress: float
    success: bool
    issues: List[str]
    recommendations: List[str]


class Decision(BaseModel):
    """Model for decisions made by the reasoning engine."""
    action: str
    reason: str
    confidence: float
    next_steps: List[str]


class RecoveryAction(BaseModel):
    """Model for recovery actions."""
    action: str
    reason: str
    alternative_tools: List[str]
    retry_count: int


class ToolResult(BaseModel):
    """Model for tool execution results."""
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = {}