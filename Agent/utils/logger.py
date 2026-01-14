"""
Cheat Engine AI Agent 的日志工具。

该模块提供了在整个代理中设置和配置日志的函数。
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None, max_bytes: int = 10485760, backup_count: int = 5):
    """
    为应用程序设置日志配置。
    
    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径（可选，如果未提供则记录到控制台）
        max_bytes: 日志文件轮转前的最大字节数
        backup_count: 要保留的备份文件数量
    """
    # 将字符串级别转换为日志常量
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建格式化器
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 清除现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    
    # 将控制台处理器添加到根日志记录器
    root_logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler with rotation
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(detailed_formatter)
        
        # Add file handler to root logger
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers if needed
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, msg: str = "An exception occurred"):
    """
    Log the current exception with a custom message.
    
    Args:
        logger: The logger to use
        msg: Custom message to include with the exception
    """
    logger.exception(msg)


def log_function_call(logger: logging.Logger, func_name: str, args: tuple = (), kwargs: dict = None):
    """
    Log a function call with its arguments.
    
    Args:
        logger: The logger to use
        func_name: The name of the function being called
        args: The positional arguments passed to the function
        kwargs: The keyword arguments passed to the function
    """
    if kwargs is None:
        kwargs = {}
    
    args_str = ', '.join([repr(arg) for arg in args])
    kwargs_str = ', '.join([f"{k}={repr(v)}" for k, v in kwargs.items()])
    
    all_args = []
    if args_str:
        all_args.append(args_str)
    if kwargs_str:
        all_args.append(kwargs_str)
    
    args_repr = ', '.join(all_args)
    logger.debug(f"Calling {func_name}({args_repr})")