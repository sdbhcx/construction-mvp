#!/usr/bin/env python3
# answer_synthesis_nodes.py - 回答合成处理节点

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


async def synthesize_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """合成回答节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行回答合成节点")
    
    query_text = state.get("query_text")
    sql_results = state.get("sql_results", [])
    reranked_results = state.get("reranked_results", [])
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 合成回答
    answer = ""
    answer_confidence = 0.0
    
    # 检查是否有结构化结果
    if sql_results:
        answer, confidence = await _synthesize_from_sql(sql_results, query_text)
        answer_confidence = confidence
    elif reranked_results:
        # 没有结构化结果，从非结构化结果中合成
        answer, confidence = await _synthesize_from_vector(reranked_results, query_text)
        answer_confidence = confidence
    else:
        # 没有任何结果
        answer = "没有找到相关信息。"
        answer_confidence = 0.1
    
    # 更新状态
    return {
        **state,
        "synthesized_answer": answer,
        "answer_confidence": answer_confidence,
        "answer_synthesized": True
    }


async def validate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """验证回答节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行回答验证节点")
    
    answer = state.get("synthesized_answer")
    answer_confidence = state.get("answer_confidence", 0.0)
    
    if not answer:
        return {
            **state,
            "answer_valid": False,
            "answer_validation_error": "回答内容为空"
        }
    
    # 简单的回答验证
    validation = {
        "length_valid": len(answer) > 10,  # 回答长度至少10个字符
        "confidence_valid": answer_confidence > 0.3,  # 置信度至少0.3
        "content_valid": "没有找到相关信息" not in answer  # 不是默认回答
    }
    
    answer_valid = all(validation.values())
    
    # 更新状态
    return {
        **state,
        "answer_valid": answer_valid,
        "answer_validation": validation,
        "answer_validation_completed": True
    }


async def _synthesize_from_sql(sql_results: List[Dict[str, Any]], query_text: str) -> tuple[str, float]:
    """从SQL结果合成回答
    
    Args:
        sql_results: SQL查询结果
        query_text: 查询文本
        
    Returns:
        tuple[str, float]: 合成的回答和置信度
    """
    # 简单的SQL结果合成
    if "安全隐患" in query_text:
        # 安全隐患查询
        answer = f"根据查询，最近一个月共有 {len(sql_results)} 条安全隐患记录：\n"
        for i, hazard in enumerate(sql_results, 1):
            answer += f"{i}. {hazard.get('location', '未知位置')}：{hazard.get('description', '未知描述')}（{hazard.get('severity', '未知严重程度')}）- {hazard.get('date', '未知日期')}\n"
        confidence = 0.95
    elif "完成量" in query_text or "进度" in query_text:
        # 进度查询
        answer = "施工进度情况如下：\n"
        for record in sql_results:
            answer += f"{record.get('workpoint', '未知工点')} - {record.get('process', '未知工序')}：{record.get('total_quantity', 0)}{'m³' if '混凝土' in record.get('process', '') else ''}\n"
        confidence = 0.90
    elif "施工记录" in query_text:
        # 施工记录查询
        answer = f"查询到 {len(sql_results)} 条施工记录：\n"
        for record in sql_results:
            answer += f"{record.get('date', '未知日期')} - {record.get('workpoint', '未知工点')} - {record.get('process', '未知工序')} - {record.get('quantity', 0)}{'m³' if '混凝土' in record.get('process', '') else ''}\n"
        confidence = 0.85
    else:
        # 默认合成
        answer = f"查询到 {len(sql_results)} 条记录：\n"
        for record in sql_results:
            answer += "；".join([f"{k}: {v}" for k, v in record.items()]) + "\n"
        confidence = 0.80
    
    return answer.strip(), confidence


async def _synthesize_from_vector(vector_results: List[Dict[str, Any]], query_text: str) -> tuple[str, float]:
    """从向量搜索结果合成回答
    
    Args:
        vector_results: 向量搜索结果
        query_text: 查询文本
        
    Returns:
        tuple[str, float]: 合成的回答和置信度
    """
    # 简单的向量结果合成
    if "安全隐患" in query_text:
        # 安全隐患查询
        answer = "根据查询到的安全记录：\n"
        for result in vector_results:
            answer += f"- {result.get('title', '未知文档')}：{result.get('content', '').replace('。', '。\n')}\n"
        confidence = 0.85
    elif "施工规范" in query_text or "如何" in query_text:
        # 规范查询
        answer = "根据施工规范：\n"
        for result in vector_results:
            if "规范" in result.get('title', '') or "手册" in result.get('title', ''):
                answer += result.get('content', '') + "\n"
        confidence = 0.90
    elif "进度" in query_text or "完成" in query_text:
        # 进度查询
        answer = "施工进度情况：\n"
        for result in vector_results:
            if "进度" in result.get('title', '') or "月报" in result.get('title', ''):
                answer += result.get('content', '') + "\n"
        confidence = 0.80
    else:
        # 默认合成
        answer = "根据相关文档：\n"
        for result in vector_results:
            answer += f"【{result.get('title', '未知文档')}】{result.get('content', '')}\n"
        confidence = 0.75
    
    return answer.strip(), confidence


async def format_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """格式化回答节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行回答格式化节点")
    
    answer = state.get("synthesized_answer")
    answer_confidence = state.get("answer_confidence", 0.0)
    
    if not answer:
        return {
            **state,
            "formatted_answer": "没有找到相关信息。",
            "answer_formatted": True
        }
    
    # 格式化回答
    formatted_answer = f"## 回答\n\n{answer}\n\n**置信度**: {round(answer_confidence * 100, 1)}%"
    
    # 更新状态
    return {
        **state,
        "formatted_answer": formatted_answer,
        "answer_formatted": True
    }
