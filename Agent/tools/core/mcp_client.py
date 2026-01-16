"""
Cheat Engine AI Agent 的 MCP 客户端。

该模块负责与 MCP_Server 进行通信，包括命令发送、响应处理和连接管理。
"""
# 优先使用orjson进行更快的JSON解析
try:
    import orjson as json
except ImportError:
    import json
import struct
import time
import socket
from typing import Dict, Any, Optional
import win32file
import win32pipe
import win32con
import pywintypes
from ...utils.logger import get_logger
from .command_adapter import MCPCommandAdapter
from .parameter_validator import MCPParameterValidator


from ...utils.errors import (
    MCPConnectionError,
    MCPCommandError,
    MCPTimeoutError
)


class MCPBridgeClient:
    """MCP桥接客户端，负责与Cheat Engine MCP服务器进行通信。"""
    
    def __init__(self, pipe_name: str = r"\\.\pipe\CE_MCP_Bridge_v99", max_retries: int = 3):
        """
        初始化MCP桥接客户端。
        
        Args:
            pipe_name: 命名管道名称
            max_retries: 最大重试次数
        """
        self.pipe_name = pipe_name
        self.max_retries = max_retries
        self.handle = None
        self.logger = get_logger(__name__)
        self.command_adapter = MCPCommandAdapter()
        self.parameter_validator = MCPParameterValidator()
    
    def connect(self) -> bool:
        """
        尝试连接到CE命名管道。
        
        Returns:
            如果连接成功则返回 True，否则返回 False
        """
        try:
            # 创建与Cheat Engine Lua脚本的命名管道连接
            self.handle = win32file.CreateFile(
                self.pipe_name,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            return True
        except pywintypes.error as e:
            self.logger.error(f"连接错误: {e}")
            return False
    
    def close(self) -> None:
        """关闭管道连接。"""
        if self.handle:
            try:
                win32file.CloseHandle(self.handle)
            except Exception as e:
                self.logger.error(f"关闭连接错误: {e}")
            finally:
                self.handle = None
    
    def send_command(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        发送命令到CE桥接，失败时自动重连。
        
        Args:
            method: 命令方法名
            params: 命令参数
            timeout: 超时时间（秒）
            
        Returns:
            命令执行结果
            
        Raises:
            MCPConnectionError: 如果连接失败
            MCPCommandError: 如果命令执行失败
            MCPTimeoutError: 如果命令执行超时
        """
        if params is None:
            params = {}
        
        # 验证参数
        if not self.parameter_validator.validate(method, params):
            raise MCPCommandError(f"无效的命令参数: {params}")
        
        # 适配参数格式
        adapted_params = self.command_adapter.adapt_command(method, params)
        
        max_retries = self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            if not self.handle:
                if not self.connect():
                    raise MCPConnectionError("Cheat Engine桥接 (v11/v99) 未运行（找不到管道）。")
            
            # 构造JSON-RPC请求
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": adapted_params,
                "id": int(time.time() * 1000)  # 使用时间戳作为唯一ID
            }
            
            try:
                # 发送请求
                response = self._send_request(request, timeout)
                return response
            except pywintypes.error as e:
                # 发生通信错误，关闭连接并重试
                self.close()
                last_error = MCPConnectionError(f"管道通信失败: {e}")
                if attempt < max_retries - 1:
                    self.logger.warning(f"通信错误，重试中... (尝试 {attempt+2}/{max_retries})")
                    time.sleep(0.5)  # 短暂延迟后重试
                continue
            except Exception as e:
                # 其他错误，不重试
                self.close()
                raise e
        
        # 所有重试都失败
        if last_error:
            raise last_error
        raise MCPConnectionError("未知通信错误")
    
    def _send_request(self, request: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        发送单个JSON-RPC请求并接收响应。
        
        Args:
            request: JSON-RPC请求
            timeout: 超时时间（秒）
            
        Returns:
            命令执行结果
            
        Raises:
            MCPTimeoutError: 如果命令执行超时
            MCPCommandError: 如果命令执行失败
        """
        # 设置超时
        if timeout is not None:
            start_time = time.time()
        
        try:
            # 将请求序列化为JSON并编码为字节
            req_json = json.dumps(request)
            if isinstance(req_json, str):
                req_json = req_json.encode('utf-8')
            # 创建长度头（小端序）
            header = struct.pack('<I', len(req_json))
            
            # 发送长度头和JSON请求
            win32file.WriteFile(self.handle, header)
            win32file.WriteFile(self.handle, req_json)
            
            # 检查超时
            if timeout is not None and time.time() - start_time > timeout:
                raise MCPTimeoutError(f"命令执行超时（{timeout}秒）")
            
            # 读取响应头（4字节长度）
            resp_header_buffer = win32file.ReadFile(self.handle, 4)[1]
            if len(resp_header_buffer) < 4:
                raise MCPConnectionError("来自CE的响应头不完整。")
            
            # 检查超时
            if timeout is not None and time.time() - start_time > timeout:
                raise MCPTimeoutError(f"命令执行超时（{timeout}秒）")
            
            # 解析响应长度
            resp_len = struct.unpack('<I', resp_header_buffer)[0]
            
            # 检查响应大小是否过大
            if resp_len > 16 * 1024 * 1024:  # 限制最大响应大小为16MB
                raise MCPCommandError(f"响应过大: {resp_len} 字节")
            
            # 读取响应体，添加超时检查
            resp_body_buffer = b''
            remaining_bytes = resp_len
            while remaining_bytes > 0:
                # 检查超时
                if timeout is not None and time.time() - start_time > timeout:
                    raise MCPTimeoutError(f"命令执行超时（{timeout}秒）")
                
                # 每次读取最多4096字节
                chunk_size = min(4096, remaining_bytes)
                chunk = win32file.ReadFile(self.handle, chunk_size)[1]
                if not chunk:
                    raise MCPConnectionError("连接已关闭，无法读取完整响应")
                resp_body_buffer += chunk
                remaining_bytes -= len(chunk)
            
            # 检查超时
            if timeout is not None and time.time() - start_time > timeout:
                raise MCPTimeoutError(f"命令执行超时（{timeout}秒）")
            
            # 解析JSON响应
            response = json.loads(resp_body_buffer.decode('utf-8'))
            
            # 检查是否有错误返回
            if 'error' in response:
                error_msg = str(response['error'])
                raise MCPCommandError(error_msg)
            if 'result' in response:
                return response['result']
                
            return response
        
        except json.JSONDecodeError:
            raise MCPCommandError("从CE接收到无效JSON")
        except Exception as e:
            if isinstance(e, (MCPConnectionError, MCPCommandError, MCPTimeoutError)):
                raise
            raise MCPCommandError(f"请求处理失败: {str(e)}")
    
    def ping(self) -> Dict[str, Any]:
        """
        检查连接性和获取版本信息。
        
        Returns:
            连接状态和版本信息
        """
        return self.send_command("ping")
    
    def __enter__(self) -> "MCPBridgeClient":
        """进入上下文管理器，自动连接。"""
        if not self.handle and not self.connect():
            raise MCPConnectionError("无法连接到Cheat Engine桥接")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文管理器，自动关闭连接。"""
        self.close()


class MCPConnectionPool:
    """MCP连接池，用于管理多个MCP连接。"""
    
    def __init__(self, pool_size: int = 5, min_size: int = 2, pipe_name: str = r"\\.\\pipe\\CE_MCP_Bridge_v99", max_idle_time: float = 300.0, health_check_interval: float = 30.0):
        """
        初始化连接池。
        
        Args:
            pool_size: 连接池最大大小
            min_size: 连接池最小大小
            pipe_name: 管道名称
            max_idle_time: 连接最大空闲时间（秒）
            health_check_interval: 健康检查间隔（秒）
        """
        self.pool_size = pool_size
        self.min_size = min_size
        self.pipe_name = pipe_name
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.pool = []
        self.logger = get_logger(__name__)
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "borrowed_connections": 0,
            "failed_connections": 0,
            "retries": 0
        }
        self.last_health_check = time.time()
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """初始化连接池。"""
        self.logger.info(f"初始化MCP连接池，大小: {self.pool_size}, 最小大小: {self.min_size}")
        # 确保连接池至少有min_size个连接
        while len(self.pool) < self.min_size:
            client = self._create_connection()
            if client:
                self.pool.append(client)
        
        self.logger.info(f"连接池初始化完成，可用连接数: {len(self.pool)}")
        self._update_stats()
    
    def _create_connection(self) -> Optional[MCPBridgeClient]:
        """
        创建一个新的连接。
        
        Returns:
            MCPBridgeClient实例，如果创建失败则返回None
        """
        try:
            client = MCPBridgeClient(self.pipe_name)
            if client.connect():
                # 添加连接创建时间和最后使用时间
                client.created_at = time.time()
                client.last_used = time.time()
                self.stats["total_connections"] += 1
                return client
            else:
                self.stats["failed_connections"] += 1
                return None
        except Exception as e:
            self.logger.error(f"创建连接失败: {e}")
            self.stats["failed_connections"] += 1
            return None
    
    def _is_connection_healthy(self, client: MCPBridgeClient) -> bool:
        """
        检查连接是否健康。
        
        Args:
            client: MCPBridgeClient实例
            
        Returns:
            如果连接健康则返回True，否则返回False
        """
        try:
            # 使用ping命令检查连接是否健康
            client.ping()
            return True
        except Exception as e:
            self.logger.warning(f"连接健康检查失败: {e}")
            return False
    
    def _update_stats(self) -> None:
        """更新连接池统计信息。"""
        self.stats["idle_connections"] = len(self.pool)
        self.stats["active_connections"] = self.stats["total_connections"] - self.stats["idle_connections"]
    
    def _check_health(self) -> None:
        """执行连接池健康检查。"""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return
        
        self.logger.debug("执行连接池健康检查...")
        self.last_health_check = current_time
        
        # 检查所有连接
        healthy_connections = []
        for client in self.pool:
            # 检查连接是否超时
            if current_time - client.last_used > self.max_idle_time:
                self.logger.info(f"关闭空闲超时连接")
                client.close()
                continue
            
            # 检查连接是否健康
            if self._is_connection_healthy(client):
                healthy_connections.append(client)
            else:
                self.logger.info(f"关闭不健康连接")
                client.close()
        
        # 更新连接池
        self.pool = healthy_connections
        
        # 确保连接池至少有min_size个连接
        self._initialize_pool()
        self._update_stats()
    
    def get_connection(self, timeout: Optional[float] = None, max_retries: int = 3) -> MCPBridgeClient:
        """
        从连接池获取一个连接。
        
        Args:
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            
        Returns:
            MCPBridgeClient实例
            
        Raises:
            MCPConnectionError: 如果没有可用连接
        """
        start_time = time.time()
        retries = 0
        
        while True:
            # 执行健康检查
            self._check_health()
            
            if self.pool:
                # 获取连接
                client = self.pool.pop()
                
                # 再次检查连接是否健康
                if self._is_connection_healthy(client):
                    client.last_used = time.time()
                    self.stats["borrowed_connections"] += 1
                    self._update_stats()
                    return client
                else:
                    self.logger.warning(f"获取到不健康连接，关闭并尝试下一个")
                    client.close()
                    self.stats["failed_connections"] += 1
            
            # 检查是否超时
            if timeout is not None and time.time() - start_time > timeout:
                raise MCPTimeoutError(f"获取连接超时（{timeout}秒）")
            
            # 检查是否达到最大重试次数
            retries += 1
            if retries > max_retries:
                raise MCPConnectionError(f"无法从连接池获取连接，已重试 {max_retries} 次")
            
            # 智能重试机制：基于重试次数调整延迟
            delay = min(1.0 * (2 ** (retries - 1)), 5.0)  # 指数退避，最大延迟5秒
            self.logger.warning(f"连接池为空，{delay}秒后重试... (尝试 {retries}/{max_retries})")
            self.stats["retries"] += 1
            time.sleep(delay)
            
            # 尝试创建新连接
            self.logger.info(f"尝试创建新连接...")
            new_client = self._create_connection()
            if new_client:
                new_client.last_used = time.time()
                self.stats["borrowed_connections"] += 1
                self._update_stats()
                return new_client
    
    def return_connection(self, client: MCPBridgeClient) -> None:
        """
        将连接返回给连接池。
        
        Args:
            client: MCPBridgeClient实例
        """
        try:
            # 检查连接是否健康
            if self._is_connection_healthy(client):
                # 更新最后使用时间
                client.last_used = time.time()
                
                # 检查连接池是否已满
                if len(self.pool) < self.pool_size:
                    self.pool.append(client)
                else:
                    # 连接池已满，关闭多余连接
                    self.logger.info(f"连接池已满，关闭多余连接")
                    client.close()
            else:
                # 连接不健康，直接关闭
                self.logger.info(f"返回不健康连接，直接关闭")
                client.close()
        except Exception as e:
            self.logger.error(f"返回连接时出错: {e}")
            client.close()
        
        self._update_stats()
    
    def close(self) -> None:
        """关闭连接池中的所有连接。"""
        self.logger.info(f"关闭连接池，共 {len(self.pool)} 个连接")
        for client in self.pool:
            try:
                client.close()
            except Exception as e:
                self.logger.error(f"关闭连接时出错: {e}")
        self.pool.clear()
        self._update_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取连接池统计信息。
        
        Returns:
            连接池统计信息
        """
        return self.stats.copy()
    
    def __enter__(self) -> "MCPConnectionPool":
        """进入上下文管理器。"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文管理器，关闭所有连接。"""
        self.close()


# 创建全局MCP客户端实例
mcp_client = MCPBridgeClient()
