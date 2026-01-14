from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置管理"""
    # MCP服务器配置
    MCP_SERVER_NAME: str = "cheatengine"
    PIPE_NAME: str = r"\\.\\pipe\\CE_MCP_Bridge_v99"
    
    # Ollama配置
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # LangChain配置
    AGENT_LOG_LEVEL: str = "INFO"
    AGENT_PROMPT: Optional[str] = None
    
    # 代理配置
    MAX_AGENT_STEPS: int = 6
    
    # 日志配置
    LOG_DIR: str = "logs"
    
    # 连接配置
    MAX_RETRIES: int = 2
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
