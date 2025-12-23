# message_publisher.py - 消息发布组件
import logging
import asyncio
from typing import Dict, Any, Optional
import json
import uuid

logger = logging.getLogger(__name__)

class MessagePublisher:
    """消息发布组件，用于将消息发布到消息队列"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.queue_type = config.get('type', 'memory')
        
        # 初始化不同类型的队列
        if self.queue_type == 'redis':
            self._init_redis_queue()
        elif self.queue_type == 'rabbitmq':
            self._init_rabbitmq_queue()
        elif self.queue_type == 'kafka':
            self._init_kafka_queue()
        else:
            # 默认使用内存队列（模拟）
            self._init_memory_queue()
        
        logger.info(f"初始化消息发布器: {self.queue_type}")
    
    async def publish_async(self, queue_name: str, message: Dict[str, Any], 
                           priority: int = 5) -> bool:
        """异步发布消息到指定队列"""
        try:
            # 根据队列类型发布消息
            if self.queue_type == 'redis':
                return await self._publish_to_redis(queue_name, message, priority)
            elif self.queue_type == 'rabbitmq':
                return await self._publish_to_rabbitmq(queue_name, message, priority)
            elif self.queue_type == 'kafka':
                return await self._publish_to_kafka(queue_name, message, priority)
            else:
                # 使用内存队列
                return self._publish_to_memory(queue_name, message, priority)
            
        except Exception as e:
            logger.error(f"发布消息失败: {e}")
            # 对于内存队列，即使出错也返回True（模拟成功）
            if self.queue_type == 'memory':
                return True
            return False
    
    def _init_memory_queue(self):
        """初始化内存队列"""
        self.memory_queues = {}
        # 用于模拟处理的任务队列
        self.processing_tasks = []
    
    def get_memory_queues(self) -> Dict[str, list]:
        """获取内存队列（用于订阅器访问）"""
        return self.memory_queues
    
    def _init_redis_queue(self):
        """初始化Redis队列（准备工作，实际连接在发布时进行）"""
        self.redis_config = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 6379),
            'db': self.config.get('db', 0)
        }
        self.redis_client = None
    
    def _init_rabbitmq_queue(self):
        """初始化RabbitMQ队列（准备工作，实际连接在发布时进行）"""
        self.rabbitmq_config = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 5672),
            'username': self.config.get('username', 'guest'),
            'password': self.config.get('password', 'guest'),
            'virtual_host': self.config.get('virtual_host', '/')
        }
        self.rabbitmq_channel = None
    
    def _init_kafka_queue(self):
        """初始化Kafka队列（准备工作，实际连接在发布时进行）"""
        self.kafka_config = {
            'bootstrap_servers': self.config.get('bootstrap_servers', ['localhost:9092'])
        }
        self.kafka_producer = None
    
    def _publish_to_memory(self, queue_name: str, message: Dict[str, Any], 
                          priority: int) -> bool:
        """发布消息到内存队列"""
        try:
            # 如果队列不存在，创建队列
            if queue_name not in self.memory_queues:
                self.memory_queues[queue_name] = []
            
            # 添加优先级到消息
            message_with_priority = {
                **message,
                'priority': priority,
                'publish_timestamp': self._get_current_timestamp()
            }
            
            # 将消息添加到队列
            self.memory_queues[queue_name].append(message_with_priority)
            
            # 按照优先级排序（优先级越高，越靠前）
            self.memory_queues[queue_name].sort(
                key=lambda x: x.get('priority', 5), 
                reverse=True
            )
            
            logger.info(f"发布消息到内存队列: {queue_name} - {message['message_id']} (优先级: {priority})")
            
            # 模拟处理消息（异步）
            asyncio.create_task(self._simulate_message_processing(queue_name, message_with_priority))
            
            return True
            
        except Exception as e:
            logger.error(f"发布消息到内存队列失败: {e}")
            return False
    
    async def _publish_to_redis(self, queue_name: str, message: Dict[str, Any], 
                               priority: int) -> bool:
        """发布消息到Redis队列"""
        try:
            # 这里是模拟实现，实际应该使用redis-py或aioredis
            logger.info(f"模拟发布消息到Redis队列: {queue_name} - {message['message_id']}")
            # 为了演示，这里直接调用内存队列实现
            return self._publish_to_memory(queue_name, message, priority)
        except Exception as e:
            logger.error(f"发布消息到Redis队列失败: {e}")
            return False
    
    async def _publish_to_rabbitmq(self, queue_name: str, message: Dict[str, Any], 
                                  priority: int) -> bool:
        """发布消息到RabbitMQ队列"""
        try:
            # 这里是模拟实现，实际应该使用aio-pika或pika
            logger.info(f"模拟发布消息到RabbitMQ队列: {queue_name} - {message['message_id']}")
            # 为了演示，这里直接调用内存队列实现
            return self._publish_to_memory(queue_name, message, priority)
        except Exception as e:
            logger.error(f"发布消息到RabbitMQ队列失败: {e}")
            return False
    
    async def _publish_to_kafka(self, queue_name: str, message: Dict[str, Any], 
                               priority: int) -> bool:
        """发布消息到Kafka队列"""
        try:
            # 这里是模拟实现，实际应该使用aiokafka
            logger.info(f"模拟发布消息到Kafka队列: {queue_name} - {message['message_id']}")
            # 为了演示，这里直接调用内存队列实现
            return self._publish_to_memory(queue_name, message, priority)
        except Exception as e:
            logger.error(f"发布消息到Kafka队列失败: {e}")
            return False
    
    async def _simulate_message_processing(self, queue_name: str, message: Dict[str, Any]):
        """模拟消息处理过程"""
        try:
            logger.info(f"开始处理消息: {message['message_id']}")
            
            # 模拟处理延迟
            processing_delay = 1.0  # 1秒
            await asyncio.sleep(processing_delay)
            
            logger.info(f"完成处理消息: {message['message_id']}")
            
            # 从队列中移除已处理的消息
            if queue_name in self.memory_queues:
                self.memory_queues[queue_name] = [
                    msg for msg in self.memory_queues[queue_name] 
                    if msg['message_id'] != message['message_id']
                ]
                
        except Exception as e:
            logger.error(f"模拟处理消息失败: {e}")
    
    def get_queue_size(self, queue_name: str) -> int:
        """获取队列大小"""
        if queue_name in self.memory_queues:
            return len(self.memory_queues[queue_name])
        return 0
    
    def get_all_queues(self) -> Dict[str, int]:
        """获取所有队列的大小"""
        return {
            queue_name: len(queue)
            for queue_name, queue in self.memory_queues.items()
        }
    
    def clear_queue(self, queue_name: str):
        """清空指定队列"""
        if queue_name in self.memory_queues:
            self.memory_queues[queue_name] = []
            logger.info(f"清空队列: {queue_name}")
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def close(self):
        """关闭消息发布器，释放资源"""
        try:
            if self.queue_type == 'redis' and self.redis_client:
                await self.redis_client.close()
            elif self.queue_type == 'rabbitmq' and self.rabbitmq_channel:
                await self.rabbitmq_channel.close()
            elif self.queue_type == 'kafka' and self.kafka_producer:
                await self.kafka_producer.stop()
            
            logger.info(f"关闭消息发布器: {self.queue_type}")
            return True
        except Exception as e:
            logger.error(f"关闭消息发布器失败: {e}")
            return False
