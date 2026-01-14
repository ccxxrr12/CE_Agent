import sys
import os

# ============================================================================
# 关键：为MCP修复Windows换行符（猴子补丁）
# MCP SDK的stdio_server在没有newline='\n'的情况下使用TextIOWrapper，
# 导致Windows输出CRLF（\r\n）而不是LF（\n）。这会导致错误：
# "invalid trailing data at the end of stream"
# 我们必须在导入FastMCP之前修补MCP SDK。
# ============================================================================

if sys.platform == "win32":
    import msvcrt
    from io import TextIOWrapper
    from contextlib import asynccontextmanager
    
    # 设置底层文件句柄的二进制模式
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    
    # 修补MCP SDK的stdio_server以使用newline='\n'
    import mcp.server.stdio as mcp_stdio
    import anyio
    import anyio.lowlevel
    from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
    import mcp.types as types
    from mcp.shared.message import SessionMessage
    
    @asynccontextmanager
    async def _patched_stdio_server(
        stdin: "anyio.AsyncFile[str] | None" = None,
        stdout: "anyio.AsyncFile[str] | None" = None,
    ):
        """修补的stdio_server，具有正确的Windows换行符处理。"""
        if not stdin:
            # 使用newline='\n'以防止Windows上的CRLF转换
            stdin = anyio.wrap_file(TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline='\n'))
        if not stdout:
            # 使用newline='\n'以防止Windows上的CRLF转换
            stdout = anyio.wrap_file(TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline='\n'))

        read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

        async def stdin_reader():
            try:
                async with read_stream_writer:
                    async for line in stdin:
                        try:
                            message = types.JSONRPCMessage.model_validate_json(line)
                        except Exception as exc:
                            await read_stream_writer.send(exc)
                            continue
                        session_message = SessionMessage(message)
                        await read_stream_writer.send(session_message)
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async def stdout_writer():
            try:
                async with write_stream_reader:
                    async for session_message in write_stream_reader:
                        json = session_message.message.model_dump_json(by_alias=True, exclude_none=True)
                        await stdout.write(json + "\n")
                        await stdout.flush()
            except anyio.ClosedResourceError:
                await anyio.lowlevel.checkpoint()

        async with anyio.create_task_group() as tg:
            tg.start_soon(stdin_reader)
            tg.start_soon(stdout_writer)
            yield read_stream, write_stream
    
    # 应用猴子补丁
    mcp_stdio.stdio_server = _patched_stdio_server

# ============================================================================
# MCP输出流保护
# MCP使用stdout进行JSON-RPC。任何杂散输出都会破坏它。
# ============================================================================

# 保存原始stdout供MCP使用
_mcp_stdout = sys.stdout

# 重定向stdout到stderr，以便任何意外打印都会转到日志，而不是MCP流
sys.stdout = sys.stderr

# 现在可以安全地导入可能在导入期间打印的库
import json
import struct
import time
import traceback

try:
    import win32file
    import win32pipe
    import win32con
    import pywintypes
    from mcp.server.fastmcp import FastMCP
    
    # 关键：还要修补fastmcp模块内的引用
    # FastMCP已经在我们的补丁之前导入了stdio_server，所以我们也需要更新它的引用
    if sys.platform == "win32":
        import mcp.server.fastmcp.server as fastmcp_server
        fastmcp_server.stdio_server = _patched_stdio_server
        
except ImportError as e:
    print(f"[MCP CE] 导入错误: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

# 导入完成后恢复stdout供MCP使用
sys.stdout = _mcp_stdout

# 调试助手 - 总是转到stderr，永远不会破坏MCP
def debug_log(msg):
    print(f"[MCP CE] {msg}", file=sys.stderr, flush=True)

# 辅助函数，将结果格式化为适当的JSON字符串供MCP工具使用
def format_result(result):
    """将CE桥接结果格式化为适当的JSON字符串供AI消费。"""
    if isinstance(result, dict):
        return json.dumps(result, indent=None, ensure_ascii=False)
    elif isinstance(result, str):
        return result  # 已经是字符串
    else:
        return json.dumps(result)

# ============================================================================
# 配置
# ============================================================================

# V11桥接使用'CE_MCP_Bridge_v99'
PIPE_NAME = r"\\.\pipe\CE_MCP_Bridge_v99"
MCP_SERVER_NAME = "cheatengine"
MAX_RETRIES = 3

# ============================================================================
# 管道客户端
# ============================================================================

class CEBridgeClient:
    def __init__(self):
        # 初始化管道句柄
        self.handle = None

    def connect(self):
        """尝试连接到CE命名管道。"""
        try:
            # 创建与Cheat Engine Lua脚本的命名管道连接
            self.handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            return True
        except pywintypes.error as e:
            # sys.stderr.write(f"[CEBridge] 连接错误: {e}\n")
            return False

    def send_command(self, method, params=None):
        """发送命令到CE桥接，失败时自动重连。"""
        max_retries = MAX_RETRIES
        last_error = None
        
        for attempt in range(max_retries):
            if not self.handle:
                if not self.connect():
                    raise ConnectionError("Cheat Engine桥接 (v11/v99) 未运行（找不到管道）。")

            # 构造JSON-RPC请求
            request = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": int(time.time() * 1000)  # 使用时间戳作为唯一ID
            }
            
            try:
                # 将请求序列化为JSON并编码为字节
                req_json = json.dumps(request).encode('utf-8')
                # 创建长度头（小端序）
                header = struct.pack('<I', len(req_json))
                
                # 发送长度头和JSON请求
                win32file.WriteFile(self.handle, header)
                win32file.WriteFile(self.handle, req_json)
                
                # 读取响应头（4字节长度）
                resp_header_buffer = win32file.ReadFile(self.handle, 4)[1]
                if len(resp_header_buffer) < 4:
                    self.close()
                    last_error = ConnectionError("来自CE的响应头不完整。")
                    continue  # 重试
                
                # 解析响应长度
                resp_len = struct.unpack('<I', resp_header_buffer)[0]
                
                # 检查响应大小是否过大
                if resp_len > 16 * 1024 * 1024: 
                    self.close()
                    raise ConnectionError(f"响应过大: {resp_len} 字节")

                # 读取响应体
                resp_body_buffer = win32file.ReadFile(self.handle, resp_len)[1]
                
                try:
                    # 解析JSON响应
                    response = json.loads(resp_body_buffer.decode('utf-8'))
                except json.JSONDecodeError:
                    self.close()
                    last_error = ConnectionError("从CE接收到无效JSON")
                    continue  # 重试
                
                # 检查是否有错误返回
                if 'error' in response:
                    return {"success": False, "error": str(response['error'])}
                if 'result' in response:
                    return response['result']
                    
                return response

            except pywintypes.error as e:
                # 发生通信错误，关闭连接
                self.close()
                last_error = ConnectionError(f"管道通信失败: {e}")
                if attempt < max_retries - 1:
                    continue  # 重试
        
        # 所有重试都失败
        if last_error:
            raise last_error
        raise ConnectionError("未知通信错误")

    def close(self):
        """关闭管道连接。"""
        if self.handle:
            try:
                win32file.CloseHandle(self.handle)
            except:
                pass
            self.handle = None

# 创建全局客户端实例
ce_client = CEBridgeClient()

# ============================================================================
# MCP服务器 - v11实现
# ============================================================================

mcp = FastMCP(MCP_SERVER_NAME)

# --- 进程和模块相关工具 ---

@mcp.tool()
def get_process_info() -> str:
    """获取当前进程ID、名称、模块计数和架构。"""
    return format_result(ce_client.send_command("get_process_info"))

@mcp.tool()
def enum_modules() -> str:
    """列出所有加载的模块(DLL)及其基地址和大小。"""
    return format_result(ce_client.send_command("enum_modules"))

@mcp.tool()
def get_thread_list() -> str:
    """获取附加进程中的线程列表。"""
    return format_result(ce_client.send_command("get_thread_list"))

@mcp.tool()
def get_symbol_address(symbol: str) -> str:
    """将符号名(例如'Engine.GameEngine')解析为地址。"""
    return format_result(ce_client.send_command("get_symbol_address", {"symbol": symbol}))

@mcp.tool()
def get_address_info(address: str, include_modules: bool = True, include_symbols: bool = True, include_sections: bool = False) -> str:
    """获取地址的符号名和模块信息(get_symbol_address的逆向操作)。"""
    return format_result(ce_client.send_command("get_address_info", {
        "address": address, 
        "include_modules": include_modules, 
        "include_symbols": include_symbols,
        "include_sections": include_sections
    }))

@mcp.tool()
def get_rtti_classname(address: str) -> str:
    """尝试使用运行时类型信息识别地址处对象的类名。"""
    return format_result(ce_client.send_command("get_rtti_classname", {"address": address}))

# --- 内存读取工具 ---

@mcp.tool()
def read_memory(address: str, size: int = 256) -> str:
    """从内存读取原始字节。"""
    return format_result(ce_client.send_command("read_memory", {"address": address, "size": size}))

@mcp.tool()
def read_integer(address: str, type: str = "dword") -> str:
    """从内存读取数字。类型: byte, word, dword, qword, float, double。"""
    return format_result(ce_client.send_command("read_integer", {"address": address, "type": type}))

@mcp.tool()
def read_string(address: str, max_length: int = 256, wide: bool = False) -> str:
    """从内存读取字符串(ASCII或宽/UTF-16)。"""
    return format_result(ce_client.send_command("read_string", {"address": address, "max_length": max_length, "wide": wide}))

@mcp.tool()
def read_pointer(address: str, offsets: list[int] = None) -> str:
    """读取指针链。返回最终地址和值。"""
    # V11支持简单的反引用'read_pointer'命令或用于多个偏移的'read_pointer_chain'
    if offsets:
        return format_result(ce_client.send_command("read_pointer_chain", {"base": address, "offsets": offsets}))
    else:
        return format_result(ce_client.send_command("read_pointer_chain", {"base": address, "offsets": [0]}))

@mcp.tool()
def read_pointer_chain(base: str, offsets: list[int]) -> str:
    """跟随多级指针链并返回每一步的分析。"""
    return format_result(ce_client.send_command("read_pointer_chain", {"base": base, "offsets": offsets}))

@mcp.tool()
def checksum_memory(address: str, size: int) -> str:
    """计算内存区域的MD5校验和以检测更改。"""
    return format_result(ce_client.send_command("checksum_memory", {"address": address, "size": size}))

# --- 扫描工具 ---

@mcp.tool()
def scan_all(value: str, type: str = "exact", protection: str = "+W-C") -> str:
    """统一内存扫描器。类型: exact, string, array。保护: +W-C (可写, 非写时复制)。"""
    return format_result(ce_client.send_command("scan_all", {"value": value, "type": type, "protection": protection}))

@mcp.tool()
def get_scan_results(max: int = 100) -> str:
    """获取上次'scan_all'操作的结果。使用'max'限制输出。"""
    return format_result(ce_client.send_command("get_scan_results", {"max": max}))

@mcp.tool()
def aob_scan(pattern: str, protection: str = "+X", limit: int = 100) -> str:
    """扫描字节数组(AOB)模式。示例: '48 89 5C 24'。"""
    return format_result(ce_client.send_command("aob_scan", {"pattern": pattern, "protection": protection, "limit": limit}))

@mcp.tool()
def search_string(string: str, wide: bool = False, limit: int = 100) -> str:
    """快速在内存中搜索文本字符串。"""
    return format_result(ce_client.send_command("search_string", {"string": string, "wide": wide, "limit": limit}))

@mcp.tool()
def generate_signature(address: str) -> str:
    """生成唯一AOB签名，可用于再次找到此特定地址。"""
    return format_result(ce_client.send_command("generate_signature", {"address": address}))

@mcp.tool()
def get_memory_regions(max: int = 100) -> str:
    """获取常见基址附近的有效内存区域列表。"""
    return format_result(ce_client.send_command("get_memory_regions", {"max": max}))

@mcp.tool()
def enum_memory_regions_full(max: int = 500) -> str:
    """枚举进程中的所有内存区域(原生EnumMemoryRegions)。"""
    return format_result(ce_client.send_command("enum_memory_regions_full", {"max": max}))

# --- 分析和反汇编工具 ---

@mcp.tool()
def disassemble(address: str, count: int = 20) -> str:
    """从地址开始反汇编指令。"""
    return format_result(ce_client.send_command("disassemble", {"address": address, "count": count}))

@mcp.tool()
def get_instruction_info(address: str) -> str:
    """获取单条指令的详细信息(大小、字节、操作码)。"""
    return format_result(ce_client.send_command("get_instruction_info", {"address": address}))

@mcp.tool()
def find_function_boundaries(address: str, max_search: int = 4096) -> str:
    """尝试找到包含地址的函数的开始和结束。"""
    return format_result(ce_client.send_command("find_function_boundaries", {"address": address, "max_search": max_search}))

@mcp.tool()
def analyze_function(address: str) -> str:
    """分析函数以找出所有CALL指令输出(此函数所做的调用)。"""
    return format_result(ce_client.send_command("analyze_function", {"address": address}))

@mcp.tool()
def find_references(address: str, limit: int = 50) -> str:
    """查找访问(引用)此地址的指令。"""
    return format_result(ce_client.send_command("find_references", {"address": address, "limit": limit}))

@mcp.tool()
def find_call_references(function_address: str, limit: int = 100) -> str:
    """查找调用此函数的所有位置。"""
    return format_result(ce_client.send_command("find_call_references", {"address": function_address, "limit": limit}))

@mcp.tool()
def dissect_structure(address: str, size: int = 256) -> str:
    """使用CE的自动猜测功能将地址处的内存解释为结构。"""
    return format_result(ce_client.send_command("dissect_structure", {"address": address, "size": size}))

# --- 调试和断点工具 ---

@mcp.tool()
def set_breakpoint(address: str, id: str = None, capture_registers: bool = True, capture_stack: bool = False, stack_depth: int = 16) -> str:
    """设置硬件执行断点。仅非中断/日志记录。"""
    return format_result(ce_client.send_command("set_breakpoint", {
        "address": address, 
        "id": id,
        "capture_registers": capture_registers,
        "capture_stack": capture_stack,
        "stack_depth": stack_depth
    }))

@mcp.tool()
def set_data_breakpoint(address: str, id: str = None, access_type: str = "w", size: int = 4) -> str:
    """设置硬件数据断点(监视点)。类型: 'r'(读取), 'w'(写入), 'rw'(访问)。"""
    return format_result(ce_client.send_command("set_data_breakpoint", {
        "address": address, 
        "id": id,
        "access_type": access_type,
        "size": size
    }))

@mcp.tool()
def remove_breakpoint(id: str) -> str:
    """按ID移除断点。"""
    return format_result(ce_client.send_command("remove_breakpoint", {"id": id}))

@mcp.tool()
def list_breakpoints() -> str:
    """列出所有活动断点。"""
    return format_result(ce_client.send_command("list_breakpoints"))

@mcp.tool()
def clear_all_breakpoints() -> str:
    """移除所有断点。"""
    return format_result(ce_client.send_command("clear_all_breakpoints"))

@mcp.tool()
def get_breakpoint_hits(id: str = None, clear: bool = False) -> str:
    """获取特定断点ID的命中次数(如果没有ID则获取全部)。设置clear=True刷新缓冲区。"""
    return format_result(ce_client.send_command("get_breakpoint_hits", {"id": id, "clear": clear}))

# --- DBVM / 虚拟机管理程序工具 (Ring -1) ---

@mcp.tool()
def get_physical_address(address: str) -> str:
    """将虚拟地址转换为物理地址(需要DBVM)。"""
    return format_result(ce_client.send_command("get_physical_address", {"address": address}))

@mcp.tool()
def start_dbvm_watch(address: str, mode: str = "w", max_entries: int = 1000) -> str:
    """启动隐形DBVM虚拟机管理程序监视。模式: 'w'(写入), 'r'(读取), 'x'(执行)。"""
    return format_result(ce_client.send_command("start_dbvm_watch", {"address": address, "mode": mode, "max_entries": max_entries}))

@mcp.tool()
def stop_dbvm_watch(address: str) -> str:
    """停止DBVM监视并返回结果。"""
    return format_result(ce_client.send_command("stop_dbvm_watch", {"address": address}))

@mcp.tool()
def poll_dbvm_watch(address: str, max_results: int = 1000) -> str:
    """轮询DBVM监视日志而不停止。返回每次执行命中的寄存器状态。"""
    return format_result(ce_client.send_command("poll_dbvm_watch", {
        "address": address, 
        "max_results": max_results
    }))

# --- 脚本和控制工具 ---

@mcp.tool()
def evaluate_lua(code: str) -> str:
    """在Cheat Engine中执行任意Lua代码。"""
    return format_result(ce_client.send_command("evaluate_lua", {"code": code}))

@mcp.tool()
def auto_assemble(script: str) -> str:
    """运行AutoAssembler脚本(注入、代码洞等)。"""
    return format_result(ce_client.send_command("auto_assemble", {"script": script}))

@mcp.tool()
def ping() -> str:
    """检查连接性和获取版本信息。"""
    return format_result(ce_client.send_command("ping"))

if __name__ == "__main__":
    try:
        debug_log("正在启动FastMCP服务器(v11/v99兼容)...")
        mcp.run()
    except Exception as e:
        debug_log(f"致命错误: {e}")
        traceback.print_exc(file=sys.stderr)