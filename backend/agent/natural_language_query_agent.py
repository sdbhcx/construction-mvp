# natural_language_query_agent.py - 自然语言查询agent
import logging
import asyncio
from typing import Dict, Any
from .message_subscriber import MessageSubscriber

logger = logging.getLogger(__name__)

class NaturalLanguageQueryAgent:
    """自然语言查询agent，用于处理用户的自然语言查询请求"""
    
    def __init__(self):
        self.subscriber = None
        self.running = False
        
        logger.info("初始化自然语言查询agent")
    
    def start(self, subscriber_config: Dict[str, Any]):
        """启动agent，开始监听队列"""
        if self.running:
            logger.warning("自然语言查询agent已经在运行中")
            return
        
        self.running = True
        
        # 创建消息订阅器
        self.subscriber = MessageSubscriber(subscriber_config)
        
        # 订阅自然语言查询队列
        self.subscriber.subscribe(
            'natural_language_query_agent', 
            self._handle_message
        )
        
        # 启动订阅器
        asyncio.create_task(self.subscriber.start())
        
        logger.info("自然语言查询agent已启动，开始监听队列: natural_language_query_agent")
    
    def stop(self):
        """停止agent，停止监听队列"""
        if not self.running:
            logger.warning("自然语言查询agent已经停止")
            return
        
        self.running = False
        
        # 停止订阅器
        if self.subscriber:
            asyncio.create_task(self.subscriber.stop())
        
        logger.info("自然语言查询agent已停止")
    
    def _handle_message(self, message: Dict[str, Any]):
        """处理接收到的消息"""
        try:
            logger.info(f"自然语言查询agent收到消息: {message['message_id']}")
            
            # 解析消息内容
            content = message.get('content', '')
            request_info = message.get('request_info', {})
            context = message.get('context', {})
            
            logger.info(f"查询内容: {content}")
            logger.info(f"请求信息: {request_info}")
            logger.info(f"上下文: {context}")
            
            # 模拟处理自然语言查询
            self._process_query(content, request_info, context)
            
        except Exception as e:
            logger.error(f"自然语言查询agent处理消息失败: {e}")
    
    def _process_query(self, content: str, request_info: Dict[str, Any], context: Dict[str, Any]):
        """处理自然语言查询"""
        try:
            logger.info(f"正在处理自然语言查询: {content}")
            
            # 这里是自然语言查询的核心处理逻辑
            # 1. 解析用户查询意图
            # 2. 执行查询操作
            # 3. 生成响应结果
            
            # 模拟处理延迟
            import time
            time.sleep(0.5)
            
            logger.info(f"完成处理自然语言查询: {content}")
            
        except Exception as e:
            logger.error(f"处理自然语言查询失败: {e}")

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建并启动agent
    agent = NaturalLanguageQueryAgent()
    agent.start({'type': 'memory'})
    
    # 保持运行
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        agent.stop()