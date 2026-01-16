"""
Cheat Engine AI Agent 的类型转换工具。

该模块提供了用于转换和验证数据类型的工具函数。
"""
from typing import Any, Optional, Union, Type


def convert_to_type(value: Any, target_type: Type, default: Any = None) -> Any:
    """
    将值转换为指定类型。
    
    Args:
        value: 要转换的值
        target_type: 目标类型
        default: 转换失败时返回的默认值
        
    Returns:
        转换后的值，如果转换失败则返回默认值
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


def validate_type(value: Any, expected_type: Type) -> bool:
    """
    验证值是否为指定类型。
    
    Args:
        value: 要验证的值
        expected_type: 预期类型
        
    Returns:
        如果值为预期类型则返回True，否则返回False
    """
    return isinstance(value, expected_type)


def is_numeric(value: Any) -> bool:
    """
    检查值是否为数值类型。
    
    Args:
        value: 要检查的值
        
    Returns:
        如果值为数值类型则返回True，否则返回False
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def to_bool(value: Any) -> bool:
    """
    将值转换为布尔值。
    
    Args:
        value: 要转换的值
        
    Returns:
        转换后的布尔值
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', 't', 'yes', 'y', '1')
    
    if isinstance(value, (int, float)):
        return value != 0
    
    return bool(value)


def to_list(value: Any) -> list:
    """
    将值转换为列表。
    
    Args:
        value: 要转换的值
        
    Returns:
        转换后的列表
    """
    if isinstance(value, list):
        return value
    
    if isinstance(value, (tuple, set)):
        return list(value)
    
    return [value]


def sanitize_string(value: Optional[str]) -> str:
    """
    清理字符串，确保它不是None或空字符串。
    
    Args:
        value: 要清理的字符串
        
    Returns:
        清理后的字符串
    """
    if value is None:
        return ""
    
    if not isinstance(value, str):
        return str(value)
    
    return value.strip()


def ensure_positive_integer(value: Any, default: int = 1) -> int:
    """
    确保值为正整数。
    
    Args:
        value: 要检查的值
        default: 如果值不是正整数则返回的默认值
        
    Returns:
        正整数值
    """
    try:
        num = int(value)
        return num if num > 0 else default
    except (ValueError, TypeError):
        return default
