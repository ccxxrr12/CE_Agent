"""
Cheat Engine AI Agent 包

该包实现了一个通过 MCP 与 Cheat Engine 接口的 AI 代理，
使用 LLM 实现高级内存分析和逆向工程功能。
"""
__version__ = "0.1.0"
__author__ = "Cheat Engine MCP Bridge Team"

from .config import Config
from .mcp import MCPClient
from .llm import OllamaClient
from .tools import ToolRegistry
from .core import Agent, AgentStatus
from .ui import CLI