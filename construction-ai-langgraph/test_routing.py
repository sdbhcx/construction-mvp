#!/usr/bin/env python3
# test_routing.py - 智能体调度器路由规则测试脚本

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from agents.orchestrator import OrchestratorAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_document_routing():
    """测试文档路由功能"""
    logger.info("=== 开始测试文档路由功能 ===")
    
    orchestrator = OrchestratorAgent()
    
    # 测试用例1: PDF文档（默认配置）
    logger.info("\n1. 测试PDF文档路由")
    pdf_doc = {
        'file_path': '/path/to/test.pdf',
        'file_type': 'pdf',
        'file_size': 1024,
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(pdf_doc)
        logger.info(f"✓ PDF文档路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ PDF文档路由失败: {e}")
    
    # 测试用例2: 图片文档（OCR路由）
    logger.info("\n2. 测试图片文档路由")
    image_doc = {
        'file_path': '/path/to/test.jpg',
        'file_type': 'image',
        'file_size': 2048,
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(image_doc)
        logger.info(f"✓ 图片文档路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 图片文档路由失败: {e}")
    
    # 测试用例3: Excel文档（表格分析路由）
    logger.info("\n3. 测试Excel文档路由")
    excel_doc = {
        'file_path': '/path/to/test.xlsx',
        'file_type': 'excel',
        'file_size': 4096,
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(excel_doc)
        logger.info(f"✓ Excel文档路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ Excel文档路由失败: {e}")
    
    # 测试用例4: 用户意图为存储（存储路由）
    logger.info("\n4. 测试用户意图为存储的文档路由")
    store_doc = {
        'file_path': '/path/to/store.pdf',
        'file_type': 'pdf',
        'file_size': 1024,
        'user_intent': 'store',
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(store_doc)
        logger.info(f"✓ 存储意图文档路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 存储意图文档路由失败: {e}")
    
    # 测试用例5: 大文件（低优先级）
    logger.info("\n5. 测试大文件路由")
    large_doc = {
        'file_path': '/path/to/large.pdf',
        'file_type': 'pdf',
        'file_size': 20 * 1024 * 1024,  # 20MB
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_document(large_doc)
        logger.info(f"✓ 大文件路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 大文件路由失败: {e}")
    
    return orchestrator


def test_query_routing(orchestrator):
    """测试查询路由功能"""
    logger.info("\n=== 开始测试查询路由功能 ===")
    
    # 测试用例1: 默认查询（问题）
    logger.info("\n1. 测试默认查询路由")
    default_query = {
        'query_text': '项目A的进度如何？',
        'user_id': 'user_789',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_query(default_query)
        logger.info(f"✓ 默认查询路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 默认查询路由失败: {e}")
    
    # 测试用例2: 统计查询
    logger.info("\n2. 测试统计查询路由")
    stats_query = {
        'query_text': '统计上个月的安全隐患数量',
        'intent': 'statistics',
        'user_id': 'user_789',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_query(stats_query)
        logger.info(f"✓ 统计查询路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 统计查询路由失败: {e}")
    
    # 测试用例3: 报告查询
    logger.info("\n3. 测试报告查询路由")
    report_query = {
        'query_text': '生成项目进度报告',
        'intent': 'report',
        'user_id': 'user_789',
        'project_id': 'proj_456'
    }
    try:
        task = orchestrator.route_query(report_query)
        logger.info(f"✓ 报告查询路由成功: 队列={task.metadata.get('queue', '未知')}, 任务类型={task.type}, 优先级={task.priority}")
    except Exception as e:
        logger.error(f"✗ 报告查询路由失败: {e}")


if __name__ == "__main__":
    logger.info("智能体调度器路由规则测试开始")
    
    # 测试文档路由
    orchestrator = test_document_routing()
    
    # 测试查询路由
    test_query_routing(orchestrator)
    
    logger.info("\n智能体调度器路由规则测试完成")
