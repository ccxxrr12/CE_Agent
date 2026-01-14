# 工具参数确定与LLM响应解析改进方案

## 问题一：工具参数确定

### 当前实现分析

在 `Agent/core/agent.py` 的 `_determine_tool_args` 方法中，当前的实现非常简化：

```python
def _determine_tool_args(self, tool_name: str, context) -> dict:
    """根据上下文确定工具的参数。"""
    tool_info = self.tool_registry.get_tool(tool_name)
    if not tool_info:
        self.logger.warning(f"Tool not found in registry: {tool_name}")
        return {}
    
    metadata = tool_info['metadata']
    args = {}
    
    # 目前，对于大多数工具返回空参数，但处理一些常见情况
    if tool_name == "get_process_info":
        pass
    elif tool_name == "read_memory":
        pass
    elif tool_name == "disassemble":
        pass
    elif tool_name == "ping":
        pass
    else:
        # 对于其他工具，在中间结果中查找相关值
        for param in metadata.parameters:
            if param.name in context.intermediate_results:
                args[param.name] = context.intermediate_results[param.name]
    
    return args
```

### 存在的问题

#### 1. 参数来源单一
- 只从 `context.intermediate_results` 查找
- 没有考虑用户原始请求中的参数
- 没有利用之前工具执行结果的嵌套数据
- 没有从执行历史中提取相关数据

#### 2. 缺乏智能推断
- 无法根据上下文智能推断参数值
- 例如：如果用户说"扫描10000"，应该推断出 `scan_all(value="10000")`

#### 3. 没有参数验证
- 不检查参数是否满足工具要求
- 不验证参数类型是否正确
- 不检查必需参数是否缺失

#### 4. 硬编码逻辑
- 只有少数工具有特殊处理
- 其他工具统一返回空字典
- 缺乏可扩展性

#### 5. 缺少默认值处理
- 没有使用工具元数据中的默认值
- 可选参数没有合理默认值

### 改进方案

#### 方案一：基于规则的智能参数推断

```python
def _determine_tool_args(self, tool_name: str, context) -> dict:
    """根据上下文确定工具的参数（改进版）。"""
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
    """从用户请求中提取工具参数。"""
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
    }
    
    for param_name, pattern in patterns.items():
        match = re.search(pattern, request_lower)
        if match:
            value = match.group(1)
            # 类型转换
            if param_name in ['address', 'size', 'count']:
                try:
                    if value.startswith('0x') or len(value) > 8:
                        args[param_name] = int(value, 16)
                    else:
                        args[param_name] = int(value)
                except ValueError:
                    continue
            else:
                args[param_name] = value
    
    return args

def _find_value_in_context(self, param_name: str, context) -> Any:
    """在上下文中查找参数值。"""
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
    """从执行历史中推断参数值。"""
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
        
        # 特定工具的推断逻辑
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
    
    return None

def _apply_tool_specific_logic(self, tool_name: str, args: dict, context) -> dict:
    """应用特定工具的智能逻辑。"""
    
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
            # 查找最近的地址
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
                    if isinstance(result, dict) and 'address' in result:
                        args['address'] = result['address']
                        break
    
    return args

def _validate_tool_args(self, tool_name: str, args: dict) -> bool:
    """验证工具参数。"""
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
```

#### 方案二：基于LLM的智能参数确定

```python
def _determine_tool_args_with_llm(self, tool_name: str, context) -> dict:
    """使用LLM智能确定工具参数。"""
    if not self.ollama_client or not self.use_llm:
        return self._determine_tool_args(tool_name, context)
    
    tool_info = self.tool_registry.get_tool(tool_name)
    if not tool_info:
        return {}
    
    metadata = tool_info['metadata']
    
    # 构建提示词
    prompt = self._build_arg_determination_prompt(
        tool_name=tool_name,
        metadata=metadata,
        context=context
    )
    
    system_prompt = self.prompt_manager.get_system_prompt()
    messages = self.prompt_manager.format_chat_messages(
        system_prompt=system_prompt,
        user_prompt=prompt
    )
    
    try:
        response = self.ollama_client.chat(messages)
        if 'message' in response and 'content' in response['message']:
            response_text = response['message']['content']
            args_dict = self.response_parser.parse_json(response_text)
            
            if args_dict and 'arguments' in args_dict:
                args = args_dict['arguments']
                
                # 验证参数
                if self._validate_tool_args(tool_name, args):
                    return args
                else:
                    self.logger.warning(f"LLM generated invalid arguments, falling back to rule-based")
                    return self._determine_tool_args(tool_name, context)
    except Exception as e:
        self.logger.error(f"Error in LLM argument determination: {e}")
    
    return self._determine_tool_args(tool_name, context)

def _build_arg_determination_prompt(self, tool_name: str, metadata, context) -> str:
    """构建参数确定的提示词。"""
    
    # 工具信息
    tool_info = f"""
Tool: {tool_name}
Description: {metadata.description}
Category: {metadata.category}

Parameters:
"""
    for param in metadata.parameters:
        required = "required" if param.required else "optional"
        default = f" (default: {param.default})" if param.default is not None else ""
        tool_info += f"  - {param.name} ({param.type}, {required}): {param.description}{default}\n"
    
    # 上下文信息
    context_info = f"""
User Request: {context.user_request}

Execution Context:
  - Task Type: {context.execution_plan.task_type}
  - Current Step: {context.current_step}
  - Total Steps: {context.execution_plan.estimated_steps}

Recent Results:
"""
    for step in context.history[-5:]:  # 最近5个步骤
        context_info += f"  - {step.tool_name}: {step.success}\n"
        if step.success and step.result:
            if isinstance(step.result, dict):
                for key, value in step.result.items():
                    if isinstance(value, (str, int, float, bool)):
                        context_info += f"      {key}: {value}\n"
            else:
                context_info += f"      Result: {str(step.result)[:100]}\n"
    
    # 中间结果
    if context.intermediate_results:
        context_info += "\nIntermediate Results:\n"
        for key, value in context.intermediate_results.items():
            if isinstance(value, (str, int, float, bool)):
                context_info += f"  - {key}: {value}\n"
    
    prompt = f"""Based on the following information, determine the appropriate arguments for the tool.

{tool_info}

{context_info}

Your task:
1. Analyze the user's request and context
2. Determine appropriate values for each parameter
3. Use available context data when possible
4. Provide reasonable defaults for optional parameters
5. Return ONLY a JSON object with the arguments

Provide your response in JSON format:
{{
  "arguments": {{
    "param1": "value1",
    "param2": "value2"
  }},
  "reasoning": "Explanation of your choices"
}}

Important:
- If a required parameter cannot be determined, use null
- For optional parameters, provide sensible defaults
- Use actual values from the context when available
- Convert values to the correct type (integer, string, etc.)
"""
    
    return prompt
```

---

## 问题二：LLM响应解析

### 当前实现分析

在 `Agent/llm/response_parser.py` 中，LLM响应解析依赖于LLM返回正确的JSON格式：

```python
def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
    """从文本中提取JSON对象。"""
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
```

### 存在的问题

#### 1. 依赖LLM输出格式
- 假设LLM总是返回有效的JSON
- 没有处理LLM返回非结构化文本的情况
- 没有处理JSON格式错误的情况

#### 2. 缺乏容错机制
- 如果JSON解析失败，直接返回None
- 没有尝试修复常见的JSON错误
- 没有从文本中提取关键信息的备用方案

#### 3. 没有处理嵌套JSON
- 无法处理嵌套的JSON结构
- 无法处理JSON数组

#### 4. 缺少语义理解
- 无法理解LLM的自然语言解释
- 无法从非JSON文本中提取信息

#### 5. 没有验证提取的数据
- 不验证提取的数据是否符合预期格式
- 不检查必需字段是否存在

### 改进方案

#### 方案一：增强的JSON提取和修复

```python
import json
import re
from typing import Dict, Any, Optional, List, Tuple

class EnhancedResponseParser:
    """增强的LLM响应解析器。"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON对象（增强版）。"""
        
        # 1. 尝试标准JSON提取
        result = self._try_standard_json_extraction(text)
        if result:
            return result
        
        # 2. 尝试修复常见的JSON错误
        result = self._try_json_repair(text)
        if result:
            return result
        
        # 3. 尝试从自然语言中提取结构化信息
        result = self._extract_from_natural_language(text)
        if result:
            return result
        
        # 4. 尝试部分JSON提取
        result = self._try_partial_json_extraction(text)
        if result:
            return result
        
        return None
    
    def _try_standard_json_extraction(self, text: str) -> Optional[Dict[str, Any]]:
        """尝试标准JSON提取。"""
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
        """清理JSON字符串中的常见问题。"""
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
        """尝试修复JSON错误。"""
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
        """查找文本中的JSON片段。"""
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
        """修复括号不匹配。"""
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
        """修复引号不匹配。"""
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
        """从自然语言中提取结构化信息。"""
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
        """尝试部分JSON提取。"""
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
    
    def parse_with_fallback(self, text: str, expected_keys: List[str]) -> Dict[str, Any]:
        """使用备用方案解析响应。"""
        # 1. 尝试JSON提取
        result = self._extract_json(text)
        if result:
            # 验证必需键
            if all(key in result for key in expected_keys):
                return result
        
        # 2. 尝试从自然语言提取
        result = self._extract_from_natural_language(text)
        if result:
            # 验证必需键
            if all(key in result for key in expected_keys):
                return result
        
        # 3. 返回部分结果
        return result if result else {}
    
    def parse_task_plan(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析任务计划（增强版）。"""
        result = self._extract_json(response_text)
        
        if result:
            # 验证并填充缺失字段
            if 'task_type' not in result:
                result['task_type'] = 'COMPREHENSIVE_ANALYSIS'
            
            if 'subtasks' not in result:
                # 尝试从文本中提取子任务
                result['subtasks'] = self._extract_subtasks_from_text(response_text)
            
            # 验证子任务格式
            if isinstance(result['subtasks'], list):
                for i, subtask in enumerate(result['subtasks']):
                    if isinstance(subtask, dict):
                        subtask.setdefault('id', i + 1)
                        subtask.setdefault('description', f'Subtask {i + 1}')
                        subtask.setdefault('tools', [])
                        subtask.setdefault('expected_output', '')
                        subtask.setdefault('dependencies', [])
            
            return result
        
        return None
    
    def _extract_subtasks_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取子任务。"""
        subtasks = []
        
        # 查找编号列表
        numbered_pattern = r'(?:\d+\.|step\s+\d+)[\s:]+([^\n]+)'
        matches = re.findall(numbered_pattern, text, re.IGNORECASE)
        
        for i, description in enumerate(matches, 1):
            subtasks.append({
                'id': i,
                'description': description.strip(),
                'tools': [],
                'expected_output': '',
                'dependencies': []
            })
        
        return subtasks
    
    def parse_reasoning(self, response_text: str) -> Optional[Dict[str, Any]]:
        """解析推理结果（增强版）。"""
        result = self._extract_json(response_text)
        
        if result:
            # 验证并填充缺失字段
            result.setdefault('analysis', '')
            result.setdefault('findings', [])
            result.setdefault('next_action', 'continue')
            result.setdefault('next_tool', None)
            result.setdefault('tool_args', {})
            result.setdefault('reasoning', '')
            result.setdefault('confidence', 0.8)
            
            return result
        
        # 尝试从文本中提取
        return self._extract_reasoning_from_text(response_text)
    
    def _extract_reasoning_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取推理信息。"""
        result = {
            'analysis': '',
            'findings': [],
            'next_action': 'continue',
            'next_tool': None,
            'tool_args': {},
            'reasoning': '',
            'confidence': 0.5
        }
        
        # 提取分析
        analysis_patterns = [
            r'(?:analysis|conclusion)[\s:]+([^\n]+)',
            r'(?:i\s+conclude|it\s+appears)[\s:]+([^\n]+)',
        ]
        for pattern in analysis_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['analysis'] = match.group(1).strip()
                break
        
        # 提取发现
        findings_patterns = [
            r'(?:finding|observation)[\s:]+([^\n]+)',
            r'(?:i\s+found|i\s+noticed)[\s:]+([^\n]+)',
        ]
        for pattern in findings_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            result['findings'].extend([m.strip() for m in matches])
        
        # 提取下一步动作
        action_patterns = [
            r'(?:next\s+action|should|will)[\s:]+(\w+)',
            r'(?:continue|adjust|abort|finalize|recover)',
        ]
        for pattern in action_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                action = match.group(1).lower() if match.group(1) else match.group(0).lower()
                if action in ['continue', 'adjust', 'abort', 'finalize', 'recover']:
                    result['next_action'] = action
                    break
        
        # 提取推理
        reasoning_patterns = [
            r'(?:reasoning|because|since|as)[\s:]+([^\n]+)',
        ]
        for pattern in reasoning_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['reasoning'] = match.group(1).strip()
                break
        
        return result if any([result['analysis'], result['findings'], result['reasoning']]) else None
```

#### 方案二：使用LLM进行响应解析

```python
def parse_with_llm(self, response_text: str, expected_type: str, expected_keys: List[str]) -> Dict[str, Any]:
    """使用LLM解析响应。"""
    if not self.ollama_client:
        return self._extract_json(response_text) or {}
    
    # 构建解析提示词
    prompt = f"""Parse the following LLM response and extract structured information.

Expected Type: {expected_type}
Expected Keys: {', '.join(expected_keys)}

LLM Response:
{response_text}

Your task:
1. Extract the structured information from the response
2. Ensure all expected keys are present
3. Convert values to appropriate types
4. Return ONLY a JSON object

Provide your response in JSON format:
{{
  "success": true,
  "data": {{
    "key1": "value1",
    "key2": "value2"
  }},
  "confidence": 0.9
}}

If the response doesn't contain the expected information, set "success" to false and provide a partial result.
"""
    
    try:
        system_prompt = "You are a JSON parser. Extract structured information from text and return valid JSON."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.ollama_client.chat(messages)
        if 'message' in response and 'content' in response['message']:
            response_text = response['message']['content']
            parsed = self._extract_json(response_text)
            
            if parsed and parsed.get('success') and 'data' in parsed:
                return parsed['data']
    except Exception as e:
        self.logger.error(f"Error in LLM parsing: {e}")
    
    # 回退到标准解析
    return self._extract_json(response_text) or {}
```

---

## 总结

### 工具参数确定改进要点

1. **多源参数提取** - 从用户请求、中间结果、执行历史等多个来源提取参数
2. **智能类型推断** - 根据参数类型和上下文智能推断值
3. **工具特定逻辑** - 为不同工具实现特定的参数处理逻辑
4. **参数验证** - 验证参数的完整性和正确性
5. **LLM辅助** - 使用LLM进行智能参数确定（可选）

### LLM响应解析改进要点

1. **增强的JSON提取** - 支持多种JSON格式和代码块
2. **JSON修复** - 自动修复常见的JSON错误
3. **自然语言提取** - 从非结构化文本中提取信息
4. **部分提取** - 即使JSON不完整也能提取有用信息
5. **备用方案** - 多层备用方案确保总能提取到信息
6. **LLM辅助解析** - 使用LLM进行响应解析（可选）

这些改进将显著提高系统的鲁棒性和智能性，使其能够更好地处理各种边界情况和异常输入。
