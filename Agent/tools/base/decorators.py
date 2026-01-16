"""
Cheat Engine AI Agent 的工具装饰器。

该模块提供了用于定义和注册工具的装饰器，
简化工具的开发和维护。
"""
import inspect
from typing import Callable, Type, Any, Dict, List, Optional
from ..models.base import ToolMetadata, Parameter, ToolCategory
from .tool_registry import ToolRegistry


# 全局注册表实例
_global_registry: Optional[ToolRegistry] = None


def set_global_registry(registry: ToolRegistry) -> None:
    """
    设置全局工具注册表实例。
    
    Args:
        registry: 工具注册表实例
    """
    global _global_registry
    _global_registry = registry


def get_global_registry() -> Optional[ToolRegistry]:
    """
    获取全局工具注册表实例。
    
    Returns:
        工具注册表实例，如果未设置则返回 None
    """
    return _global_registry


def tool(
    name: Optional[str] = None,
    category: Optional[ToolCategory] = None,
    description: Optional[str] = None,
    parameters: Optional[List[Parameter]] = None,
    examples: Optional[List[str]] = None,
    timeout: Optional[float] = None,
    destructive: bool = False,
    requires_approval: bool = False
) -> Callable:
    """
    工具装饰器，用于定义和注册工具。
    
    Args:
        name: 工具名称，如果未提供则使用函数名
        category: 工具类别
        description: 工具描述
        parameters: 工具参数列表，如果未提供则从函数签名自动生成
        examples: 工具使用示例
        timeout: 工具执行超时时间（秒）
        destructive: 工具是否具有破坏性
        requires_approval: 工具执行是否需要批准
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        # 使用函数名作为工具名称（如果未提供）
        tool_name = name or func.__name__
        
        # 如果未提供参数列表，则从函数签名自动生成
        if parameters is None:
            sig = inspect.signature(func)
            tool_params = []
            
            # 跳过第一个参数 mcp_client
            param_list = list(sig.parameters.items())
            if param_list and param_list[0][0] == 'mcp_client':
                param_list = param_list[1:]
            
            for param_name, param in param_list:
                # 跳过 *args 和 **kwargs
                if param.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                    continue
                
                # 确定参数是否为必需
                required = param.default == inspect.Parameter.empty
                
                # 获取参数类型
                param_type = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "string"
                
                # 创建 Parameter 对象
                param_obj = Parameter(
                    name=param_name,
                    type=param_type,
                    required=required,
                    description="",  # 默认空描述
                    default=param.default if not required else None
                )
                tool_params.append(param_obj)
        else:
            tool_params = parameters
        
        # 创建工具元数据
        metadata = ToolMetadata(
            name=tool_name,
            category=category or ToolCategory.BASIC,
            description=description or func.__doc__ or "",
            parameters=tool_params,
            examples=examples or [],
            timeout=timeout,
            destructive=destructive,
            requires_approval=requires_approval
        )
        
        # 注册工具到全局注册表
        registry = get_global_registry()
        if registry:
            registry.register_tool(metadata, func)
        
        # 保存元数据到函数对象
        func._tool_metadata = metadata
        
        return func
    
    return decorator


def async_tool(
    name: Optional[str] = None,
    category: Optional[ToolCategory] = None,
    description: Optional[str] = None,
    parameters: Optional[List[Parameter]] = None,
    examples: Optional[List[str]] = None,
    timeout: Optional[float] = None,
    destructive: bool = False,
    requires_approval: bool = False
) -> Callable:
    """
    异步工具装饰器，用于定义和注册异步工具。
    
    Args:
        name: 工具名称，如果未提供则使用函数名
        category: 工具类别
        description: 工具描述
        parameters: 工具参数列表，如果未提供则从函数签名自动生成
        examples: 工具使用示例
        timeout: 工具执行超时时间（秒）
        destructive: 工具是否具有破坏性
        requires_approval: 工具执行是否需要批准
    
    Returns:
        装饰器函数
    """
    return tool(
        name=name,
        category=category,
        description=description,
        parameters=parameters,
        examples=examples,
        timeout=timeout,
        destructive=destructive,
        requires_approval=requires_approval
    )
