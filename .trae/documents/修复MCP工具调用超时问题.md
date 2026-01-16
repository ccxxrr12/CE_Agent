## 问题分析

1. **问题现象**：只有ping工具可以正常调用，其他工具（如get_process_info）执行后无响应并最终超时

2. **根本原因**：客户端在二进制模式下使用`readline()`读取MCP服务器响应，这与FastMCP的stdio传输模式不兼容
   - 客户端设置了`text=False`和`bufsize=0`，stdout处于二进制模式
   - `readline()`在二进制模式下查找`b'\n'`作为换行符
   - 但FastMCP服务器返回的是完整的JSON响应，不是简单的单行文本
   - 当响应包含多行JSON或没有明确的换行符时，`readline()`会阻塞直到超时

3. **为什么ping工具可以工作**：
   - ping工具的响应通常非常简单，可能刚好符合`readline()`的预期格式
   - 而其他工具（如get_process_info）返回的响应更复杂，包含更多数据，导致`readline()`无法正确读取

## 解决方案

修改`mcp/client.py`中的响应读取机制，不再使用`readline()`，而是实现一个正确的JSON响应读取器。

### 修复步骤

1. **修改`_readline_with_timeout`方法**：
   - 替换基于`readline()`的实现
   - 实现一个能够读取完整JSON响应的机制
   - 考虑使用select或其他非阻塞方式读取数据
   - 直到获得完整的JSON对象

2. **优化响应解析**：
   - 读取到足够数据后尝试解析JSON
   - 解析成功则返回响应，否则继续读取
   - 设置合理的超时机制

### 代码修改思路

```python
# 新的响应读取逻辑
def _read_response_with_timeout(self, timeout: float) -> Optional[str]:
    # 使用select或其他方式读取数据
    # 尝试解析JSON直到成功或超时
    # 返回完整的JSON响应
```

### 预期结果

- 修复后所有MCP工具都能正常调用
- 不再出现工具超时无响应的情况
- 客户端与服务器的通信更加可靠

## 测试建议

1. 调用ping工具验证基本连接
2. 调用get_process_info工具验证复杂响应处理
3. 调用其他工具（如enum_modules、read_memory等）验证全面修复
4. 测试各种参数组合下的工具调用