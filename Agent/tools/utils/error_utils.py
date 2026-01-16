"""
Cheat Engine AI Agent 的错误处理工具。

该模块提供了用于处理错误的工具函数，如错误分类、格式化和转换等。
"""
from typing import Dict, Any, Optional, Union
from ..core.mcp_client import MCPConnectionError, MCPCommandError, MCPTimeoutError


def categorize_error(error: Exception) -> str:
    """
    将异常分类为错误代码。
    
    Args:
        error: 要分类的异常
        
    Returns:
        错误代码字符串
    """
    if isinstance(error, MCPConnectionError):
        return "CONNECTION_ERROR"
    elif isinstance(error, MCPCommandError):
        return "COMMAND_ERROR"
    elif isinstance(error, MCPTimeoutError):
        return "TIMEOUT_ERROR"
    elif isinstance(error, ValueError):
        return "PARAMETER_ERROR"
    elif isinstance(error, TypeError):
        return "TYPE_ERROR"
    elif isinstance(error, PermissionError):
        return "PERMISSION_ERROR"
    elif isinstance(error, FileNotFoundError):
        return "NOT_FOUND_ERROR"
    else:
        return "UNKNOWN_ERROR"


def format_error(error: Exception, command_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    将异常格式化为标准错误响应格式。
    
    Args:
        error: 要格式化的异常
        command_name: 命令名称（可选）
        params: 命令参数（可选）
        
    Returns:
        格式化后的错误响应字典
    """
    error_code = categorize_error(error)
    error_msg = str(error)
    
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_msg,
            "details": {
                "command": command_name,
                "parameters": params
            }
        }
    }


def create_error_response(
    message: str,
    code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建标准错误响应。
    
    Args:
        message: 错误消息
        code: 错误代码（可选）
        details: 错误详情（可选）
        
    Returns:
        标准错误响应字典
    """
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }


def create_success_response(
    result: Any,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建标准成功响应。
    
    Args:
        result: 操作结果
        message: 成功消息（可选）
        
    Returns:
        标准成功响应字典
    """
    response = {
        "success": True,
        "result": result
    }
    
    if message:
        response["message"] = message
    
    return response
