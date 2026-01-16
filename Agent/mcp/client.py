"""
Cheat Engine AI Agent 的 MCP (Model Context Protocol) 客户端。

该模块提供了一个客户端，用于通过子进程的 stdio 与 Cheat Engine MCP 服务器通信。
"""
import json
import logging
import subprocess
import sys
import os
import select
from typing import Dict, Any, Optional
from ..config import Config


class MCPClient:
    """用于与 Cheat Engine MCP 服务器通信的客户端。"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        """
        初始化 MCP 客户端。
        
        Args:
            host: MCP 服务器的主机地址（保留用于兼容性）
            port: MCP 服务器的端口（保留用于兼容性）
        """
        self.host = host
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.request_id = 0
    
    def connect(self) -> bool:
        """
        连接到 MCP 服务器（通过启动子进程）。
        
        Returns:
            如果连接成功返回 True，否则返回 False
        """
        try:
            # 获取 MCP 服务器脚本的路径
            server_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "MCP_Server",
                "mcp_cheatengine.py"
            )
            
            if not os.path.exists(server_script):
                self.logger.error(f"MCP 服务器脚本不存在: {server_script}")
                return False
            
            # 启动 MCP 服务器作为子进程
            self.process = subprocess.Popen(
                [sys.executable, server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                bufsize=0
            )
            
            # 等待进程启动
            import time
            time.sleep(1)
            
            if self.process.poll() is not None:
                # 进程已经退出
                stderr_output = self.process.stderr.read()
                if stderr_output:
                    stderr_output = stderr_output.decode('utf-8')
                self.logger.error(f"MCP 服务器启动失败: {stderr_output}")
                return False
            
            self.connected = True
            self.logger.info(f"已启动 MCP 服务器子进程 (PID: {self.process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"连接到 MCP 服务器失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """从 MCP 服务器断开连接。"""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
                self.logger.info("已停止 MCP 服务器子进程")
            except Exception as e:
                self.logger.error(f"停止 MCP 服务器子进程时出错: {e}")
        self.process = None
        self.connected = False
    
    def is_connected(self) -> bool:
        """
        检查客户端是否已连接到 MCP 服务器。
        
        Returns:
            如果已连接返回 True，否则返回 False
        """
        return self.connected and self.process is not None and self.process.poll() is None
    
    def send_command(self, method: str, params: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        使用 JSON-RPC 向 MCP 服务器发送命令。
        
        Args:
            method: 要调用的方法名
            params: 方法的参数
            timeout: 超时时间（秒），None 表示无限等待
            
        Returns:
            MCP 服务器的响应
        """
        if not self.is_connected():
            self.logger.error("未连接到 MCP 服务器")
            return {"error": "未连接到 MCP 服务器"}
        
        self.request_id += 1
        
        # 创建 JSON-RPC 请求
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        try:
            # 发送请求
            request_json = json.dumps(request)
            self.logger.info(f"发送 MCP 命令: {method}, 超时: {timeout if timeout else self.config.mcp_connection_timeout}秒")
            self.process.stdin.write((request_json + "\n").encode('utf-8'))
            self.process.stdin.flush()
            
            # 接收响应（带超时）
            if timeout is None:
                timeout = self.config.mcp_connection_timeout
            
            self.logger.info(f"等待 MCP 响应，超时: {timeout}秒...")
            response_line = self._readline_with_timeout(timeout)
            
            if not response_line:
                self.logger.error(f"从 MCP 服务器读取响应失败（超时: {timeout}秒）")
                return {"error": f"从 MCP 服务器读取响应失败（超时: {timeout}秒）"}
            
            self.logger.info(f"收到 MCP 响应，长度: {len(response_line)}")
            response = json.loads(response_line.strip())
            
            self.logger.debug(f"MCP 请求: {method} -> 响应: {response}")
            return response
        
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 MCP 响应失败: {e}")
            return {"error": f"解析 MCP 响应失败: {str(e)}"}
        except Exception as e:
            self.logger.error(f"向 MCP 服务器发送命令时出错: {e}")
            return {"error": f"向 MCP 服务器发送命令时出错: {str(e)}"}
    
    def _readline_with_timeout(self, timeout: float) -> Optional[str]:
        """
        带超时的读取一行。
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            读取的行，如果超时则返回 None
        """
        import threading
        result = [None]
        exception = [None]
        
        def read_line():
            try:
                line = self.process.stdout.readline()
                if line:
                    result[0] = line.decode('utf-8')
                else:
                    result[0] = None
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=read_line)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            self.logger.warning(f"MCP 响应读取超时（{timeout}秒）")
            return None
        
        if exception[0] is not None:
            raise exception[0]
        
        return result[0]
    
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
