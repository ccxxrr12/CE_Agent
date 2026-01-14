"""
Cheat Engine AI Agent 的 MCP (Model Context Protocol) 模块。

这包括用于通过命名管道上的 JSON-RPC 与
Cheat Engine MCP 服务器通信的类和函数。
"""
from .client import MCPClient

__all__ = ['MCPClient']