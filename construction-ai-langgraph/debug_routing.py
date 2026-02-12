#!/usr/bin/env python3
# debug_routing.py - 智能体调度器路由调试脚本

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agents.orchestrator import OrchestratorAgent

# 配置日志为DEBUG级别
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def debug_document_routing():
    """调试文档路由功能"""
    logger.info("=== 开始调试文档路由功能 ===")
    
    orchestrator = OrchestratorAgent()
    
    # 测试图片文档路由
    logger.info("\n1. 调试图片文档路由")
    image_doc = {
        'file_path': '/path/to/test.jpg',
        'file_type': 'image',
        'file_size': 2048,
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(image_doc)
        logger.info(f"图片文档路由结果: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"图片文档路由失败: {e}")


if __name__ == "__main__":
    debug_document_routing()
