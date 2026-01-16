#!/usr/bin/env python3
# review_nodes.py - 人工复核处理节点

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def check_review_needed_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """检查是否需要人工复核节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行人工复核检查节点")
    
    # 检查是否需要人工复核
    needs_review = False
    review_reasons = []
    
    # 检查置信度
    confidence = state.get("vlm_confidence", 0.0) or state.get("ner_results", {}).get("confidence", 0.0)
    if confidence < 0.8:
        needs_review = True
        review_reasons.append(f"置信度低 ({confidence:.2f})")
    
    # 检查是否有缺失的必填字段
    extracted_data = state.get("extracted_data", {})
    required_fields = ["date", "workpoint", "team", "subproject", "position", "process", "quantity", "weather"]
    
    missing_fields = [field for field in required_fields if field not in extracted_data or not extracted_data[field]]
    if missing_fields:
        needs_review = True
        review_reasons.append(f"缺少必填字段: {', '.join(missing_fields)}")
    
    # 检查是否需要VLM验证但未通过
    if state.get("vlm_verified") is False:
        needs_review = True
        review_reasons.append("VLM验证未通过")
    
    logger.info(f"人工复核检查结果: {'需要' if needs_review else '不需要'}")
    
    # 更新状态
    return {
        **state,
        "needs_review": needs_review,
        "review_reasons": review_reasons
    }


async def add_to_review_queue_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """添加到人工复核队列节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行添加到人工复核队列节点")
    
    needs_review = state.get("needs_review", False)
    
    if not needs_review:
        logger.info("不需要人工复核，跳过队列添加")
        return state
    
    # 模拟添加到人工复核队列
    # 实际项目中，这里应该将任务添加到真实的复核队列系统
    
    # 生成复核任务ID
    review_task_id = f"review_{abs(hash(str(state) + datetime.now().isoformat())) % 1000000:06d}"
    
    logger.info(f"已添加到人工复核队列，任务ID: {review_task_id}")
    
    # 更新状态
    return {
        **state,
        "review_task_id": review_task_id,
        "added_to_review_queue": True
    }


async def process_review_result_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """处理人工复核结果节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行处理人工复核结果节点")
    
    review_result = state.get("review_result")
    
    if not review_result:
        logger.warning("缺少人工复核结果")
        return state
    
    # 处理人工复核结果
    is_approved = review_result.get("approved", False)
    feedback = review_result.get("feedback", "")
    reviewer_id = review_result.get("reviewer_id", "")
    
    if is_approved:
        logger.info("人工复核通过")
        return {
            **state,
            "review_approved": True,
            "review_feedback": feedback,
            "reviewer_id": reviewer_id,
            "review_completed": True
        }
    else:
        logger.info("人工复核未通过")
        return {
            **state,
            "review_approved": False,
            "review_feedback": feedback,
            "reviewer_id": reviewer_id,
            "review_completed": True
        }


async def update_after_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """根据复核结果更新节点
    
    Args:
        state: 处理状态
        
    Returns:
        Dict[str, Any]: 更新后的状态
    """
    logger.info("执行复核后更新节点")
    
    review_approved = state.get("review_approved")
    review_feedback = state.get("review_feedback", "")
    review_completed = state.get("review_completed", False)
    
    if not review_completed:
        logger.warning("人工复核未完成，跳过更新")
        return state
    
    if review_approved:
        # 复核通过，更新状态
        logger.info("人工复核通过，更新处理状态")
        return {
            **state,
            "status": "reviewed_approved",
            "review_feedback": review_feedback
        }
    else:
        # 复核未通过，更新状态
        logger.info("人工复核未通过，更新处理状态")
        return {
            **state,
            "status": "reviewed_rejected",
            "review_feedback": review_feedback
        }
