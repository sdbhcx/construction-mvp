# construction_record_processing_agent.py - 多模态施工记录处理agent
import logging
import asyncio
from typing import Dict, Any
from common.message_subscriber import MessageSubscriber

logger = logging.getLogger(__name__)

class ConstructionRecordProcessingAgent:
    """多模态施工记录处理agent，用于处理施工记录相关的请求"""
    
    def __init__(self):
        self.subscriber = None
        self.running = False
        
        logger.info("初始化多模态施工记录处理agent")
    
    def start(self, subscriber_config: Dict[str, Any]):
        """启动agent，开始监听队列"""
        if self.running:
            logger.warning("多模态施工记录处理agent已经在运行中")
            return
        
        self.running = True
        
        # 创建消息订阅器
        self.subscriber = MessageSubscriber(subscriber_config)
        
        # 订阅施工记录处理队列
        self.subscriber.subscribe(
            'construction_record_processing_agent', 
            self._handle_message
        )
        
        # 启动订阅器
        asyncio.create_task(self.subscriber.start())
        
        logger.info("多模态施工记录处理agent已启动，开始监听队列: construction_record_processing_agent")
    
    def stop(self):
        """停止agent，停止监听队列"""
        if not self.running:
            logger.warning("多模态施工记录处理agent已经停止")
            return
        
        self.running = False
        
        # 停止订阅器
        if self.subscriber:
            asyncio.create_task(self.subscriber.stop())
        
        logger.info("多模态施工记录处理agent已停止")
    
    def _handle_message(self, message: Dict[str, Any]):
        """处理接收到的消息"""
        try:
            logger.info(f"多模态施工记录处理agent收到消息: {message['message_id']}")
            
            # 解析消息内容
            content = message.get('content', '')
            request_info = message.get('request_info', {})
            context = message.get('context', {})
            recognition_result = message.get('recognition_result', {})
            
            logger.info(f"处理内容: {content}")
            logger.info(f"请求信息: {request_info}")
            logger.info(f"上下文: {context}")
            logger.info(f"识别结果: {recognition_result}")
            
            # 模拟处理施工记录请求
            self._process_construction_record(content, request_info, context, recognition_result)
            
        except Exception as e:
            logger.error(f"多模态施工记录处理agent处理消息失败: {e}")
    
    def _process_construction_record(self, content: str, request_info: Dict[str, Any], 
                                   context: Dict[str, Any], recognition_result: Dict[str, Any]):
        """处理施工记录请求"""
        try:
            logger.info(f"正在处理施工记录请求: {content}")
            
            # 这里是施工记录处理的核心逻辑
            # 1. 解析施工记录内容
            # 2. 执行多模态处理（文本、图片、视频等）
            # 3. 生成处理结果
            
            # 模拟处理延迟
            import time
            time.sleep(1.0)  # 施工记录处理通常更复杂，延迟更长
            
            logger.info(f"完成处理施工记录请求: {content}")
            
        except Exception as e:
            logger.error(f"处理施工记录请求失败: {e}")

# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建并启动agent
    agent = ConstructionRecordProcessingAgent()
    agent.start({'type': 'memory'})
    
    # 保持运行
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        agent.stop()