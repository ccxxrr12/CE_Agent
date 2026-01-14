from ..models.core_models import (
    Analysis, StateEvaluation, Decision, RecoveryAction, 
    ExecutionContext, TaskState, ExecutionStep, ToolResult
)
from ..utils.logger import get_logger
from ..llm.prompt_manager import PromptManager
from ..llm.response_parser import ResponseParser
from ..llm.client import OllamaClient
from typing import List, Dict, Any, Optional
import time


class ReasoningEngine:
    """AI 代理的推理引擎。"""
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None, use_llm: bool = True, use_simple_prompt: bool = False, use_minimal_prompt: bool = False, use_json_prompt: bool = False, cli_callback: Optional[callable] = None):
        """
        初始化推理引擎。
        
        Args:
            ollama_client: 用于LLM推理的Ollama客户端
            use_llm: 是否使用LLM进行推理
            use_simple_prompt: 是否使用简化版提示词
            use_minimal_prompt: 是否使用超简洁版提示词
            use_json_prompt: 是否使用JSON格式提示词
            cli_callback: 日志回调函数
        """
        self.ollama_client = ollama_client
        self.use_llm = use_llm
        self.cli_callback = cli_callback
        self.prompt_manager = PromptManager(use_simple_prompt=use_simple_prompt, use_minimal_prompt=use_minimal_prompt, use_json_prompt=use_json_prompt) if use_llm else None
        self.response_parser = ResponseParser() if use_llm else None
        self.logger = get_logger(__name__)
    
    def analyze_result(self, result: ToolResult, context: ExecutionContext) -> Analysis:
        """
        分析工具执行的结果。
        
        Args:
            result: 工具执行的结果
            context: 当前执行上下文
            
        Returns:
            结果的分析
        """
        if self.cli_callback:
            self.cli_callback('reasoning', f'分析工具执行结果: {result.tool_name}')
        
        if self.use_llm and self.ollama_client:
            return self._analyze_with_llm(result, context)
        else:
            return self._analyze_with_rules(result, context)
    
    def _analyze_with_llm(self, result: ToolResult, context: ExecutionContext) -> Analysis:
        """
        使用LLM进行智能结果分析。
        
        Args:
            result: 工具执行的结果
            context: 当前执行上下文
            
        Returns:
            结果的分析
        """
        try:
            if self.cli_callback:
                self.cli_callback('reasoning', '使用LLM进行智能分析')
            
            result_dict = {
                'tool_name': result.tool_name,
                'success': result.success,
                'result': result.result,
                'error': result.error,
                'execution_time': result.execution_time
            }
            
            context_dict = {
                'task_id': context.task_id,
                'current_step': context.current_step,
                'total_steps': context.execution_plan.estimated_steps,
                'state': context.state.value
            }
            
            prompt = self.prompt_manager.get_result_analysis_prompt(
                result=result_dict,
                tool_name=result.tool_name,
                context=context_dict
            )
            
            system_prompt = self.prompt_manager.get_system_prompt()
            messages = self.prompt_manager.format_chat_messages(
                system_prompt=system_prompt,
                user_prompt=prompt
            )
            
            if self.cli_callback:
                self.cli_callback('llm_call', '结果分析', status='starting')
            
            start_time = time.time()
            response = self.ollama_client.chat(messages)
            execution_time = time.time() - start_time
            
            if self.cli_callback:
                self.cli_callback('llm_call', '结果分析', status='success', duration=execution_time)
            
            if 'message' in response and 'content' in response['message']:
                response_text = response['message']['content']
                
                if self.cli_callback:
                    self.cli_callback('reasoning', '解析LLM分析结果')
                
                analysis_dict = self.response_parser.parse_result_analysis(response_text)
                
                if analysis_dict:
                    analysis = Analysis(
                        success=analysis_dict.get('success', result.success),
                        findings=[{
                            'type': 'finding',
                            'message': finding,
                            'data': None
                        } for finding in analysis_dict.get('findings', [])],
                        conclusions=analysis_dict.get('insights', []),
                        next_steps=analysis_dict.get('next_steps', []),
                        confidence=0.8
                    )
                    
                    if self.cli_callback:
                        self.cli_callback('reasoning', f'LLM分析完成: {len(analysis.findings)} 个发现, {len(analysis.conclusions)} 个结论')
                    
                    return analysis
            
            if self.cli_callback:
                self.cli_callback('warning', 'LLM分析解析失败，回退到规则引擎')
            
            if self.logger:
                self.logger.warning("Failed to parse LLM analysis, falling back to rule-based analysis")
            
            return self._analyze_with_rules(result, context)
            
        except Exception as e:
            if self.cli_callback:
                self.cli_callback('error', f'LLM分析出错: {e}')
            
            if self.logger:
                self.logger.error(f"Error in LLM analysis: {e}, falling back to rule-based analysis")
            return self._analyze_with_rules(result, context)
    
    def _analyze_with_rules(self, result: ToolResult, context: ExecutionContext) -> Analysis:
        """
        使用规则引擎进行结果分析（回退方案）。
        
        Args:
            result: 工具执行的结果
            context: 当前执行上下文
            
        Returns:
            结果的分析
        """
        try:
            if self.cli_callback:
                self.cli_callback('reasoning', '使用规则引擎进行分析')
            
            success = result.success
            findings = []
            conclusions = []
            next_steps = []
            confidence = 0.8  # 默认置信度
            
            if success:
                # 从成功结果中提取发现
                findings.append({
                    "type": "success",
                    "message": f"工具 '{result.tool_name}' 执行成功",
                    "data": result.result
                })
                
                # 确定此结果是否满足当前子任务的预期输出
                current_subtask_idx = min(context.current_step, len(context.execution_plan.subtasks) -1)
                if current_subtask_idx >= 0:
                    current_subtask = context.execution_plan.subtasks[current_subtask_idx]
                    
                    # 添加关于子任务进度的结论
                    conclusions.append(f"子任务 '{current_subtask.description}' 部分完成")
                    
                    # Determine next steps based on subtask completion
                    if self._is_subtask_complete(current_subtask, context):
                        next_steps.append(f"Move to next subtask: {self._get_next_subtask(context)}")
                    else:
                        next_steps.append(f"Continue current subtask: {current_subtask.description}")
            else:
                # Handle failure case
                findings.append({
                    "type": "error",
                    "message": f"Tool '{result.tool_name}' failed: {result.error}",
                    "data": None
                })
                
                # Lower confidence due to failure
                confidence = 0.3
                conclusions.append(f"Tool execution failed, need to adjust approach")
                
                # Determine recovery steps
                next_steps.append("Attempt recovery or alternative approach")
            
            analysis = Analysis(
                success=success,
                findings=findings,
                conclusions=conclusions,
                next_steps=next_steps,
                confidence=confidence
            )
            
            if self.cli_callback:
                self.cli_callback('reasoning', f'规则引擎分析完成: {len(findings)} 个发现, {len(conclusions)} 个结论')
            
            return analysis
        except Exception as e:
            if self.cli_callback:
                self.cli_callback('error', f'规则引擎分析出错: {e}')
            
            self.logger.error(f"Error analyzing result: {e}")
            return Analysis(
                success=False,
                findings=[{
                    "type": "error",
                    "message": f"Failed to analyze result: {str(e)}",
                    "data": None
                }],
                conclusions=["Could not analyze result due to internal error"],
                next_steps=["Retry analysis or skip to next step"],
                confidence=0.1
            )
    
    def evaluate_state(self, context: ExecutionContext) -> StateEvaluation:
        """
        Evaluate the current state of execution.
        
        Args:
            context: The current execution context
            
        Returns:
            An evaluation of the current state
        """
        try:
            # Calculate progress
            total_subtasks = len(context.execution_plan.subtasks)
            completed_steps = len([step for step in context.history if step.success])
            total_expected_steps = context.execution_plan.estimated_steps
            
            progress = min(completed_steps / max(total_expected_steps, 1), 1.0)
            
            # Determine success based on current state
            success = context.state != TaskState.FAILED and progress < 1.0
            
            # Identify any issues
            issues = []
            recent_errors = [step for step in context.history if not step.success][-3:]  # Last 3 errors
            
            if recent_errors:
                issues.extend([f"Recent error in step {step.step_id}: {step.error}" for step in recent_errors])
            
            # Check if we're stuck
            if len(context.history) > 0 and len(recent_errors) == len(context.history[-5:]):  # Last 5 steps all failed
                issues.append("Appears to be stuck in error loop")
            
            # Generate recommendations
            recommendations = []
            if progress >= 1.0:
                recommendations.append("Task appears complete, finalize results")
            elif issues:
                recommendations.append("Address identified issues before proceeding")
            else:
                recommendations.append("Continue with planned execution")
            
            return StateEvaluation(
                current_state=context.state,
                progress=progress,
                success=success,
                issues=issues,
                recommendations=recommendations
            )
        except Exception as e:
            self.logger.error(f"Error evaluating state: {e}")
            return StateEvaluation(
                current_state=TaskState.FAILED,
                progress=0.0,
                success=False,
                issues=[f"State evaluation failed: {str(e)}"],
                recommendations=["Restart execution or abort"]
            )
    
    def make_decision(self, evaluation: StateEvaluation, context: ExecutionContext) -> Decision:
        """
        Make a decision based on state evaluation.
        
        Args:
            evaluation: The state evaluation
            context: The current execution context
            
        Returns:
            A decision to guide next actions
        """
        if self.cli_callback:
            self.cli_callback('decision', f'根据状态评估做出决策: 进度 {evaluation.progress:.1%}')
        
        if self.use_llm and self.ollama_client:
            return self._make_decision_with_llm(evaluation, context)
        else:
            return self._make_decision_with_rules(evaluation, context)
    
    def _make_decision_with_llm(self, evaluation: StateEvaluation, context: ExecutionContext) -> Decision:
        """
        使用LLM进行智能决策。
        
        Args:
            evaluation: 状态评估
            context: 当前执行上下文
            
        Returns:
            决策对象
        """
        try:
            if self.cli_callback:
                self.cli_callback('reasoning', '使用LLM进行智能决策')
            
            evaluation_dict = {
                'current_state': evaluation.current_state.value,
                'progress': evaluation.progress,
                'success': evaluation.success,
                'issues': evaluation.issues,
                'recommendations': evaluation.recommendations
            }
            
            context_dict = {
                'task_id': context.task_id,
                'current_step': context.current_step,
                'total_steps': context.execution_plan.estimated_steps,
                'task_type': context.execution_plan.task_type
            }
            
            prompt = self.prompt_manager.get_reasoning_prompt(
                current_result=evaluation_dict,
                context=context_dict,
                available_tools=[]
            )
            
            system_prompt = self.prompt_manager.get_system_prompt()
            messages = self.prompt_manager.format_chat_messages(
                system_prompt=system_prompt,
                user_prompt=prompt
            )
            
            if self.cli_callback:
                self.cli_callback('llm_call', '决策推理', status='starting')
            
            start_time = time.time()
            response = self.ollama_client.chat(messages)
            execution_time = time.time() - start_time
            
            if self.cli_callback:
                self.cli_callback('llm_call', '决策推理', status='success', duration=execution_time)
            
            if 'message' in response and 'content' in response['message']:
                response_text = response['message']['content']
                
                if self.cli_callback:
                    self.cli_callback('reasoning', '解析LLM决策')
                
                reasoning_dict = self.response_parser.parse_reasoning(response_text)
                
                if reasoning_dict:
                    decision = Decision(
                        action=reasoning_dict.get('next_action', 'continue'),
                        reason=reasoning_dict.get('reasoning', ''),
                        confidence=reasoning_dict.get('confidence', 0.8),
                        next_steps=reasoning_dict.get('next_steps', [])
                    )
                    
                    if self.cli_callback:
                        self.cli_callback('decision', f'LLM决策: {decision.action} (置信度: {decision.confidence:.1%})')
                    
                    return decision
            
            if self.cli_callback:
                self.cli_callback('warning', 'LLM决策解析失败，回退到规则引擎')
            
            if self.logger:
                self.logger.warning("Failed to parse LLM decision, falling back to rule-based decision")
            
            return self._make_decision_with_rules(evaluation, context)
            
        except Exception as e:
            if self.cli_callback:
                self.cli_callback('error', f'LLM决策出错: {e}')
            
            if self.logger:
                self.logger.error(f"Error in LLM decision: {e}, falling back to rule-based decision")
            return self._make_decision_with_rules(evaluation, context)
    
    def _make_decision_with_rules(self, evaluation: StateEvaluation, context: ExecutionContext) -> Decision:
        """
        使用规则引擎进行决策（回退方案）。
        
        Args:
            evaluation: 状态评估
            context: 当前执行上下文
            
        Returns:
            决策对象
        """
        try:
            if self.cli_callback:
                self.cli_callback('reasoning', '使用规则引擎进行决策')
            
            action = ""
            reason = ""
            confidence = evaluation.progress  # Base confidence on progress
            next_steps = []
            
            if evaluation.current_state == TaskState.COMPLETED:
                action = "finalize"
                reason = "Task has been marked as completed"
                next_steps = ["Generate final report"]
            elif evaluation.current_state == TaskState.FAILED:
                action = "abort"
                reason = "Task has been marked as failed"
                next_steps = ["Abort execution and report error"]
            elif evaluation.issues:
                # Address issues first
                if "stuck in error loop" in evaluation.issues:
                    action = "recover"
                    reason = "Detected error loop, attempting recovery"
                    confidence = 0.5
                    next_steps = ["Try alternative tools or approaches"]
                else:
                    action = "adjust"
                    reason = "Issues detected, need to adjust plan"
                    confidence = 0.7
                    next_steps = evaluation.recommendations
            elif evaluation.progress >= 1.0:
                action = "finalize"
                reason = "Estimated steps completed"
                next_steps = ["Generate final report"]
            else:
                action = "continue"
                reason = "No major issues detected, continue with plan"
                next_steps = ["Execute next planned step"]
            
            # Adjust confidence based on issues
            if evaluation.issues:
                confidence *= 0.7  # Reduce confidence if issues exist
            
            decision = Decision(
                action=action,
                reason=reason,
                confidence=confidence,
                next_steps=next_steps
            )
            
            if self.cli_callback:
                self.cli_callback('decision', f'规则引擎决策: {decision.action} (置信度: {decision.confidence:.1%})')
            
            return decision
        except Exception as e:
            if self.cli_callback:
                self.cli_callback('error', f'规则引擎决策出错: {e}')
            
            self.logger.error(f"Error making decision: {e}")
            return Decision(
                action="error",
                reason=f"Decision making failed: {str(e)}",
                confidence=0.1,
                next_steps=["Abort execution due to internal error"]
            )
    
    def adjust_plan(self, decision: Decision, context: ExecutionContext) -> None:
        """
        Adjust the execution plan based on a decision.
        
        Args:
            decision: The decision to act on
            context: The current execution context
        """
        try:
            if self.cli_callback:
                self.cli_callback('decision', f'根据决策调整计划: {decision.action}')
            
            if decision.action == "recover":
                # Attempt recovery by adjusting the plan
                if self.cli_callback:
                    self.cli_callback('decision', '尝试恢复执行')
                self._attempt_recovery(context)
            elif decision.action == "adjust":
                # Modify the plan based on current state
                if self.cli_callback:
                    self.cli_callback('decision', '调整执行计划')
                self._modify_plan(context)
            elif decision.action == "continue":
                # Continue with the existing plan
                if self.cli_callback:
                    self.cli_callback('decision', '继续执行现有计划')
                pass  # No adjustment needed
            elif decision.action == "finalize":
                # Mark context as completed
                if self.cli_callback:
                    self.cli_callback('success', '任务完成')
                context.state = TaskState.COMPLETED
            elif decision.action == "abort":
                # Mark context as failed
                if self.cli_callback:
                    self.cli_callback('error', '任务中止')
                context.state = TaskState.FAILED
        except Exception as e:
            if self.cli_callback:
                self.cli_callback('error', f'调整计划出错: {e}')
            self.logger.error(f"Error adjusting plan: {e}")
    
    def recover_from_error(self, error: Exception, context: ExecutionContext) -> RecoveryAction:
        """
        Generate a recovery action when an error occurs.
        
        Args:
            error: The error that occurred
            context: The current execution context
            
        Returns:
            A recovery action to attempt
        """
        try:
            error_str = str(error)
            
            # Determine appropriate recovery action based on error type
            if "timeout" in error_str.lower():
                action = "retry"
                reason = "Timeout occurred, attempting retry with longer timeout"
                alternative_tools = []
                retry_count = 1
            elif "connection" in error_str.lower() or "pipe" in error_str.lower():
                action = "reconnect"
                reason = "Connection issue detected, attempting to reconnect"
                alternative_tools = []
                retry_count = 1
            elif "access denied" in error_str.lower() or "permission" in error_str.lower():
                action = "switch_approach"
                reason = "Permission denied, trying alternative approach"
                # Suggest alternative tools that might work
                alternative_tools = self._suggest_alternative_tools(context)
                retry_count = 0
            else:
                action = "switch_approach"
                reason = f"General error occurred: {error_str}, trying alternative approach"
                alternative_tools = self._suggest_alternative_tools(context)
                retry_count = 0
            
            return RecoveryAction(
                action=action,
                reason=reason,
                alternative_tools=alternative_tools,
                retry_count=retry_count
            )
        except Exception as e:
            self.logger.error(f"Error generating recovery action: {e}")
            return RecoveryAction(
                action="abort",
                reason=f"Could not generate recovery action: {str(e)}",
                alternative_tools=[],
                retry_count=0
            )
    
    def _is_subtask_complete(self, subtask, context: ExecutionContext) -> bool:
        """
        Check if a subtask is considered complete based on execution history.
        
        Args:
            subtask: The subtask to check
            context: The current execution context
            
        Returns:
            True if the subtask is complete, False otherwise
        """
        # Simple heuristic: if all required tools for the subtask have been successfully executed
        successful_tool_calls = [step for step in context.history if step.success]
        subtask_tools_used = [step.tool_name for step in successful_tool_calls if step.tool_name in subtask.tools]
        
        # Consider subtask complete if we've used most of the required tools
        return len(set(subtask_tools_used)) >= max(1, len(subtask.tools) // 2)
    
    def _get_next_subtask(self, context: ExecutionContext) -> str:
        """
        Get the description of the next subtask.
        
        Args:
            context: The current execution context
            
        Returns:
            Description of the next subtask
        """
        next_idx = min(context.current_step + 1, len(context.execution_plan.subtasks) - 1)
        if next_idx < len(context.execution_plan.subtasks):
            return context.execution_plan.subtasks[next_idx].description
        return "No more subtasks"
    
    def _attempt_recovery(self, context: ExecutionContext) -> None:
        """
        Attempt to recover from an error state.
        
        Args:
            context: The current execution context
        """
        # Try using alternative tools for the current step
        current_subtask_idx = min(context.current_step, len(context.execution_plan.subtasks) - 1)
        if current_subtask_idx >= 0:
            current_subtask = context.execution_plan.subtasks[current_subtask_idx]
            
            # Log recovery attempt
            self.logger.info(f"Attempting recovery for subtask: {current_subtask.description}")
    
    def _modify_plan(self, context: ExecutionContext) -> None:
        """
        Modify the execution plan based on current state.
        
        Args:
            context: The current execution context
        """
        # In a more sophisticated implementation, this would modify the plan
        # For now, we'll just log that a modification was needed
        self.logger.info("Plan modification suggested but not implemented in this version")
    
    def _suggest_alternative_tools(self, context: ExecutionContext) -> List[str]:
        """
        Suggest alternative tools when the current approach fails.
        
        Args:
            context: The current execution context
            
        Returns:
            List of alternative tool names
        """
        # Simple heuristic: suggest other tools in the same category
        current_subtask_idx = min(context.current_step, len(context.execution_plan.subtasks) - 1)
        if current_subtask_idx >= 0:
            current_subtask = context.execution_plan.subtasks[current_subtask_idx]
            
            # For now, return a general list of alternative tools
            # In a real implementation, this would come from the tool registry
            return [tool for tool in current_subtask.tools]
        
        return []