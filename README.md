# CE_Agent

将 AI 智能代理与 Cheat Engine 内存分析工具深度集成，实现自动化内存分析任务。

## 项目概述

CE_Agent 是一个创新工具，通过模型上下文协议（MCP）将 AI 代理与 Cheat Engine 连接起来，实现程序内存的智能分析和操作。该项目包含两个主要组件：

1. **MCP 服务器** - 基于 FastMCP 的 Python 服务器，通过命名管道与 Cheat Engine 通信
2. **CE_Agent 智能代理** - 集成 Ollama 本地大模型和火山引擎云端模型的 AI 代理系统，支持智能任务规划和推理

### 核心价值

| 传统手动分析 | AI 智能代理 |
|------------|------------|
| 需要数天手动扫描和分析 | 数分钟自动完成 |
| 需要深入的逆向工程知识 | 自然语言交互即可使用 |
| 容易遗漏关键信息 | 全面系统分析 |
| 难以处理复杂任务链 | 自动规划任务链 |

### 典型应用场景

- **数据包解密函数分析** - 扫描网络相关值、设置断点、反汇编解密函数、分析算法逻辑
- **玩家数据结构分析** - 扫描玩家相关值、分析内存结构、识别字段类型
- **操作码定位与分析** - 扫描特定功能、设置断点、反汇编操作码函数

## 项目结构

```
CE_Agent/
├── AI_Context/                    # AI 上下文文档
│   ├── AI_Guide_MCP_Server_Implementation.md
│   ├── CE_LUA_Documentation.md
│   └── MCP_Bridge_Command_Reference.md
├── Agent/                        # AI 代理系统
│   ├── core/                      # 核心组件
│   │   ├── __init__.py
│   │   ├── agent.py               # Agent 主类
│   │   ├── context_manager.py     # 上下文管理器
│   │   ├── reasoning_engine.py    # 推理引擎
│   │   ├── result_synthesizer.py  # 结果综合器
│   │   └── task_planner.py        # 任务规划器
│   ├── llm/                       # LLM 层
│   │   ├── __init__.py
│   │   ├── client.py              # Ollama 客户端
│   │   ├── prompt_manager.py      # 提示词管理器
│   │   ├── response_parser.py     # LLM 响应解析器
│   │   └── volcengine_client.py   # 火山引擎客户端
│   ├── logs/                      # 日志目录
│   │   └── __init__.py
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                # 基础模型
│   │   └── core_models.py         # 核心模型
│   ├── prompts/                   # 提示词模板
│   │   ├── __init__.py
│   │   ├── SYSTEM_PROMPT.json     # JSON 格式系统提示词
│   │   ├── SYSTEM_PROMPT.md       # 详细系统提示词
│   │   ├── SYSTEM_PROMPT_MINIMAL.md # 最小化系统提示词
│   │   └── SYSTEM_PROMPT_SIMPLE.md # 简化系统提示词
│   ├── tools/                     # 工具层
│   │   ├── base/                  # 工具基础组件
│   │   │   ├── decorators.py      # 工具装饰器
│   │   │   ├── result_parser.py   # 结果解析器
│   │   │   ├── tool_executor.py   # 工具执行器
│   │   │   └── tool_registry.py   # 工具注册表
│   │   ├── core/                  # 核心工具组件
│   │   │   ├── command_adapter.py # 命令适配器
│   │   │   ├── mcp_client.py      # MCP 客户端
│   │   │   └── parameter_validator.py # 参数验证器
│   │   ├── models/                # 工具模型
│   │   │   └── base.py            # 基础工具模型
│   │   ├── tools/                 # 具体工具实现
│   │   │   ├── basic_tools.py     # 基础工具
│   │   │   ├── breakpoint_tools.py # 断点工具
│   │   │   ├── dbvm_tools.py      # DBVM 工具
│   │   │   ├── debug_tools.py     # 调试工具
│   │   │   ├── memory_tools.py    # 内存读取工具
│   │   │   ├── process_tools.py   # 进程工具
│   │   │   └── scan_tools.py      # 扫描工具
│   │   └── utils/                 # 工具工具函数
│   │       ├── address_utils.py   # 地址处理工具
│   │       ├── error_utils.py     # 错误处理工具
│   │       ├── tool_helper.py     # 工具助手
│   │       └── type_utils.py      # 类型工具
│   ├── ui/                        # 用户界面
│   │   ├── __init__.py
│   │   └── cli.py                 # 命令行界面
│   ├── utils/                     # 通用工具函数
│   │   ├── __init__.py
│   │   ├── errors.py              # 错误定义
│   │   ├── logger.py              # 日志工具
│   │   └── validators.py          # 验证器
│   ├── __init__.py
│   ├── config.py                  # 配置管理
│   └── main.py                    # 主入口
├── MCP_Server/                    # MCP 服务器实现
│   ├── __init__.py
│   ├── ce_mcp_bridge.lua          # Cheat Engine Lua 桥接脚本
│   ├── mcp_cheatengine.py         # FastMCP 服务器主文件
│   └── test_mcp.py                # 测试套件
├── .gitignore                     # Git 忽略文件
├── ARCHITECTURE_DESIGN.md         # 架构设计文档
├── LICENSE                        # 许可证
├── README.md                      # 本文件
├── __init__.py
└── requirements.txt               # 依赖配置
```

## 快速开始

### 前置要求

1. **Cheat Engine 7.4+** - 启用 DBVM 功能
2. **Python 3.10+** - 运行 MCP 服务器和 AI 代理
3. **Ollama** - 本地 LLM 服务（可选，用于 AI 功能）

### 安装依赖

```bash
pip install -r requirements.txt
```

#### 依赖列表

| 类别 | 依赖 | 版本要求 | 用途 |
|------|------|----------|------|
| 核心协议 | mcp | >=1.0.0 | 模型上下文协议支持 |
| 异步通信 | anyio | >=4.0.0 | 异步 I/O 支持 |
| JSON 解析 | orjson | >=3.9.0 | 高性能 JSON 解析 |
| Windows API | pywin32 | >=306 | Windows 平台支持 |
| HTTP 客户端 | requests | >=2.30.0 | HTTP 请求支持 |
| 数据验证 | pydantic | >=2.5.0 | 数据模型验证 |
| CLI 支持 | colorama | >=0.4.6 | 彩色命令行输出 |
| LLM 集成 | ollama | >=0.1.0 | Ollama 本地模型支持 |
| 测试框架 | pytest | >=7.0.0 | 测试套件支持 |

#### 可选依赖

- **ollama** - 用于本地 LLM 模型集成（推荐）
- **pytest** - 用于运行测试套件

### 启动步骤

#### 1. 启动 Cheat Engine 并加载桥接脚本

1. 打开 Cheat Engine
2. 启用 DBVM（Edit → Settings → Extra → Enable DBVM）
3. 附加到目标进程
4. 文件 → 执行脚本 → 打开 `MCP_Server/ce_mcp_bridge.lua` → 执行

#### 2. 启动 Ollama 服务（推荐）

```bash
# 下载并安装 Ollama: https://ollama.com/download
# 启动 Ollama 服务
ollama serve

# 拉取模型（可选）
ollama pull deepseek-r1:8b
```

#### 3. 运行 CE_Agent

```bash
cd CE_Agent
python -m Agent.main
```

**注意**：CE_Agent 会自动启动 MCP 服务器子进程，无需手动启动 MCP 服务器。

## 使用指南

### CE_Agent 交互模式

启动 CE_Agent 后，您可以通过自然语言与系统交互：

```
═════════════════════════════════════════════════════════════════════
    CHEAT ENGINE AI AGENT
═════════════════════════════════════════════════════════════════════
Welcome to Cheat Engine AI Agent!
This tool enables natural language interaction with Cheat Engine for memory analysis and reverse engineering.
Type 'help' for available commands or 'quit' to exit.
------------------------------------------------------------

>>> ping
[MCP Bridge] Connected to Cheat Engine v11.4.0
Process: game.exe (PID: 12345)
Architecture: x64

>>> 扫描金币值 10000
Scanning for value: 10000
Found 47 results

>>> 金币变为 10050
Refining scan...
Found 3 results

>>> 分析第一个地址
Address: 0x12345678
Setting up analysis...
```

### 可用的 MCP 工具

CE_Agent 的工具系统采用模块化设计，根据功能类型进行分类。所有工具通过 MCP 协议与 Cheat Engine 通信，实现对内存的各种操作。

#### 工具分类

| 工具模块 | 文件位置 | 主要功能 |
|---------|----------|----------|
| 基础工具 | `tools/core/basic_tools.py` | 连接检查、进程信息、模块枚举、符号解析 |
| 进程工具 | `tools/core/process_tools.py` | 进程信息、模块枚举、符号处理 |
| 内存读取工具 | `tools/core/memory_tools.py` | 内存读取、字符串读取、指针跟踪、校验和计算 |
| 模式扫描工具 | `tools/core/scan_tools.py` | 内存扫描、AOB 搜索、字符串搜索、签名生成 |
| 调试工具 | `tools/core/debug_tools.py` | 反汇编、指令分析、函数边界检测、引用查找 |
| 断点工具 | `tools/core/breakpoint_tools.py` | 硬件断点、数据断点、断点管理 |
| DBVM 工具 | `tools/core/dbvm_tools.py` | 物理地址转换、隐形内存监视 |

#### 工具详情

##### 基础工具
| 工具 | 描述 |
|------|-------------|
| `ping` | 检查 MCP 服务器连接性和版本信息 |
| `get_process_info` | 获取当前进程信息（ID、名称、架构） |
| `enum_modules` | 列出所有加载的模块（DLL）及其基地址 |
| `get_thread_list` | 获取附加进程中的线程列表 |
| `get_symbol_address` | 将符号名解析为地址 |
| `get_address_info` | 获取地址的符号名和模块信息 |
| `get_rtti_classname` | 使用 RTTI 识别对象的类名 |

##### 内存读取工具
| 工具 | 描述 |
|------|-------------|
| `read_memory` | 从内存读取原始字节 |
| `read_integer` | 读取数字（byte, word, dword, qword, float, double） |
| `read_string` | 读取 ASCII 或 UTF-16 字符串 |
| `read_pointer` | 读取单个指针 |
| `read_pointer_chain` | 跟踪多级指针链 |
| `checksum_memory` | 计算内存区域的 MD5 校验和 |

##### 扫描与搜索工具
| 工具 | 描述 |
|------|-------------|
| `scan_all` | 统一内存扫描器 |
| `get_scan_results` | 检索扫描结果 |
| `aob_scan` | 搜索字节数组（AOB）模式 |
| `search_string` | 在内存中搜索文本字符串 |
| `generate_signature` | 为地址生成唯一的 AOB 签名 |
| `get_memory_regions` | 列出常见基址附近的有效内存区域 |
| `enum_memory_regions_full` | 枚举所有内存区域 |

##### 分析与反汇编工具
| 工具 | 描述 |
|------|-------------|
| `disassemble` | 从地址反汇编指令 |
| `get_instruction_info` | 获取单条指令的详细信息 |
| `find_function_boundaries` | 检测函数开始/结束 |
| `analyze_function` | 分析函数调用图 |
| `find_references` | 查找访问地址的指令 |
| `find_call_references` | 查找所有对函数的调用 |
| `dissect_structure` | 自动检测内存中的字段和类型 |

##### 断点与调试工具
| 工具 | 描述 |
|------|-------------|
| `set_breakpoint` | 设置硬件执行断点 |
| `set_data_breakpoint` | 设置硬件数据断点（监视点） |
| `remove_breakpoint` | 移除断点 |
| `list_breakpoints` | 列出所有活动断点 |
| `clear_all_breakpoints` | 移除所有断点 |
| `get_breakpoint_hits` | 获取断点命中次数 |

##### DBVM 工具（Ring -1）
| 工具 | 描述 |
|------|-------------|
| `get_physical_address` | 将虚拟地址转换为物理地址 |
| `start_dbvm_watch` | 启动隐形 DBVM 虚拟机监视 |
| `stop_dbvm_watch` | 停止 DBVM 监视并返回结果 |
| `poll_dbvm_watch` | 轮询 DBVM 监视日志 |

##### 脚本工具
| 工具 | 描述 |
|------|-------------|
| `evaluate_lua` | 在 Cheat Engine 中执行 Lua 代码 |
| `auto_assemble` | 运行 AutoAssembler 脚本 |

## 配置

### CE_Agent 配置

CE_Agent 使用一个结构化的配置系统，通过 `Config` 类管理所有配置参数。配置可以通过环境变量（优先级最高）、配置文件或默认值进行设置。

#### 配置类结构

编辑 `Agent/config.py`：

```python
@dataclass
class Config:
    # MCP 服务器配置
    mcp_host: str = "localhost"
    mcp_port: int = 8080
    
    # MCP 子进程配置
    mcp_server_script: str = "MCP_Server/mcp_cheatengine.py"
    mcp_process_startup_timeout: int = 5
    mcp_process_shutdown_timeout: int = 5
    
    # Ollama 配置
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    model_name: str = "deepseek-r1:8b"
    
    # 火山引擎配置
    use_volcengine: bool = True
    volcengine_api_key: str = "c7d62175-a6db-465d-ab06-6e6b2baa6914"
    volcengine_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    volcengine_model: str = "glm-4-7-251222"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/ce_agent.log"
    
    # 提示词配置
    use_simple_prompt: bool = False
    use_minimal_prompt: bool = False
    use_json_prompt: bool = True
    system_prompt_file: str = "prompts/SYSTEM_PROMPT.md"
    system_prompt_simple_file: str = "prompts/SYSTEM_PROMPT_SIMPLE.md"
    system_prompt_minimal_file: str = "prompts/SYSTEM_PROMPT_MINIMAL.md"
    system_prompt_json_file: str = "prompts/SYSTEM_PROMPT.json"
    
    # Agent 配置
    max_retries: int = 3
    timeout: int = 180
    max_context_length: int = 4096
    
    # MCP 连接配置（保留用于向后兼容）
    mcp_connection_timeout: int = 300
    mcp_retry_delay: float = 1.0
```

#### 配置加载优先级

1. **环境变量** - 以 `CE_AGENT_` 为前缀，例如 `CE_AGENT_MODEL_NAME=llama3:8b`
2. **配置文件** - JSON 格式配置文件（可选）
3. **默认值** - 上述代码中定义的默认值

#### 配置示例

使用环境变量配置：

```bash
set CE_AGENT_MODEL_NAME=llama3:8b
set CE_AGENT_LOG_LEVEL=DEBUG
set CE_AGENT_USE_VOLCENGINE=false
python -m Agent.main
```

#### 配置管理器

项目使用 `ConfigManager` 类来加载和管理配置：

```python
# 获取配置实例
from Agent.config import config

# 重新加载配置
from Agent.config import config_manager
config_manager.reload_config()
```

## 技术架构

### CE_Agent 架构

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
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP 通信层                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MCP 客户端 (MCPClient)                                  │   │
│  │  - 子进程管理                                            │   │
│  │  - stdio 通信                                            │   │
│  │  - JSON-RPC 协议                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cheat Engine MCP 服务器                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastMCP 服务器（子进程）                                  │   │
│  │  - 39 个 MCP 工具                                         │   │
│  │  - stdio 传输模式                                         │   │
│  │  - JSON-RPC 协议                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cheat Engine Lua 桥接                         │
│  - 命名管道通信                                                  │
│  - CE API 调用                                                  │
│  - 内存操作                                                      │
└─────────────────────────────────────────────────────────────────┘
```

### CE_Agent 工作流程

```
用户输入自然语言请求
         │
         ▼
┌─────────────────┐
│  TaskPlanner    │
│  - LLM 规划     │
│  - 规则回退     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ReasoningEngine│
│  - 选择工具     │
│  - 决策执行     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ToolExecutor   │
│  - 执行 MCP 工具│
│  - 错误处理     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ContextManager │
│  - 更新上下文   │
│  - 记录结果     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ReasoningEngine│
│  - 分析结果     │
│  - 决定下一步   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ResultSynthesizer│
│  - 综合结果     │
│  - 生成报告     │
└────────┬────────┘
         │
         ▼
    返回分析报告
```

## 技术栈

| 类别 | 技术/工具 | 用途 |
|----------|----------------|---------|
| 编程语言 | Python 3.10+ | MCP 服务器和 AI 代理实现 |
| 脚本语言 | Lua | Cheat Engine 桥接脚本 |
| 通信协议 | MCP (JSON-RPC) | AI 代理到 MCP 服务器通信 |
| 进程间通信 | 命名管道 | MCP 服务器到 Cheat Engine 通信 |
| 子进程通信 | stdio (stdin/stdout) | AI 代理到 MCP 服务器通信（子进程模式）|
| 进程管理 | subprocess | MCP 服务器子进程生命周期管理 |
| Windows API | win32file, win32pipe | 管道通信和文件操作 |
| 内存操作 | Cheat Engine API | 执行实际的内存操作 |
| 虚拟机监视 | DBVM (Ring -1) | 隐形内存监视 |
| LLM 支持 | Ollama HTTP API | 本地 LLM 模型集成 |
| LLM 支持 | Volcengine API | 火山引擎云端模型集成 |
| 数据验证 | pydantic | 数据模型验证 |
| CLI 支持 | colorama | 彩色输出 |
| 异步处理 | asyncio | 异步任务执行 |

## 开展工作

### 1. Windows 特定优化
- **行结束符修复**：修补 MCP SDK，在 Windows 上使用 LF（\n）而不是 CRLF（\r\n）
- **二进制模式设置**：将 stdin/stdout 设置为二进制模式，防止编码问题
- **MCP 输出流保护**：将 stdout 重定向到 stderr，防止 MCP 流损坏
- **双重修补**：同时修补 stdio_server 和 fastmcp 模块，确保完全兼容

### 2. 通信可靠性
- **命名管道通信**：使用 Windows 命名管道进行可靠的进程间通信
- **自动重连机制**：在管道通信失败时自动尝试重连
- **错误处理**：全面的错误捕获和处理，确保系统稳定性
- **响应验证**：验证 JSON 响应，处理不完整或无效数据

### 3. 跨架构兼容性
- **32/64 位自动检测**：自动识别目标进程架构
- **统一指针处理**：使用 `read_pointer` 函数自动处理 32/64 位指针
- **架构感知指令分析**：对不同架构使用不同的指令分析策略
- **测试适配**：测试套件自动适应 x86/x64 目标

### 4. 反作弊安全性
- **硬件断点**：使用硬件调试寄存器设置断点，避免软件断点检测
- **DBVM 监视**：使用 Ring -1 级监视，完全隐藏调试行为
- **内存访问优化**：避免可能触发反作弊的内存访问模式
- **安全监视模式**：尽可能使用只读监视，最小化检测面

### 5. CE_AGENT代理集成
- **双模推理引擎**：LLM 智能推理与规则引擎无缝切换
- **智能任务规划**：自动将复杂用户请求分解为可执行的子任务序列
- **多步决策制定**：基于工具执行结果动态调整执行策略
- **提示词管理**：集中管理各类提示词模板，支持动态生成
- **响应解析**：智能解析 LLM 响应，提取结构化数据
- **完整验证系统**：多层次数据验证，确保输入输出正确性

### 6. 交互式 CLI
- **彩色输出**：使用 colorama 提供清晰的视觉反馈
- **实时进度**：显示任务执行进度和状态
- **错误处理**：友好的错误消息和恢复建议

## 测试

运行测试套件：

```bash
cd CE_Agent
python MCP_Server/test_mcp.py
```

测试套件会自动：
- 检测目标进程架构（x86/x64）
- 测试所有 MCP 工具功能
- 验证通信可靠性
- 生成详细的测试报告


## 文档

- [架构设计文档](ARCHITECTURE_DESIGN.md) - 详细的系统架构设计
  
- [MCP 命令参考](AI_Context/MCP_Bridge_Command_Reference.md) - 所有 MCP 工具的详细说明
- [Cheat Engine Lua 文档](AI_Context/CE_LUA_Documentation.md) - Cheat Engine Lua API 参考
- [AI 代理技术文档](AI_Context/AI_Guide_MCP_Server_Implementation.md) - AI 代理实现指南

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献指南

我们欢迎社区贡献，包括但不限于：

### 贡献流程

1. **Fork 项目** - 在 GitHub 上 Fork 本项目
2. **创建分支** - 为您的功能创建一个新分支
3. **开发功能** - 实现您的功能或修复
4. **测试** - 确保您的代码通过所有测试
5. **提交 PR** - 提交 Pull Request 到主分支

### 开发规范

- **代码风格** - 遵循 Python PEP 8 规范
- **注释** - 为关键代码添加清晰的注释
- **测试** - 为新功能添加测试用例
- **文档** - 更新相关文档
- **提交信息** - 使用清晰的提交信息

### 报告问题

如果您发现任何问题，请在 GitHub Issues 中报告，包括：

- 详细的问题描述
- 重现步骤
- 预期行为
- 实际行为
- 环境信息

## 免责声明

此代码仅用于教育和研究目的。它的创建是为了展示模型上下文协议（MCP）和基于 LLM 的调试能力。本人不赞成将这些工具用于恶意黑客攻击、多人游戏作弊或违反服务条款。



## 联系方式

如有问题或建议，请通过 GitHub Issues 或邮件xueruic0@outlook.com与我联系。
