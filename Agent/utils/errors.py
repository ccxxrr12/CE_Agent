"""
Cheat Engine AI Agent 的统一错误处理模块。

该模块定义了在整个代理中使用的统一错误类型层次结构。
"""


class AgentBaseError(Exception):
    """所有Agent错误的基类。"""
    
    def __init__(self, message: str, error_code: int = 500, details: dict = None):
        """
        初始化Agent基础错误。
        
        Args:
            message: 错误消息
            error_code: 错误代码（默认500）
            details: 错误详情（可选）
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """
        将错误转换为字典格式。
        
        Returns:
            包含错误信息的字典
        """
        return {
            "error": {
                "message": self.message,
                "error_code": self.error_code,
                "details": self.details
            }
        }


class ConfigurationError(AgentBaseError):
    """配置相关错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=400, details=details)


class ConnectionError(AgentBaseError):
    """连接相关错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=503, details=details)


class ToolError(AgentBaseError):
    """工具执行相关错误。"""
    
    def __init__(self, tool_name: str, message: str, details: dict = None):
        full_message = f"Tool '{tool_name}': {message}"
        self.tool_name = tool_name
        super().__init__(full_message, error_code=500, details=details)


class LLMError(AgentBaseError):
    """LLM相关错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=502, details=details)


class TimeoutError(AgentBaseError):
    """超时相关错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=408, details=details)


class ValidationError(AgentBaseError):
    """参数验证相关错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=400, details=details)


class MCPError(AgentBaseError):
    """MCP相关错误的基类。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=500, details=details)


class MCPConnectionError(MCPError):
    """MCP连接错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details=details)


class MCPCommandError(MCPError):
    """MCP命令错误。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details=details)


class MCPTimeoutError(MCPError):
    """MCP命令超时。"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=408, details=details)
