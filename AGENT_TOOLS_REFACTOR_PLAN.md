# Cheat Engine AI Agent 工具模块重构方案

## 1. 重构目标与具体改进指标

### 1.1 核心目标
- **参数一致性**：确保客户端工具实现、SYSTEM_PROMPT.json和MCP_Server之间的参数完全一致
- **错误处理**：实现统一、可预测的错误处理机制
- **代码结构**：提高代码模块化、可维护性和可扩展性
- **性能优化**：优化工具调用性能，减少重复代码
- **维护性**：降低新增工具的开发复杂度
- **兼容性**：保持与现有系统的向后兼容性

### 1.2 具体改进指标
| 指标 | 现状 | 目标 | 改进幅度 |
|------|------|------|----------|
| 参数不一致率 | >10% | 0% | 100% 消除 |
| 错误处理覆盖率 | <50% | >95% | 90%+ 提升 |
| 代码重复率 | >30% | <10% | 67% 降低 |
| 工具开发效率 | 低（需手动实现所有逻辑） | 高（使用模板和装饰器） | 50%+ 提升 |
| 性能（平均响应时间） | 基准 | 基准的1.2倍 | 20% 提升 |
| 维护成本（代码行数） | 约3000行 | 约2000行 | 33% 减少 |

## 2. 新的工具调用流程设计

### 2.1 总体流程
```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ 工具定义与注册 │────▶│ 参数验证与转换 │────▶│ 命令发送与超时 │────▶│ 结果解析与返回 │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

### 2.2 详细流程

#### 2.2.1 工具定义与注册
- 使用装饰器`@tool()`定义工具元数据和实现
- 自动注册到工具注册表，无需手动调用注册函数
- 支持参数类型提示和默认值

```python
@tool(name="scan_all", category=ToolCategory.PATTERN_SCAN,
      description="扫描所有内存区域以查找特定值")
def scan_all_impl(mcp_client, value: str, type: str = "exact", protection: str = "+W-C"):
    return mcp_client.send_command("scan_all", {
        "value": value,
        "type": type,
        "protection": protection
    })
```

#### 2.2.2 参数验证与转换
- 自动验证必填参数是否存在
- 自动转换参数类型（如字符串地址转整数）
- 验证参数值是否符合预期范围或格式

```python
# 自动将address参数从字符串转换为整数
@tool(name="read_memory")
def read_memory_impl(mcp_client, address: int, size: int = 256):
    return mcp_client.send_command("read_memory", {
        "address": address,
        "size": size
    })
```

#### 2.2.3 命令发送与超时
- 统一的MCP命令发送接口
- 为不同类型的工具设置合理的超时时间
- 支持异步命令发送（可选）

```python
# 自动为扫描工具设置较长超时
@tool(name="scan_all", timeout=300)
def scan_all_impl(mcp_client, value: str, type: str = "exact", protection: str = "+W-C"):
    return mcp_client.send_command("scan_all", {
        "value": value,
        "type": type,
        "protection": protection
    })
```

#### 2.2.4 结果解析与返回
- 统一的结果解析逻辑
- 标准化错误格式
- 支持不同类型结果的自动解析

## 3. 与MCP_Server的接口适配方案

### 3.1 接口一致性保障
- **参数映射**：建立客户端参数与MCP_Server参数的明确映射关系
- **类型转换**：自动处理不同类型参数的转换（如字符串地址转整数）
- **默认值统一**：确保默认参数值与MCP_Server一致

### 3.2 命令适配层设计
```python
class MCPCommandAdapter:
    """MCP命令适配层，负责将客户端参数转换为MCP_Server期望的格式"""
    
    @staticmethod
    def adapt_command(command_name: str, params: dict) -> dict:
        """根据命令名称适配参数格式"""
        adaptors = {
            "read_memory": lambda p: {
                "address": p["address"],
                "size": p["size"]
            },
            "scan_all": lambda p: {
                "value": p["value"],
                "type": p["type"],
                "protection": p["protection"]
            },
            # 其他命令的适配逻辑
        }
        
        if command_name in adaptors:
            return adaptors[command_name](params)
        return params
```

### 3.3 参数验证层
```python
class MCPParameterValidator:
    """MCP参数验证器，确保参数符合MCP_Server的要求"""
    
    @staticmethod
    def validate(command_name: str, params: dict) -> bool:
        """验证命令参数是否有效"""
        validators = {
            "scan_all": lambda p: (
                isinstance(p.get("value"), str) and
                p.get("type") in ["exact", "string", "array"] and
                isinstance(p.get("protection"), str)
            ),
            # 其他命令的验证逻辑
        }
        
        if command_name in validators:
            return validators[command_name](params)
        return True
```

## 4. 文件结构调整与模块划分

### 4.1 新的文件结构
```
Agent/tools/
├── __init__.py              # 模块初始化和导出
├── base/                   # 基础模块
│   ├── __init__.py
│   ├── tool_registry.py    # 工具注册表
│   ├── tool_executor.py    # 工具执行器
│   ├── result_parser.py    # 结果解析器
│   └── decorators.py       # 工具装饰器
├── core/                   # 核心功能
│   ├── __init__.py
│   ├── mcp_client.py       # MCP客户端
│   ├── command_adapter.py  # 命令适配层
│   └── parameter_validator.py # 参数验证器
├── tools/                  # 具体工具实现
│   ├── __init__.py
│   ├── basic_tools.py      # 基础工具
│   ├── memory_tools.py     # 内存操作工具
│   ├── scan_tools.py       # 扫描工具
│   ├── debug_tools.py      # 调试工具
│   ├── dbvm_tools.py       # DBVM工具
│   └── process_tools.py    # 进程/模块工具
└── utils/                  # 工具函数
    ├── __init__.py
    ├── address_utils.py    # 地址处理工具
    ├── error_utils.py      # 错误处理工具
    └── type_utils.py       # 类型转换工具
```

### 4.2 模块职责划分
- **base/**：提供基础架构，包括工具注册表、执行器和装饰器
- **core/**：处理与MCP_Server的通信，包括命令适配和参数验证
- **tools/**：按功能类别实现具体工具
- **utils/**：提供通用工具函数，如地址处理、错误处理和类型转换

### 4.3 工具分类

| 类别 | 工具列表 |
|------|----------|
| 基础工具 | ping, evaluate_lua, auto_assemble |
| 内存工具 | read_memory, read_integer, read_string, read_pointer, read_pointer_chain, checksum_memory |
| 扫描工具 | scan_all, get_scan_results, aob_scan, search_string, generate_signature, get_memory_regions, enum_memory_regions_full |
| 调试工具 | disassemble, get_instruction_info, find_function_boundaries, analyze_function, find_references, find_call_references, dissect_structure |
| 断点工具 | set_breakpoint, set_data_breakpoint, remove_breakpoint, list_breakpoints, clear_all_breakpoints, get_breakpoint_hits |
| DBVM工具 | get_physical_address, start_dbvm_watch, stop_dbvm_watch, poll_dbvm_watch |
| 进程工具 | enum_modules, get_thread_list, get_symbol_address, get_address_info, get_process_info |

## 5. 错误处理机制设计

### 5.1 错误分类

| 错误类型 | 描述 | 示例 |
|----------|------|------|
| 参数错误 | 参数缺失、类型错误或值无效 | 缺少必填参数、地址格式错误 |
| 连接错误 | 无法连接到MCP服务器 | 管道不存在、连接超时 |
| 执行错误 | 命令执行过程中发生错误 | 内存读取失败、扫描超时 |
| 服务器错误 | MCP服务器返回错误 | 命令未找到、权限不足 |

### 5.2 错误处理流程

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ 捕获异常      │────▶│ 分类错误类型   │────▶│ 格式化错误信息 │────▶│ 返回标准错误   │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

### 5.3 错误格式标准化

```python
# 标准错误格式
error_response = {
    "success": False,
    "error": {
        "code": "PARAMETER_ERROR",  # 错误代码
        "message": "缺少必填参数: address",  # 错误信息
        "details": {
            "parameter": "address",
            "expected_type": "integer"
        }  # 错误详情
    },
    "request_id": "uuid-12345",  # 请求ID
    "timestamp": 1234567890  # 时间戳
}
```

### 5.4 错误处理实现

```python
class MCPErrorHandler:
    """MCP错误处理程序，负责捕获、分类和格式化错误"""
    
    @staticmethod
    def handle_error(e: Exception, command_name: str, params: dict) -> dict:
        """处理MCP命令执行过程中的错误"""
        error_map = {
            ValueError: ("PARAMETER_ERROR", "参数值无效"),
            TypeError: ("PARAMETER_ERROR", "参数类型错误"),
            ConnectionError: ("CONNECTION_ERROR", "无法连接到MCP服务器"),
            TimeoutError: ("TIMEOUT_ERROR", "命令执行超时"),
            # 其他错误类型映射
        }
        
        error_type = type(e)
        code, message = error_map.get(error_type, ("UNKNOWN_ERROR", "未知错误"))
        
        return {
            "success": False,
            "error": {
                "code": code,
                "message": f"{message}: {str(e)}",
                "details": {
                    "command": command_name,
                    "parameters": params
                }
            }
        }
```

## 6. 性能优化策略

### 6.1 连接池管理
- 实现MCP客户端连接池，减少连接建立和关闭的开销
- 支持连接复用和自动重连

### 6.2 异步工具执行
- 支持异步工具执行，提高并发处理能力
- 使用asyncio实现非阻塞工具调用

### 6.3 超时优化
- 根据工具类型设置合理的超时时间
- 实现自适应超时机制，根据历史执行时间调整超时设置

### 6.4 缓存机制
- 对频繁访问但不常变化的数据进行缓存
- 支持缓存失效策略

### 6.5 批量处理
- 支持批量工具调用，减少通信开销
- 实现工具调用的并行执行

## 7. 向后兼容性保障措施

### 7.1 接口兼容
- 保持现有工具名称和参数不变
- 支持旧的工具调用方式
- 提供兼容层，自动转换旧格式的参数

### 7.2 配置兼容
- 保持SYSTEM_PROMPT.json的格式不变
- 支持自动更新SYSTEM_PROMPT.json以适应新的工具定义

### 7.3 迁移策略
- 逐步迁移现有工具到新的实现
- 提供迁移工具，自动转换旧的工具实现到新格式
- 支持混合使用新旧工具实现

## 8. 实现步骤

### 8.1 阶段1：基础架构搭建（1-2天）
1. 创建新的文件结构
2. 实现工具注册表和装饰器
3. 实现命令适配层和参数验证层
4. 实现统一的错误处理机制

### 8.2 阶段2：核心功能实现（2-3天）
1. 实现MCP客户端连接池
2. 实现工具执行器的新功能
3. 实现结果解析器
4. 实现基础工具的新实现

### 8.3 阶段3：工具迁移（3-4天）
1. 迁移内存工具到新实现
2. 迁移扫描工具到新实现
3. 迁移调试工具到新实现
4. 迁移断点工具到新实现
5. 迁移DBVM工具到新实现
6. 迁移进程工具到新实现

### 8.4 阶段4：测试和优化（2-3天）
1. 单元测试各个模块
2. 集成测试工具调用流程
3. 性能测试和优化
4. 兼容性测试

### 8.5 阶段5：部署和文档（1-2天）
1. 更新文档
2. 部署新的工具模块
3. 提供迁移指南

## 9. 测试验证方法及验收标准

### 9.1 单元测试
- 测试工具注册表的注册和查找功能
- 测试命令适配层的参数转换功能
- 测试参数验证器的验证功能
- 测试错误处理程序的错误分类和格式化功能

### 9.2 集成测试
- 测试完整的工具调用流程
- 测试参数一致性
- 测试错误处理的完整性
- 测试性能优化效果

### 9.3 验收标准
1. **参数一致性**：所有工具的参数与MCP_Server完全一致
2. **错误处理**：95%以上的错误场景得到正确处理
3. **性能**：工具调用性能提升20%以上
4. **兼容性**：现有代码无需修改即可使用新的工具模块
5. **维护性**：新增工具的开发时间减少50%以上

### 9.4 测试用例

| 测试用例 | 预期结果 |
|----------|----------|
| 调用不存在的工具 | 返回工具未找到错误 |
| 缺少必填参数 | 返回参数错误 |
| 参数类型错误 | 返回参数类型错误 |
| 连接失败 | 返回连接错误 |
| 执行超时 | 返回超时错误 |
| 服务器返回错误 | 返回服务器错误 |
| 成功执行工具 | 返回正确结果 |

## 10. 技术选型依据

### 10.1 装饰器模式
- **优点**：简化工具定义，减少样板代码，提高可读性
- **适用场景**：工具注册和元数据定义

### 10.2 工厂模式
- **优点**：统一创建对象，提高代码的灵活性和可维护性
- **适用场景**：命令适配和参数验证

### 10.3 连接池
- **优点**：减少连接开销，提高性能
- **适用场景**：MCP客户端管理

### 10.4 异步编程
- **优点**：提高并发处理能力，减少资源消耗
- **适用场景**：工具执行和命令发送

### 10.5 错误处理策略
- **优点**：统一错误处理，提高代码的可维护性
- **适用场景**：工具调用过程中的错误处理

## 11. 风险评估与应对措施

### 11.1 风险评估

| 风险 | 影响 | 可能性 | 应对措施 |
|------|------|--------|----------|
| 兼容性问题 | 现有代码无法使用新的工具模块 | 中 | 提供兼容层，保持接口不变 |
| 性能下降 | 新的实现比旧实现性能差 | 低 | 进行性能测试和优化 |
| 错误处理不完整 | 某些错误场景未得到处理 | 中 | 编写全面的测试用例 |
| 迁移困难 | 现有工具难以迁移到新实现 | 中 | 提供迁移工具和指南 |

### 11.2 应对措施
- **渐进式迁移**：逐步迁移工具，确保系统稳定性
- **全面测试**：编写单元测试、集成测试和性能测试
- **文档更新**：提供详细的文档和迁移指南
- **回滚机制**：支持快速回滚到旧版本

## 12. 结论

本重构方案旨在解决Cheat Engine AI Agent工具模块中存在的参数不一致、错误处理不完整、代码结构混乱等问题。通过采用模块化设计、统一的错误处理、性能优化和向后兼容性保障措施，将显著提高工具模块的可维护性、可扩展性和性能。

重构后的工具模块将具有以下特点：
- **参数一致性**：确保客户端、配置文件和服务器之间的参数完全一致
- **模块化设计**：按功能类别组织工具，提高代码的可维护性
- **统一接口**：提供统一的工具定义、注册和调用接口
- **高效执行**：优化工具调用性能，支持异步执行
- **全面错误处理**：统一的错误捕获、分类和格式化
- **向后兼容**：支持现有代码的无缝迁移

该重构方案将为Cheat Engine AI Agent的后续发展提供坚实的基础，使其能够更好地支持复杂的内存分析和逆向工程任务。