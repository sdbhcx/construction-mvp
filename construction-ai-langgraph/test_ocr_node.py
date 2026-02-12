#!/usr/bin/env python3
# test_ocr_node.py - OCR节点测试脚本

import logging
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from nodes.ocr_nodes import run_ocr_node, postprocess_ocr_node

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_ocr_node():
    """测试OCR节点"""
    logger.info("=== 开始测试OCR节点 ===")
    
    # 创建一个简单的测试状态
    test_state = {
        "file_path": "d:\project\my\deep-learning\construction-mvp\construction-ai-langgraph\test_image.jpg",  # 替换为实际的测试图片路径
        "file_type": "jpg"
    }
    
    try:
        # 执行OCR节点
        result_state = await run_ocr_node(test_state)
        
        logger.info("✓ OCR节点执行成功")
        logger.info(f"识别到的文本: {result_state.get('extracted_text')}")
        logger.info(f"OCR置信度: {result_state.get('ocr_confidence')}")
        logger.info(f"识别页数: {result_state.get('ocr_results', {}).get('pages')}")
        logger.info(f"识别区块数: {len(result_state.get('ocr_results', {}).get('layout', {}).get('blocks', []))}")
        
        # 执行后处理节点
        postprocess_state = await postprocess_ocr_node(result_state)
        
        logger.info("\n✓ OCR后处理节点执行成功")
        logger.info(f"后处理后的文本: {postprocess_state.get('extracted_text')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ OCR节点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 检查是否有测试图片
    test_image_path = "d:\project\my\deep-learning\construction-mvp\construction-ai-langgraph\test_image.jpg"
    if not os.path.exists(test_image_path):
        logger.warning(f"测试图片不存在: {test_image_path}")
        logger.info("请将测试图片放在项目根目录下，命名为test_image.jpg")
        sys.exit(1)
    
    # 运行测试
    asyncio.run(test_ocr_node())
