#!/usr/bin/env python3
# orchestrator.py - 智能体调度器

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Task(BaseModel):
    """任务模型"""
    type: str  # 'extraction' 或 'query'
    priority: int = Field(default=5, ge=1, le=10)
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class OrchestratorAgent:
    """智能体调度器，负责接收和路由请求"""
    
    def __init__(self):
        """初始化智能体调度器"""
        logger.info("初始化智能体调度器")
        # 初始化消息队列客户端（这里使用模拟实现，实际应替换为真实的消息队列客户端）
        self.message_queue = self._init_message_queue()
    
    def _init_message_queue(self):
        """初始化消息队列客户端"""
        # 这里使用模拟实现，实际应替换为RabbitMQ、Kafka等消息队列客户端
        logger.info("初始化消息队列客户端（模拟实现）")
        return MockMessageQueue()
    
    def route_document(self, document: Dict[str, Any]) -> Task:
        """路由文档处理请求
        
        Args:
            document: 文档信息，包含file_path, file_type等
            
        Returns:
            Task: 路由后的任务对象
        """
        try:
            logger.info(f"路由文档处理请求: {document.get('file_path', '未知文件')}")
            
            # 验证文档信息
            if not self._validate_document(document):
                logger.error("文档验证失败")
                raise ValueError("文档验证失败")
            
            # 创建文档处理任务
            task = Task(
                type='extraction',
                priority=8,  # 文档处理优先级较高
                payload=document,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'task_type': 'document_processing',
                    'file_type': document.get('file_type', 'unknown')
                }
            )
            
            # 发布任务到消息队列
            self.publish_task(task, queue='document_processing')
            
            logger.info(f"成功路由文档处理请求到信息抽取智能体")
            return task
            
        except Exception as e:
            logger.error(f"路由文档处理请求失败: {e}")
            raise
    
    def route_query(self, query: Dict[str, Any]) -> Task:
        """路由查询请求
        
        Args:
            query: 查询信息，包含query_text, user_id等
            
        Returns:
            Task: 路由后的任务对象
        """
        try:
            logger.info(f"路由查询请求: {query.get('query_text', '未知查询')}")
            
            # 验证查询信息
            if not self._validate_query(query):
                logger.error("查询验证失败")
                raise ValueError("查询验证失败")
            
            # 创建查询处理任务
            task = Task(
                type='query',
                priority=7,  # 查询优先级较高
                payload=query,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'task_type': 'query_processing',
                    'user_id': query.get('user_id')
                }
            )
            
            # 发布任务到消息队列
            self.publish_task(task, queue='query_processing')
            
            logger.info(f"成功路由查询请求到问答与查询智能体")
            return task
            
        except Exception as e:
            logger.error(f"路由查询请求失败: {e}")
            raise
    
    def publish_task(self, task: Task, queue: str):
        """发布任务到消息队列
        
        Args:
            task: 任务对象
            queue: 队列名称
        """
        try:
            logger.info(f"发布任务到队列 {queue}: {task.type} (优先级: {task.priority})")
            # 实际项目中，这里应使用真实的消息队列客户端发布任务
            self.message_queue.publish(queue, task.model_dump())
        except Exception as e:
            logger.error(f"发布任务到队列 {queue} 失败: {e}")
            raise
    
    def _validate_document(self, document: Dict[str, Any]) -> bool:
        """验证文档信息
        
        Args:
            document: 文档信息
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = ['file_path', 'file_type']
        for field in required_fields:
            if field not in document:
                logger.error(f"文档缺少必填字段: {field}")
                return False
        return True
    
    def _validate_query(self, query: Dict[str, Any]) -> bool:
        """验证查询信息
        
        Args:
            query: 查询信息
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = ['query_text']
        for field in required_fields:
            if field not in query:
                logger.error(f"查询缺少必填字段: {field}")
                return False
        return True
    
    def start(self):
        """启动智能体调度器"""
        logger.info("启动智能体调度器")
    
    def stop(self):
        """停止智能体调度器"""
        logger.info("停止智能体调度器")


class MockMessageQueue:
    """模拟消息队列客户端"""
    
    def __init__(self):
        self.queues = {}
    
    def publish(self, queue: str, message: Dict[str, Any]):
        """发布消息到队列
        
        Args:
            queue: 队列名称
            message: 消息内容
        """
        if queue not in self.queues:
            self.queues[queue] = []
        self.queues[queue].append(message)
        logger.info(f"模拟消息队列: 发布消息到 {queue}，队列长度: {len(self.queues[queue])}")
    
    def consume(self, queue: str) -> Optional[Dict[str, Any]]:
        """从队列消费消息
        
        Args:
            queue: 队列名称
            
        Returns:
            Optional[Dict[str, Any]]: 消息内容或None
        """
        if queue in self.queues and self.queues[queue]:
            return self.queues[queue].pop(0)
        return None


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    orchestrator = OrchestratorAgent()
    orchestrator.start()
    
    # 测试文档路由
    test_document = {
        'file_path': '/path/to/test.pdf',
        'file_type': 'pdf',
        'file_size': 1024,
        'uploader_id': 'user_123',
        'project_id': 'proj_456'
    }
    
    try:
        task = orchestrator.route_document(test_document)
        logger.info(f"文档路由测试成功: {task}")
    except Exception as e:
        logger.error(f"文档路由测试失败: {e}")
    
    # 测试查询路由
    test_query = {
        'query_text': '上个月B区有哪些安全隐患？',
        'user_id': 'user_789',
        'project_id': 'proj_456'
    }
    
    try:
        task = orchestrator.route_query(test_query)
        logger.info(f"查询路由测试成功: {task}")
    except Exception as e:
        logger.error(f"查询路由测试失败: {e}")
    
    orchestrator.stop()
