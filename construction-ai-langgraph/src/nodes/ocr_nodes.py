#!/usr/bin/env python3
# ocr_nodes.py - OCR处理节点

import logging
from typing import Dict, Any, Optional
import base64
import io
from PIL import Image
from paddleocr import PaddleOCR

logger = logging.getLogger(__name__)

# 初始化PaddleOCR实例（全局实例，避免重复初始化）
# enable_mkldnn参数用于启用CPU加速
# lang='ch'表示识别中文
ocr = PaddleOCR(use_angle_cls=True, lang='ch', enable_mkldnn=True)


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
        # 调用真实的PaddleOCR服务
        logger.info(f"使用PaddleOCR处理文件: {file_path}")
        
        # 执行OCR识别
        # PaddleOCR.ocr()返回格式: [[[[bbox], (text, confidence)], ...]]
        ocr_output = ocr.ocr(file_path, cls=True)
        
        logger.info(f"OCR识别完成，共识别到 {len(ocr_output)} 页")
        
        # 解析OCR结果
        pages = len(ocr_output)
        all_text = []
        all_blocks = []
        confidence_scores = []
        
        for page_num, page_content in enumerate(ocr_output):
            page_text = []
            
            if not page_content:
                continue
            
            for line_idx, line in enumerate(page_content):
                # 提取文本和置信度
                text = line[1][0]
                confidence = line[1][1]
                
                # 提取边界框
                bbox = line[0]
                # 将边界框转换为 [x1, y1, x2, y2] 格式
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                bbox_formatted = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                
                # 添加到结果列表
                page_text.append(text)
                all_text.append(text)
                confidence_scores.append(confidence)
                
                # 添加到区块列表
                all_blocks.append({
                    "text": text,
                    "confidence": confidence,
                    "bbox": bbox_formatted,
                    "page": page_num + 1,
                    "line": line_idx + 1
                })
            
        # 计算平均置信度
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # 构建与原来格式兼容的结果
        ocr_results = {
            "text": "，".join(all_text),
            "confidence": avg_confidence,
            "pages": pages,
            "layout": {
                "blocks": all_blocks
            },
            "raw_output": ocr_output  # 保存原始输出，便于调试
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
