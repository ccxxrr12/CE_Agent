"""
Cheat Engine AI Agent 的主入口点。

该模块初始化代理，设置 MCP 连接，
配置 LLM，并启动主交互循环。
"""
import asyncio
import logging
from pathlib import Path
import argparse

from .config import Config
from .core.agent import Agent
from .mcp.client import MCPClient
from .llm.client import OllamaClient
from .tools.registry import ToolRegistry
from .tools.mcp_basic_tools import register_mcp_tools
from .tools.mcp_advanced_tools import register_advanced_mcp_tools
from .utils.logger import setup_logging
from .ui.cli import CLI


def create_agent(config: Config) -> Agent:
    """
    创建并初始化Agent实例。
    
    Args:
        config: 配置对象
        
    Returns:
        初始化后的Agent实例
    """
    logger = logging.getLogger(__name__)
    
    # 初始化客户端
    mcp_client = MCPClient(config.mcp_host, config.mcp_port)
    ollama_client = OllamaClient(config.ollama_host, config.ollama_port, config.model_name)
    
    # 初始化工具注册表
    tool_registry = ToolRegistry()
    
    # 注册MCP工具
    register_mcp_tools(tool_registry, mcp_client)
    register_advanced_mcp_tools(tool_registry, mcp_client)
    
    logger.info(f"Registered {len(tool_registry.list_all_tools())} tools")
    
    # 初始化代理
    agent = Agent(config, tool_registry, mcp_client, ollama_client)
    
    return agent, mcp_client


def main():
    """初始化并运行 Cheat Engine AI Agent。"""
    # 设置日志
    config = Config()
    setup_logging(config.log_level, config.log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Cheat Engine AI Agent...")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Cheat Engine AI Agent - Natural language interface for Cheat Engine")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--batch", "-b", type=str, help="Run in batch mode with input file")
    parser.add_argument("--output", "-o", type=str, help="Output file for batch mode results")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM and use rule-based planning")
    parser.add_argument("--request", "-r", type=str, help="Process a single request and exit")
    
    args = parser.parse_args()
    
    # 创建Agent
    agent, mcp_client = create_agent(config)
    
    # 启动代理
    try:
        # 连接到MCP服务器
        logger.info("Connecting to Cheat Engine MCP server...")
        if mcp_client.connect():
            logger.info("Successfully connected to MCP server")
        else:
            logger.error("Failed to connect to MCP server")
            print("Warning: Failed to connect to MCP server. Some features may not work.")
        
        # 测试连接
        try:
            ping_result = mcp_client.send_command("ping", {})
            if 'error' not in ping_result:
                logger.info("MCP server ping successful")
        except Exception as e:
            logger.warning(f"MCP server ping failed: {e}")
        
        # 创建CLI
        cli = CLI()
        
        # 处理不同的运行模式
        if args.request:
            # 单次请求模式
            logger.info(f"Processing single request: {args.request}")
            print(f"\nProcessing request: {args.request}\n")
            
            try:
                report = agent.execute(args.request)
                cli.display_result(report)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                cli.display_error(str(e))
        
        elif args.batch:
            # 批处理模式
            logger.info(f"Running in batch mode with input file: {args.batch}")
            cli.run_batch_mode(args.batch, args.output, agent)
        
        else:
            # 交互模式（默认）
            logger.info("Running in interactive mode")
            cli.run_interactive_mode(agent)
            
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        print("\n\nOperation interrupted by user.")
    except Exception as e:
        logger.error(f"Error running Cheat Engine AI Agent: {e}")
        print(f"Error: {e}")
    finally:
        # 清理
        logger.info("Shutting down Cheat Engine AI Agent...")
        mcp_client.disconnect()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()