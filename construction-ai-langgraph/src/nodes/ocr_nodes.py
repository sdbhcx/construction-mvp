#!/usr/bin/env python3
# ocr_nodes.py - OCR处理节点

import logging
from typing import Dict, Any, Optional
import base64
import io
from PIL import Image

logger = logging.getLogger(__name__)


async def run_ocr_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行OCR识别节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行OCR识别节点")
    
    file_path = state.get("file_path")
    file_type = state.get("file_type")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    try:
        # 模拟OCR识别结果
        # 实际项目中，这里应该调用真实的OCR服务
        ocr_results = {
            "text": "2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组，工点：B区1号楼，分项工程：主体结构，部位：3层，工序：混凝土浇筑，完成量：100m³，天气：晴",
            "confidence": 0.95,
            "pages": 1,
            "layout": {
                "blocks": [
                    {
                        "text": "2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组",
                        "confidence": 0.96,
                        "bbox": [0, 0, 500, 100]
                    },
                    {
                        "text": "工点：B区1号楼，分项工程：主体结构，部位：3层",
                        "confidence": 0.94,
                        "bbox": [0, 100, 500, 200]
                    },
                    {
                        "text": "工序：混凝土浇筑，完成量：100m³，天气：晴",
                        "confidence": 0.95,
                        "bbox": [0, 200, 500, 300]
                    }
                ]
            }
        }
        
        # 更新状态
        return {
            **state,
            "ocr_results": ocr_results,
            "extracted_text": ocr_results.get("text", ""),
            "ocr_confidence": ocr_results.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        raise


async def postprocess_ocr_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """OCR结果后处理节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行OCR结果后处理节点")
    
    ocr_text = state.get("extracted_text")
    
    if not ocr_text:
        return state
    
    # 简单的后处理：移除多余空格、统一格式
    processed_text = ocr_text
    
    # 移除多余的换行符和空格
    processed_text = ' '.join(processed_text.split())
    
    # 统一日期格式（简单示例）
    import re
    # 将类似"2024年3月15日"转换为"2024-03-15"
    processed_text = re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日', r'\1-\2-\3', processed_text)
    
    # 更新状态
    return {
        **state,
        "extracted_text": processed_text,
        "ocr_postprocessed": True
    }


async def get_image_preview_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """获取图片预览节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行图片预览生成节点")
    
    file_path = state.get("file_path")
    file_type = state.get("file_type")
    
    if not file_path or file_type not in ["jpg", "jpeg", "png"]:
        return state
    
    try:
        # 生成图片预览
        with Image.open(file_path) as img:
            # 调整大小
            img.thumbnail((300, 300))
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            
            return {
                **state,
                "image_preview": f"data:image/jpeg;base64,{base64_image}",
                "preview_width": img.width,
                "preview_height": img.height
            }
            
    except Exception as e:
        logger.error(f"生成图片预览失败: {e}")
        return state
