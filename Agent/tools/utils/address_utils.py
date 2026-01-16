"""
Cheat Engine AI Agent 的地址处理工具。

该模块提供了用于处理内存地址的工具函数，如地址转换、验证和格式化等。
"""
from typing import Optional, Union


def parse_address(address: Union[str, int]) -> Optional[int]:
    """
    将字符串或整数地址解析为整数。
    
    Args:
        address: 要解析的地址，可以是十六进制字符串（带或不带0x前缀）或整数
        
    Returns:
        解析后的整数地址，如果解析失败则返回None
    """
    if isinstance(address, int):
        return address
    
    if not isinstance(address, str):
        return None
    
    try:
        # 处理带0x前缀的十六进制字符串
        if address.startswith('0x') or address.startswith('0X'):
            return int(address, 16)
        # 处理不带前缀的十六进制字符串
        elif all(c in '0123456789abcdefABCDEF' for c in address):
            return int(address, 16)
        # 处理十进制字符串
        else:
            return int(address)
    except ValueError:
        return None


def format_address(address: int, with_prefix: bool = True) -> str:
    """
    将整数地址格式化为字符串。
    
    Args:
        address: 要格式化的整数地址
        with_prefix: 是否包含0x前缀
        
    Returns:
        格式化后的地址字符串
    """
    if not isinstance(address, int):
        raise TypeError(f"地址必须是整数，而不是{type(address).__name__}")
    
    if with_prefix:
        return f'0x{address:08X}'
    else:
        return f'{address:08X}'


def is_valid_address(address: Union[str, int]) -> bool:
    """
    检查地址是否有效。
    
    Args:
        address: 要检查的地址
        
    Returns:
        如果地址有效则返回True，否则返回False
    """
    parsed = parse_address(address)
    if parsed is None:
        return False
    
    # 检查地址是否在有效范围内（32位或64位）
    return 0 <= parsed <= 0xFFFFFFFFFFFFFFFF


def align_address(address: int, alignment: int) -> int:
    """
    将地址对齐到指定的边界。
    
    Args:
        address: 要对齐的地址
        alignment: 对齐边界（必须是2的幂）
        
    Returns:
        对齐后的地址
    """
    if not isinstance(address, int) or not isinstance(alignment, int):
        raise TypeError("地址和对齐边界必须是整数")
    
    if alignment <= 0 or (alignment & (alignment - 1)) != 0:
        raise ValueError("对齐边界必须是正数且是2的幂")
    
    return (address + alignment - 1) & ~(alignment - 1)


def calculate_offset(base: int, target: int) -> int:
    """
    计算两个地址之间的偏移量。
    
    Args:
        base: 基地址
        target: 目标地址
        
    Returns:
        从基地址到目标地址的偏移量
    """
    if not isinstance(base, int) or not isinstance(target, int):
        raise TypeError("基地址和目标地址必须是整数")
    
    return target - base


def resolve_pointer_chain(base: int, offsets: list, memory_reader) -> Optional[int]:
    """
    解析指针链。
    
    Args:
        base: 基地址
        offsets: 偏移量列表
        memory_reader: 用于读取内存的函数，签名为 (address: int, size: int) -> bytes
        
    Returns:
        解析后的最终地址，如果解析失败则返回None
    """
    try:
        current_address = base
        for offset in offsets:
            # 读取指针值（8字节，因为我们假设是64位系统）
            pointer_bytes = memory_reader(current_address, 8)
            current_address = int.from_bytes(pointer_bytes, byteorder='little') + offset
        return current_address
    except Exception:
        return None
