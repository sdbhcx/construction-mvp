# test_integration.py - 整合测试文件，演示agent如何监听队列并处理消息
import asyncio
import logging
import time
from typing import Dict, Any
from message_publisher import MessagePublisher
from message_subscriber import MessageSubscriber
from natural_language_query_agent import NaturalLanguageQueryAgent
from construction_record_processing_agent import ConstructionRecordProcessingAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """整合测试主函数"""
    try:
        logger.info("开始整合测试...")
        
        # 1. 初始化消息发布器（使用内存队列）
        publisher_config = {'type': 'memory'}
        publisher = MessagePublisher(publisher_config)
        logger.info("消息发布器已初始化")
        
        # 2. 初始化消息订阅器
        subscriber_config = {'type': 'memory'}
        subscriber = MessageSubscriber(subscriber_config)
        
        # 设置内存队列引用（让订阅器可以访问发布器的内存队列）
        subscriber.set_memory_queues_ref(publisher.get_memory_queues())
        logger.info("消息订阅器已初始化")
        
        # 3. 创建并启动两个agent
        nl_query_agent = NaturalLanguageQueryAgent()
        construction_agent = ConstructionRecordProcessingAgent()
        
        # 为agent设置订阅器
        # 注意：在实际应用中，agent内部会创建自己的订阅器
        # 这里为了简化测试，我们直接使用同一个订阅器
        nl_query_agent.subscriber = subscriber
        construction_agent.subscriber = subscriber
        
        # 启动agent
        nl_query_agent.start(subscriber_config)
        construction_agent.start(subscriber_config)
        logger.info("两个agent已启动")
        
        # 等待agent启动完成
        await asyncio.sleep(1)
        
        # 4. 生成标准化消息
        def create_standard_message(content: str, message_id: str, request_type: str) -> Dict[str, Any]:
            """创建标准化消息"""
            from datetime import datetime
            return {
                'message_id': message_id,
                'timestamp': datetime.now().isoformat(),
                'request_info': {
                    'type': request_type,
                    'source': 'test_integration',
                    'user_id': 'test_user_123'
                },
                'recognition_result': {
                    'type': request_type,
                    'confidence': 0.95,
                    'content': content
                },
                'content': content,
                'context': {
                    'previous_queries': [],
                    'session_id': 'test_session_123'
                }
            }
        
        # 5. 发布自然语言查询消息
        logger.info("\n--- 发布自然语言查询消息 ---")
        nl_message = create_standard_message(
            "今天天气怎么样？",
            "nl_query_001",
            "natural_language_query"
        )
        await publisher.publish_async(
            'natural_language_query_agent',
            nl_message,
            priority=9
        )
        
        # 6. 发布施工记录处理消息
        logger.info("\n--- 发布施工记录处理消息 ---")
        construction_message = create_standard_message(
            "昨天的施工进度如何？质量检查结果是什么？",
            "construction_query_001",
            "construction_record_processing"
        )
        await publisher.publish_async(
            'construction_record_processing_agent',
            construction_message,
            priority=8
        )
        
        # 7. 等待消息处理完成
        await asyncio.sleep(3)
        
        # 8. 查看队列状态
        logger.info("\n--- 队列状态 ---")
        all_queues = publisher.get_all_queues()
        for queue_name, size in all_queues.items():
            logger.info(f"队列: {queue_name} - 大小: {size}")
        
        # 9. 停止agent和订阅器
        nl_query_agent.stop()
        construction_agent.stop()
        await subscriber.stop()
        
        logger.info("\n整合测试完成！")
        
    except Exception as e:
        logger.error(f"整合测试失败: {e}")

if __name__ == "__main__":
    # 运行整合测试
    asyncio.run(main())