"""
Cheat Engine AI Agent 的LLM响应解析器。

该模块解析LLM响应，提取工具调用、决策和结构化数据。
"""
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from ..utils.logger import get_logger
from ..models.base import ToolCall


class ResponseParser:
    """解析LLM响应的解析器。"""
    
    def __init__(self):
        """初始化响应解析器。"""
        self.logger = get_logger(__name__)
    
    def parse_tool_call(self, response_text: str) -> Optional[ToolCall]:
        """
        从LLM响应中提取工具调用。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            ToolCall对象，如果未找到则返回None
        """
        try:
            json_obj = self._extract_json(response_text)
            if json_obj is None:
                return None
            
            tool_name = json_obj.get('tool') or json_obj.get('selected_tool') or json_obj.get('function')
            if not tool_name:
                return None
            
            tool_args = json_obj.get('tool_args') or json_obj.get('arguments') or json_obj.get('parameters') or {}
            
            return ToolCall(
                name=tool_name,
                arguments=tool_args
            )
        except Exception as e:
            self.logger.error(f"Error parsing tool call: {e}")
            return None
    
    def parse_task_plan(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取任务计划。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            任务计划字典，如果解析失败则返回None
        """
        try:
            json_obj = self._extract_json(response_text)
            if json_obj is None:
                return None
            
            task_plan = {
                'task_type': json_obj.get('task_type', 'COMPREHENSIVE_ANALYSIS'),
                'subtasks': json_obj.get('subtasks', [])
            }
            
            return task_plan
        except Exception as e:
            self.logger.error(f"Error parsing task plan: {e}")
            return None
    
    def parse_reasoning(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取推理结果。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            推理结果字典，如果解析失败则返回None
        """
        try:
            json_obj = self._extract_json(response_text)
            if json_obj is None:
                return None
            
            reasoning = {
                'analysis': json_obj.get('analysis', ''),
                'findings': json_obj.get('findings', []),
                'next_action': json_obj.get('next_action', 'continue'),
                'next_tool': json_obj.get('next_tool'),
                'tool_args': json_obj.get('tool_args', {}),
                'reasoning': json_obj.get('reasoning', ''),
                'confidence': json_obj.get('confidence', 0.8)
            }
            
            return reasoning
        except Exception as e:
            self.logger.error(f"Error parsing reasoning: {e}")
            return None
    
    def parse_result_analysis(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取结果分析。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            结果分析字典，如果解析失败则返回None
        """
        try:
            json_obj = self._extract_json(response_text)
            if json_obj is None:
                return None
            
            analysis = {
                'success': json_obj.get('success', True),
                'findings': json_obj.get('findings', []),
                'errors': json_obj.get('errors', []),
                'next_steps': json_obj.get('next_steps', []),
                'insights': json_obj.get('insights', [])
            }
            
            return analysis
        except Exception as e:
            self.logger.error(f"Error parsing result analysis: {e}")
            return None
    
    def parse_decision(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取决策。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            决策字典，如果解析失败则返回None
        """
        try:
            json_obj = self._extract_json(response_text)
            if json_obj is None:
                return None
            
            decision = {
                'action': json_obj.get('action', 'continue'),
                'reason': json_obj.get('reason', ''),
                'confidence': json_obj.get('confidence', 0.8),
                'next_steps': json_obj.get('next_steps', [])
            }
            
            return decision
        except Exception as e:
            self.logger.error(f"Error parsing decision: {e}")
            return None
    
    def parse_code_generation(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        从LLM响应中提取生成的代码。
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            包含代码的字典，如果解析失败则返回None
        """
        try:
            code_blocks = self._extract_code_blocks(response_text)
            
            if not code_blocks:
                return None
            
            return {
                'code': code_blocks[0]['code'],
                'language': code_blocks[0]['language'],
                'all_blocks': code_blocks
            }
        except Exception as e:
            self.logger.error(f"Error parsing code generation: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取JSON对象。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象，如果失败则返回None
        """
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    json_str = match.strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        从文本中提取代码块。
        
        Args:
            text: 包含代码块的文本
            
        Returns:
            代码块列表，每个包含'code'和'language'
        """
        pattern = r'```(\w*)\s*([\s\S]*?)\s*```'
        matches = re.findall(pattern, text)
        
        code_blocks = []
        for language, code in matches:
            code_blocks.append({
                'language': language if language else 'text',
                'code': code.strip()
            })
        
        return code_blocks
    
    def extract_tool_calls_from_text(self, text: str) -> List[ToolCall]:
        """
        从文本中提取多个工具调用。
        
        Args:
            text: 包含工具调用的文本
            
        Returns:
            ToolCall对象列表
        """
        tool_calls = []
        
        patterns = [
            r'(?:tool|function|call):\s*["\']?(\w+)["\']?',
            r'(?:use|execute|run):\s*(\w+)\(',
            r'(\w+)\('
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                tool_name = match.group(1)
                if tool_name and tool_name.lower() not in ['if', 'for', 'while', 'def', 'class', 'return']:
                    tool_calls.append(ToolCall(name=tool_name, arguments={}))
        
        return tool_calls
    
    def parse_structured_response(self, response_text: str, expected_keys: List[str]) -> Optional[Dict[str, Any]]:
        """
        解析结构化响应，验证是否包含预期的键。
        
        Args:
            response_text: LLM响应文本
            expected_keys: 期望的键列表
            
        Returns:
            解析后的字典，如果缺少必需键则返回None
        """
        json_obj = self._extract_json(response_text)
        if json_obj is None:
            return None
        
        missing_keys = [key for key in expected_keys if key not in json_obj]
        if missing_keys:
            self.logger.warning(f"Missing expected keys in response: {missing_keys}")
            return None
        
        return json_obj
    
    def extract_addresses(self, text: str) -> List[str]:
        """
        从文本中提取内存地址。
        
        Args:
            text: 包含地址的文本
            
        Returns:
            地址列表
        """
        patterns = [
            r'0x[0-9a-fA-F]+',
            r'\$[0-9a-fA-F]+',
            r'[0-9a-fA-F]{8,16}'
        ]
        
        addresses = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            addresses.extend(matches)
        
        return list(set(addresses))
    
    def extract_signatures(self, text: str) -> List[str]:
        """
        从文本中提取AOB签名。
        
        Args:
            text: 包含签名的文本
            
        Returns:
            签名列表
        """
        patterns = [
            r'[0-9a-fA-F\s\?]{10,}',
            r'[0-9a-fA-F]{2}(\s+[0-9a-fA-F]{2}){4,}'
        ]
        
        signatures = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                sig = match.strip()
                if len(sig) >= 10:
                    signatures.append(sig)
        
        return list(set(signatures))
    
    def validate_response(self, response_text: str, response_type: str) -> Tuple[bool, Optional[str]]:
        """
        验证LLM响应是否符合预期格式。
        
        Args:
            response_text: LLM响应文本
            response_type: 响应类型（tool_call, task_plan, reasoning等）
            
        Returns:
            (是否有效, 错误消息)元组
        """
        validators = {
            'tool_call': self._validate_tool_call,
            'task_plan': self._validate_task_plan,
            'reasoning': self._validate_reasoning,
            'result_analysis': self._validate_result_analysis,
            'decision': self._validate_decision
        }
        
        validator = validators.get(response_type)
        if validator:
            return validator(response_text)
        
        return True, None
    
    def _validate_tool_call(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """验证工具调用响应。"""
        tool_call = self.parse_tool_call(response_text)
        if tool_call is None:
            return False, "Could not parse tool call from response"
        return True, None
    
    def _validate_task_plan(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """验证任务计划响应。"""
        plan = self.parse_task_plan(response_text)
        if plan is None:
            return False, "Could not parse task plan from response"
        if not plan.get('subtasks'):
            return False, "Task plan must contain subtasks"
        return True, None
    
    def _validate_reasoning(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """验证推理响应。"""
        reasoning = self.parse_reasoning(response_text)
        if reasoning is None:
            return False, "Could not parse reasoning from response"
        return True, None
    
    def _validate_result_analysis(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """验证结果分析响应。"""
        analysis = self.parse_result_analysis(response_text)
        if analysis is None:
            return False, "Could not parse result analysis from response"
        return True, None
    
    def _validate_decision(self, response_text: str) -> Tuple[bool, Optional[str]]:
        """验证决策响应。"""
        decision = self.parse_decision(response_text)
        if decision is None:
            return False, "Could not parse decision from response"
        valid_actions = ['continue', 'adjust', 'abort', 'finalize', 'recover']
        if decision.get('action') not in valid_actions:
            return False, f"Invalid action: {decision.get('action')}"
        return True, None
    
    def extract_text_before_json(self, text: str) -> str:
        """
        提取JSON之前的文本（通常包含解释）。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            JSON之前的文本
        """
        patterns = [
            r'([\s\S]*?)```json',
            r'([\s\S]*?)```',
            r'([\s\S]*?)\{'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return text
    
    def extract_text_after_json(self, text: str) -> str:
        """
        提取JSON之后的文本（通常包含额外说明）。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            JSON之后的文本
        """
        patterns = [
            r'```json[\s\S]*?```([\s\S]*)',
            r'```[\s\S]*?```([\s\S]*)',
            r'\{[\s\S]*\}([\s\S]*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return ""
