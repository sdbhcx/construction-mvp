#!/usr/bin/env python3
# vector_search_nodes.py - 向量搜索处理节点

import logging
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


async def vector_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行向量搜索节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行向量搜索节点")
    
    query_text = state.get("query_text")
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 模拟向量搜索结果
    # 实际项目中，这里应该调用真实的向量搜索服务或数据库
    search_results = [
        {
            "id": "doc_001",
            "title": "B区施工记录报告",
            "content": "2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组，工点：B区1号楼，分项工程：主体结构，部位：3层，工序：混凝土浇筑，完成量：100m³，天气：晴",
            "score": 0.95,
            "source": "construction_record",
            "date": "2024-03-15"
        },
        {
            "id": "doc_002",
            "title": "B区安全检查记录",
            "content": "2024年3月10日，B区1号楼脚手架未固定，已要求整改。2024年3月12日，B区2号楼安全网破损，已修复。",
            "score": 0.88,
            "source": "safety_record",
            "date": "2024-03-12"
        },
        {
            "id": "doc_003",
            "title": "B区进度月报",
            "content": "B区3月份完成混凝土浇筑500m³，钢筋绑扎300t，模板安装200㎡。",
            "score": 0.82,
            "source": "progress_report",
            "date": "2024-03-31"
        },
        {
            "id": "doc_004",
            "title": "施工规范手册",
            "content": "混凝土浇筑施工规范：1. 模板支撑应牢固；2. 混凝土坍落度应符合要求；3. 振捣应密实；4. 养护应及时。",
            "score": 0.75,
            "source": "manual",
            "date": "2023-01-01"
        },
        {
            "id": "doc_005",
            "title": "B区施工日志",
            "content": "2024年3月14日：B区1号楼开始支模；2024年3月15日：B区1号楼混凝土浇筑；2024年3月16日：B区2号楼钢筋绑扎。",
            "score": 0.72,
            "source": "daily_log",
            "date": "2024-03-16"
        }
    ]
    
    # 更新状态
    return {
        **state,
        "vector_results": search_results,
        "vector_search_completed": True,
        "vector_result_count": len(search_results)
    }


async def rerank_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """重排序搜索结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行结果重排序节点")
    
    vector_results = state.get("vector_results", [])
    
    if not vector_results:
        return {
            **state,
            "reranked_results": [],
            "rerank_completed": True
        }
    
    # 模拟重排序
    # 实际项目中，这里应该调用真实的重排序模型或算法
    # 简单的重排序：根据分数和日期排序
    reranked = sorted(
        vector_results,
        key=lambda x: (x["score"], x["date"]),
        reverse=True
    )
    
    # 只保留前3个结果
    reranked = reranked[:3]
    
    # 更新状态
    return {
        **state,
        "reranked_results": reranked,
        "rerank_completed": True,
        "reranked_result_count": len(reranked)
    }


async def extract_relevant_passages_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """提取相关段落节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行相关段落提取节点")
    
    reranked_results = state.get("reranked_results", [])
    query_text = state.get("query_text", "")
    
    if not reranked_results:
        return {
            **state,
            "relevant_passages": [],
            "passage_extraction_completed": True
        }
    
    # 提取相关段落
    relevant_passages = []
    
    for result in reranked_results:
        content = result.get("content", "")
        
        if not content:
            continue
        
        # 简单的相关段落提取：按句子分割，找包含查询关键词的句子
        sentences = content.split("。")
        relevant_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                # 检查是否包含查询关键词
                has_keyword = any(keyword in sentence for keyword in query_text.split())
                if has_keyword:
                    relevant_sentences.append(sentence.strip() + "。")
        
        if relevant_sentences:
            passage = {
                "document_id": result.get("id"),
                "title": result.get("title"),
                "passages": relevant_sentences,
                "score": result.get("score", 0.0)
            }
            relevant_passages.append(passage)
    
    # 更新状态
    return {
        **state,
        "relevant_passages": relevant_passages,
        "passage_extraction_completed": True
    }


async def format_vector_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """格式化向量搜索结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行向量搜索结果格式化节点")
    
    reranked_results = state.get("reranked_results", [])
    
    if not reranked_results:
        return {
            **state,
            "formatted_vector_results": [],
            "vector_formatted": True
        }
    
    # 格式化向量搜索结果
    formatted_results = []
    
    for result in reranked_results:
        formatted_result = {
            "id": result.get("id"),
            "title": result.get("title"),
            "content": result.get("content", "")[:150] + "..." if len(result.get("content", "")) > 150 else result.get("content", ""),
            "score": round(result.get("score", 0.0), 2),
            "source": result.get("source"),
            "date": result.get("date")
        }
        formatted_results.append(formatted_result)
    
    # 更新状态
    return {
        **state,
        "formatted_vector_results": formatted_results,
        "vector_formatted": True
    }
