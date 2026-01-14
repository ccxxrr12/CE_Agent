"""
Cheat Engine AI Agent 的提示词管理器。

该模块管理系统提示词，支持动态提示词生成和版本管理。
"""
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from ..utils.logger import get_logger


class PromptManager:
    """管理AI代理的提示词。"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词管理器。
        
        Args:
            prompts_dir: 存储提示词文件的目录路径
        """
        self.logger = get_logger(__name__)
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(__file__).parent.parent / "prompts"
        self.prompts: Dict[str, str] = {}
        self.prompt_templates: Dict[str, str] = {}
        
        self._load_system_prompt()
        self._load_prompt_templates()
    
    def _load_system_prompt(self):
        """加载系统提示词。"""
        system_prompt_path = self.prompts_dir / "SYSTEM_PROMPT.md"
        
        if system_prompt_path.exists():
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                self.prompts['system'] = f.read()
            self.logger.info(f"Loaded system prompt from {system_prompt_path}")
        else:
            self.prompts['system'] = self._get_default_system_prompt()
            self.logger.warning(f"System prompt file not found, using default")
    
    def _load_prompt_templates(self):
        """加载提示词模板。"""
        template_files = {
            'task_planning': 'TASK_PLANNING.md',
            'reasoning': 'REASONING.md',
            'tool_selection': 'TOOL_SELECTION.md',
            'result_analysis': 'RESULT_ANALYSIS.md'
        }
        
        for key, filename in template_files.items():
            template_path = self.prompts_dir / filename
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.prompt_templates[key] = f.read()
                self.logger.debug(f"Loaded template '{key}' from {template_path}")
            else:
                self.prompt_templates[key] = self._get_default_template(key)
                self.logger.debug(f"Using default template for '{key}'")
    
    def get_system_prompt(self) -> str:
        """
        获取系统提示词。
        
        Returns:
            系统提示词字符串
        """
        return self.prompts.get('system', self._get_default_system_prompt())
    
    def get_task_planning_prompt(self, request: str, available_tools: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成任务规划提示词。
        
        Args:
            request: 用户的请求
            available_tools: 可用工具列表
            context: 可选的上下文信息
            
        Returns:
            任务规划提示词
        """
        template = self.prompt_templates.get('task_planning', self._get_default_template('task_planning'))
        
        tools_info = "\n".join([f"- {tool}" for tool in available_tools])
        
        context_info = ""
        if context:
            context_info = "\n\nContext:\n" + json.dumps(context, indent=2, ensure_ascii=False)
        
        prompt = template.format(
            request=request,
            available_tools=tools_info,
            context=context_info
        )
        
        return prompt
    
    def get_reasoning_prompt(self, current_result: Dict[str, Any], context: Dict[str, Any], available_tools: List[str]) -> str:
        """
        生成推理提示词。
        
        Args:
            current_result: 当前工具执行结果
            context: 执行上下文
            available_tools: 可用工具列表
            
        Returns:
            推理提示词
        """
        template = self.prompt_templates.get('reasoning', self._get_default_template('reasoning'))
        
        tools_info = "\n".join([f"- {tool}" for tool in available_tools])
        
        prompt = template.format(
            current_result=json.dumps(current_result, indent=2, ensure_ascii=False),
            context=json.dumps(context, indent=2, ensure_ascii=False),
            available_tools=tools_info
        )
        
        return prompt
    
    def get_tool_selection_prompt(self, task_description: str, available_tools: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成工具选择提示词。
        
        Args:
            task_description: 任务描述
            available_tools: 可用工具列表（包含元数据）
            context: 可选的上下文信息
            
        Returns:
            工具选择提示词
        """
        template = self.prompt_templates.get('tool_selection', self._get_default_template('tool_selection'))
        
        tools_info = ""
        for tool in available_tools:
            tools_info += f"\nTool: {tool.get('name', 'unknown')}\n"
            tools_info += f"  Description: {tool.get('description', 'No description')}\n"
            tools_info += f"  Category: {tool.get('category', 'unknown')}\n"
            if 'parameters' in tool:
                params = tool['parameters']
                tools_info += f"  Parameters:\n"
                for param in params:
                    required = "required" if param.get('required', False) else "optional"
                    tools_info += f"    - {param.get('name', 'unknown')} ({param.get('type', 'any')}, {required})\n"
        
        context_info = ""
        if context:
            context_info = "\n\nContext:\n" + json.dumps(context, indent=2, ensure_ascii=False)
        
        prompt = template.format(
            task_description=task_description,
            available_tools=tools_info,
            context=context_info
        )
        
        return prompt
    
    def get_result_analysis_prompt(self, result: Dict[str, Any], tool_name: str, context: Dict[str, Any]) -> str:
        """
        生成结果分析提示词。
        
        Args:
            result: 工具执行结果
            tool_name: 工具名称
            context: 执行上下文
            
        Returns:
            结果分析提示词
        """
        template = self.prompt_templates.get('result_analysis', self._get_default_template('result_analysis'))
        
        prompt = template.format(
            tool_name=tool_name,
            result=json.dumps(result, indent=2, ensure_ascii=False),
            context=json.dumps(context, indent=2, ensure_ascii=False)
        )
        
        return prompt
    
    def format_chat_messages(self, system_prompt: str, user_prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        格式化聊天消息列表。
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            conversation_history: 可选的对话历史
            
        Returns:
            格式化的消息列表
        """
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def update_system_prompt(self, new_prompt: str):
        """
        更新系统提示词。
        
        Args:
            new_prompt: 新的系统提示词
        """
        self.prompts['system'] = new_prompt
        self.logger.info("System prompt updated")
    
    def save_system_prompt(self, filepath: Optional[str] = None):
        """
        保存系统提示词到文件。
        
        Args:
            filepath: 保存路径，默认为prompts_dir/SYSTEM_PROMPT.md
        """
        if filepath is None:
            filepath = self.prompts_dir / "SYSTEM_PROMPT.md"
        else:
            filepath = Path(filepath)
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.prompts['system'])
        
        self.logger.info(f"System prompt saved to {filepath}")
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词。"""
        return """You are an AI agent specialized in memory analysis and reverse engineering using Cheat Engine. Your role is to help users analyze memory, find functions, debug code, and understand program behavior.

Your capabilities include:
- Memory scanning and pattern matching
- Function analysis and disassembly
- Breakpoint debugging
- Data structure analysis
- Code generation and script creation

When analyzing results:
1. Be thorough and systematic
2. Provide clear explanations
3. Suggest next steps
4. Highlight important findings
5. Generate actionable code when appropriate

Always provide reasoning for your decisions and explain your thought process clearly."""
    
    def _get_default_template(self, template_type: str) -> str:
        """
        获取默认提示词模板。
        
        Args:
            template_type: 模板类型
            
        Returns:
            默认模板字符串
        """
        templates = {
            'task_planning': """Analyze the following user request and create a detailed execution plan.

User Request: {request}

Available Tools:
{available_tools}

{context}

Your task:
1. Identify the user's intent
2. Classify the task type
3. Break down the task into subtasks
4. Select appropriate tools for each subtask
5. Define dependencies between subtasks

Provide your response in JSON format:
{{
  "task_type": "TASK_TYPE",
  "subtasks": [
    {{
      "id": 1,
      "description": "Description of subtask",
      "tools": ["tool1", "tool2"],
      "expected_output": "Expected result",
      "dependencies": []
    }}
  ]
}}""",
            
            'reasoning': """Analyze the current execution result and determine the next action.

Current Result:
{current_result}

Execution Context:
{context}

Available Tools:
{available_tools}

Your task:
1. Analyze the result - was it successful?
2. What information did we learn?
3. What should we do next?
4. Do we need to adjust our approach?

Provide your response in JSON format:
{{
  "analysis": "Brief analysis of the result",
  "findings": ["Finding 1", "Finding 2"],
  "next_action": "continue|adjust|abort|finalize",
  "next_tool": "tool_name",
  "tool_args": {{}},
  "reasoning": "Explanation of your decision"
}}""",
            
            'tool_selection': """Select the most appropriate tool for the given task.

Task: {task_description}

Available Tools:
{available_tools}

{context}

Your task:
1. Analyze the task requirements
2. Select the best tool(s) for this task
3. Determine the required parameters
4. Provide reasoning for your selection

Provide your response in JSON format:
{{
  "selected_tool": "tool_name",
  "tool_args": {{
    "param1": "value1",
    "param2": "value2"
  }},
  "reasoning": "Why this tool is appropriate",
  "confidence": 0.9
}}""",
            
            'result_analysis': """Analyze the tool execution result.

Tool: {tool_name}

Result:
{result}

Context:
{context}

Your task:
1. Was the tool execution successful?
2. What information did we obtain?
3. Are there any errors or issues?
4. What should we do next?

Provide your response in JSON format:
{{
  "success": true|false,
  "findings": ["Finding 1", "Finding 2"],
  "errors": ["Error 1"],
  "next_steps": ["Step 1", "Step 2"],
  "insights": ["Insight 1"]
}}"""
        }
        
        return templates.get(template_type, "No template available for this type")
    
    def add_custom_template(self, name: str, template: str):
        """
        添加自定义提示词模板。
        
        Args:
            name: 模板名称
            template: 模板内容
        """
        self.prompt_templates[name] = template
        self.logger.info(f"Added custom template: {name}")
    
    def get_template(self, name: str) -> Optional[str]:
        """
        获取提示词模板。
        
        Args:
            name: 模板名称
            
        Returns:
            模板内容，如果不存在则返回None
        """
        return self.prompt_templates.get(name)
