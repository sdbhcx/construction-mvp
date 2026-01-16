#!/usr/bin/env python3
# output_nodes.py - 输出处理节点

import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def format_output_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """格式化输出节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行输出格式化节点")
    
    extracted_data = state.get("extracted_data", {})
    
    if not extracted_data:
        return {
            **state,
            "formatted_output": {
                "status": "failed",
                "message": "没有提取到有效数据",
                "data": {}
            }
        }
    
    # 格式化输出
    formatted = {
        "status": "success",
        "message": "数据提取成功",
        "data": extracted_data,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "confidence": state.get("vlm_confidence", 0.0) or state.get("ner_results", {}).get("confidence", 0.0),
            "verified": state.get("vlm_verified", False),
            "processing_time": state.get("processing_time", 0.0),
            "steps": state.get("current_step", "unknown")
        }
    }
    
    # 更新状态
    return {
        **state,
        "formatted_output": formatted
    }


async def save_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """保存结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行结果保存节点")
    
    formatted_output = state.get("formatted_output", {})
    file_path = state.get("file_path")
    
    if not formatted_output or not formatted_output.get("status") == "success":
        logger.warning("没有可保存的有效结果")
        return state
    
    # 模拟结果保存
    # 实际项目中，这里应该将结果保存到数据库或文件系统
    
    # 生成结果文件名
    if file_path:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        result_file_name = f"{base_name}_result.json"
    else:
        result_file_name = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 保存到临时目录
    result_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(result_dir, exist_ok=True)
    result_path = os.path.join(result_dir, result_file_name)
    
    # 保存结果
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"结果已保存到: {result_path}")
    
    # 更新状态
    return {
        **state,
        "result_saved": True,
        "result_path": result_path
    }


async def format_query_output_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """格式化查询输出节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行查询输出格式化节点")
    
    synthesized_answer = state.get("synthesized_answer")
    answer_confidence = state.get("answer_confidence", 0.0)
    
    # 格式化查询输出
    formatted = {
        "status": "success",
        "query": state.get("query_text"),
        "answer": synthesized_answer,
        "confidence": answer_confidence,
        "sources": [result.get("title") for result in state.get("reranked_results", [])],
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "intent": state.get("intent", "unknown"),
            "processing_time": state.get("processing_time", 0.0)
        }
    }
    
    # 更新状态
    return {
        **state,
        "formatted_output": formatted
    }


async def save_query_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """保存查询结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行查询结果保存节点")
    
    formatted_output = state.get("formatted_output", {})
    
    if not formatted_output:
        logger.warning("没有可保存的查询结果")
        return state
    
    # 模拟查询结果保存
    # 实际项目中，这里应该将查询结果保存到数据库或日志系统
    
    # 生成查询结果文件名
    query_hash = abs(hash(formatted_output.get("query", ""))) % 10000
    result_file_name = f"query_result_{query_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # 保存到临时目录
    result_dir = os.path.join(os.getcwd(), "query_results")
    os.makedirs(result_dir, exist_ok=True)
    result_path = os.path.join(result_dir, result_file_name)
    
    # 保存结果
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_output, f, ensure_ascii=False, indent=2)
    
    logger.info(f"查询结果已保存到: {result_path}")
    
    # 更新状态
    return {
        **state,
        "query_result_saved": True,
        "query_result_path": result_path
    }
