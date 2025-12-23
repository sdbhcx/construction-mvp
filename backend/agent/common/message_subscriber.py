# message_subscriber.py - 消息订阅组件
import logging
import asyncio
from typing import Dict, Any, Callable, Optional
import json
import uuid

logger = logging.getLogger(__name__)

class MessageSubscriber:
    """消息订阅组件，用于订阅指定队列并处理消息"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.queue_type = config.get('type', 'memory')
        self.subscribers = {}  # {queue_name: [subscriber_func1, subscriber_func2, ...]}
        self.running = False
        self.listen_tasks = []
        
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
        
        logger.info(f"初始化消息订阅器: {self.queue_type}")
    
    def subscribe(self, queue_name: str, callback: Callable[[Dict[str, Any]], None]):
        """订阅指定队列，当有消息到达时调用回调函数"""
        if queue_name not in self.subscribers:
            self.subscribers[queue_name] = []
        
        if callback not in self.subscribers[queue_name]:
            self.subscribers[queue_name].append(callback)
            logger.info(f"订阅队列: {queue_name} (回调函数ID: {id(callback)})")
            
            # 如果是内存队列，启动监听任务
            if self.queue_type == 'memory' and self.running:
                asyncio.create_task(self._listen_memory_queue(queue_name))
        
    def unsubscribe(self, queue_name: str, callback: Callable[[Dict[str, Any]], None]):
        """取消订阅指定队列"""
        if queue_name in self.subscribers:
            if callback in self.subscribers[queue_name]:
                self.subscribers[queue_name].remove(callback)
                logger.info(f"取消订阅队列: {queue_name} (回调函数ID: {id(callback)})")
            
            # 如果没有订阅者了，清理资源
            if not self.subscribers[queue_name]:
                del self.subscribers[queue_name]
                logger.info(f"没有订阅者，清理队列订阅: {queue_name}")
    
    async def start(self):
        """启动消息订阅器"""
        if self.running:
            logger.warning("消息订阅器已经在运行中")
            return
        
        self.running = True
        logger.info("启动消息订阅器")
        
        # 根据队列类型启动监听
        if self.queue_type == 'redis':
            await self._start_redis_listen()
        elif self.queue_type == 'rabbitmq':
            await self._start_rabbitmq_listen()
        elif self.queue_type == 'kafka':
            await self._start_kafka_listen()
        else:
            # 内存队列，为每个订阅的队列启动监听任务
            for queue_name in self.subscribers:
                task = asyncio.create_task(self._listen_memory_queue(queue_name))
                self.listen_tasks.append(task)
    
    async def stop(self):
        """停止消息订阅器"""
        if not self.running:
            logger.warning("消息订阅器已经停止")
            return
        
        self.running = False
        logger.info("停止消息订阅器")
        
        # 取消所有监听任务
        for task in self.listen_tasks:
            task.cancel()
        
        # 清理资源
        if self.queue_type == 'redis' and hasattr(self, 'redis_client'):
            await self.redis_client.close()
        elif self.queue_type == 'rabbitmq' and hasattr(self, 'rabbitmq_channel'):
            await self.rabbitmq_channel.close()
        elif self.queue_type == 'kafka' and hasattr(self, 'kafka_consumer'):
            await self.kafka_consumer.stop()
    
    def _init_memory_queue(self):
        """初始化内存队列"""
        # 内存队列实例将从MessagePublisher获取
        self.memory_queues = None
    
    def set_memory_queues_ref(self, memory_queues: Dict[str, list]):
        """设置内存队列引用（仅用于内存队列模式）"""
        if self.queue_type == 'memory':
            self.memory_queues = memory_queues
            logger.info("设置内存队列引用")
    
    def _init_redis_queue(self):
        """初始化Redis队列"""
        self.redis_config = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 6379),
            'db': self.config.get('db', 0)
        }
        self.redis_client = None
    
    def _init_rabbitmq_queue(self):
        """初始化RabbitMQ队列"""
        self.rabbitmq_config = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 5672),
            'username': self.config.get('username', 'guest'),
            'password': self.config.get('password', 'guest'),
            'virtual_host': self.config.get('virtual_host', '/')
        }
        self.rabbitmq_channel = None
    
    def _init_kafka_queue(self):
        """初始化Kafka队列"""
        self.kafka_config = {
            'bootstrap_servers': self.config.get('bootstrap_servers', ['localhost:9092'])
        }
        self.kafka_consumer = None
    
    async def _listen_memory_queue(self, queue_name: str):
        """监听内存队列"""
        if self.memory_queues is None:
            logger.error("内存队列引用未设置")
            return
        
        logger.info(f"开始监听内存队列: {queue_name}")
        
        try:
            while self.running:
                # 检查队列是否有消息
                if queue_name in self.memory_queues and self.memory_queues[queue_name]:
                    # 获取队列中的第一个消息（优先级最高的）
                    message = self.memory_queues[queue_name][0]
                    
                    # 通知所有订阅者
                    if queue_name in self.subscribers:
                        for callback in self.subscribers[queue_name]:
                            try:
                                callback(message)
                            except Exception as e:
                                logger.error(f"调用订阅者回调函数失败: {e}")
                    
                    # 从队列中移除消息
                    self.memory_queues[queue_name].pop(0)
                    logger.info(f"处理消息: {message['message_id']} 从队列: {queue_name}")
                
                # 短暂休眠，避免CPU占用过高
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"停止监听内存队列: {queue_name}")
        except Exception as e:
            logger.error(f"监听内存队列失败: {e}")
    
    async def _start_redis_listen(self):
        """启动Redis队列监听"""
        try:
            # 这里是模拟实现，实际应该使用aioredis
            logger.info("模拟启动Redis队列监听")
            # 为了演示，这里不进行实际监听
        except Exception as e:
            logger.error(f"启动Redis队列监听失败: {e}")
    
    async def _start_rabbitmq_listen(self):
        """启动RabbitMQ队列监听"""
        try:
            # 这里是模拟实现，实际应该使用aio-pika
            logger.info("模拟启动RabbitMQ队列监听")
            # 为了演示，这里不进行实际监听
        except Exception as e:
            logger.error(f"启动RabbitMQ队列监听失败: {e}")
    
    async def _start_kafka_listen(self):
        """启动Kafka队列监听"""
        try:
            # 这里是模拟实现，实际应该使用aiokafka
            logger.info("模拟启动Kafka队列监听")
            # 为了演示，这里不进行实际监听
        except Exception as e:
            logger.error(f"启动Kafka队列监听失败: {e}")
    
    async def _process_redis_message(self, message: Dict[str, Any]):
        """处理从Redis队列收到的消息"""
        logger.info(f"处理Redis消息: {message['message_id']}")
        # 这里应该根据消息中的queue_name字段通知相应的订阅者
    
    async def _process_rabbitmq_message(self, message: Dict[str, Any]):
        """处理从RabbitMQ队列收到的消息"""
        logger.info(f"处理RabbitMQ消息: {message['message_id']}")
        # 这里应该根据消息中的queue_name字段通知相应的订阅者
    
    async def _process_kafka_message(self, message: Dict[str, Any]):
        """处理从Kafka队列收到的消息"""
        logger.info(f"处理Kafka消息: {message['message_id']}")
        # 这里应该根据消息中的queue_name字段通知相应的订阅者
