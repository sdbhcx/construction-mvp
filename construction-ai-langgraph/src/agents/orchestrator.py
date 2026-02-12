#!/usr/bin/env python3
# orchestrator.py - 智能体调度器

import logging
import json
import yaml
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import redis

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
        # 加载路由配置
        self.routing_config = self._load_routing_config()
        # 初始化消息队列客户端
        self.message_queue = self._init_message_queue()
    
    def _load_routing_config(self) -> Dict[str, Any]:
        """加载路由配置文件"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "configs",
            "routing_config.yaml"
        )
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载路由配置: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载路由配置失败: {e}")
            # 返回默认配置
            return {
                "document_routing": {
                    "default": {
                        "task_type": "extraction",
                        "queue": "document_processing",
                        "priority": 8
                    }
                },
                "query_routing": {
                    "default": {
                        "task_type": "query",
                        "queue": "query_processing",
                        "priority": 7
                    }
                }
            }
    
    def _init_message_queue(self):
        """初始化消息队列客户端"""
        # 使用Redis作为真实的消息队列客户端
        logger.info("初始化Redis消息队列客户端")
        try:
            # 创建Redis连接
            redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            # 测试连接
            redis_client.ping()
            logger.info("Redis连接成功")
            return RedisMessageQueue(redis_client)
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            logger.warning("由于Redis服务未启动，将使用模拟消息队列进行开发测试")
            # 在开发环境中回退到模拟消息队列
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
            
            # 获取文档属性
            file_type = document.get('file_type', 'unknown').lower()
            user_intent = document.get('user_intent', 'extract').lower()
            file_size = document.get('file_size', 0)
            
            # 获取默认路由配置
            doc_config = self.routing_config.get('document_routing', {})
            default_config = doc_config.get('default', {
                'task_type': 'extraction',
                'queue': 'document_processing',
                'priority': 8
            })
            
            # 基于文件类型的路由
            file_type_config = doc_config.get('by_file_type', {}).get(file_type, {})
            
            # 基于用户意图的路由
            intent_config = doc_config.get('by_user_intent', {}).get(user_intent, {})
            
            # 合并配置（优先级：意图 > 文件类型 > 默认）
            routing_config = {
                **default_config,
                **file_type_config,
                **intent_config
            }
            
            # 基于文件大小调整优先级
            size_config = doc_config.get('by_file_size', {})
            if file_size > 0:
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    size_priority = size_config.get('large', {}).get('priority')
                elif file_size > 1 * 1024 * 1024:  # 1MB - 10MB
                    size_priority = size_config.get('medium', {}).get('priority')
                else:  # < 1MB
                    size_priority = size_config.get('small', {}).get('priority')
                
                if size_priority is not None:
                    routing_config['priority'] = size_priority
            
            # 创建文档处理任务
            task = Task(
                type=routing_config['task_type'],
                priority=routing_config['priority'],
                payload=document,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'task_type': routing_config['task_type'],
                    'file_type': file_type,
                    'user_intent': user_intent,
                    'file_size': file_size
                }
            )
            
            # 发布任务到消息队列
            self.publish_task(task, queue=routing_config['queue'])
            
            logger.info(f"成功路由文档处理请求到队列: {routing_config['queue']}")
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
            
            # 获取查询属性
            query_intent = query.get('intent', 'question').lower()
            
            # 获取默认路由配置
            query_config = self.routing_config.get('query_routing', {})
            default_config = query_config.get('default', {
                'task_type': 'query',
                'queue': 'query_processing',
                'priority': 7
            })
            
            # 基于查询意图的路由
            intent_config = query_config.get('by_intent', {}).get(query_intent, {})
            
            # 合并配置（优先级：意图 > 默认）
            routing_config = {
                **default_config,
                **intent_config
            }
            
            # 创建查询处理任务
            task = Task(
                type=routing_config['task_type'],
                priority=routing_config['priority'],
                payload=query,
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'task_type': routing_config['task_type'],
                    'user_id': query.get('user_id'),
                    'intent': query_intent
                }
            )
            
            # 发布任务到消息队列
            self.publish_task(task, queue=routing_config['queue'])
            
            logger.info(f"成功路由查询请求到队列: {routing_config['queue']}")
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


class RedisMessageQueue:
    """Redis消息队列客户端"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
    
    def publish(self, queue: str, message: Dict[str, Any]):
        """发布消息到队列
        
        Args:
            queue: 队列名称
            message: 消息内容
        """
        try:
            # 将消息转换为JSON字符串
            message_json = json.dumps(message)
            # 使用Redis的LPUSH命令将消息添加到队列
            result = self.redis_client.lpush(queue, message_json)
            logger.info(f"Redis消息队列: 发布消息到 {queue}，队列长度: {result}")
        except Exception as e:
            logger.error(f"Redis消息队列发布失败: {e}")
            raise
    
    def consume(self, queue: str, block: int = 0) -> Optional[Dict[str, Any]]:
        """从队列消费消息
        
        Args:
            queue: 队列名称
            block: 阻塞时间（秒），0表示无限阻塞
            
        Returns:
            Optional[Dict[str, Any]]: 消息内容或None
        """
        try:
            # 使用Redis的BRPOP命令从队列右侧阻塞式获取消息
            result = self.redis_client.brpop(queue, timeout=block)
            if result:
                queue_name, message_json = result
                # 将JSON字符串转换为字典
                message = json.loads(message_json)
                logger.info(f"Redis消息队列: 从 {queue_name} 消费消息")
                return message
            return None
        except Exception as e:
            logger.error(f"Redis消息队列消费失败: {e}")
            raise


class MockMessageQueue:
    """模拟消息队列客户端（开发环境回退使用）"""
    
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
    
    def consume(self, queue: str, block: int = 0) -> Optional[Dict[str, Any]]:
        """从队列消费消息
        
        Args:
            queue: 队列名称
            block: 阻塞时间（秒），0表示无限阻塞（模拟实现中忽略）
            
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
