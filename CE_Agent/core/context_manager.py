from ..models.core_models import ExecutionContext, ExecutionStep, TaskState
from ..utils.logger import get_logger
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime


class ContextManager:
    """AI 代理的上下文管理器。"""
    
    def __init__(self):
        """初始化上下文管理器。"""
        self.logger = get_logger(__name__)
        self.contexts: Dict[str, ExecutionContext] = {}
    
    def create_context(self, request: str, plan) -> ExecutionContext:
        """
        创建新的执行上下文。
        
        Args:
            request: 用户的请求
            plan: 任务的执行计划
            
        Returns:
            创建的执行上下文
        """
        task_id = str(uuid.uuid4())
        
        context = ExecutionContext(
            task_id=task_id,
            user_request=request,
            execution_plan=plan,
            current_step=0,
            history=[],
            intermediate_results={},
            state=TaskState.PENDING
        )
        
        # 存储上下文
        self.contexts[task_id] = context
        
        # 更新状态为运行中
        context.state = TaskState.RUNNING
        
        self.logger.info(f"Created new execution context with ID: {task_id}")
        
        return context
    
    def add_step(self, context: ExecutionContext, step: ExecutionStep) -> None:
        """
        Add an execution step to the context history.
        
        Args:
            context: The execution context
            step: The execution step to add
        """
        context.history.append(step)
        context.current_step += 1
        
        # Update context in storage
        self.contexts[context.task_id] = context
        
        self.logger.debug(f"Added step {step.step_id} to context {context.task_id}")
    
    def store_result(self, context: ExecutionContext, key: str, value: Any) -> None:
        """
        Store an intermediate result in the context.
        
        Args:
            context: The execution context
            key: The key to store the result under
            value: The result value to store
        """
        context.intermediate_results[key] = value
        
        # Update context in storage
        self.contexts[context.task_id] = context
        
        self.logger.debug(f"Stored intermediate result '{key}' in context {context.task_id}")
    
    def get_result(self, context: ExecutionContext, key: str) -> Optional[Any]:
        """
        Retrieve an intermediate result from the context.
        
        Args:
            context: The execution context
            key: The key of the result to retrieve
            
        Returns:
            The stored result value, or None if not found
        """
        result = context.intermediate_results.get(key)
        
        if result is not None:
            self.logger.debug(f"Retrieved intermediate result '{key}' from context {context.task_id}")
        else:
            self.logger.warning(f"Intermediate result '{key}' not found in context {context.task_id}")
        
        return result
    
    def update_state(self, context: ExecutionContext, state: TaskState) -> None:
        """
        Update the state of the execution context.
        
        Args:
            context: The execution context
            state: The new state
        """
        old_state = context.state
        context.state = state
        
        # Update context in storage
        self.contexts[context.task_id] = context
        
        self.logger.info(f"Updated context {context.task_id} state from {old_state} to {state}")
    
    def get_history(self, context: ExecutionContext) -> List[ExecutionStep]:
        """
        Get the execution history from the context.
        
        Args:
            context: The execution context
            
        Returns:
            The list of execution steps
        """
        return context.history[:]
    
    def get_context(self, task_id: str) -> Optional[ExecutionContext]:
        """
        Retrieve an execution context by task ID.
        
        Args:
            task_id: The task ID of the context to retrieve
            
        Returns:
            The execution context, or None if not found
        """
        context = self.contexts.get(task_id)
        if context:
            self.logger.debug(f"Retrieved context {task_id}")
        else:
            self.logger.warning(f"Context {task_id} not found")
        
        return context
    
    def remove_context(self, task_id: str) -> bool:
        """
        Remove an execution context by task ID.
        
        Args:
            task_id: The task ID of the context to remove
            
        Returns:
            True if the context was removed, False if not found
        """
        if task_id in self.contexts:
            del self.contexts[task_id]
            self.logger.info(f"Removed context {task_id}")
            return True
        else:
            self.logger.warning(f"Attempted to remove non-existent context {task_id}")
            return False
    
    def get_active_contexts(self) -> List[ExecutionContext]:
        """
        Get all active execution contexts.
        
        Returns:
            List of active execution contexts
        """
        active_states = [TaskState.PENDING, TaskState.RUNNING]
        active_contexts = [
            ctx for ctx in self.contexts.values() 
            if ctx.state in active_states
        ]
        
        self.logger.debug(f"Found {len(active_contexts)} active contexts")
        return active_contexts
    
    def clear_contexts(self) -> None:
        """Clear all execution contexts."""
        count = len(self.contexts)
        self.contexts.clear()
        self.logger.info(f"Cleared all {count} execution contexts")