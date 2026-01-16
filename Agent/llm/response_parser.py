"""
Cheat Engine AI Agent 的LLM响应解析器。

该模块解析LLM响应，提取工具调用、决策和结构化数据。
"""
# 优先使用orjson进行更快的JSON解析
try:
    import orjson as json
except ImportError:
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
            # 如果传入的是列表，尝试转换为字符串
            if isinstance(response_text, list):
                self.logger.warning(f"parse_task_plan received list instead of string, converting...")
                if len(response_text) > 0 and isinstance(response_text[0], dict):
                    response_text = str(response_text[0])
                else:
                    response_text = str(response_text)
            
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
            # 添加调试日志
            self.logger.debug(f"parse_reasoning received type: {type(response_text)}")
            self.logger.debug(f"parse_reasoning received content: {response_text[:500] if len(response_text) > 500 else response_text}")
            
            # 如果传入的是列表，尝试转换为字符串
            if isinstance(response_text, list):
                self.logger.warning(f"parse_reasoning received list instead of string, converting...")
                # 如果列表中有字典，尝试提取文本内容
                if len(response_text) > 0 and isinstance(response_text[0], dict):
                    response_text = str(response_text[0])
                else:
                    response_text = str(response_text)
            
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
            # 如果传入的是列表，尝试转换为字符串
            if isinstance(response_text, list):
                self.logger.warning(f"parse_result_analysis received list instead of string, converting...")
                if len(response_text) > 0 and isinstance(response_text[0], dict):
                    response_text = str(response_text[0])
                else:
                    response_text = str(response_text)
            
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
            # 如果传入的是列表，尝试转换为字符串
            if isinstance(response_text, list):
                self.logger.warning(f"parse_decision received list instead of string, converting...")
                if len(response_text) > 0 and isinstance(response_text[0], dict):
                    response_text = str(response_text[0])
                else:
                    response_text = str(response_text)
            
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
        从文本中提取JSON对象（增强版）。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象，如果失败则返回None
        """
        # 1. 尝试标准JSON提取
        result = self._try_standard_json_extraction(text)
        if result and isinstance(result, dict):
            return result
        
        # 2. 尝试修复常见的JSON错误
        result = self._try_json_repair(text)
        if result and isinstance(result, dict):
            return result
        
        # 3. 尝试从自然语言中提取结构化信息
        result = self._extract_from_natural_language(text)
        if result and isinstance(result, dict):
            return result
        
        # 4. 尝试部分JSON提取
        result = self._try_partial_json_extraction(text)
        if result and isinstance(result, dict):
            return result
        
        return None
    
    def _try_standard_json_extraction(self, text: str) -> Optional[Dict[str, Any]]:
        """
        尝试标准JSON提取。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象，如果失败则返回None
        """
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```JSON\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
            r'\[[\s\S]*\]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    json_str = match.strip()
                    # 清理常见的格式问题
                    json_str = self._clean_json_string(json_str)
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    self.logger.debug(f"JSON parse error: {e}")
                    continue
        
        return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        清理JSON字符串中的常见问题。
        
        Args:
            json_str: JSON字符串
            
        Returns:
            清理后的JSON字符串
        """
        # 移除 markdown 代码块标记
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```JSON\s*', '', json_str)
        json_str = re.sub(r'```\s*', '', json_str)
        
        # 移除注释
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 修复尾随逗号
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        # 修复单引号
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        
        # 移除控制字符
        json_str = ''.join(char for char in json_str if ord(char) >= 32 or char == '\n')
        
        return json_str
    
    def _try_json_repair(self, text: str) -> Optional[Dict[str, Any]]:
        """
        尝试修复JSON错误。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            解析后的JSON对象，如果失败则返回None
        """
        # 查找可能的JSON片段
        json_fragments = self._find_json_fragments(text)
        
        for fragment in json_fragments:
            # 尝试修复括号不匹配
            repaired = self._fix_brackets(fragment)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    continue
            
            # 尝试修复引号不匹配
            repaired = self._fix_quotes(fragment)
            if repaired:
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _find_json_fragments(self, text: str) -> List[str]:
        """
        查找文本中的JSON片段。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            JSON片段列表
        """
        fragments = []
        
        # 查找以 { 或 [ 开头的片段
        starts = []
        for i, char in enumerate(text):
            if char in ['{', '[']:
                starts.append(i)
        
        for start in starts:
            # 尝试找到匹配的结束位置
            stack = []
            for i in range(start, min(start + 2000, len(text))):  # 限制长度
                char = text[i]
                if char in ['{', '[']:
                    stack.append(char)
                elif char == '}':
                    if stack and stack[-1] == '{':
                        stack.pop()
                        if not stack:
                            fragments.append(text[start:i+1])
                            break
                elif char == ']':
                    if stack and stack[-1] == '[':
                        stack.pop()
                        if not stack:
                            fragments.append(text[start:i+1])
                            break
        
        return fragments
    
    def _fix_brackets(self, json_str: str) -> Optional[str]:
        """
        修复括号不匹配。
        
        Args:
            json_str: JSON字符串
            
        Returns:
            修复后的JSON字符串，如果无法修复则返回None
        """
        stack = []
        result = list(json_str)
        
        for i, char in enumerate(result):
            if char in ['{', '[']:
                stack.append((i, char))
            elif char == '}':
                if stack and stack[-1][1] == '{':
                    stack.pop()
                else:
                    # 缺少开括号，插入
                    result.insert(i, '{')
                    stack.append((i, '{'))
            elif char == ']':
                if stack and stack[-1][1] == '[':
                    stack.pop()
                else:
                    # 缺少开括号，插入
                    result.insert(i, '[')
                    stack.append((i, '['))
        
        # 添加缺失的闭括号
        for pos, bracket in reversed(stack):
            if bracket == '{':
                result.append('}')
            elif bracket == '[':
                result.append(']')
        
        return ''.join(result)
    
    def _fix_quotes(self, json_str: str) -> Optional[str]:
        """
        修复引号不匹配。
        
        Args:
            json_str: JSON字符串
            
        Returns:
            修复后的JSON字符串，如果无法修复则返回None
        """
        result = []
        in_string = False
        escape_next = False
        quote_char = None
        
        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char in ['"', "'"]:
                if not in_string:
                    # 开始字符串
                    in_string = True
                    quote_char = char
                    result.append('"')  # 统一使用双引号
                elif char == quote_char:
                    # 结束字符串
                    in_string = False
                    quote_char = None
                    result.append('"')
                else:
                    # 引号类型不匹配，转义
                    result.append(f'\\{char}')
            else:
                result.append(char)
        
        # 如果字符串未关闭，关闭它
        if in_string:
            result.append('"')
        
        return ''.join(result)
    
    def _extract_from_natural_language(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从自然语言中提取结构化信息。
        
        Args:
            text: 包含自然语言的文本
            
        Returns:
            提取的结构化信息，如果无法提取则返回None
        """
        result = {}
        
        # 提取键值对
        patterns = [
            r'(\w+)\s*[:=]\s*["\']?([^"\']+)["\']?',
            r'(\w+)\s*is\s+["\']?([^"\']+)["\']?',
            r'(\w+)\s*=\s*"([^"]+)"',
            r'(\w+)\s*=\s*\'([^\']+)\'',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for key, value in matches:
                # 尝试类型转换
                if value.isdigit():
                    result[key] = int(value)
                elif value.replace('.', '', 1).isdigit():
                    result[key] = float(value)
                elif value.lower() in ['true', 'false']:
                    result[key] = value.lower() == 'true'
                else:
                    result[key] = value
        
        # 提取列表
        list_pattern = r'(\w+)\s*[:=]\s*\[([^\]]+)\]'
        matches = re.findall(list_pattern, text, re.IGNORECASE)
        for key, values_str in matches:
            values = [v.strip() for v in values_str.split(',')]
            result[key] = values
        
        return result if result else None
    
    def _try_partial_json_extraction(self, text: str) -> Optional[Dict[str, Any]]:
        """
        尝试部分JSON提取。
        
        Args:
            text: 包含JSON的文本
            
        Returns:
            部分提取的JSON对象，如果无法提取则返回None
        """
        # 查找所有键值对
        kv_pattern = r'"([^"]+)"\s*:\s*([^,}\]]+)'
        matches = re.findall(kv_pattern, text)
        
        if matches:
            result = {}
            for key, value in matches:
                # 尝试解析值
                value = value.strip()
                
                # 尝试解析为不同类型
                if value.startswith('"') and value.endswith('"'):
                    result[key] = value[1:-1]
                elif value.isdigit():
                    result[key] = int(value)
                elif value.lower() == 'true':
                    result[key] = True
                elif value.lower() == 'false':
                    result[key] = False
                elif value.lower() == 'null':
                    result[key] = None
                else:
                    result[key] = value
            
            return result if result else None
        
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
