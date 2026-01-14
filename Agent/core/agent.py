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
from typing import Optional, Callable
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
    
    def __init__(self, config: Config, tool_registry: ToolRegistry, mcp_client: MCPClient, ollama_client: OllamaClient, use_llm: bool = True, use_simple_prompt: bool = False, use_minimal_prompt: bool = False, use_json_prompt: bool = False, cli_callback: Optional[Callable] = None):
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
            use_json_prompt: 是否使用JSON格式提示词
            cli_callback: 可选的CLI回调函数，用于实时日志输出
        """
        self.config = config
        self.tool_registry = tool_registry
        self.mcp_client = mcp_client
        self.ollama_client = ollama_client
        self.logger = get_logger(__name__)
        self.cli_callback = cli_callback
        
        # 初始化核心组件
        self.task_planner = TaskPlanner(tool_registry, ollama_client, use_llm=use_llm, use_simple_prompt=use_simple_prompt, use_minimal_prompt=use_minimal_prompt, use_json_prompt=use_json_prompt, cli_callback=self._log_callback)
        self.reasoning_engine = ReasoningEngine(ollama_client, use_llm=use_llm, use_simple_prompt=use_simple_prompt, use_minimal_prompt=use_minimal_prompt, use_json_prompt=use_json_prompt, cli_callback=self._log_callback)
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
    
    def _log_callback(self, log_type: str, message: str, **kwargs):
        """
        实时日志回调函数。
        
        Args:
            log_type: 日志类型 (step, tool_call, llm_call, analysis)
            message: 日志消息
            **kwargs: 额外的日志参数
        """
        if self.cli_callback:
            try:
                self.cli_callback(log_type, message, **kwargs)
            except Exception as e:
                self.logger.error(f"CLI callback error: {e}")
    
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
            self._log_callback('step', f'开始执行请求: {request}')
            self.logger.info(f"开始执行请求: {request}")
            
            # 更新代理状态
            self.status = AgentStatus.RUNNING
            
            # 规划任务
            self._log_callback('step', '正在规划任务...')
            self.logger.debug("正在规划任务...")
            execution_plan = self.task_planner.plan(request)
            
            # 创建执行上下文
            self._log_callback('step', '正在创建执行上下文...')
            self.logger.debug("正在创建执行上下文...")
            context = self.context_manager.create_context(request, execution_plan)
            
            # 执行计划
            self._log_callback('step', '正在执行计划...')
            self.logger.debug("正在执行计划...")
            self._execute_plan(context)
            
            # 生成最终报告
            self._log_callback('step', '正在生成最终报告...')
            self.logger.debug("正在生成最终报告...")
            report = self.result_synthesizer.synthesize(context)
            
            # 更新执行时间
            report.execution_time = time.time() - start_time
            
            self._log_callback('success', f'任务 {context.task_id} 执行成功')
            self.logger.info(f"任务 {context.task_id} 执行成功")
            
            return report
        except Exception as e:
            self._log_callback('error', f'执行过程中出错: {str(e)}')
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
        根据上下文确定工具的参数（改进版 - 基于规则的智能参数推断）。
        
        Args:
            tool_name: 要执行的工具名称
            context: 执行上下文
            
        Returns:
            工具的参数字典
        """
        import re
        
        tool_info = self.tool_registry.get_tool(tool_name)
        if not tool_info:
            self.logger.warning(f"Tool not found in registry: {tool_name}")
            return {}
        
        metadata = tool_info['metadata']
        args = {}
        
        # 1. 从工具元数据中获取默认值
        for param in metadata.parameters:
            if not param.required and param.default is not None:
                args[param.name] = param.default
        
        # 2. 从用户请求中提取参数
        user_args = self._extract_args_from_request(tool_name, context.user_request)
        args.update(user_args)
        
        # 3. 从中间结果中查找参数
        for param in metadata.parameters:
            if param.name not in args:
                value = self._find_value_in_context(param.name, context)
                if value is not None:
                    args[param.name] = value
        
        # 4. 从执行历史中推断参数
        for param in metadata.parameters:
            if param.name not in args:
                value = self._infer_value_from_history(param.name, param.type, context)
                if value is not None:
                    args[param.name] = value
        
        # 5. 特定工具的智能处理
        args = self._apply_tool_specific_logic(tool_name, args, context)
        
        # 6. 参数验证
        if not self._validate_tool_args(tool_name, args):
            self.logger.warning(f"Invalid arguments for tool {tool_name}: {args}")
            return {}
        
        return args
    
    def _extract_args_from_request(self, tool_name: str, request: str) -> dict:
        """
        从用户请求中提取工具参数。
        
        Args:
            tool_name: 工具名称
            request: 用户请求
            
        Returns:
            提取的参数字典
        """
        import re
        args = {}
        request_lower = request.lower()
        
        # 常见参数模式
        patterns = {
            'address': r'(?:at|address|addr|0x)?\s*([0-9a-fA-F]{4,16})',
            'value': r'(?:value|scan|search|find)\s*[:\s]*([^\s,]+)',
            'size': r'(?:size|length)\s*[:\s]*(\d+)',
            'count': r'(?:count|number)\s*[:\s]*(\d+)',
            'pattern': r'(?:pattern|aob|signature)\s*[:\s]*([0-9a-fA-F\s\?]+)',
            'symbol': r'(?:symbol|function)\s*[:\s]*([a-zA-Z0-9_.]+)',
            'string': r'(?:string|text)\s*[:\s]*["\']([^"\']+)["\']',
            'search_string': r'(?:search.*?string|find.*?text)\s*[:\s]*["\']([^"\']+)["\']',
            'max_results': r'(?:max|limit)\s*[:\s]*(\d+)',
            'timeout': r'(?:timeout|wait)\s*[:\s]*(\d+)',
            'condition': r'(?:condition|when)\s*[:\s]*["\']([^"\']+)["\']',
            'assembly': r'(?:assembly|code)\s*[:\s]*["\']([^"\']+)["\']',
            'offsets': r'(?:offset|off)\s*[:\s]*\[([^\]]+)\]',
            'virtual_address': r'(?:virtual|vaddr)\s*[:\s]*([0-9a-fA-F]{4,16})',
            'base_address': r'(?:base|baddr)\s*[:\s]*([0-9a-fA-F]{4,16})',
        }
        
        for param_name, pattern in patterns.items():
            match = re.search(pattern, request_lower)
            if match:
                value = match.group(1)
                # 类型转换
                if param_name in ['address', 'size', 'count', 'max_results', 'timeout', 'virtual_address', 'base_address']:
                    try:
                        if value.startswith('0x') or len(value) > 8:
                            args[param_name] = int(value, 16)
                        else:
                            args[param_name] = int(value)
                    except ValueError:
                        continue
                elif param_name == 'offsets':
                    # 解析偏移量列表
                    try:
                        offsets = [int(x.strip(), 16 if x.strip().startswith('0x') else 10) 
                                  for x in value.split(',')]
                        args[param_name] = offsets
                    except ValueError:
                        continue
                else:
                    args[param_name] = value
        
        return args
    
    def _find_value_in_context(self, param_name: str, context) -> Any:
        """
        在上下文中查找参数值。
        
        Args:
            param_name: 参数名称
            context: 执行上下文
            
        Returns:
            找到的值，如果未找到则返回None
        """
        # 1. 直接在中间结果中查找
        if param_name in context.intermediate_results:
            return context.intermediate_results[param_name]
        
        # 2. 在中间结果的嵌套结构中查找
        for key, value in context.intermediate_results.items():
            if isinstance(value, dict):
                if param_name in value:
                    return value[param_name]
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and param_name in value[0]:
                    return value[0][param_name]
        
        # 3. 使用模糊匹配
        similar_keys = [k for k in context.intermediate_results.keys() 
                       if param_name.lower() in k.lower()]
        if similar_keys:
            return context.intermediate_results[similar_keys[0]]
        
        return None
    
    def _infer_value_from_history(self, param_name: str, param_type: str, context) -> Any:
        """
        从执行历史中推断参数值。
        
        Args:
            param_name: 参数名称
            param_type: 参数类型
            context: 执行上下文
            
        Returns:
            推断的值，如果无法推断则返回None
        """
        # 反向遍历历史，查找最近的匹配值
        for step in reversed(context.history):
            if not step.success or not step.result:
                continue
            
            result = step.result
            if isinstance(result, dict):
                # 直接匹配
                if param_name in result:
                    return result[param_name]
                
                # 类型匹配
                if param_type == 'integer':
                    for key, value in result.items():
                        if isinstance(value, int):
                            return value
                elif param_type == 'string':
                    for key, value in result.items():
                        if isinstance(value, str) and len(value) < 200:
                            return value
                elif param_type == 'list':
                    for key, value in result.items():
                        if isinstance(value, list):
                            return value
            
            # 特定参数的推断逻辑
            if param_name == 'address':
                # 从任何包含地址的结果中提取
                if isinstance(result, dict) and 'address' in result:
                    return result['address']
                elif isinstance(result, dict) and 'addresses' in result:
                    if isinstance(result['addresses'], list) and len(result['addresses']) > 0:
                        return result['addresses'][0]
            
            elif param_name == 'value':
                # 从扫描结果中提取
                if isinstance(result, dict) and 'value' in result:
                    return result['value']
            
            elif param_name == 'symbol':
                # 从符号相关结果中提取
                if isinstance(result, dict) and 'symbol' in result:
                    return result['symbol']
        
        return None
    
    def _apply_tool_specific_logic(self, tool_name: str, args: dict, context) -> dict:
        """
        应用特定工具的智能逻辑。
        
        Args:
            tool_name: 工具名称
            args: 当前参数字典
            context: 执行上下文
            
        Returns:
            更新后的参数字典
        """
        import re
        
        # scan_all 工具
        if tool_name == "scan_all":
            # 如果没有提供值，尝试从用户请求中提取
            if 'value' not in args:
                request_lower = context.user_request.lower()
                # 提取数字值
                number_match = re.search(r'\b(\d+)\b', request_lower)
                if number_match:
                    args['value'] = number_match.group(1)
            
            # 设置默认扫描类型
            if 'scan_type' not in args:
                args['scan_type'] = 'Auto Assembler'
        
        # disassemble 工具
        elif tool_name == "disassemble":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认指令数量
            if 'count' not in args:
                args['count'] = 10
        
        # read_memory 工具
        elif tool_name == "read_memory":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认读取大小
            if 'size' not in args:
                args['size'] = 16
        
        # aob_scan 工具
        elif tool_name == "aob_scan":
            # 如果没有模式，尝试从用户请求中提取
            if 'pattern' not in args:
                request_lower = context.user_request.lower()
                # 提取十六进制模式
                hex_match = re.search(r'([0-9a-fA-F\s\?]{10,})', request_lower)
                if hex_match:
                    args['pattern'] = hex_match.group(1).strip()
            
            # 设置默认选项
            if 'writable' not in args:
                args['writable'] = False
            if 'executable' not in args:
                args['executable'] = True
        
        # set_breakpoint 工具
        elif tool_name == "set_breakpoint":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
        
        # set_data_breakpoint 工具
        elif tool_name == "set_data_breakpoint":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认大小
            if 'size' not in args:
                args['size'] = 4
            # 设置默认访问类型
            if 'access_type' not in args:
                args['access_type'] = 'rw'
        
        # analyze_function 工具
        elif tool_name == "analyze_function":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
        
        # find_references 工具
        elif tool_name == "find_references":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
        
        # generate_signature 工具
        elif tool_name == "generate_signature":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认大小
            if 'size' not in args:
                args['size'] = 256
        
        # get_scan_results 工具
        elif tool_name == "get_scan_results":
            # 设置默认最大结果数
            if 'max_results' not in args:
                args['max_results'] = 100
        
        # get_breakpoint_hits 工具
        elif tool_name == "get_breakpoint_hits":
            # 设置默认超时
            if 'timeout' not in args:
                args['timeout'] = 5000
        
        # read_string 工具
        elif tool_name == "read_string":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认长度
            if 'length' not in args:
                args['length'] = 256
        
        # search_string 工具
        elif tool_name == "search_string":
            # 如果没有搜索字符串，尝试从用户请求中提取
            if 'search_string' not in args:
                request_lower = context.user_request.lower()
                # 提取引号中的文本
                quote_match = re.search(r'["\']([^"\']+)["\']', request_lower)
                if quote_match:
                    args['search_string'] = quote_match.group(1)
            
            # 设置默认区分大小写
            if 'case_sensitive' not in args:
                args['case_sensitive'] = True
        
        # evaluate_lua 工具
        elif tool_name == "evaluate_lua":
            # 如果没有脚本，尝试从用户请求中提取
            if 'script' not in args:
                # 提取代码块中的脚本
                code_match = re.search(r'```lua\s*([\s\S]*?)\s*```', context.user_request)
                if code_match:
                    args['script'] = code_match.group(1).strip()
                else:
                    # 提取引号中的脚本
                    quote_match = re.search(r'["\']([^"\']+)["\']', context.user_request)
                    if quote_match:
                        args['script'] = quote_match.group(1)
        
        # auto_assemble 工具
        elif tool_name == "auto_assemble":
            # 如果没有汇编代码，尝试从用户请求中提取
            if 'assembly' not in args:
                # 提取代码块中的汇编
                code_match = re.search(r'```(?:asm|assembly)?\s*([\s\S]*?)\s*```', context.user_request)
                if code_match:
                    args['assembly'] = code_match.group(1).strip()
            
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
        
        # read_pointer_chain 工具
        elif tool_name == "read_pointer_chain":
            # 如果没有基地址，尝试从上下文中查找
            if 'base_address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['base_address'] = step.result['address']
                            break
            
            # 如果没有偏移量，尝试从用户请求中提取
            if 'offsets' not in args:
                request_lower = context.user_request.lower()
                # 提取偏移量列表
                offset_match = re.search(r'(?:offset|off)\s*[:\s]*\[([^\]]+)\]', request_lower)
                if offset_match:
                    try:
                        offsets = [int(x.strip(), 16 if x.strip().startswith('0x') else 10) 
                                  for x in offset_match.group(1).split(',')]
                        args['offsets'] = offsets
                    except ValueError:
                        pass
        
        # checksum_memory 工具
        elif tool_name == "checksum_memory":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认大小
            if 'size' not in args:
                args['size'] = 4096
        
        # start_dbvm_watch 工具
        elif tool_name == "start_dbvm_watch":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
            
            # 设置默认大小
            if 'size' not in args:
                args['size'] = 256
            # 设置默认访问类型
            if 'access_type' not in args:
                args['access_type'] = 'rw'
        
        # stop_dbvm_watch 工具
        elif tool_name == "stop_dbvm_watch":
            # 如果没有地址，尝试从上下文中查找
            if 'address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['address'] = step.result['address']
                            break
        
        # get_physical_address 工具
        elif tool_name == "get_physical_address":
            # 如果没有虚拟地址，尝试从上下文中查找
            if 'virtual_address' not in args:
                for step in reversed(context.history):
                    if step.success and step.result:
                        if isinstance(step.result, dict) and 'address' in step.result:
                            args['virtual_address'] = step.result['address']
                            break
        
        return args
    
    def _validate_tool_args(self, tool_name: str, args: dict) -> bool:
        """
        验证工具参数。
        
        Args:
            tool_name: 工具名称
            args: 参数字典
            
        Returns:
            如果参数有效返回True，否则返回False
        """
        tool_info = self.tool_registry.get_tool(tool_name)
        if not tool_info:
            return False
        
        metadata = tool_info['metadata']
        
        # 检查必需参数
        for param in metadata.parameters:
            if param.required and param.name not in args:
                self.logger.warning(f"Missing required parameter: {param.name}")
                return False
        
        # 检查参数类型
        for param in metadata.parameters:
            if param.name in args:
                value = args[param.name]
                expected_type = param.type
                
                # 简单类型检查
                if expected_type == 'integer' and not isinstance(value, int):
                    try:
                        args[param.name] = int(value)
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid type for {param.name}: expected integer, got {type(value)}")
                        return False
                elif expected_type == 'string' and not isinstance(value, str):
                    args[param.name] = str(value)
                elif expected_type == 'list' and not isinstance(value, list):
                    self.logger.warning(f"Invalid type for {param.name}: expected list, got {type(value)}")
                    return False
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    args[param.name] = bool(value)
        
        return True