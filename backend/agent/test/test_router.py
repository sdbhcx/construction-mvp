# test_router.py - 测试智能路由功能
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.intelligent_router import IntelligentRouter

def test_router():
    """测试智能路由功能"""
    # 创建路由实例
    config = {}
    router = IntelligentRouter(config)
    
    print("=== 测试智能路由功能 ===\n")
    
    # 测试用例1: 自然语言查询
    print("测试用例1: 自然语言查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.95,
        'content': '今天天气怎么样？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"路由结果: {routing_result}\n")
    
    # 测试用例2: 施工记录查询
    print("测试用例2: 施工记录查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.95,
        'content': '上周的施工进度如何？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"路由结果: {routing_result}\n")
    
    # 测试用例3: 施工质量查询
    print("测试用例3: 施工质量查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.95,
        'content': '昨天的质量检查结果是什么？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"路由结果: {routing_result}\n")
    
    # 测试用例4: 设备使用查询
    print("测试用例4: 设备使用查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.95,
        'content': '施工设备的使用情况如何？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"路由结果: {routing_result}\n")
    
    # 测试用例5: 其他自然语言查询
    print("测试用例5: 其他自然语言查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.95,
        'content': '如何使用这个系统？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"路由结果: {routing_result}\n")
    
    # 测试用例6: 低置信度查询
    print("测试用例6: 低置信度查询")
    recognition_result = {
        'type': 'query',
        'confidence': 0.3,
        'content': '施工进度如何？'
    }
    context = {}
    routing_result = router.route_request(recognition_result, context)
    print(f"用户输入: {recognition_result['content']}")
    print(f"置信度: {recognition_result['confidence']}")
    print(f"路由结果: {routing_result}\n")

if __name__ == "__main__":
    test_router()