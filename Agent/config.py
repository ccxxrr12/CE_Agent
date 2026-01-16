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
    # 注意：MCP 服务器现在通过子进程 stdio 通信，以下参数保留用于向后兼容
    mcp_host: str = "localhost"
    mcp_port: int = 8080
    
    # MCP 子进程配置
    mcp_server_script: str = "MCP_Server/mcp_cheatengine.py"
    mcp_process_startup_timeout: int = 5
    mcp_process_shutdown_timeout: int = 5
    
    # Ollama 配置
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    model_name: str = "deepseek-r1:8b"
    
    # 火山引擎配置
    use_volcengine: bool = True
    volcengine_api_key: str = "c7d62175-a6db-465d-ab06-6e6b2baa6914"
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_model: str = "glm-4-7-251222"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/ce_agent.log"
    
    # 提示词配置
    use_simple_prompt: bool = False
    use_minimal_prompt: bool = False
    use_json_prompt: bool = True
    system_prompt_file: str = "prompts/SYSTEM_PROMPT.md"
    system_prompt_simple_file: str = "prompts/SYSTEM_PROMPT_SIMPLE.md"
    system_prompt_minimal_file: str = "prompts/SYSTEM_PROMPT_MINIMAL.md"
    system_prompt_json_file: str = "prompts/SYSTEM_PROMPT.json"
    
    # Agent 配置
    max_retries: int = 3
    timeout: int = 300
    max_context_length: int = 4096
    
    # MCP 连接配置（保留用于向后兼容）
    mcp_connection_timeout: int = 300
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
        if self.mcp_process_startup_timeout <= 0:
            raise ValueError("mcp_process_startup_timeout 必须大于 0")
        if self.mcp_process_shutdown_timeout <= 0:
            raise ValueError("mcp_process_shutdown_timeout 必须大于 0")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)


# 单例配置实例
config = Config()
