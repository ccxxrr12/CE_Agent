"""
Cheat Engine AI Agent 配置模块。

该模块包含在整个 Agent 中使用的配置类和常量。
"""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Cheat Engine AI Agent 的配置类。"""
    
    # MCP 服务器配置
    mcp_host: str = "localhost"
    mcp_port: int = 8080
    
    # Ollama 配置
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    model_name: str = "deepseek-r1:8b"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/ce_agent.log"
    
    # Agent 配置
    max_retries: int = 3
    timeout: int = 30
    max_context_length: int = 4096
    
    # MCP 连接配置
    mcp_connection_timeout: int = 10
    mcp_retry_delay: float = 1.0
    
    def __post_init__(self):
        """初始化后验证配置值。"""
        if self.max_retries <= 0:
            raise ValueError("max_retries 必须大于 0")
        if self.timeout <= 0:
            raise ValueError("timeout 必须大于 0")
        if self.mcp_connection_timeout <= 0:
            raise ValueError("mcp_connection_timeout 必须大于 0")
        if self.mcp_retry_delay <= 0:
            raise ValueError("mcp_retry_delay 必须大于 0")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)


# 单例配置实例
config = Config()