from ..core.task_planner import TaskPlanner
from ..core.reasoning_engine import ReasoningEngine
from ..core.context_manager import ContextManager
from ..core.result_synthesizer import ResultSynthesizer
from ..models.core_models import AnalysisReport, ExecutionStep
from ..tools.registry import ToolRegistry
from ..tools.executor import ToolExecutor
from ..mcp.client import MCPClient
from ..llm.client import OllamaClient
from ..config import Config
from ..utils.logger import get_logger
from typing import Optional
import time
import datetime
import threading
import queue


class AgentStatus:
    """代理状态枚举。"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class Agent:
    """协调所有组件的主 AI 代理。"""
    
    def __init__(self, config: Config, tool_registry: ToolRegistry, mcp_client: MCPClient, ollama_client: OllamaClient, use_llm: bool = True, use_simple_prompt: bool = False, use_minimal_prompt: bool = False):
        """
        初始化 AI 代理。
        
        Args:
            config: 配置对象
            tool_registry: 可用工具的注册表
            mcp_client: 用于与 Cheat Engine 通信的 MCP 客户端
            ollama_client: 用于 LLM 交互的 Ollama 客户端
            use_llm: 是否使用 LLM
            use_simple_prompt: 是否使用简化版提示词
            use_minimal_prompt: 是否使用超简洁版提示词
        """
        self.config = config
        self.tool_registry = tool_registry
        self.mcp_client = mcp_client
        self.ollama_client = ollama_client
        self.logger = get_logger(__name__)
        
        # 初始化核心组件
        self.task_planner = TaskPlanner(tool_registry, ollama_client, use_llm=use_llm, use_simple_prompt=use_simple_prompt, use_minimal_prompt=use_minimal_prompt)
        self.reasoning_engine = ReasoningEngine(ollama_client, use_llm=use_llm, use_simple_prompt=use_simple_prompt, use_minimal_prompt=use_minimal_prompt)
        self.context_manager = ContextManager()
        self.result_synthesizer = ResultSynthesizer()
        
        # 初始化工具执行器
        self.tool_executor = ToolExecutor(tool_registry, mcp_client)
        
        # 设置内部状态
        self.status = AgentStatus.STOPPED
        self.stop_event = threading.Event()
        self.task_queue = queue.Queue()
        self.active_task = None
        
        # 为子组件设置日志记录器
        self.task_planner.logger = self.logger
        self.reasoning_engine.logger = self.logger
        self.context_manager.logger = self.logger
        self.result_synthesizer.logger = self.logger
    
    def execute(self, request: str) -> AnalysisReport:
        """
        从头到尾执行单个请求。
        
        Args:
            request: 用户的请求
            
        Returns:
            分析报告
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始执行请求: {request}")
            
            # 更新代理状态
            self.status = AgentStatus.RUNNING
            
            # 规划任务
            self.logger.debug("正在规划任务...")
            execution_plan = self.task_planner.plan(request)
            
            # 创建执行上下文
            self.logger.debug("正在创建执行上下文...")
            context = self.context_manager.create_context(request, execution_plan)
            
            # 执行计划
            self.logger.debug("正在执行计划...")
            self._execute_plan(context)
            
            # 生成最终报告
            self.logger.debug("正在生成最终报告...")
            report = self.result_synthesizer.synthesize(context)
            
            # 更新执行时间
            report.execution_time = time.time() - start_time
            
            self.logger.info(f"任务 {context.task_id} 执行成功")
            
            return report
        except Exception as e:
            self.logger.error(f"执行过程中出错: {e}")
            self.status = AgentStatus.ERROR
            
            # 创建错误报告
            error_report = AnalysisReport(
                task_id="error-" + str(int(time.time())),
                success=False,
                summary="由于内部错误导致执行失败",
                details={"error": str(e)},
                insights=["由于错误无法完成执行"],
                recommendations=["重试请求或联系支持"],
                execution_time=time.time() - start_time,
                error=str(e)
            )
            
            return error_report
        finally:
            # 更新代理状态
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.STOPPED
    
    def run(self) -> None:
        """
        启动代理的主执行循环以处理排队的任务。
        """
        self.logger.info("Starting agent main loop")
        self.status = AgentStatus.RUNNING
        self.stop_event.clear()
        
        try:
            while not self.stop_event.is_set():
                try:
                    # 从队列获取下一个任务（带超时）
                    try:
                        request = self.task_queue.get(timeout=1.0)
                        self.logger.debug(f"正在处理排队的任务: {request}")
                        
                        # 执行任务
                        self.active_task = request
                        self.execute(request)
                        self.active_task = None
                        
                        # 标记任务为已完成
                        self.task_queue.task_done()
                    except queue.Empty:
                        # 队列为空，继续循环
                        continue
                except Exception as e:
                    self.logger.error(f"代理主循环中出错: {e}")
                    self.status = AgentStatus.ERROR
                    break
                    
                # 短暂休眠以防止忙等待
                time.sleep(0.1)
        finally:
            self.status = AgentStatus.STOPPED
            self.stop_event.set()
            self.logger.info("Agent main loop stopped")
    
    def submit_task(self, request: str) -> None:
        """
        将任务提交到代理的队列进行处理。
        
        Args:
            request: 要处理的用户请求
        """
        self.task_queue.put(request)
        self.logger.info(f"已将任务提交到队列: {request}")
    
    def stop(self) -> None:
        """优雅地停止代理。"""
        self.logger.info("Stopping agent...")
        self.stop_event.set()
        self.status = AgentStatus.STOPPED
        
        # 清空任务队列
        with self.task_queue.mutex:
            self.task_queue.queue.clear()
        
        self.logger.info("Agent stopped")
    
    def get_status(self) -> str:
        """
        获取代理的当前状态。
        
        Returns:
            当前的代理状态
        """
        return self.status
    
    def _execute_plan(self, context) -> None:
        """
        在给定上下文中执行执行计划。
        
        Args:
            context: 执行上下文
        """
        try:
            # 遍历子任务
            for subtask in context.execution_plan.subtasks:
                self.logger.info(f"Executing subtask: {subtask.description}")
                
                # 检查依赖是否满足
                if not self._check_dependencies_satisfied(subtask, context):
                    self.logger.warning(f"Dependencies not satisfied for subtask: {subtask.description}")
                    continue
                
                # 为此子任务执行工具
                for tool_name in subtask.tools:
                    if self.stop_event.is_set():
                        self.logger.info("Stop event received, terminating execution")
                        return
                    
                    # 准备工具参数
                    # 在实际实现中，我们会根据上下文确定参数
                    # 目前，我们将使用空参数，让各个工具处理默认值
                    tool_args = self._determine_tool_args(tool_name, context)
                    
                    # 执行工具
                    self.logger.debug(f"Executing tool: {tool_name}")
                    result = self.tool_executor.execute(tool_name, **tool_args)
                    
                    # 创建执行步骤
                    step = ExecutionStep(
                        step_id=len(context.history) + 1,
                        tool_name=tool_name,
                        tool_args=tool_args,
                        result=result.result,
                        timestamp=datetime.datetime.now(),
                        success=result.success,
                        error=result.error
                    )
                    
                    # 将步骤添加到上下文
                    self.context_manager.add_step(context, step)
                    
                    # 如果结果有意义，则存储
                    if result.success and result.result is not None:
                        # 使用基于工具名称和步骤 ID 的键存储
                        result_key = f"{tool_name}_{step.step_id}"
                        self.context_manager.store_result(context, result_key, result.result)
                    
                    # 分析结果
                    self.logger.debug(f"Analyzing result from tool: {tool_name}")
                    analysis = self.reasoning_engine.analyze_result(result, context)
                    
                    # 评估当前状态
                    state_evaluation = self.reasoning_engine.evaluate_state(context)
                    
                    # 根据分析和状态做出决策
                    decision = self.reasoning_engine.make_decision(state_evaluation, context)
                    
                    self.logger.debug(f"Decision: {decision.action} - {decision.reason}")
                    
                    # 根据决策调整计划（如果需要）
                    self.reasoning_engine.adjust_plan(decision, context)
                    
                    # 如果决策是中止，则停止执行
                    if decision.action == "abort":
                        self.logger.warning(f"Aborting execution due to decision: {decision.reason}")
                        self.context_manager.update_state(context, type.__dict__['TaskState'].FAILED)
                        return
                    
                    # 工具执行之间的短暂暂停
                    time.sleep(0.1)
                
                # 更新上下文中的当前步骤
                context.current_step += 1
        
        except Exception as e:
            self.logger.error(f"Error executing plan: {e}")
            self.context_manager.update_state(context, type.__dict__['TaskState'].FAILED)
            raise
    
    def _check_dependencies_satisfied(self, subtask, context) -> bool:
        """
        检查子任务的依赖是否满足。
        
        Args:
            subtask: 要检查的子任务
            context: 执行上下文
            
        Returns:
            如果依赖满足则返回 True，否则返回 False
        """
        for dep_id in subtask.dependencies:
            # 查找具有此 ID 的子任务是否已完成
            dep_subtask = None
            for st in context.execution_plan.subtasks:
                if st.id == dep_id:
                    dep_subtask = st
                    break
            
            if dep_subtask is None:
                return False
            
            # 检查与依赖关联的工具是否已执行
            dep_tools_executed = any(
                step.tool_name in dep_subtask.tools and step.success 
                for step in context.history
            )
            
            if not dep_tools_executed:
                return False
        
        return True
    
    def _determine_tool_args(self, tool_name: str, context) -> dict:
        """
        根据上下文确定工具的参数。
        
        Args:
            tool_name: 要执行的工具名称
            context: 执行上下文
            
        Returns:
            工具的参数字典
        """
        # 这是一个简化的实现
        # 在实际实现中，这会更加复杂
        
        # 获取工具元数据以了解所需参数
        tool_info = self.tool_registry.get_tool(tool_name)
        if not tool_info:
            self.logger.warning(f"Tool not found in registry: {tool_name}")
            return {}
        
        metadata = tool_info['metadata']
        args = {}
        
        # 目前，对于大多数工具返回空参数，但处理一些常见情况
        if tool_name == "get_process_info":
            # 可能会从上下文中获取进程信息
            pass
        elif tool_name == "read_memory":
            # 可能会在上下文中查找地址
            # 目前，返回默认参数
            pass
        elif tool_name == "disassemble":
            # 可能会在上下文中查找地址
            pass
        elif tool_name == "ping":
            # 不需要参数
            pass
        else:
            # 对于其他工具，在中间结果中查找相关值
            for param in metadata.parameters:
                # 检查我们在上下文中是否有此参数的值
                if param.name in context.intermediate_results:
                    args[param.name] = context.intermediate_results[param.name]
        
        return args