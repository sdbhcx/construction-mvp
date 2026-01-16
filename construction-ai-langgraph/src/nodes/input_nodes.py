#!/usr/bin/env python3
# input_nodes.py - 输入处理节点

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def load_document_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """加载文档节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行文档加载节点")
    
    file_path = state.get("file_path")
    
    if not file_path:
        raise ValueError("文件路径不能为空")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 获取文件信息
    file_size = os.path.getsize(file_path)
    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    # 读取文件内容（根据文件类型）
    file_type = state.get("file_type")
    if not file_type:
        # 从文件扩展名获取文件类型
        _, ext = os.path.splitext(file_path)
        file_type = ext.lower().lstrip('.')
    
    # 更新状态
    return {
        **state,
        "file_size": file_size,
        "file_mtime": file_mtime.isoformat(),
        "file_type": file_type,
        "file_exists": True
    }


async def validate_document_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """验证文档节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行文档验证节点")
    
    file_path = state.get("file_path")
    file_type = state.get("file_type")
    file_size = state.get("file_size")
    
    # 验证文件类型
    supported_types = ["jpg", "jpeg", "png", "pdf", "txt", "md"]
    if file_type not in supported_types:
        raise ValueError(f"不支持的文件类型: {file_type}，支持的类型: {supported_types}")
    
    # 验证文件大小（最大100MB）
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        raise ValueError(f"文件过大: {file_size}字节，最大支持: {max_size}字节")
    
    # 更新状态
    return {
        **state,
        "validation_passed": True,
        "validation_results": {
            "file_type": "valid",
            "file_size": "valid",
            "file_path": "valid"
        }
    }


async def preprocess_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """预处理查询节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行查询预处理节点")
    
    query_text = state.get("query_text")
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 预处理查询文本
    processed_query = query_text.strip()
    processed_query = processed_query.lower()
    
    # 移除不必要的标点符号
    import re
    processed_query = re.sub(r'[^\w\s]', '', processed_query)
    
    # 更新状态
    return {
        **state,
        "preprocessed_query": processed_query,
        "query_length": len(query_text)
    }


async def validate_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """验证查询节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行查询验证节点")
    
    query_text = state.get("query_text")
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 验证查询长度
    if len(query_text) < 3:
        raise ValueError("查询文本太短，至少需要3个字符")
    
    if len(query_text) > 1000:
        raise ValueError("查询文本太长，最多支持1000个字符")
    
    # 更新状态
    return {
        **state,
        "query_valid": True,
        "validation_results": {
            "query_length": "valid",
            "query_content": "valid"
        }
    }


async def recognize_intent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """识别查询意图节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行查询意图识别节点")
    
    query_text = state.get("query_text")
    preprocessed_query = state.get("preprocessed_query", query_text)
    
    # 简单的意图识别逻辑
    structured_keywords = [
        '多少', '数量', '统计', '总', '平均', '计数', '完成', '进度', '工时', '成本',
        '有多少', '共有', '总计', '合计', '百分比', '比例', '排行', '排名'
    ]
    
    unstructured_keywords = [
        '什么', '如何', '为什么', '原因', '说明', '解释', '定义', '文档', '记录', '报告',
        '怎么', '怎样', '如何', '为何', '因为', '所以', '导致', '由于', '结果', '影响'
    ]
    
    # 检查意图
    is_structured = any(keyword in preprocessed_query for keyword in structured_keywords)
    is_unstructured = any(keyword in preprocessed_query for keyword in unstructured_keywords)
    
    if is_structured and is_unstructured:
        intent = "hybrid_query"
    elif is_structured:
        intent = "structured_query"
    elif is_unstructured:
        intent = "unstructured_query"
    else:
        intent = "unknown"
    
    # 更新状态
    return {
        **state,
        "intent": intent,
        "intent_confidence": 0.8  # 简单实现，固定置信度
    }
