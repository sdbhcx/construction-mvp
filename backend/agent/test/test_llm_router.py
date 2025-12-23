# test_llm_router.py - 测试基于LLM的智能路由
import logging
import os
import sys
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.common.intelligent_router import IntelligentRouter

def test_llm_router():
    """测试基于LLM的智能路由"""
    try:
        logger.info("开始测试基于LLM的智能路由...")
        
        # 配置智能路由
        router_config = {
            'llm_model': 'gpt-3.5-turbo',
            'llm_temperature': 0.1,
            'llm_max_tokens': 100
            # 'openai_api_key': 'your-api-key'  # 可以在这里直接配置，或通过环境变量
        }
        
        # 创建智能路由实例
        router = IntelligentRouter(router_config)
        
        # 测试用例
        test_cases = [
            # 自然语言查询测试用例
            {
                'name': '天气查询',
                'content': '今天北京的天气怎么样？',
                'expected_queue': 'natural_language_query_agent'
            },
            {
                'name': '时间查询',
                'content': '现在几点了？',
                'expected_queue': 'natural_language_query_agent'
            },
            {
                'name': '常识查询',
                'content': '什么是人工智能？',
                'expected_queue': 'natural_language_query_agent'
            },
            {
                'name': '会议查询',
                'content': '明天几点开会？',
                'expected_queue': 'natural_language_query_agent'
            },
            
            # 施工记录查询测试用例
            {
                'name': '施工进度查询',
                'content': '昨天的施工进度如何？',
                'expected_queue': 'construction_record_processing_agent'
            },
            {
                'name': '质量检查查询',
                'content': '质量检查结果是什么？',
                'expected_queue': 'construction_record_processing_agent'
            },
            {
                'name': '材料使用查询',
                'content': '施工材料的使用情况怎样？',
                'expected_queue': 'construction_record_processing_agent'
            },
            {
                'name': '隐蔽工程验收查询',
                'content': '隐蔽工程验收结果如何？',
                'expected_queue': 'construction_record_processing_agent'
            },
            {
                'name': '复合施工查询',
                'content': '昨天的施工进度如何？质量检查结果是什么？',
                'expected_queue': 'construction_record_processing_agent'
            },
            {
                'name': '安全检查查询',
                'content': '施工现场安全检查情况怎么样？',
                'expected_queue': 'construction_record_processing_agent'
            }
        ]
        
        # 运行测试用例
        results = []
        for test_case in test_cases:
            logger.info(f"\n=== 测试用例: {test_case['name']} ===")
            logger.info(f"输入内容: {test_case['content']}")
            
            # 构造识别结果
            recognition_result = {
                'type': 'query',
                'confidence': 0.95,
                'content': test_case['content']
            }
            
            # 构造上下文
            context = {
                'user_id': 'test_user_123',
                'session_id': 'test_session_456',
                'user_role': 'admin'
            }
            
            # 进行路由决策
            routing_result = router.route_request(recognition_result, context)
            
            # 获取实际路由队列
            actual_queue = routing_result['target_queue']
            expected_queue = test_case['expected_queue']
            
            # 判断是否匹配
            matched = actual_queue == expected_queue
            results.append({
                'test_case': test_case['name'],
                'content': test_case['content'],
                'actual_queue': actual_queue,
                'expected_queue': expected_queue,
                'matched': matched
            })
            
            # 输出测试结果
            logger.info(f"路由结果: {actual_queue}")
            logger.info(f"预期结果: {expected_queue}")
            logger.info(f"匹配状态: {'✅ 成功' if matched else '❌ 失败'}")
        
        # 输出测试报告
        logger.info("\n" + "="*60)
        logger.info("测试报告")
        logger.info("="*60)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['matched'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过数: {passed_tests}")
        logger.info(f"失败数: {failed_tests}")
        logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n失败的测试用例:")
            for result in results:
                if not result['matched']:
                    logger.info(f"- {result['test_case']}: {result['content']}")
                    logger.info(f"  实际: {result['actual_queue']}，预期: {result['expected_queue']}")
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_router()
    sys.exit(0 if success else 1)