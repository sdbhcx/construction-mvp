#!/usr/bin/env python3
# ner_nodes.py - 命名实体识别节点

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


async def run_ner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行命名实体识别节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行命名实体识别节点")
    
    text = state.get("extracted_text")
    
    if not text:
        return {
            **state,
            "ner_results": {
                "entities": [],
                "confidence": 0.0
            }
        }
    
    # 模拟NER识别结果
    # 实际项目中，这里应该调用真实的NER模型或服务
    entities = []
    
    # 识别日期
    date_pattern = r'\d{4}[-年]\d{1,2}[-月]\d{1,2}[日]?'
    for match in re.finditer(date_pattern, text):
        entities.append({
            "text": match.group(),
            "type": "DATE",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.99
        })
    
    # 识别地点
    location_pattern = r'[A-Za-z]*区\w+[工地|楼|号楼]'
    for match in re.finditer(location_pattern, text):
        entities.append({
            "text": match.group(),
            "type": "LOCATION",
            "start": match.start(),
            "end": match.end(),
            "confidence": 0.95
        })
    
    # 识别施工队伍
    team_pattern = r'施工队伍[:：]?\s*([\u4e00-\u9fa5]+班组)'
    for match in re.finditer(team_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "TEAM",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.96
        })
    
    # 识别工点
    workpoint_pattern = r'工点[:：]?\s*([\u4e00-\u9fa5\w]+)'
    for match in re.finditer(workpoint_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "WORKPOINT",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.97
        })
    
    # 识别分项工程
    subproject_pattern = r'分项工程[:：]?\s*([\u4e00-\u9fa5]+)'
    for match in re.finditer(subproject_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "SUBPROJECT",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.98
        })
    
    # 识别部位
    position_pattern = r'部位[:：]?\s*([\d层|地下室|屋面]+)'
    for match in re.finditer(position_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "POSITION",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.99
        })
    
    # 识别工序
    process_pattern = r'工序[:：]?\s*([\u4e00-\u9fa5]+)'
    for match in re.finditer(process_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "PROCESS",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.98
        })
    
    # 识别完成量
    quantity_pattern = r'完成量[:：]?\s*([\d.]+\s*[m³|t|㎡|m|kg]+)'
    for match in re.finditer(quantity_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "QUANTITY",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.99
        })
    
    # 识别天气
    weather_pattern = r'天气[:：]?\s*([\u4e00-\u9fa5]+)'
    for match in re.finditer(weather_pattern, text):
        entities.append({
            "text": match.group(1),
            "type": "WEATHER",
            "start": match.start(1),
            "end": match.end(1),
            "confidence": 0.95
        })
    
    # 计算平均置信度
    avg_confidence = sum(entity["confidence"] for entity in entities) / len(entities) if entities else 0.0
    
    # 更新状态
    return {
        **state,
        "ner_results": {
            "entities": entities,
            "confidence": avg_confidence
        }
    }


async def link_entities_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """实体链接节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行实体链接节点")
    
    ner_results = state.get("ner_results", {})
    entities = ner_results.get("entities", [])
    
    if not entities:
        return state
    
    # 模拟实体链接结果
    # 实际项目中，这里应该调用真实的实体链接服务或数据库查询
    linked_entities = []
    
    for entity in entities:
        linked_entity = entity.copy()
        
        # 为不同类型的实体生成ID
        if entity["type"] == "WORKPOINT":
            # 模拟工点ID生成
            linked_entity["id"] = f"wp_{abs(hash(entity['text'])) % 1000:03d}"
        elif entity["type"] == "TEAM":
            # 模拟队伍ID生成
            linked_entity["id"] = f"team_{abs(hash(entity['text'])) % 1000:03d}"
        elif entity["type"] == "SUBPROJECT":
            # 模拟分项工程ID生成
            linked_entity["id"] = f"sp_{abs(hash(entity['text'])) % 1000:03d}"
        elif entity["type"] == "POSITION":
            # 模拟部位ID生成
            linked_entity["id"] = f"pos_{abs(hash(entity['text'])) % 1000:03d}"
        elif entity["type"] == "PROCESS":
            # 模拟工序ID生成
            linked_entity["id"] = f"proc_{abs(hash(entity['text'])) % 1000:03d}"
        
        linked_entities.append(linked_entity)
    
    # 更新状态
    return {
        **state,
        "ner_results": {
            **ner_results,
            "entities": linked_entities
        },
        "entities_linked": True
    }


async def extract_structured_data_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """从NER结果中提取结构化数据节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行结构化数据提取节点")
    
    ner_results = state.get("ner_results", {})
    entities = ner_results.get("entities", [])
    
    # 提取结构化数据
    structured_data = {}
    
    for entity in entities:
        entity_type = entity["type"]
        if entity_type == "DATE":
            structured_data["date"] = entity["text"]
        elif entity_type == "WEATHER":
            structured_data["weather"] = entity["text"]
        elif entity_type == "WORKPOINT":
            structured_data["workpoint"] = entity["text"]
            structured_data["workpoint_id"] = entity.get("id")
        elif entity_type == "TEAM":
            structured_data["team"] = entity["text"]
            structured_data["team_id"] = entity.get("id")
        elif entity_type == "SUBPROJECT":
            structured_data["subproject"] = entity["text"]
            structured_data["subproject_id"] = entity.get("id")
        elif entity_type == "POSITION":
            structured_data["position"] = entity["text"]
            structured_data["position_id"] = entity.get("id")
        elif entity_type == "PROCESS":
            structured_data["process"] = entity["text"]
            structured_data["process_id"] = entity.get("id")
        elif entity_type == "QUANTITY":
            structured_data["quantity"] = entity["text"]
    
    # 更新状态
    return {
        **state,
        "extracted_data": structured_data
    }
