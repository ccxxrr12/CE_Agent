"""
Cheat Engine AI Agent 的结果解析器。

该模块实现了工具执行结果的解析逻辑，
处理来自 MCP 工具的不同数据类型和格式。
"""
import json
import re
from typing import Any, Dict, Optional, List
from ..models.base import ToolResult, ToolMetadata
from ..utils.logger import get_logger


class ResultParser:
    """工具执行结果的解析器。"""
    
    def __init__(self):
        """初始化结果解析器。"""
        self.logger = get_logger(__name__)
    
    def parse(self, raw_result: Any, tool: Optional[ToolMetadata] = None) -> ToolResult:
        """
        解析工具执行的原始结果。
        
        Args:
            raw_result: 工具的原始结果
            tool: 用于上下文的可选工具元数据
            
        Returns:
            解析后的 ToolResult 对象
        """
        try:
            # 处理不同类型的原始结果
            if isinstance(raw_result, dict):
                return self._parse_dict_result(raw_result, tool)
            elif isinstance(raw_result, str):
                return self._parse_string_result(raw_result, tool)
            elif isinstance(raw_result, (list, tuple)):
                return self._parse_list_result(raw_result, tool)
            else:
                # 对于其他类型，将它们包装在成功结果中
                return ToolResult(
                    success=True,
                    tool_name=tool.name if tool else "unknown",
                    parameters={},
                    result=raw_result
                )
        except Exception as e:
            self.logger.error(f"Error parsing result: {e}")
            return ToolResult(
                success=False,
                tool_name=tool.name if tool else "unknown",
                parameters={},
                error=f"Error parsing result: {str(e)}",
                result=raw_result
            )
    
    def _parse_dict_result(self, raw_result: Dict[str, Any], tool: Optional[ToolMetadata]) -> ToolResult:
        """Parse a dictionary result."""
        # Check if this looks like an error response
        if 'error' in raw_result or 'Error' in raw_result:
            error_key = 'error' if 'error' in raw_result else 'Error'
            return ToolResult(
                success=False,
                tool_name=tool.name if tool else "unknown",
                parameters={},
                error=raw_result[error_key],
                result=raw_result
            )
        
        # Check if this has a success flag
        success = raw_result.get('success', True)
        
        return ToolResult(
            success=success,
            tool_name=tool.name if tool else "unknown",
            parameters={},
            result=raw_result
        )
    
    def _parse_string_result(self, raw_result: str, tool: Optional[ToolMetadata]) -> ToolResult:
        """Parse a string result."""
        # Try to parse as JSON first
        try:
            json_result = json.loads(raw_result)
            return self._parse_dict_result(json_result, tool)
        except json.JSONDecodeError:
            # If not JSON, treat as plain text
            # Check for common error indicators in text
            error_indicators = ['error', 'exception', 'failed', 'invalid']
            lower_result = raw_result.lower()
            
            for indicator in error_indicators:
                if indicator in lower_result:
                    return ToolResult(
                        success=False,
                        tool_name=tool.name if tool else "unknown",
                        parameters={},
                        error=raw_result,
                        result=raw_result
                    )
            
            # Assume success for plain text
            return ToolResult(
                success=True,
                tool_name=tool.name if tool else "unknown",
                parameters={},
                result=raw_result
            )
    
    def _parse_list_result(self, raw_result: Any, tool: Optional[ToolMetadata]) -> ToolResult:
        """Parse a list or tuple result."""
        # Check if any element indicates an error
        for item in raw_result:
            if isinstance(item, dict) and ('error' in item or 'Error' in item):
                error_key = 'error' if 'error' in item else 'Error'
                return ToolResult(
                    success=False,
                    tool_name=tool.name if tool else "unknown",
                    parameters={},
                    error=item[error_key],
                    result=raw_result
                )
        
        return ToolResult(
            success=True,
            tool_name=tool.name if tool else "unknown",
            parameters={},
            result=raw_result
        )
    
    def parse_json(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON from text.
        
        Args:
            text: Text that should contain JSON
            
        Returns:
            The parsed JSON object
        """
        try:
            # Look for JSON within text that might contain other content
            # Find the first JSON object/array in the text
            brace_pos = text.find('{')
            bracket_pos = text.find('[')
            
            start_pos = min(pos for pos in [brace_pos, bracket_pos] if pos != -1)
            
            if start_pos == -1:
                raise ValueError("No JSON object found in text")
            
            # Extract JSON portion
            json_text = text[start_pos:]
            
            # Find the matching closing brace/bracket
            stack = []
            for i, char in enumerate(json_text):
                if char in ['{', '[']:
                    stack.append(char)
                elif char == '}':
                    if stack and stack[-1] == '{':
                        stack.pop()
                        if not stack:
                            json_text = json_text[:i+1]
                            break
                elif char == ']':
                    if stack and stack[-1] == '[':
                        stack.pop()
                        if not stack:
                            json_text = json_text[:i+1]
                            break
            
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error parsing JSON: {e}")
            raise
    
    def parse_binary(self, data: bytes) -> Dict[str, Any]:
        """
        Parse binary data into a structured format.
        
        Args:
            data: Binary data to parse
            
        Returns:
            A dictionary representation of the binary data
        """
        try:
            # Try to decode as hex string first
            hex_str = data.hex()
            
            # Attempt to parse as possible encoded JSON
            try:
                # If it looks like it might be encoded JSON, try to decode
                decoded = bytes.fromhex(data.hex()).decode('utf-8', errors='ignore')
                if decoded.startswith('{') or decoded.startswith('['):
                    json_obj = json.loads(decoded)
                    return {
                        'decoded_json': json_obj,
                        'original_hex': data.hex(),
                        'original_size': len(data)
                    }
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            
            return {
                'hex': data.hex(),
                'size': len(data),
                'preview': data[:50].hex()  # First 50 bytes as hex
            }
        except Exception as e:
            self.logger.error(f"Error parsing binary data: {e}")
            raise
    
    def extract_error(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract error message from a result dictionary.
        
        Args:
            result: A result dictionary that may contain an error
            
        Returns:
            The error message if found, None otherwise
        """
        # Common keys for errors
        error_keys = ['error', 'Error', 'errorMessage', 'error_message', 
                     'exception', 'Exception', 'fail', 'failure']
        
        for key in error_keys:
            if key in result:
                return str(result[key])
        
        # Check if success is explicitly False
        if 'success' in result and result['success'] is False:
            # Return the whole result as error if no specific error message
            return str(result)
        
        return None
    
    def validate_result(self, result: ToolResult) -> bool:
        """
        Validate a parsed result.
        
        Args:
            result: The ToolResult to validate
            
        Returns:
            True if the result is valid, False otherwise
        """
        # A result is valid if it has either a result or an error
        return result.result is not None or result.error is not None
    
    def format_for_llm(self, result: ToolResult) -> str:
        """
        Format a result for consumption by the LLM.
        
        Args:
            result: The ToolResult to format
            
        Returns:
            A string representation suitable for LLM processing
        """
        if result.success:
            if isinstance(result.result, dict):
                # Format dictionary results nicely
                return json.dumps(result.result, indent=2, ensure_ascii=False)
            elif isinstance(result.result, (list, tuple)):
                # Format list results nicely
                return json.dumps(result.result, indent=2, ensure_ascii=False)
            else:
                # For other types, convert to string
                return str(result.result)
        else:
            return f"Error: {result.error}"
    
    def extract_addresses(self, result: ToolResult) -> List[str]:
        """
        Extract memory addresses from a result.
        
        Args:
            result: The ToolResult to extract addresses from
            
        Returns:
            A list of extracted addresses
        """
        addresses = []
        
        if result.success and result.result:
            text = str(result.result)
            # Look for hex addresses (0x prefix or standalone hex)
            hex_pattern = r'(?:0x)?([0-9a-fA-F]{4,16})\b'
            matches = re.findall(hex_pattern, text)
            
            for match in matches:
                # If it doesn't start with 0x, add it
                addr = match if match.lower().startswith('0x') else f"0x{match}"
                try:
                    # Validate it's a proper address
                    int(addr, 16)
                    addresses.append(addr)
                except ValueError:
                    continue
        
        return list(set(addresses))  # Remove duplicates
