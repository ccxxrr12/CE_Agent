"""
Cheat Engine AI Agent 的日志工具。

该模块提供了一个简单的日志记录接口，用于记录工具执行的状态和错误。
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# 默认日志配置
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_FILE = 'ce_agent.log'
DEFAULT_LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_LOG_BACKUP_COUNT = 5

def get_logger(name: str, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    获取或创建一个日志记录器。
    
    Args:
        name: 日志记录器的名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果 logger 已经配置过，直接返回
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 创建文件处理器（带旋转功能）
    log_file = os.path.join(os.getcwd(), DEFAULT_LOG_FILE)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=DEFAULT_LOG_MAX_BYTES,
        backupCount=DEFAULT_LOG_BACKUP_COUNT
    )
    file_handler.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到 logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
