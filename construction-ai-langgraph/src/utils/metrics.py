#!/usr/bin/env python3
# metrics.py - 指标工具

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, name: str, value: Any, labels: Optional[Dict[str, str]] = None):
        """记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            labels: 指标标签
        """
        metric = {
            "name": name,
            "value": value,
            "timestamp": time.time(),
            "labels": labels or {}
        }
        
        # 保存指标
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(metric)
        
        # 记录日志
        logger.info(f"Metric recorded: {name} = {value} {labels}")
    
    def get_metrics(self, name: Optional[str] = None) -> Dict[str, Any]:
        """获取指标
        
        Args:
            name: 指标名称，为空则返回所有指标
            
        Returns:
            Dict[str, Any]: 指标数据
        """
        if name:
            return {name: self.metrics.get(name, [])}
        return self.metrics


# 创建全局指标收集器实例
_metrics_collector = MetricsCollector()


def record_metric(name: str, value: Any, labels: Optional[Dict[str, str]] = None):
    """记录指标（全局函数）
    
    Args:
        name: 指标名称
        value: 指标值
        labels: 指标标签
    """
    _metrics_collector.record(name, value, labels)


def get_metrics(name: Optional[str] = None) -> Dict[str, Any]:
    """获取指标（全局函数）
    
    Args:
        name: 指标名称，为空则返回所有指标
        
    Returns:
        Dict[str, Any]: 指标数据
    """
    return _metrics_collector.get_metrics(name)
