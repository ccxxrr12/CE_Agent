"""
Cheat Engine AI Agent 的火山引擎客户端。

该模块提供了一个客户端，用于与火山引擎（ARK）API通信，
以运行云端 LLM 进行 AI 交互。
"""
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from ..config import Config


class VolcengineClient:
    """用于与火山引擎（ARK）API通信的客户端。"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model_name: str = "glm-4-7-251222"):
        """
        初始化火山引擎客户端。
        
        Args:
            api_key: 火山引擎API密钥
            base_url: API基础URL
            model_name: 要使用的模型名称
        """
        self.config = Config()
        
        # 从参数或配置中获取API密钥
        self.api_key = api_key or self.config.volcengine_api_key
        self.base_url = base_url or self.config.volcengine_base_url
        self.model_name = model_name or self.config.volcengine_model
        
        # 初始化OpenAI客户端（火山引擎兼容OpenAI API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"VolcengineClient initialized with model: {self.model_name}")
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用提供的提示从 LLM 生成响应。
        
        Args:
            prompt: LLM 的输入提示
            **kwargs: 要传递给模型的额外参数
            
        Returns:
            LLM 响应
        """
        try:
            # 使用responses.create方法（火山引擎特有）
            response = self.client.responses.create(
                model=self.model_name,
                input=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            # 提取响应内容
            result = {
                "response": response.output[0].content[0].text if response.output else "",
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
            self.logger.debug(f"Volcengine generate response: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Volcengine generate error: {e}")
            return {"error": f"生成失败: {str(e)}"}
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        与 LLM 进行聊天对话。
        
        Args:
            messages: 对话中的消息列表
            **kwargs: 要传递给模型的额外参数
            
        Returns:
            LLM 响应
        """
        try:
            # 使用responses.create方法
            response = self.client.responses.create(
                model=self.model_name,
                input=messages,
                **kwargs
            )
            
            # 提取响应内容并转换为与Ollama兼容的格式
            content = ""
            if response.output and len(response.output) > 0:
                # 火山引擎的响应格式：output[0]是推理过程，output[1]是实际输出
                # 我们需要找到type='message'的输出
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and len(item.content) > 0:
                            if hasattr(item.content[0], 'text'):
                                content = item.content[0].text
                                break
            
            result = {
                "message": {
                    "content": content,
                    "role": "assistant"
                },
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
            self.logger.debug(f"Volcengine chat response: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Volcengine chat error: {e}")
            return {"error": f"聊天失败: {str(e)}"}
    
    def embeddings(self, input_text: str) -> Dict[str, Any]:
        """
        为给定的输入文本生成嵌入。
        
        Args:
            input_text: 要生成嵌入的文本
            
        Returns:
            嵌入向量
        """
        try:
            # 火山引擎的嵌入API（如果支持）
            response = self.client.embeddings.create(
                model=self.model_name,
                input=input_text
            )
            
            result = {
                "embedding": response.data[0].embedding,
                "model": response.model
            }
            
            self.logger.debug(f"Volcengine embeddings response: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Volcengine embeddings error: {e}")
            return {"error": f"嵌入生成失败: {str(e)}"}
    
    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从 LLM 响应文本中提取工具调用。
        
        Args:
            text: LLM 响应文本
            
        Returns:
            表示工具调用的字典，如果未找到工具调用则返回 None
        """
        import json
        import re
        
        try:
            # 查找类似 {"tool": "...", ...} 的模式
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                json_str = json_str.strip()
                tool_call = json.loads(json_str)
                
                # 检查这是否看起来像有效的工具调用
                if isinstance(tool_call, dict) and ("tool" in tool_call or "function" in tool_call):
                    return tool_call
        except (json.JSONDecodeError, ValueError):
            pass
        
        return None
    
    def list_models(self) -> Dict[str, Any]:
        """
        列出火山引擎上的可用模型。
        
        Returns:
            可用模型列表
        """
        try:
            models = self.client.models.list()
            return {"models": [{"id": model.id} for model in models.data]}
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return {"error": f"列出模型失败: {str(e)}"}
    
    def test_connection(self) -> bool:
        """
        测试与火山引擎API的连接。
        
        Returns:
            如果连接成功返回 True，否则返回 False
        """
        try:
            response = self.chat([{"role": "user", "content": "test"}])
            if "error" not in response:
                self.logger.info("Volcengine API connection test successful")
                return True
            else:
                self.logger.error(f"Volcengine API connection test failed: {response.get('error')}")
                return False
        except Exception as e:
            self.logger.error(f"Volcengine API connection test error: {e}")
            return False
