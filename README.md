# CE_Agent

将 AI 智能代理与 Cheat Engine 内存分析工具深度集成，实现自动化内存分析任务。

## 项目概述

CE_Agent 是一个创新工具，通过模型上下文协议（MCP）将 AI 代理与 Cheat Engine 连接起来，实现程序内存的智能分析和操作。该项目包含两个主要组件：

1. **MCP 服务器** - 基于 FastMCP 的 Python 服务器，通过命名管道与 Cheat Engine 通信
2. **CE_Agent 智能代理** - 集成 Ollama 本地大模型的 AI 代理系统，支持智能任务规划和推理

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
├── MCP_Server/                    # MCP 服务器实现
│   ├── mcp_cheatengine.py         # FastMCP 服务器主文件
│   ├── ce_mcp_bridge.lua          # Cheat Engine Lua 桥接脚本
│   └── test_mcp.py                # 测试套件
├── Agent/                        # AI 代理系统
│   ├── core/                      # 核心组件
│   │   ├── agent.py               # Agent 主类
│   │   ├── task_planner.py        # 任务规划器
│   │   ├── reasoning_engine.py    # 推理引擎
│   │   ├── context_manager.py     # 上下文管理器
│   │   └── result_synthesizer.py  # 结果综合器
│   ├── tools/                     # 工具层
│   │   ├── registry.py            # 工具注册表
│   │   ├── executor.py            # 工具执行器
│   │   ├── parser.py              # 结果解析器
│   │   ├── mcp_basic_tools.py     # MCP 基础工具
│   │   └── mcp_advanced_tools.py  # MCP 高级工具
│   ├── llm/                       # LLM 层
│   │   ├── client.py              # Ollama 客户端
│   │   ├── prompt_manager.py      # 提示词管理器
│   │   └── response_parser.py     # LLM 响应解析器
│   ├── mcp/                       # MCP 通信层
│   │   └── client.py              # MCP 客户端
│   ├── models/                    # 数据模型
│   │   ├── base.py                # 基础模型
│   │   └── core_models.py         # 核心模型
│   ├── ui/                        # 用户界面
│   │   └── cli.py                 # 命令行界面
│   ├── utils/                     # 工具函数
│   │   ├── logger.py              # 日志工具
│   │   └── validators.py          # 验证器
│   ├── prompts/                   # 提示词模板
│   │   └── SYSTEM_PROMPT.md      # 系统提示词
│   ├── main.py                    # 主入口
│   └── config.py                  # 配置管理
├── AI_Context/                    # AI 上下文文档
│   ├── AI_Guide_MCP_Server_Implementation.md
│   ├── CE_LUA_Documentation.md
│   └── MCP_Bridge_Command_Reference.md
├── ARCHITECTURE_DESIGN.md         # 架构设计文档
├── IMPLEMENTATION_PLAN.md         # 实现计划
├── LICENSE                        # 许可证
├── requirements.txt               # 依赖配置
└── README.md                      # 本文件
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

### 启动步骤

#### 1. 启动 Cheat Engine 并加载桥接脚本

1. 打开 Cheat Engine
2. 启用 DBVM（Edit → Settings → Extra → Enable DBVM）
3. 附加到目标进程
4. 文件 → 执行脚本 → 打开 `MCP_Server/ce_mcp_bridge.lua` → 执行

#### 2. 启动 MCP 服务器

```bash
cd CE_Agent
python MCP_Server/mcp_cheatengine.py
```

查找输出：`[MCP CE] 正在启动FastMCP服务器(v11/v99兼容)...`

#### 3. 启动 Ollama 服务（可选）

```bash
# 下载并安装 Ollama: https://ollama.com/download
# 启动 Ollama 服务
ollama serve

# 拉取模型（可选）
ollama pull deepseek-r1:8b
```

#### 4. 运行 CE_Agent

```bash
cd CE_Agent
python -m Agent.main
```

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

#### 基础工具
| 工具 | 描述 |
|------|-------------|
| `ping` | 检查 MCP 服务器连接性和版本信息 |
| `get_process_info` | 获取当前进程信息（ID、名称、架构） |
| `enum_modules` | 列出所有加载的模块（DLL）及其基地址 |
| `get_thread_list` | 获取附加进程中的线程列表 |
| `get_symbol_address` | 将符号名解析为地址 |
| `get_address_info` | 获取地址的符号名和模块信息 |
| `get_rtti_classname` | 使用 RTTI 识别对象的类名 |

#### 内存读取工具
| 工具 | 描述 |
|------|-------------|
| `read_memory` | 从内存读取原始字节 |
| `read_integer` | 读取数字（byte, word, dword, qword, float, double） |
| `read_string` | 读取 ASCII 或 UTF-16 字符串 |
| `read_pointer` | 读取单个指针 |
| `read_pointer_chain` | 跟踪多级指针链 |
| `checksum_memory` | 计算内存区域的 MD5 校验和 |

#### 扫描与搜索工具
| 工具 | 描述 |
|------|-------------|
| `scan_all` | 统一内存扫描器 |
| `get_scan_results` | 检索扫描结果 |
| `aob_scan` | 搜索字节数组（AOB）模式 |
| `search_string` | 在内存中搜索文本字符串 |
| `generate_signature` | 为地址生成唯一的 AOB 签名 |
| `get_memory_regions` | 列出常见基址附近的有效内存区域 |
| `enum_memory_regions_full` | 枚举所有内存区域 |

#### 分析与反汇编工具
| 工具 | 描述 |
|------|-------------|
| `disassemble` | 从地址反汇编指令 |
| `get_instruction_info` | 获取单条指令的详细信息 |
| `find_function_boundaries` | 检测函数开始/结束 |
| `analyze_function` | 分析函数调用图 |
| `find_references` | 查找访问地址的指令 |
| `find_call_references` | 查找所有对函数的调用 |
| `dissect_structure` | 自动检测内存中的字段和类型 |

#### 断点与调试工具
| 工具 | 描述 |
|------|-------------|
| `set_breakpoint` | 设置硬件执行断点 |
| `set_data_breakpoint` | 设置硬件数据断点（监视点） |
| `remove_breakpoint` | 按移除断点 |
| `list_breakpoints` | 列出所有活动断点 |
| `clear_all_breakpoints` | 移除所有断点 |
| `get_breakpoint_hits` | 获取断点命中次数 |

#### DBVM 工具（Ring -1）
| 工具 | 描述 |
|------|-------------|
| `get_physical_address` | 将虚拟地址转换为物理地址 |
| `start_dbvm_watch` | 启动隐形 DBVM 虚拟机监视 |
| `stop_dbvm_watch` | 停止 DBVM 监视并返回结果 |
| `poll_dbvm_watch` | 轮询 DBVM 监视日志 |

#### 脚本工具
| 工具 | 描述 |
|------|-------------|
| `evaluate_lua` | 在 Cheat Engine 中执行 Lua 代码 |
| `auto_assemble` | 运行 AutoAssembler 脚本 |

## 配置

### CE_Agent 配置

编辑 `Agent/config.py`：

```python
# MCP 服务器配置
mcp_host = "localhost"
mcp_port = 8080

# Ollama 配置
ollama_host = "localhost"
ollama_port = 11434
model_name = "deepseek-r1:8b"

# 日志配置
log_level = "INFO"
log_file = "logs/ce_agent.log"

# Agent 配置
max_retries = 3
timeout = 30
max_context_length = 4096

# MCP 连接配置
mcp_connection_timeout = 10
mcp_retry_delay = 1.0
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
│  │  - HTTP 通信                                              │   │
│  │  - 命令发送                                              │   │
│  │  - 响应解析                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Cheat Engine MCP 服务器                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastMCP 服务器                                           │   │
│  │  - 39 个 MCP 工具                                         │   │
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
| Windows API | win32file, win32pipe | 管道通信和文件操作 |
| 内存操作 | Cheat Engine API | 执行实际的内存操作 |
| 虚拟机监视 | DBVM (Ring -1) | 隐形内存监视 |
| LLM 支持 | Ollama HTTP API | 本地 LLM 模型集成 |
| 数据验证 | pydantic | 数据模型验证 |
| CLI 支持 | colorama | 彩色输出 |
| 异步处理 | asyncio | 异步任务执行 |

## 技术实现亮点

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

### 5. 智能代理集成
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

## 故障排除

### 常见问题

**Q: MCP 服务器无法启动**
- 确保 Cheat Engine 已启动并加载了桥接脚本
- 检查命名管道名称是否正确
- 查看日志文件获取详细错误信息

**Q: Ollama 连接失败**
- 确保 Ollama 服务正在运行：`ollama serve`
- 检查模型是否已下载：`ollama list`
- 验证配置中的主机和端口设置

**Q: 工具执行超时**
- 增加 `timeout` 配置值
- 检查网络连接和 MCP 服务器状态
- 查看日志了解具体超时的工具

**Q: Windows 换行符错误**
- 确保使用最新版本的 MCP SDK
- 检查是否正确应用了 Windows 补丁
- 验证 stdin/stdout 的二进制模式设置

## 文档

- [架构设计文档](ARCHITECTURE_DESIGN.md) - 详细的系统架构设计
- [实现计划](IMPLEMENTATION_PLAN.md) - 项目实现计划和进度
- [MCP 命令参考](AI_Context/MCP_Bridge_Command_Reference.md) - 所有 MCP 工具的详细说明
- [Cheat Engine Lua 文档](AI_Context/CE_LUA_Documentation.md) - Cheat Engine Lua API 参考
- [AI 代理技术文档](AI_Context/AI_Guide_MCP_Server_Implementation.md) - AI 代理实现指南

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 免责声明

此代码仅用于教育和研究目的。它的创建是为了展示模型上下文协议（MCP）和基于 LLM 的调试能力。我不赞成将这些工具用于恶意黑客攻击、多人游戏作弊或违反服务条款。这是软件工程自动化的演示。

## 贡献

欢迎贡献！请随时提交问题报告或拉取请求。

## 联系方式

如有问题或建议，请通过 GitHub Issues 联系。
