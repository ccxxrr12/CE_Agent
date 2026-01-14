"""
Cheat Engine AI Agent 的 Ollama 客户端。

该模块提供了一个客户端，用于与 Ollama 服务器通信，
以运行本地 LLM 进行 AI 交互。
"""
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin
from ..config import Config


class OllamaClient:
    """用于与 Ollama 服务器通信的客户端。"""
    
    def __init__(self, host: str = "localhost", port: int = 11434, model_name: str = "mistral:7b-instruct-v0.2-q4_K_M"):
        """
        初始化 Ollama 客户端。
        
        Args:
            host: Ollama 服务器的主机地址
            port: Ollama 服务器的端口
            model_name: 要使用的模型名称
        """
        self.host = host
        self.port = port
        self.model_name = model_name
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.logger.info(f"OllamaClient initialized with model: {self.model_name}")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        向 Ollama API 发出请求。
        
        Args:
            endpoint: 要调用的 API 端点
            data: 请求负载
            
        Returns:
            API 响应
        """
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Ollama 请求到 {endpoint}: {data} -> 响应: {result}")
                return result
            else:
                self.logger.error(f"Ollama API 错误: {response.status_code} - {response.text}")
                return {"error": f"API 错误: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"向 Ollama 的请求失败: {e}")
            return {"error": f"请求失败: {str(e)}"}
        except Exception as e:
            self.logger.error(f"调用 Ollama 时发生意外错误: {e}")
            return {"error": f"意外错误: {str(e)}"}
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        使用提供的提示从 LLM 生成响应。
        
        Args:
            prompt: LLM 的输入提示
            **kwargs: 要传递给模型的额外参数
            
        Returns:
            LLM 响应
        """
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "num_gpu": -1,
            **kwargs
        }
        
        self.logger.debug(f"Generating with model: {self.model_name}")
        return self._make_request("/api/generate", data)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        与 LLM 进行聊天对话。
        
        Args:
            messages: 对话中的消息列表
            **kwargs: 要传递给模型的额外参数
            
        Returns:
            LLM 响应
        """
        data = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "num_gpu": -1,
            **kwargs
        }
        
        return self._make_request("/api/chat", data)
    
    def embeddings(self, input_text: str) -> Dict[str, Any]:
        """
        为给定的输入文本生成嵌入。
        
        Args:
            input_text: 要生成嵌入的文本
            
        Returns:
            嵌入向量
        """
        data = {
            "model": self.model_name,
            "prompt": input_text
        }
        
        return self._make_request("/api/embeddings", data)
    
    def extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """
        从 LLM 响应文本中提取工具调用。
        
        Args:
            text: LLM 响应文本
            
        Returns:
            表示工具调用的字典，如果未找到工具调用则返回 None
        """
        # 查找表示工具调用的模式
        # 这可以根据预期的格式进行自定义
        try:
            # 尝试查找可能表示工具调用的类似 JSON 的结构
            import re
            # 查找类似 {"tool": "...", ...} 的模式
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # 清理潜在的格式问题
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
        列出 Ollama 服务器上的可用模型。
        
        Returns:
            可用模型列表
        """
        try:
            response = requests.get(
                urljoin(self.base_url, "/api/tags"),
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to list models: {response.status_code}")
                return {"error": f"Failed to list models: {response.status_code}"}
        except Exception as e:
            self.logger.error(f"Error listing models: {e}")
            return {"error": f"Error listing models: {str(e)}"}
    
    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """
        从 Ollama 注册表拉取模型。
        
        Args:
            model_name: 要拉取的模型名称
            
        Returns:
            拉取操作的结果
        """
        data = {
            "name": model_name
        }
        
        try:
            response = requests.post(
                urljoin(self.base_url, "/api/pull"),
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True}
            else:
                self.logger.error(f"Failed to pull model: {response.status_code}")
                return {"error": f"Failed to pull model: {response.status_code}"}
        except Exception as e:
            self.logger.error(f"Error pulling model: {e}")
            return {"error": f"Error pulling model: {str(e)}"}