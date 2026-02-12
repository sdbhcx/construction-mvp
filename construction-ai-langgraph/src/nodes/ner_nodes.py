#!/usr/bin/env python3
# ner_nodes.py - 命名实体识别节点

python
import logging
from typing import Dict, Any
import torch
from transformers import BertTokenizerFast, BertForTokenClassification
from transformers import pipeline

logger = logging.getLogger(__name__)

# 全局NER管道，避免重复加载
_ner_pipeline = None

def get_ner_pipeline():
    global _ner_pipeline
    if _ner_pipeline is None:
        # 可替换为更适合中文NER的模型，如"ckiplab/bert-base-chinese-ner"
        model_name = "ckiplab/bert-base-chinese-ner"
        _ner_pipeline = pipeline("ner", model=model_name, tokenizer=model_name, grouped_entities=True, device=0 if torch.cuda.is_available() else -1)
    return _ner_pipeline

async def run_ner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """执行命名实体识别节点，调用真实模型"""
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
    ner = get_ner_pipeline()
    ner_outputs = ner(text)
    entities = []
    for ent in ner_outputs:
        entities.append({
            "text": ent["word"],
            "type": ent["entity_group"] if "entity_group" in ent else ent["entity"],
            "start": ent["start"],
            "end": ent["end"],
            "confidence": float(ent.get("score", 1.0))
        })
    avg_confidence = sum(e["confidence"] for e in entities) / len(entities) if entities else 0.0
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
