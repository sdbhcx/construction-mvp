#!/usr/bin/env python3
# intent_nodes.py - 意图识别处理节点

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


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
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 结构化查询关键词
    structured_keywords = [
        '多少', '数量', '统计', '总', '平均', '计数', '完成', '进度', '工时', '成本',
        '有多少', '共有', '总计', '合计', '百分比', '比例', '排行', '排名',
        '多少个', '多少人', '多少吨', '多少米', '多少平方', '多少立方',
        '统计', '汇总', '合计', '总计', '总数', '总量'
    ]
    
    # 非结构化查询关键词
    unstructured_keywords = [
        '什么', '如何', '为什么', '原因', '说明', '解释', '定义', '文档', '记录', '报告',
        '怎么', '怎样', '如何', '为何', '因为', '所以', '导致', '由于', '结果', '影响',
        '是什么', '为什么', '怎么办', '如何', '怎样', '解释', '说明', '含义', '定义',
        '方法', '步骤', '流程', '指南', '规则', '规范', '标准', '要求', '注意事项'
    ]
    
    # 检查意图
    has_structured = any(keyword in preprocessed_query for keyword in structured_keywords)
    has_unstructured = any(keyword in preprocessed_query for keyword in unstructured_keywords)
    
    # 确定意图
    if has_structured and has_unstructured:
        intent = "hybrid_query"
    elif has_structured:
        intent = "structured_query"
    elif has_unstructured:
        intent = "unstructured_query"
    else:
        intent = "unknown"
    
    # 计算意图置信度（简单示例）
    confidence = 0.8
    if intent == "unknown":
        confidence = 0.3
    
    logger.info(f"查询意图识别结果: {intent} (置信度: {confidence:.2f})")
    
    # 更新状态
    return {
        **state,
        "intent": intent,
        "intent_confidence": confidence
    }
