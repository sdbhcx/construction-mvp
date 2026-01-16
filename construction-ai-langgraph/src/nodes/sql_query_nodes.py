#!/usr/bin/env python3
# sql_query_nodes.py - SQL查询处理节点

import logging
from typing import Dict, Any, List, Optional
import sqlite3
import re

logger = logging.getLogger(__name__)


async def generate_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """生成SQL查询节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行SQL生成节点")
    
    query_text = state.get("query_text")
    preprocessed_query = state.get("preprocessed_query")
    
    if not query_text:
        raise ValueError("查询文本不能为空")
    
    # 模拟SQL生成
    # 实际项目中，这里应该调用真实的SQL生成模型或服务
    sql_query = ""
    
    # 简单的模板匹配示例
    if "安全隐患" in preprocessed_query:
        sql_query = "SELECT * FROM safety_hazards WHERE date >= DATE('now', '-1 month')"
    elif "完成量" in preprocessed_query or "进度" in preprocessed_query:
        sql_query = "SELECT workpoint, process, SUM(quantity) as total_quantity FROM construction_records GROUP BY workpoint, process"
    elif "施工记录" in preprocessed_query:
        sql_query = "SELECT * FROM construction_records LIMIT 10"
    elif "天气" in preprocessed_query:
        sql_query = "SELECT date, weather, COUNT(*) as record_count FROM construction_records GROUP BY date, weather"
    else:
        # 默认查询
        sql_query = "SELECT * FROM construction_records LIMIT 5"
    
    # 更新状态
    return {
        **state,
        "sql_query": sql_query,
        "sql_generated": True
    }


async def execute_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行SQL查询节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行SQL查询节点")
    
    sql_query = state.get("sql_query")
    
    if not sql_query:
        return {
            **state,
            "sql_results": [],
            "sql_executed": True
        }
    
    # 模拟SQL执行结果
    # 实际项目中，这里应该连接真实的数据库并执行查询
    try:
        # 模拟不同查询的结果
        results = []
        
        if "safety_hazards" in sql_query:
            # 安全隐患查询结果
            results = [
                {
                    "id": "haz_001",
                    "location": "B区1号楼",
                    "description": "脚手架未固定",
                    "severity": "high",
                    "date": "2024-03-10",
                    "status": "resolved"
                },
                {
                    "id": "haz_002",
                    "location": "B区2号楼",
                    "description": "安全网破损",
                    "severity": "medium",
                    "date": "2024-03-12",
                    "status": "pending"
                }
            ]
        elif "GROUP BY workpoint, process" in sql_query:
            # 完成量统计结果
            results = [
                {
                    "workpoint": "B区1号楼",
                    "process": "混凝土浇筑",
                    "total_quantity": 500
                },
                {
                    "workpoint": "B区2号楼",
                    "process": "钢筋绑扎",
                    "total_quantity": 300
                },
                {
                    "workpoint": "A区3号楼",
                    "process": "模板安装",
                    "total_quantity": 200
                }
            ]
        elif "construction_records" in sql_query:
            # 施工记录查询结果
            results = [
                {
                    "id": "rec_001",
                    "date": "2024-03-15",
                    "workpoint": "B区1号楼",
                    "team": "张三班组",
                    "process": "混凝土浇筑",
                    "quantity": 100,
                    "weather": "晴"
                },
                {
                    "id": "rec_002",
                    "date": "2024-03-16",
                    "workpoint": "B区2号楼",
                    "team": "李四班组",
                    "process": "钢筋绑扎",
                    "quantity": 50,
                    "weather": "阴"
                }
            ]
        
        # 更新状态
        return {
            **state,
            "sql_results": results,
            "sql_executed": True,
            "sql_result_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"SQL执行失败: {e}")
        return {
            **state,
            "sql_results": [],
            "sql_executed": True,
            "sql_error": str(e)
        }


async def format_sql_result_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """格式化SQL结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行SQL结果格式化节点")
    
    sql_results = state.get("sql_results", [])
    
    if not sql_results:
        return {
            **state,
            "formatted_sql_results": [],
            "sql_formatted": True
        }
    
    # 格式化SQL结果
    formatted_results = []
    
    for result in sql_results:
        formatted_result = {}
        
        for key, value in result.items():
            # 格式化字段名
            formatted_key = key.replace('_', ' ').title()
            formatted_result[formatted_key] = value
        
        formatted_results.append(formatted_result)
    
    # 更新状态
    return {
        **state,
        "formatted_sql_results": formatted_results,
        "sql_formatted": True
    }


async def validate_sql_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """验证SQL查询节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行SQL查询验证节点")
    
    sql_query = state.get("sql_query")
    
    if not sql_query:
        return {
            **state,
            "sql_valid": False
        }
    
    # 简单的SQL验证规则
    invalid_patterns = [
        r'\bDROP\b',
        r'\bDELETE\b',
        r'\bUPDATE\b',
        r'\bINSERT\b',
        r'\bTRUNCATE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
        r'\bSHUTDOWN\b',
        r'\bALTER\b',
        r'\bCREATE\b'
    ]
    
    # 检查是否包含危险操作
    for pattern in invalid_patterns:
        if re.search(pattern, sql_query, re.IGNORECASE):
            logger.warning(f"检测到危险SQL操作: {sql_query}")
            return {
                **state,
                "sql_valid": False,
                "sql_validation_error": "包含危险SQL操作"
            }
    
    # 检查是否为SELECT查询
    if not re.match(r'^\s*SELECT', sql_query, re.IGNORECASE):
        logger.warning(f"只允许SELECT查询: {sql_query}")
        return {
            **state,
            "sql_valid": False,
            "sql_validation_error": "只允许SELECT查询"
        }
    
    # 更新状态
    return {
        **state,
        "sql_valid": True
    }
