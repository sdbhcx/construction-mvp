#!/usr/bin/env python3
# logger.py - 日志工具

import logging
import sys
from datetime import datetime
import os

# 创建日志目录
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 创建日志文件名
log_file = os.path.join(log_dir, f"construction-ai-{datetime.now().strftime('%Y%m%d')}.log")

# 配置日志记录器
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 移除默认处理器（防止重复输出）
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.INFO)

# 定义日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器到记录器
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# 创建一个用于模块级别的日志记录器
module_logger = logging.getLogger(__name__)
