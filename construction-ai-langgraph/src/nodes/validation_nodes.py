#!/usr/bin/env python3
# validation_nodes.py - 验证处理节点

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


async def validate_extraction_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """验证提取结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行提取结果验证节点")
    
    extracted_data = state.get("extracted_data", {})
    
    if not extracted_data:
        return {
            **state,
            "validation_results": {
                "valid": False,
                "message": "没有提取到数据",
                "errors": ["缺少提取数据"]
            }
        }
    
    # 验证必填字段
    required_fields = ["date", "workpoint", "team", "subproject", "position", "process", "quantity", "weather"]
    missing_fields = [field for field in required_fields if field not in extracted_data or not extracted_data[field]]
    
    # 验证数据格式
    format_errors = []
    
    # 验证日期格式（简单示例）
    if "date" in extracted_data:
        date_value = extracted_data["date"]
        # 简单的日期格式验证
        if len(date_value) < 8:
            format_errors.append(f"日期格式不正确: {date_value}")
    
    # 验证数量格式
    if "quantity" in extracted_data:
        quantity_value = extracted_data["quantity"]
        # 简单的数量格式验证
        if not any(char.isdigit() for char in quantity_value):
            format_errors.append(f"数量格式不正确: {quantity_value}")
    
    # 汇总验证结果
    errors = missing_fields + format_errors
    is_valid = len(errors) == 0
    
    validation_results = {
        "valid": is_valid,
        "message": "验证通过" if is_valid else f"验证失败，共 {len(errors)} 个错误",
        "errors": errors,
        "required_fields": required_fields,
        "checked_fields": list(extracted_data.keys())
    }
    
    logger.info(f"提取结果验证: {'通过' if is_valid else '失败'}")
    
    # 更新状态
    return {
        **state,
        "validation_results": validation_results
    }


async def calculate_confidence_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """计算置信度节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行置信度计算节点")
    
    # 从不同来源获取置信度
    ocr_confidence = state.get("ocr_confidence", 0.0)
    ner_confidence = state.get("ner_results", {}).get("confidence", 0.0)
    vlm_confidence = state.get("vlm_confidence", 0.0)
    
    # 计算整体置信度（加权平均）
    # OCR: 30%, NER: 40%, VLM: 30%
    overall_confidence = (ocr_confidence * 0.3) + (ner_confidence * 0.4) + (vlm_confidence * 0.3)
    
    # 确保置信度在0-1之间
    overall_confidence = max(0.0, min(1.0, overall_confidence))
    
    # 计算各个字段的置信度（简单示例）
    extracted_data = state.get("extracted_data", {})
    field_confidences = {}
    
    for field in extracted_data:
        # 简单的字段置信度计算，实际项目中应该更复杂
        field_confidences[field] = overall_confidence
    
    confidence_scores = {
        "overall": overall_confidence,
        "ocr": ocr_confidence,
        "ner": ner_confidence,
        "vlm": vlm_confidence,
        "fields": field_confidences
    }
    
    logger.info(f"计算置信度: {overall_confidence:.2f}")
    
    # 更新状态
    return {
        **state,
        "confidence_scores": confidence_scores
    }
