"""
Cheat Engine AI Agent 的 MCP (Model Context Protocol) 客户端。

该模块提供了一个客户端，用于通过命名管道上的 JSON-RPC 与 Cheat Engine MCP 服务器通信。
"""
import json
import logging
import socket
import time
from typing import Dict, Any, Optional
from ..config import Config


class MCPClient:
    """用于与 Cheat Engine MCP 服务器通信的客户端。"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        初始化 MCP 客户端。
        
        Args:
            host: MCP 服务器的主机地址
            port: MCP 服务器的端口
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.config = Config()
    
    def connect(self) -> bool:
        """
        连接到 MCP 服务器。
        
        Returns:
            如果连接成功返回 True，否则返回 False
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.config.mcp_connection_timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.logger.info(f"已连接到 MCP 服务器 {self.host}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"连接到 MCP 服务器失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """从 MCP 服务器断开连接。"""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("已从 MCP 服务器断开连接")
            except Exception as e:
                self.logger.error(f"从 MCP 服务器断开连接时出错: {e}")
        self.socket = None
        self.connected = False
    
    def is_connected(self) -> bool:
        """
        检查客户端是否已连接到 MCP 服务器。
        
        Returns:
            如果已连接返回 True，否则返回 False
        """
        return self.connected
    
    def send_command(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 JSON-RPC 向 MCP 服务器发送命令。
        
        Args:
            method: 要调用的方法名
            params: 方法的参数
            
        Returns:
            MCP 服务器的响应
        """
        if not self.connected or not self.socket:
            self.logger.error("未连接到 MCP 服务器")
            return {"error": "未连接到 MCP 服务器"}
        
        # 创建 JSON-RPC 请求
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time() * 1000)  # 使用时间戳作为 ID
        }
        
        try:
            # 发送请求
            request_json = json.dumps(request)
            self.socket.sendall(request_json.encode() + b'\n')
            
            # 接收响应
            response_data = self.socket.recv(4096).decode().strip()
            response = json.loads(response_data)
            
            self.logger.debug(f"MCP 请求: {request} -> 响应: {response}")
            return response
        
        except Exception as e:
            self.logger.error(f"向 MCP 服务器发送命令时出错: {e}")
            return {"error": f"向 MCP 服务器发送命令时出错: {str(e)}"}
    
    def execute_script(self, script: str) -> Dict[str, Any]:
        """
        在 Cheat Engine 中执行 Lua 脚本。
        
        Args:
            script: 要执行的 Lua 脚本
            
        Returns:
            脚本执行的结果
        """
        return self.send_command("execute_script", {"script": script})
    
    def read_memory(self, address: int, size: int) -> Dict[str, Any]:
        """
        从 Cheat Engine 读取内存。
        
        Args:
            address: 要读取的内存地址
            size: 要读取的字节数
            
        Returns:
            内存内容
        """
        return self.send_command("read_memory", {"address": address, "size": size})
    
    def write_memory(self, address: int, data: bytes) -> Dict[str, Any]:
        """
        向 Cheat Engine 的内存写入数据。
        
        Args:
            address: 要写入的内存地址
            data: 要写入的数据
            
        Returns:
            写入操作的结果
        """
        return self.send_command("write_memory", {"address": address, "data": data.hex()})
    
    def scan_memory(self, pattern: str, start_addr: int = 0x0, end_addr: int = 0x7FFFFFFF) -> Dict[str, Any]:
        """
        在 Cheat Engine 中扫描特定模式的内存。
        
        Args:
            pattern: 要搜索的模式
            start_addr: 扫描的起始地址（默认: 0x0）
            end_addr: 扫描的结束地址（默认: 0x7FFFFFFF）
            
        Returns:
            找到模式的地址列表
        """
        return self.send_command("scan_memory", {
            "pattern": pattern,
            "start_addr": start_addr,
            "end_addr": end_addr
        })
    
    def get_processes(self) -> Dict[str, Any]:
        """
        从 Cheat Engine 获取进程列表。
        
        Returns:
            进程列表
        """
        return self.send_command("get_processes", {})
    
    def attach_to_process(self, process_name: str) -> Dict[str, Any]:
        """
        在 Cheat Engine 中附加到进程。
        
        Args:
            process_name: 要附加的进程名称
            
        Returns:
            附加操作的结果
        """
        return self.send_command("attach_to_process", {"process_name": process_name})