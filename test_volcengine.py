"""
测试火山引擎API连接
"""
from openai import OpenAI

api_key = "c7d62175-a6db-465d-ab06-6e6b2baa6914"

client = OpenAI(
    base_url='https://ark.cn-beijing.volces.com/api/v3',
    api_key=api_key
)

try:
    # 测试简单的对话请求
    response = client.responses.create(
        model="glm-4-7-251222",
        input=[{"role": "user", "content": "你好，请回复：测试成功"}]
    )
    
    print("✅ API连接成功！")
    
    # 提取响应内容
    content = ""
    if response.output and len(response.output) > 0:
        # 火山引擎的响应格式：output[0]是推理过程，output[1]是实际输出
        # 我们需要找到type='message'的输出
        for item in response.output:
            if hasattr(item, 'type') and item.type == 'message':
                if hasattr(item, 'content') and len(item.content) > 0:
                    if hasattr(item.content[0], 'text'):
                        content = item.content[0].text
                        break
    
    print(f"响应内容: {content}")
    print(f"使用的模型: {response.model}")
    print(f"Token使用: {response.usage}")
    
except Exception as e:
    print(f"❌ API连接失败: {e}")
    print(f"错误类型: {type(e).__name__}")
    import traceback
    traceback.print_exc()
