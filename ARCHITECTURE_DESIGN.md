# Cheat Engine AI Agent - 架构设计文档 v2.0

## 1. 概述

### 1.1 设计目标

构建一个智能代理系统，将 Ollama 本地大模型与 Cheat Engine 内存分析工具（MCP 服务器）深度集成，实现自动化内存分析任务。该系统应能够：

- **自主任务规划**：理解用户意图，自动分解复杂任务为可执行的子任务
- **智能工具选择**：根据任务需求自动选择合适的 MCP 工具
- **多步推理**：基于工具执行结果进行推理和决策
- **上下文管理**：维护任务执行的上下文和历史信息
- **错误恢复**：自动处理错误并尝试恢复
- **结果综合**：将多步执行结果综合成有意义的分析报告

### 1.2 核心价值

| 传统手动分析 | AI 智能代理 |
|------------|------------|
| 需要数天手动扫描和分析 | 数分钟自动完成 |
| 需要深入的逆向工程知识 | 自然语言交互即可使用 |
| 容易遗漏关键信息 | 全面系统分析 |
| 难以处理复杂任务链 | 自动规划任务链 |

### 1.3 典型应用场景

1. **数据包解密函数分析**
   - 扫描网络相关值
   - 设置断点跟踪数据包处理
   - 反汇编解密函数
   - 分析算法逻辑
   - 生成解密脚本

2. **玩家数据结构分析**
   - 扫描玩家相关值
   - 分析内存结构
   - 识别字段类型和含义
   - 生成结构定义

3. **操作码定位与分析**
   - 扫描特定功能相关值
   - 设置断点跟踪修改
   - 反汇编操作码函数
   - 分析工作原理
   - 生成训练器代码

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│  - 命令行界面 (CLI)                                              │
│  - 自然语言输入                                                  │
│  - 实时进度反馈                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI 代理核心层                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  任务规划器 (TaskPlanner)                                │   │
│  │  - 理解用户意图                                          │   │
│  │  - 分解复杂任务                                          │   │
│  │  - 生成执行计划                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  推理引擎 (ReasoningEngine)                              │   │
│  │  - 多步推理                                              │   │
│  │  - 决策制定                                              │   │
│  │  - 工具选择                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  上下文管理器 (ContextManager)                           │   │
│  │  - 维护执行历史                                          │   │
│  │  - 管理中间结果                                          │   │
│  │  - 状态跟踪                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  结果综合器 (ResultSynthesizer)                          │   │
│  │  - 整合多步结果                                          │   │
│  │  - 生成分析报告                                          │   │
│  │  - 提取关键洞察                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      工具执行层                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  工具注册表 (ToolRegistry)                              │   │
│  │  - 管理所有 MCP 工具                                     │   │
│  │  - 工具元数据                                            │   │
│  │  - 工具分类                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  工具执行器 (ToolExecutor)                               │   │
│  │  - 执行工具调用                                          │   │
│  │  - 错误处理                                              │   │
│  │  - 重试机制                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  结果解析器 (ResultParser)                               │   │
│  │  - 解析工具输出                                          │   │
│  │  - 数据验证                                              │   │
│  │  - 格式转换                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP 通信层                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MCP 客户端 (MCPClient)                                  │   │
│  │  - 命名管道通信                                          │   │
│  │  - JSON-RPC 协议                                         │   │
│  │  - 连接管理                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Cheat Engine MCP 服务器                         │
│  - 40+ 内存分析工具                                             │
│  - 命名管道接口                                                  │
│  - Lua 桥接脚本                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cheat Engine                                 │
│  - 内存访问                                                      │
│  - 断点管理                                                      │
│  - 反汇编                                                        │
│  - DBVM 监视                                                    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

#### 2.2.1 任务规划器 (TaskPlanner)

**职责**：
- 解析用户自然语言请求
- 识别任务类型和目标
- 分解复杂任务为子任务序列
- 生成可执行的计划

**输入**：
- 用户自然语言请求
- 可用工具列表
- 上下文信息

**输出**：
- 结构化的执行计划
- 子任务列表
- 预期工具调用序列

**示例**：
```
输入: "找到游戏的数据包解密函数并分析其算法"

输出:
{
  "task_type": "packet_decryption_analysis",
  "subtasks": [
    {
      "id": 1,
      "description": "扫描网络相关值",
      "tools": ["scan_all", "get_scan_results"],
      "expected_output": "网络相关地址列表"
    },
    {
      "id": 2,
      "description": "设置断点跟踪数据包处理",
      "tools": ["set_breakpoint", "get_breakpoint_hits"],
      "expected_output": "数据包处理函数地址"
    },
    {
      "id": 3,
      "description": "反汇编解密函数",
      "tools": ["disassemble", "analyze_function"],
      "expected_output": "解密函数汇编代码"
    },
    {
      "id": 4,
      "description": "分析算法逻辑",
      "tools": ["dissect_structure", "get_instruction_info"],
      "expected_output": "算法描述"
    },
    {
      "id": 5,
      "description": "生成解密脚本",
      "tools": ["evaluate_lua"],
      "expected_output": "Python 解密脚本"
    }
  ]
}
```

#### 2.2.2 推理引擎 (ReasoningEngine)

**职责**：
- 基于工具执行结果进行推理
- 决定下一步操作
- 处理异常情况
- 调整执行计划

**推理流程**：
1. 分析工具执行结果
2. 评估结果是否符合预期
3. 决定是否需要额外操作
4. 选择下一个工具或子任务
5. 处理错误和异常

**示例推理逻辑**：
```
当前状态: 扫描到 47 个网络相关地址
推理:
- 地址太多，需要缩小范围
- 设置数据断点跟踪写入操作
- 观察哪些地址被频繁写入
- 筛选出最可能的解密函数地址
```

#### 2.2.3 上下文管理器 (ContextManager)

**职责**：
- 维护任务执行历史
- 存储中间结果
- 跟踪执行状态
- 提供上下文查询

**数据结构**：
```python
class ExecutionContext:
    task_id: str
    user_request: str
    execution_plan: ExecutionPlan
    current_step: int
    history: List[ExecutionStep]
    intermediate_results: Dict[str, Any]
    state: TaskState
    
class ExecutionStep:
    step_id: int
    tool_name: str
    tool_args: Dict[str, Any]
    result: Any
    timestamp: datetime
    success: bool
    error: Optional[str]
```

#### 2.2.4 结果综合器 (ResultSynthesizer)

**职责**：
- 整合多步执行结果
- 生成结构化分析报告
- 提取关键洞察
- 格式化输出

**输出格式**：
```markdown
# 数据包解密函数分析报告

## 执行摘要
- 任务: 找到游戏的数据包解密函数并分析其算法
- 执行时间: 2分34秒
- 执行步骤: 5步
- 成功: 是

## 分析结果

### 1. 解密函数信息
- 函数地址: 0x12345678
- 函数名称: sub_12345678
- 模块: game.exe

### 2. 算法分析
- 算法类型: AES-128-CBC
- 密钥位置: [[game.exe+0x1000]+0x20]
- IV 位置: [[game.exe+0x1000]+0x30]

### 3. 关键代码片段
```
0x12345678: push ebp
0x12345679: mov ebp, esp
...
```

### 4. 生成的解密脚本
[decrypt_packet.py 代码]

## 执行步骤
1. ✅ 扫描网络相关值 - 找到47个地址
2. ✅ 设置断点跟踪 - 识别出3个候选函数
3. ✅ 反汇编分析 - 确认解密函数
4. ✅ 算法分析 - 识别为AES-128-CBC
5. ✅ 生成脚本 - 创建解密工具
```

#### 2.2.5 工具注册表 (ToolRegistry)

**职责**：
- 管理所有 MCP 工具
- 提供工具元数据
- 工具分类和索引
- 工具查询接口

**工具分类**：

| 类别 | 工具数量 | 示例工具 |
|------|---------|---------|
| 基础工具 | 5 | ping, get_process_info |
| 内存读取 | 6 | read_memory, read_integer, read_string, read_pointer, read_pointer_chain, checksum_memory |
| 模式扫描 | 7 | scan_all, get_scan_results, aob_scan, search_string, generate_signature, get_memory_regions, enum_memory_regions_full |
| 反汇编分析 | 7 | disassemble, get_instruction_info, find_function_boundaries, analyze_function, find_references, find_call_references, dissect_structure |
| 断点调试 | 6 | set_breakpoint, set_data_breakpoint, remove_breakpoint, list_breakpoints, clear_all_breakpoints, get_breakpoint_hits |
| DBVM工具 | 4 | get_physical_address, start_dbvm_watch, stop_dbvm_watch, poll_dbvm_watch |
| 进程模块 | 5 | get_process_info, enum_modules, get_thread_list, get_symbol_address, get_address_info |
| 脚本控制 | 3 | evaluate_lua, auto_assemble, ping |

**工具元数据结构**：
```python
class ToolMetadata:
    name: str
    category: str
    description: str
    parameters: List[Parameter]
    destructive: bool
    requires_approval: bool
    examples: List[str]
    
class Parameter:
    name: str
    type: str
    required: bool
    default: Any
    description: str
```

#### 2.2.6 工具执行器 (ToolExecutor)

**职责**：
- 执行工具调用
- 错误处理和重试
- 超时控制
- 结果验证

**执行流程**：
1. 验证工具参数
2. 检查权限（破坏性操作）
3. 执行工具调用
4. 处理错误和重试
5. 验证结果
6. 返回结果

**重试策略**：
- 网络错误：最多3次重试
- 临时错误：指数退避
- 权限错误：不重试
- 参数错误：不重试

#### 2.2.7 结果解析器 (ResultParser)

**职责**：
- 解析工具输出
- 数据验证
- 格式转换
- 错误提取

**支持的输出格式**：
- JSON
- 文本
- 二进制数据
- 混合格式

#### 2.2.8 MCP 客户端 (MCPClient)

**职责**：
- 命名管道通信
- JSON-RPC 协议处理
- 连接管理
- 错误处理

**通信流程**：
1. 连接到命名管道
2. 发送 JSON-RPC 请求
3. 接收响应
4. 解析结果
5. 处理错误

## 3. 核心工作流程

### 3.1 完整执行流程

```
1. 用户输入
   ↓
2. 任务规划器解析请求
   ↓
3. 生成执行计划
   ↓
4. 推理引擎开始执行
   ↓
5. 循环执行子任务:
   a. 选择工具
   b. 工具执行器调用工具
   c. MCP 客户端通信
   d. 结果解析器解析结果
   e. 上下文管理器保存结果
   f. 推理引擎分析结果
   g. 决定下一步操作
   ↓
6. 所有子任务完成
   ↓
7. 结果综合器生成报告
   ↓
8. 输出结果给用户
```

### 3.2 任务规划流程

```
用户请求 → 意图识别 → 任务分类 → 子任务分解 → 工具选择 → 计划生成
```

**意图识别**：
- 分析用户自然语言
- 提取关键信息
- 识别任务类型

**任务分类**：
- 数据结构分析
- 函数分析
- 模式搜索
- 断点调试
- 综合分析

**子任务分解**：
- 将复杂任务分解为简单步骤
- 确定步骤之间的依赖关系
- 估计每步的预期输出

**工具选择**：
- 根据子任务选择合适的工具
- 考虑工具的输入输出
- 优化工具调用顺序

### 3.3 推理决策流程

```
工具执行结果 → 结果分析 → 状态评估 → 决策制定 → 下一步操作
```

**结果分析**：
- 解析工具输出
- 提取关键信息
- 识别异常情况

**状态评估**：
- 比较实际结果与预期
- 判断是否达到目标
- 识别需要调整的地方

**决策制定**：
- 确定下一步操作
- 调整执行计划
- 处理异常情况

## 4. 技术实现

### 4.1 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 编程语言 | Python 3.10+ | 主要实现语言 |
| LLM | Ollama | 本地大模型推理 |
| HTTP 客户端 | requests | Ollama API 通信 |
| 数据验证 | pydantic | 数据模型验证 |
| 配置管理 | pydantic-settings | 配置管理 |
| 日志系统 | logging | 日志记录 |
| 异步处理 | asyncio | 异步执行 |

### 4.2 目录结构

```
CE_Agent/
├── __init__.py
├── main.py                    # 主入口
├── config.py                  # 配置管理
├── core/
│   ├── __init__.py
│   ├── agent.py               # AI 代理核心
│   ├── task_planner.py        # 任务规划器
│   ├── reasoning_engine.py    # 推理引擎
│   ├── context_manager.py     # 上下文管理器
│   └── result_synthesizer.py  # 结果综合器
├── tools/
│   ├── __init__.py
│   ├── tool_registry.py       # 工具注册表
│   ├── tool_executor.py       # 工具执行器
│   ├── result_parser.py       # 结果解析器
│   └── tool_definitions.py    # 工具定义
├── mcp/
│   ├── __init__.py
│   ├── mcp_client.py          # MCP 客户端
│   └── protocol.py            # MCP 协议处理
├── llm/
│   ├── __init__.py
│   ├── ollama_client.py       # Ollama 客户端
│   ├── prompt_manager.py      # Prompt 管理
│   └── response_parser.py    # 响应解析
├── models/
│   ├── __init__.py
│   ├── task.py                # 任务模型
│   ├── context.py             # 上下文模型
│   └── tool.py                # 工具模型
├── utils/
│   ├── __init__.py
│   ├── logger.py              # 日志工具
│   ├── retry.py               # 重试机制
│   └── validators.py          # 验证器
├── prompts/
│   ├── system_prompt.txt      # 系统 Prompt
│   ├── task_planning.txt      # 任务规划 Prompt
│   ├── reasoning.txt          # 推理 Prompt
│   └── synthesis.txt           # 结果综合 Prompt
└── logs/                      # 日志目录
```

### 4.3 关键设计模式

#### 4.3.1 策略模式

用于不同的任务类型和推理策略：

```python
class TaskStrategy(ABC):
    @abstractmethod
    def plan(self, request: str) -> ExecutionPlan:
        pass

class PacketDecryptionStrategy(TaskStrategy):
    def plan(self, request: str) -> ExecutionPlan:
        # 数据包解密任务规划
        pass

class DataStructureAnalysisStrategy(TaskStrategy):
    def plan(self, request: str) -> ExecutionPlan:
        # 数据结构分析任务规划
        pass
```

#### 4.3.2 责任链模式

用于工具执行和错误处理：

```python
class ToolExecutionHandler(ABC):
    def __init__(self, next_handler: Optional['ToolExecutionHandler'] = None):
        self.next_handler = next_handler
    
    def handle(self, execution: ToolExecution) -> ToolResult:
        if self.next_handler:
            return self.next_handler.handle(execution)
        return execution.result

class ValidationHandler(ToolExecutionHandler):
    def handle(self, execution: ToolExecution) -> ToolResult:
        # 验证参数
        return super().handle(execution)

class PermissionHandler(ToolExecutionHandler):
    def handle(self, execution: ToolExecution) -> ToolResult:
        # 检查权限
        return super().handle(execution)

class ExecutionHandler(ToolExecutionHandler):
    def handle(self, execution: ToolExecution) -> ToolResult:
        # 执行工具
        return execution.execute()
```

#### 4.3.3 观察者模式

用于进度通知和日志记录：

```python
class ExecutionObserver(ABC):
    @abstractmethod
    def on_step_start(self, step: ExecutionStep):
        pass
    
    @abstractmethod
    def on_step_complete(self, step: ExecutionStep):
        pass

class ProgressObserver(ExecutionObserver):
    def on_step_start(self, step: ExecutionStep):
        print(f"开始执行步骤 {step.step_id}")
    
    def on_step_complete(self, step: ExecutionStep):
        print(f"完成步骤 {step.step_id}")
```

### 4.4 错误处理策略

#### 4.4.1 错误分类

| 错误类型 | 处理策略 |
|---------|---------|
| 网络错误 | 重试（最多3次） |
| 超时错误 | 重试（最多2次） |
| 参数错误 | 不重试，返回错误信息 |
| 权限错误 | 不重试，请求审批 |
| 工具执行错误 | 记录日志，继续下一步 |

#### 4.4.2 重试机制

```python
def retry_with_backoff(func, max_attempts=3, base_delay=1):
    for attempt in range(max_attempts):
        try:
            return func()
        except RetryableError as e:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)
```

### 4.5 性能优化

#### 4.5.1 并行执行

对于独立的工具调用，可以并行执行：

```python
async def execute_parallel(tools: List[ToolCall]) -> List[ToolResult]:
    tasks = [execute_tool(tool) for tool in tools]
    return await asyncio.gather(*tasks)
```

#### 4.5.2 缓存机制

缓存常用结果，避免重复调用：

```python
class ResultCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        entry = self.cache.get(key)
        if entry and time.time() - entry['timestamp'] < self.ttl:
            return entry['value']
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
```

## 5. 安全考虑

### 5.1 权限控制

- 破坏性操作需要审批
- 敏感操作需要确认
- 操作日志记录

### 5.2 输入验证

- 验证所有工具参数
- 防止注入攻击
- 限制资源使用

### 5.3 审计日志

- 记录所有工具调用
- 记录所有 LLM 交互
- 记录所有决策过程

## 6. 扩展性

### 6.1 新工具集成

添加新工具只需：
1. 在 tool_definitions.py 中定义工具元数据
2. 在 tool_registry.py 中注册工具
3. 更新工具分类

### 6.2 新任务类型

添加新任务类型只需：
1. 创建新的 TaskStrategy
2. 在 TaskPlanner 中注册策略
3. 更新任务分类逻辑

### 6.3 新 LLM 集成

支持新的 LLM 只需：
1. 创建新的 LLM 客户端适配器
2. 实现 LLMClient 接口
3. 更新配置

## 7. 测试策略

### 7.1 单元测试

- 测试每个组件的功能
- 测试工具封装
- 测试结果解析

### 7.2 集成测试

- 测试组件之间的交互
- 测试完整的工作流程
- 测试错误处理

### 7.3 端到端测试

- 测试真实的任务执行
- 测试与 Cheat Engine 的集成
- 测试复杂任务场景

## 8. 监控和日志

### 8.1 日志级别

- DEBUG: 详细调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息
- CRITICAL: 严重错误

### 8.2 性能指标

- 工具执行时间
- LLM 响应时间
- 任务完成时间
- 错误率

## 9. 未来改进

### 9.1 短期改进

- [ ] 实现完整的工具封装（40+ 工具）
- [ ] 实现智能任务规划
- [ ] 实现多步推理
- [ ] 实现上下文管理
- [ ] 实现结果综合

### 9.2 中期改进

- [ ] 添加任务模板库
- [ ] 实现任务并行执行
- [ ] 添加可视化界面
- [ ] 实现任务保存和恢复

### 9.3 长期改进

- [ ] 支持多 LLM 模型
- [ ] 实现分布式执行
- [ ] 添加机器学习优化
- [ ] 实现自动任务学习
