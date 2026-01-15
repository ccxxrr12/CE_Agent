"""
测试推理流程
"""
import sys
sys.path.insert(0, '.')

from Agent.llm.volcengine_client import VolcengineClient
from Agent.llm.response_parser import ResponseParser
import logging

# 设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')

# 初始化客户端和解析器
client = VolcengineClient()
parser = ResponseParser()

print("=" * 60)
print("测试1: 模拟推理流程")
print("=" * 60)

# 模拟推理提示词
current_result = {
    "success": True,
    "issues": [],
    "recommendations": ["Continue with planned execution"]
}

context = {
    "task_id": "test-task-123",
    "current_step": 1,
    "total_steps": 5,
    "task_type": "COMPREHENSIVE_ANALYSIS"
}

available_tools = ["ping", "get_process_info", "read_memory"]

# 构建提示词（模拟 prompt_manager 的逻辑）
prompt = f"""分析当前执行结果并确定下一步行动。

当前结果：
{current_result}

执行上下文：
{context}

可用工具：
{available_tools}

你的任务：
1. 分析结果 - 是否成功？
2. 我们学到了什么信息？
3. 接下来应该做什么？
4. 我们需要调整方法吗？

**重要：你必须以纯 JSON 格式回复，不要包含任何其他文本。**

JSON 格式示例：
{{
  "analysis": "对结果的简要分析",
  "findings": ["发现1", "发现2"],
  "next_action": "continue|adjust|abort|finalize",
  "next_tool": "tool_name",
  "tool_args": {{}},
  "reasoning": "你的决策解释",
  "confidence": 0.9
}}"""

print(f"\n发送的提示词：\n{prompt}\n")

# 发送请求
messages = [{"role": "user", "content": prompt}]
response = client.chat(messages)

print(f"\n收到的响应类型: {type(response)}")
print(f"收到的响应: {response}")

# 提取内容
if 'message' in response and 'content' in response['message']:
    content = response['message']['content']
    print(f"\n提取的内容类型: {type(content)}")
    print(f"提取的内容: {content[:500]}")
    
    # 尝试解析
    print(f"\n尝试解析...")
    reasoning = parser.parse_reasoning(content)
    print(f"解析结果: {reasoning}")
