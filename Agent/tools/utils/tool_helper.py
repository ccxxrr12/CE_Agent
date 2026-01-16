"""
Cheat Engine AI Agent 的工具助手模块。

该模块包含工具实现的公共逻辑和辅助函数，用于消除代码重复。
"""
from typing import Any, Dict, Callable, List, Optional
from ..base.decorators import tool
from ..models.base import ToolMetadata, Parameter, ToolCategory
from ...utils.logger import get_logger
from ..core.mcp_client import MCPBridgeClient

logger = get_logger(__name__)


def create_simple_mcp_tool(
    name: str,
    category: ToolCategory,
    description: str,
    method: str,
    parameters: Optional[List[Parameter]] = None,
    examples: Optional[List[str]] = None,
    requires_approval: bool = False,
    destructive: bool = False
) -> Callable[..., Dict[str, Any]]:
    """
    创建一个简单的MCP工具实现，用于消除代码重复。
    
    该函数是一个高阶函数，用于自动生成简单的MCP工具实现，避免重复编写相似的代码。
    它接收工具的元数据和配置，返回一个完整的工具实现函数，该函数会自动处理MCP命令的发送和错误处理。
    
    Args:
        name: 工具名称
        category: 工具类别
        description: 工具描述
        method: 要调用的MCP方法名
        parameters: 工具参数列表
        examples: 工具使用示例
        requires_approval: 是否需要用户批准
        destructive: 是否具有破坏性
        
    Returns:
        工具实现函数，接收MCP客户端实例和工具参数，返回工具执行结果
    """
    @tool(
        name=name,
        category=category,
        description=description,
        parameters=parameters or [],
        examples=examples or [],
        requires_approval=requires_approval,
        destructive=destructive
    )
    def tool_impl(mcp_client: MCPBridgeClient, **kwargs: Any) -> Dict[str, Any]:
        """
        工具实现函数，用于执行MCP命令。
        
        Args:
            mcp_client: MCP客户端实例，用于与Cheat Engine通信
            **kwargs: 工具参数
            
        Returns:
            工具执行结果，包含命令的响应或错误信息
        """
        try:
            # 调用MCP客户端发送命令
            response = mcp_client.send_command(method, kwargs)
            return response
        except Exception as e:
            # 记录错误日志
            logger.error(f"{name} 命令执行失败: {e}")
            # 返回错误信息
            return {"error": str(e)}
    
    return tool_impl
