#!/usr/bin/env python3
"""
全面 MCP 桥接测试套件 v3
=======================================
增强的测试套件包括:
- 数据正确性验证（不仅仅是成功/失败）
- 正确的代码地址测试（使用模块入口点，而不是头部数据）
- 架构验证（32/64位检测）
- 带清理的断点测试
- 正确的跳过(SKIPPED)与通过(PASSED)区分
- analyze_function 和 find_call_references 测试

此测试套件旨在对 MCP 桥接可靠性提供 100% 的信心.
"""

import win32file
import win32pipe
import struct
import json
import time
import sys
from typing import Optional, Dict, Any, Tuple, List, Callable

PIPE_NAME = r"\\.\pipe\CE_MCP_Bridge_v99"

class TestResult:
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class MCPTestClient:
    def __init__(self):
        self.handle = None
        self.request_id = 0
        
    def connect(self) -> bool:
        try:
            self.handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            print(f"✓ 连接到 {PIPE_NAME}")
            return True
        except Exception as e:
            print(f"✗ 连接失败: {e}")
            return False
    
    def send_command(self, method: str, params: Optional[dict] = None) -> dict:
        if params is None:
            params = {}
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.request_id
        }
        
        # 将请求序列化为JSON并编码为字节
        data = json.dumps(request)
        if isinstance(data, str):
            data = data.encode('utf-8')
        header = struct.pack('<I', len(data))
        win32file.WriteFile(self.handle, header + data)
        
        _, resp_header = win32file.ReadFile(self.handle, 4)
        resp_len = struct.unpack('<I', resp_header)[0]
        _, resp_data = win32file.ReadFile(self.handle, resp_len)
        
        return json.loads(resp_data.decode('utf-8'))
    
    def close(self):
        if self.handle:
            win32file.CloseHandle(self.handle)


# ============================================================================
# 验证助手
# ============================================================================

def validate_hex_address(value: str) -> bool:
    """验证字符串是否为有效的十六进制地址 (0x...)"""
    if not isinstance(value, str):
        return False
    if not value.startswith("0x") and not value.startswith("0X"):
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False

def validate_bytes_match_data(bytes_array: list, data_string: str) -> bool:
    """验证字节数组是否匹配空格分隔的十六进制数据字符串"""
    expected_bytes = [int(b, 16) for b in data_string.split()]
    return bytes_array == expected_bytes

def validate_integer_in_range(value: int, min_val: int, max_val: int) -> bool:
    """验证整数是否在预期范围内"""
    return isinstance(value, int) and min_val <= value <= max_val


# ============================================================================
# 测试框架
# ============================================================================

class TestCase:
    """表示具有验证功能的单个测试用例"""
    def __init__(self, name: str, method: str, params: dict = None,
                 validators: List[Callable] = None, skip_reason: str = None):
        self.name = name
        self.method = method
        self.params = params or {}
        self.validators = validators or []
        self.skip_reason = skip_reason
        self.result = None
        self.response = None
        self.error = None
        self.validation_errors = []
    
    def run(self, client: MCPTestClient) -> str:
        """运行测试并返回结果状态"""
        print(f"\n{'='*60}")
        print(f"测试: {self.name}")
        print(f"{'='*60}")
        
        if self.skip_reason:
            print(f"⊘ 已跳过: {self.skip_reason}")
            self.result = TestResult.SKIPPED
            return self.result
        
        try:
            raw_result = client.send_command(self.method, self.params)
            
            # 检查协议级错误
            if "error" in raw_result and raw_result["error"]:
                self.error = raw_result['error']
                print(f"✗ 协议错误: {self.error}")
                self.result = TestResult.FAILED
                return self.result
            
            self.response = raw_result.get("result", {})
            
            # 检查命令级失败
            if self.response.get("success") == False:
                # 检查这是否是预期的失败（如"未附加进程"）
                error_msg = self.response.get('error', '未知错误')
                self.error = error_msg
                print(f"✗ 命令失败: {error_msg}")
                self.result = TestResult.FAILED
                return self.result
            
            # 运行验证器
            self.validation_errors = []
            for validator in self.validators:
                try:
                    valid, msg = validator(self.response)
                    if not valid:
                        self.validation_errors.append(msg)
                except Exception as e:
                    self.validation_errors.append(f"验证器异常: {e}")
            
            # 打印响应（截断）
            resp_str = json.dumps(self.response, indent=2)
            if len(resp_str) > 500:
                resp_str = resp_str[:500] + "\n  ... (已截断)"
            print(f"响应: {resp_str}")
            
            if self.validation_errors:
                print(f"✗ 验证失败:")
                for err in self.validation_errors:
                    print(f"  - {err}")
                self.result = TestResult.FAILED
            else:
                print(f"✓ 通过")
                self.result = TestResult.PASSED
            
            return self.result
            
        except Exception as e:
            self.error = str(e)
            print(f"✗ 异常: {e}")
            self.result = TestResult.FAILED
            return self.result


# ============================================================================
# 验证器工厂
# ============================================================================

def has_field(field: str, field_type: type = None):
    """验证器: 响应包含必需字段"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少必需字段: {field}"
        if field_type and not isinstance(resp[field], field_type):
            return False, f"字段 '{field}' 应为 {field_type.__name__}, 实际为 {type(resp[field]).__name__}"
        return True, ""
    return validator

def field_equals(field: str, expected):
    """验证器: 字段等于期望值"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少字段: {field}"
        if resp[field] != expected:
            return False, f"字段 '{field}' = {resp[field]}, 期望值 {expected}"
        return True, ""
    return validator

def field_in_range(field: str, min_val, max_val):
    """验证器: 数值字段在范围内"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少字段: {field}"
        val = resp[field]
        if not isinstance(val, (int, float)):
            return False, f"字段 '{field}' 不是数值类型"
        if not (min_val <= val <= max_val):
            return False, f"字段 '{field}' = {val}, 期望范围 [{min_val}, {max_val}]"
        return True, ""
    return validator

def field_is_hex_address(field: str):
    """验证器: 字段是有效的十六进制地址字符串"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少字段: {field}"
        if not validate_hex_address(resp[field]):
            return False, f"字段 '{field}' = {resp[field]}, 不是有效的十六进制地址"
        return True, ""
    return validator

def array_not_empty(field: str):
    """验证器: 数组字段不为空"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少字段: {field}"
        if not isinstance(resp[field], list):
            return False, f"字段 '{field}' 不是数组"
        if len(resp[field]) == 0:
            return False, f"字段 '{field}' 为空, 期望至少一个元素"
        return True, ""
    return validator

def array_min_length(field: str, min_len: int):
    """验证器: 数组有最小长度"""
    def validator(resp):
        if field not in resp:
            return False, f"缺少字段: {field}"
        if not isinstance(resp[field], list):
            return False, f"字段 '{field}' 不是数组"
        if len(resp[field]) < min_len:
            return False, f"字段 '{field}' 有 {len(resp[field])} 项, 期望 >= {min_len}"
        return True, ""
    return validator

def bytes_match_pattern(bytes_field: str, data_field: str):
    """验证器: 字节数组匹配数据字符串"""
    def validator(resp):
        if bytes_field not in resp:
            return False, f"缺少字段: {bytes_field}"
        if data_field not in resp:
            return False, f"缺少字段: {data_field}"
        if not validate_bytes_match_data(resp[bytes_field], resp[data_field]):
            return False, f"字节数组与数据字符串不匹配"
        return True, ""
    return validator

def mz_header_check():
    """验证器: 前两个字节是 'MZ' (0x4D, 0x5A) 表示 PE 头"""
    def validator(resp):
        if "bytes" not in resp:
            return False, "缺少 'bytes' 字段"
        bytes_arr = resp["bytes"]
        if len(bytes_arr) < 2:
            return False, "字节数不足以检查 MZ 头部"
        if bytes_arr[0] != 0x4D or bytes_arr[1] != 0x5A:
            return False, f"期望 MZ 头部 (4D 5A), 得到 {bytes_arr[0]:02X} {bytes_arr[1]:02X}"
        return True, ""
    return validator

def arch_is_valid():
    """验证器: 架构字段为 'x86' 或 'x64'"""
    def validator(resp):
        if "arch" not in resp:
            return False, "缺少 'arch' 字段"
        if resp["arch"] not in ["x86", "x64"]:
            return False, f"无效架构: {resp['arch']}, 期望 'x86' 或 'x64'"
        return True, ""
    return validator

def version_check(expected_prefix: str):
    """验证器: 版本以期望前缀开头"""
    def validator(resp):
        if "version" not in resp:
            return False, "缺少 'version' 字段"
        if not resp["version"].startswith(expected_prefix):
            return False, f"版本 '{resp['version']}' 不以 '{expected_prefix}' 开头"
        return True, ""
    return validator


# ============================================================================
# 主要测试套件
# ============================================================================

def main():
    print("=" * 70)
    print("MCP 桥接全面测试套件 v3")
    print("增强的数据验证和正确性检查")
    print("=" * 70)
    
    client = MCPTestClient()
    if not client.connect():
        sys.exit(1)
    
    all_tests: Dict[str, TestCase] = {}
    
    # =========================================================================
    # 类别 1: 基础和实用命令
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 1: 基础和实用命令")
    print("=" * 70)
    
    all_tests["ping"] = TestCase(
        "Ping", "ping",
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("version", str),
            version_check("11.4"),
            has_field("message", str),
            has_field("timestamp", int),
        ]
    )
    
    all_tests["get_process_info"] = TestCase(
        "获取进程信息", "get_process_info",
        validators=[
            has_field("success", bool),
            has_field("process_id", int),
            field_in_range("process_id", 1, 0xFFFFFFFF),  # 有效PID范围
        ]
    )
    
    all_tests["evaluate_lua_simple"] = TestCase(
        "执行Lua (2+2)", "evaluate_lua",
        params={"code": "return 2 + 2"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("result", str),
            field_equals("result", "4"),  # 精确结果验证!
        ]
    )
    
    all_tests["evaluate_lua_complex"] = TestCase(
        "执行Lua (getCEVersion)", "evaluate_lua",
        params={"code": "return getCEVersion()"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("result", str),
        ]
    )
    
    all_tests["evaluate_lua_targetIs64Bit"] = TestCase(
        "执行Lua (targetIs64Bit)", "evaluate_lua",
        params={"code": "return tostring(targetIs64Bit())"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("result", str),
            # 结果应为 "true" 或 "false"
            lambda r: (r.get("result") in ["true", "false"], 
                      f"期望 'true' 或 'false', 得到 '{r.get('result')}'"),
        ]
    )
    
    # 运行类别 1
    for test in ["ping", "get_process_info", "evaluate_lua_simple", "evaluate_lua_complex", "evaluate_lua_targetIs64Bit"]:
        all_tests[test].run(client)
    
    # 获取架构信息用于后续测试
    arch_result = client.send_command("evaluate_lua", {"code": "return tostring(targetIs64Bit())"})
    is_64bit = arch_result.get("result", {}).get("result") == "true"
    print(f"\n[目标架构: {'x64' if is_64bit else 'x86'}]")
    
    # =========================================================================
    # 类别 2: 内存扫描
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 2: 内存扫描")
    print("=" * 70)
    
    all_tests["scan_all"] = TestCase(
        "扫描全部 (值=1)", "scan_all",
        params={"value": 1, "type": "dword"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("count", int),
            field_in_range("count", 1, 100000000),  # 至少1个结果
        ]
    )
    
    all_tests["get_scan_results"] = TestCase(
        "获取扫描结果", "get_scan_results",
        params={"max": 5},
        validators=[
            has_field("success", bool),
            has_field("returned", int),
            has_field("results", list),
            array_not_empty("results"),
        ]
    )
    
    all_tests["aob_scan"] = TestCase(
        "AOB扫描 (MZ头部)", "aob_scan",
        params={"pattern": "4D 5A 90 00", "limit": 5},
        validators=[
            has_field("success", bool),
            has_field("count", int),
            has_field("addresses", list),
            array_not_empty("addresses"),
        ]
    )
    
    all_tests["search_string"] = TestCase(
        "搜索字符串 (test)", "search_string",
        params={"string": "test", "limit": 5},
        validators=[
            has_field("success", bool),
            has_field("count", int),
            has_field("addresses", list),
        ]
    )
    
    # 运行类别 2
    for test in ["scan_all", "get_scan_results", "aob_scan", "search_string"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 获取正确的测试地址
    # =========================================================================
    # 使用模块基址 (PE头部) 进行内存测试
    # 使用入口点 (代码) 进行反汇编/分析测试
    
    modules_result = client.send_command("enum_modules")
    module_base = None
    module_name = None
    
    if modules_result.get("result", {}).get("modules"):
        # 查找一个模块 (优先选择主可执行文件)
        for mod in modules_result["result"]["modules"]:
            module_base = int(mod["address"], 16) if isinstance(mod["address"], str) else mod["address"]
            module_name = mod["name"]
            break
    
    if module_base:
        print(f"\n[使用模块 '{module_name}' 位于 {hex(module_base)} 进行测试]")
    else:
        # 回退到 0x400000 (常见基址)
        module_base = 0x400000
        print(f"\n[使用回退地址 {hex(module_base)} 进行测试]")
    
    # =========================================================================
    # 类别 3: 内存读取 - 带数据验证
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 3: 内存读取 (带数据验证)")
    print("=" * 70)
    
    all_tests["read_memory"] = TestCase(
        "读取内存 (PE头部的16字节)", "read_memory",
        params={"address": module_base, "size": 16},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("bytes", list),
            has_field("data", str),
            has_field("size", int),
            field_equals("size", 16),
            mz_header_check(),  # 验证前2字节为 'MZ'
            bytes_match_pattern("bytes", "data"),  # 交叉验证字节与数据字符串
        ]
    )
    
    all_tests["read_integer_byte"] = TestCase(
        "读取整数 (字节) - 应为 0x4D (M)", "read_integer",
        params={"address": module_base, "type": "byte"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("value", int),
            field_equals("value", 0x4D),  # MZ头部的'M'
            has_field("type", str),
            field_equals("type", "byte"),
        ]
    )
    
    all_tests["read_integer_word"] = TestCase(
        "读取整数 (字) - 应为 0x5A4D (ZM小端序)", "read_integer",
        params={"address": module_base, "type": "word"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("value", int),
            field_equals("value", 0x5A4D),  # MZ小端序
            has_field("type", str),
            field_equals("type", "word"),
        ]
    )
    
    all_tests["read_integer_dword"] = TestCase(
        "读取整数 (双字)", "read_integer",
        params={"address": module_base, "type": "dword"},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("value", int),
            has_field("type", str),
            field_equals("type", "dword"),
        ]
    )
    
    all_tests["read_string"] = TestCase(
        "读取字符串 (MZ头部)", "read_string",
        params={"address": module_base, "max_length": 32},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("value", str),
            # 值应以"MZ"开头或包含它
            lambda r: ("MZ" in r.get("value", "") or r["value"].startswith("MZ"), 
                      f"期望 'MZ' 在值中, 得到 '{r.get('value')}'"),
        ]
    )
    
    # 运行类别 3
    for test in ["read_memory", "read_integer_byte", "read_integer_word", "read_integer_dword", "read_string"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 4: 反汇编和分析
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 4: 反汇编和分析")
    print("=" * 70)
    
    # 对于反汇编, 使用代码地址 (入口点), 而不是头部数据
    # 读取PE头部以查找入口点
    entry_point = None
    pe_offset_result = client.send_command("read_integer", {"address": module_base + 0x3C, "type": "dword"})
    if pe_offset_result.get("result", {}).get("success"):
        pe_offset = pe_offset_result["result"]["value"]
        entry_rva_result = client.send_command("read_integer", {"address": module_base + pe_offset + 0x28, "type": "dword"})
        if entry_rva_result.get("result", {}).get("success"):
            entry_rva = entry_rva_result["result"]["value"]
            entry_point = module_base + entry_rva
            print(f"[找到入口点在 {hex(entry_point)}]")
    
    if not entry_point:
        # 回退 - 只使用模块基址+一些偏移
        entry_point = module_base + 0x1000
        print(f"[使用回退代码地址 {hex(entry_point)}]")
    
    all_tests["disassemble"] = TestCase(
        "反汇编 (入口点的5条指令)", "disassemble",
        params={"address": entry_point, "count": 5},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("instructions", list),
            array_min_length("instructions", 1),
            # 每条指令应有地址, 字节, 指令字段
            lambda r: (all("address" in i and "bytes" in i and "instruction" in i 
                         for i in r.get("instructions", [])),
                       "指令缺少必需字段 (address, bytes, instruction)"),
        ]
    )
    
    all_tests["get_instruction_info"] = TestCase(
        "获取指令信息", "get_instruction_info",
        params={"address": entry_point},
        validators=[
            has_field("success", bool),
            field_equals("success", True),
            has_field("instruction", str),
            has_field("size", int),
            field_in_range("size", 1, 15),  # x86指令为1-15字节
            has_field("bytes", str),
        ]
    )
    
    all_tests["find_function_boundaries"] = TestCase(
        "查找函数边界", "find_function_boundaries",
        params={"address": entry_point},
        validators=[
            has_field("success", bool),
            # 注意: 可能找不到前言, 但应有架构字段
            arch_is_valid(),
        ]
    )
    
    all_tests["analyze_function"] = TestCase(
        "分析函数", "analyze_function",
        params={"address": entry_point},
        validators=[
            has_field("success", bool),
            # 注意: 可能无法找到函数开始, 但应返回适当的错误或架构
        ]
    )
    
    # 运行类别 4
    for test in ["disassemble", "get_instruction_info", "find_function_boundaries", "analyze_function"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 5: 引用查找
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 5: 引用查找")
    print("=" * 70)
    
    all_tests["find_references"] = TestCase(
        "查找引用", "find_references",
        params={"address": entry_point, "limit": 5},
        validators=[
            has_field("success", bool),
            arch_is_valid(),
            has_field("references", list),
            has_field("count", int),
        ]
    )
    
    all_tests["find_call_references"] = TestCase(
        "查找CALL引用", "find_call_references",
        params={"address": entry_point, "limit": 5},
        validators=[
            has_field("success", bool),
        ]
    )
    
    # 运行类别 5
    for test in ["find_references", "find_call_references"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 6: 断点 (带清理)
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 6: 断点")
    print("=" * 70)
    
    all_tests["list_breakpoints"] = TestCase(
        "列出断点", "list_breakpoints",
        validators=[
            has_field("success", bool),
            has_field("breakpoints", list),
            has_field("count", int),
        ]
    )
    
    all_tests["clear_all_breakpoints"] = TestCase(
        "清除所有断点", "clear_all_breakpoints",
        validators=[
            has_field("success", bool),
            has_field("removed", int),
        ]
    )
    
    # 运行类别 6 - 只是列出和清除 (安全操作)
    for test in ["list_breakpoints", "clear_all_breakpoints"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 7: 模块
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 7: 模块操作")
    print("=" * 70)
    
    all_tests["enum_modules"] = TestCase(
        "枚举模块", "enum_modules",
        validators=[
            has_field("success", bool),
            has_field("count", int),
            has_field("modules", list),
            # 如果附加了进程, 应至少有1个模块
        ]
    )
    
    all_tests["get_symbol_address"] = TestCase(
        "获取符号地址", "get_symbol_address",
        params={"symbol": hex(module_base)},
        validators=[
            has_field("success", bool),
        ]
    )
    
    all_tests["get_memory_regions"] = TestCase(
        "获取内存区域", "get_memory_regions",
        params={"max": 5},
        validators=[
            has_field("success", bool),
            has_field("regions", list),
            has_field("count", int),
        ]
    )
    
    # 运行类别 7
    for test in ["enum_modules", "get_symbol_address", "get_memory_regions"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 8: 高级分析工具
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 8: 高级分析工具")
    print("=" * 70)
    
    all_tests["get_thread_list"] = TestCase(
        "获取线程列表", "get_thread_list",
        validators=[
            has_field("success", bool),
            has_field("threads", list),
            array_not_empty("threads"),
        ]
    )
    
    all_tests["enum_memory_regions_full"] = TestCase(
        "枚举内存区域完整版 (原生API)", "enum_memory_regions_full",
        params={"max": 10},
        validators=[
            has_field("success", bool),
            has_field("regions", list),
            has_field("count", int),
        ]
    )
    
    all_tests["dissect_structure"] = TestCase(
        "解构结构 (自动猜测)", "dissect_structure",
        params={"address": hex(module_base), "size": 64},
        validators=[
            has_field("success", bool),
            has_field("base_address", str),
            has_field("size_analyzed", int),
        ]
    )
    
    all_tests["read_pointer_chain"] = TestCase(
        "读取指针链", "read_pointer_chain",
        params={"base": hex(module_base), "offsets": [0x3C]},
        validators=[
            has_field("success", bool),
            has_field("base", str),
            has_field("chain", list),
            has_field("final_address", str),
            field_is_hex_address("final_address"),
        ]
    )
    
    all_tests["auto_assemble"] = TestCase(
        "自动汇编 (安全分配)", "auto_assemble",
        params={"script": "globalalloc(mcp_test_region_v3,4)"},
        validators=[
            has_field("success", bool),
            has_field("executed", bool),
        ]
    )
    
    all_tests["get_rtti_classname"] = TestCase(
        "获取RTTI类名", "get_rtti_classname",
        params={"address": hex(module_base)},
        validators=[
            has_field("success", bool),
            # RTTI可能找不到, 但应有'found'字段
            has_field("found", bool),
        ]
    )
    
    all_tests["get_address_info"] = TestCase(
        "获取地址信息", "get_address_info",
        params={"address": hex(module_base)},
        validators=[
            has_field("success", bool),
            has_field("address", str),
        ]
    )
    
    all_tests["checksum_memory"] = TestCase(
        "校验内存 (MD5)", "checksum_memory",
        params={"address": hex(module_base), "size": 256},
        validators=[
            has_field("success", bool),
            has_field("md5_hash", str),
            # MD5哈希应为32个十六进制字符
            lambda r: (len(r.get("md5_hash", "")) == 32, 
                      f"MD5哈希应为32个字符, 得到 {len(r.get('md5_hash', ''))}"),
        ]
    )
    
    all_tests["generate_signature"] = TestCase(
        "生成签名 (AOB)", "generate_signature",
        params={"address": hex(entry_point)},
        skip_reason="getUniqueAOB扫描所有内存 (阻塞, 可能需要几分钟)"
    )
    
    # 运行类别 8
    for test in ["get_thread_list", "enum_memory_regions_full", "dissect_structure", 
                 "read_pointer_chain", "auto_assemble", "get_rtti_classname", 
                 "get_address_info", "checksum_memory", "generate_signature"]:
        all_tests[test].run(client)
    
    # =========================================================================
    # 类别 9: DBVM管理程序工具
    # =========================================================================
    print("\n" + "=" * 70)
    print("类别 9: DBVM管理程序工具 (Ring -1)")
    print("=" * 70)
    print("注意: 这些需要在CE中加载DBVM/DBK驱动.")
    
    all_tests["get_physical_address"] = TestCase(
        "获取物理地址", "get_physical_address",
        params={"address": hex(module_base)},
        validators=[
            has_field("success", bool),
            has_field("virtual_address", str),
            # 成功时应存在物理地址
            lambda r: (not r.get("success") or "physical_address" in r,
                      "成功时缺少物理地址"),
        ]
    )
    
    # 首先运行get_physical_address以检查DBVM是否可用
    all_tests["get_physical_address"].run(client)
    
    # 根据物理地址测试检查DBVM是否可用
    dbvm_available = (all_tests["get_physical_address"].result == TestResult.PASSED and 
                      all_tests["get_physical_address"].response.get("success"))
    
    if dbvm_available:
        print(f"\n[检测到DBVM - 运行完整DBVM监控测试并清理]")
        
        # 使用读取地址 (模块基址) 进行安全监控
        # 读取监控比写入监控更安全
        dbvm_test_addr = hex(module_base)
        
        all_tests["start_dbvm_watch"] = TestCase(
            "开始DBVM监控 (读取模式)", "start_dbvm_watch",
            params={"address": dbvm_test_addr, "mode": "r"},
            validators=[
                has_field("success", bool),
                # 如果成功, 应有watch_id和状态
                lambda r: (not r.get("success") or "watch_id" in r,
                          "成功时缺少watch_id"),
                lambda r: (not r.get("success") or r.get("status") == "monitoring",
                          f"期望状态 'monitoring', 得到 '{r.get('status')}'"),
            ]
        )
        
        all_tests["start_dbvm_watch"].run(client)
        
        # 无论开始是否成功, 都要运行停止清理
        all_tests["stop_dbvm_watch"] = TestCase(
            "停止DBVM监控 (清理)", "stop_dbvm_watch",
            params={"address": dbvm_test_addr},
            validators=[
                has_field("success", bool),
                # 如果开始失败, 停止可能会失败, 这是正常的
            ]
        )
        
        all_tests["stop_dbvm_watch"].run(client)
        
    else:
        print(f"\n[未检测到DBVM - 跳过监控测试]")
        
        all_tests["start_dbvm_watch"] = TestCase(
            "开始DBVM监控", "start_dbvm_watch",
            params={"address": hex(module_base), "mode": "w"},
            skip_reason="DBVM未加载 (get_physical_address失败)"
        )
        
        all_tests["stop_dbvm_watch"] = TestCase(
            "停止DBVM监控", "stop_dbvm_watch",
            params={"address": hex(module_base)},
            skip_reason="DBVM未加载 (无活动监控)"
        )
        
        all_tests["start_dbvm_watch"].run(client)
        all_tests["stop_dbvm_watch"].run(client)
    
    # =========================================================================
    # 汇总
    # =========================================================================
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    
    passed = sum(1 for t in all_tests.values() if t.result == TestResult.PASSED)
    failed = sum(1 for t in all_tests.values() if t.result == TestResult.FAILED)
    skipped = sum(1 for t in all_tests.values() if t.result == TestResult.SKIPPED)
    total = len(all_tests)
    
    categories = {
        "基础和实用": ["ping", "get_process_info", "evaluate_lua_simple", "evaluate_lua_complex", "evaluate_lua_targetIs64Bit"],
        "扫描": ["scan_all", "get_scan_results", "aob_scan", "search_string"],
        "内存读取": ["read_memory", "read_integer_byte", "read_integer_word", "read_integer_dword", "read_string"],
        "反汇编": ["disassemble", "get_instruction_info", "find_function_boundaries", "analyze_function"],
        "引用": ["find_references", "find_call_references"],
        "断点": ["list_breakpoints", "clear_all_breakpoints"],
        "模块": ["enum_modules", "get_symbol_address", "get_memory_regions"],
        "高级": ["get_thread_list", "enum_memory_regions_full", "dissect_structure", "read_pointer_chain", 
                      "auto_assemble", "get_rtti_classname", "get_address_info", "checksum_memory", "generate_signature"],
        "DBVM": ["get_physical_address", "start_dbvm_watch", "stop_dbvm_watch"],
    }
    
    for cat_name, tests in categories.items():
        cat_passed = sum(1 for t in tests if all_tests.get(t) and all_tests[t].result == TestResult.PASSED)
        cat_failed = sum(1 for t in tests if all_tests.get(t) and all_tests[t].result == TestResult.FAILED)
        cat_skipped = sum(1 for t in tests if all_tests.get(t) and all_tests[t].result == TestResult.SKIPPED)
        cat_total = len(tests)
        print(f"\n{cat_name}: {cat_passed}/{cat_total - cat_skipped} 通过" + (f" ({cat_skipped} 跳过)" if cat_skipped else ""))
        for test in tests:
            if test in all_tests:
                t = all_tests[test]
                if t.result == TestResult.PASSED:
                    print(f"  ✓ {test}")
                elif t.result == TestResult.SKIPPED:
                    print(f"  ⊘ {test} (跳过)")
                else:
                    print(f"  ✗ {test}")
                    if t.validation_errors:
                        for err in t.validation_errors[:2]:  # 显示前2个错误
                            print(f"      → {err}")
    
    print(f"\n{'='*70}")
    print(f"总计: {passed} 通过, {failed} 失败, {skipped} 跳过 (共 {total})")
    print(f"通过率: {100*passed//(total-skipped)}% (不包括跳过)")
    print(f"{'='*70}")
    
    if failed == 0:
        print("\n🎉 所有测试通过! MCP桥接完全功能正常并已验证.")
    elif failed <= 2:
        print(f"\n✅ 基本通过. {failed} 个测试失败 - 请查看上面.")
    else:
        print(f"\n⚠ {failed} 个测试失败. 请查看上面的错误.")
    
    client.close()
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
