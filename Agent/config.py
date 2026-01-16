"""
Cheat Engine AI Agent 配置模块。

该模块包含在整个 Agent 中使用的配置类和常量，支持从环境变量和配置文件加载配置。
"""
import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path


class ConfigManager:
    """配置管理器，负责加载和管理配置。"""
    
    def __init__(self):
        """初始化配置管理器。"""
        self._config: Optional[Config] = None
        self._config_file: Optional[str] = None
    
    def load_config(self, config_file: Optional[str] = None) -> "Config":
        """
        加载配置。
        
        Args:
            config_file: 配置文件路径（可选）
            
        Returns:
            配置实例
        """
        # 加载默认配置
        config_dict = asdict(Config())
        
        # 如果提供了配置文件，加载配置文件
        if config_file:
            self._config_file = config_file
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    config_dict.update(file_config)
        
        # 从环境变量加载配置（优先级最高）
        env_config = self._load_from_env()
        config_dict.update(env_config)
        
        # 创建配置实例
        self._config = Config(**config_dict)
        return self._config
    
    def _load_from_env(self) -> Dict[str, Any]:
        """
        从环境变量加载配置。
        
        Returns:
            从环境变量加载的配置
        """
        env_config = {}
        prefix = "CE_AGENT_"
        
        for key in os.environ:
            if key.startswith(prefix):
                # 转换环境变量名称为配置属性名称
                # 例如：CE_AGENT_MCP_HOST -> mcp_host
                config_key = key[len(prefix):].lower()
                config_key = config_key.replace("_", " ")
                config_key = config_key.title().replace(" ", "")
                config_key = config_key[0].lower() + config_key[1:]
                
                # 尝试转换值的类型
                value = os.environ[key]
                if value.lower() == "true":
                    env_config[config_key] = True
                elif value.lower() == "false":
                    env_config[config_key] = False
                else:
                    try:
                        env_config[config_key] = int(value)
                    except ValueError:
                        try:
                            env_config[config_key] = float(value)
                        except ValueError:
                            env_config[config_key] = value
        
        return env_config
    
    def get_config(self) -> "Config":
        """
        获取配置实例。
        
        Returns:
            配置实例
        """
        if self._config is None:
            self.load_config()
        return self._config
    
    def reload_config(self) -> "Config":
        """
        重新加载配置。
        
        Returns:
            重新加载后的配置实例
        """
        return self.load_config(self._config_file)
    
    def save_config(self, config_file: str) -> None:
        """
        保存配置到文件。
        
        Args:
            config_file: 配置文件路径
        """
        if self._config is None:
            self.load_config()
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)


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
    timeout: int = 180
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
            os.makedirs(log_dir, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典。
        
        Returns:
            配置字典
        """
        return asdict(self)


# 配置管理器实例
config_manager = ConfigManager()

# 单例配置实例
config = config_manager.get_config()
