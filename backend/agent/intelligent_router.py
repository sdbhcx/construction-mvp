# intelligent_router.py - 智能路由组件
import logging
from typing import Dict, Any, Optional
import random
import os
from dotenv import load_dotenv
import openai

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class IntelligentRouter:
    """智能路由组件，根据请求类型和上下文决定处理队列"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 路由规则映射
        self.routing_rules = {
            'upload': {
                'target_queue': 'file_processing',
                'priority': 7,
                'description': '文件上传处理队列'
            },
            'query': {
                'target_queue': 'query_processing',
                'priority': 9,
                'description': '查询处理队列'
            },
            'natural_language_query': {
                'target_queue': 'natural_language_query_agent',
                'priority': 9,
                'description': '自然语言查询agent队列'
            },
            'construction_record_processing': {
                'target_queue': 'construction_record_processing_agent',
                'priority': 8,
                'description': '多模态施工记录数据处理agent队列'
            }
        }
        
        # 从配置中更新路由规则
        if 'rules' in config:
            self.routing_rules.update(config['rules'])
        
        # 默认队列
        self.default_queue = config.get('default_queue', 'default_processing')
        
        # 队列健康状态（模拟）
        self.queue_health = {
            'file_processing': {'healthy': True, 'load': 0.7},
            'query_processing': {'healthy': True, 'load': 0.5},
            'natural_language_query_agent': {'healthy': True, 'load': 0.4},
            'construction_record_processing_agent': {'healthy': True, 'load': 0.6},
            'batch_processing': {'healthy': True, 'load': 0.3},
            'status_queue': {'healthy': True, 'load': 0.1},
            'system_queue': {'healthy': True, 'load': 0.2},
            'default_processing': {'healthy': True, 'load': 0.4}
        }
        
        # 初始化LLM配置
        self.llm_config = {
            'model': config.get('llm_model', 'gpt-3.5-turbo'),
            'temperature': config.get('llm_temperature', 0.1),
            'max_tokens': config.get('llm_max_tokens', 100),
            'api_key': config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        }
        
        # 验证API密钥
        if not self.llm_config['api_key']:
            logger.warning("未配置OpenAI API密钥，将回退到规则路由")
            self.use_llm = False
        else:
            # 初始化OpenAI客户端
            openai.api_key = self.llm_config['api_key']
            self.use_llm = True
        
        # 设计LLM提示词
        self.llm_prompt = """
你是一个施工项目智能路由助手，需要根据用户的输入内容判断其意图，并输出对应的路由类型。

## 任务说明
分析用户输入内容，判断其属于以下哪种路由类型：
1. **natural_language_query**：通用自然语言查询，如天气、时间、常识等与施工项目无关的内容
2. **construction_record_processing**：与施工记录相关的查询，如施工进度、质量检查、验收结果等施工项目相关内容

## 输出格式要求
请仅输出路由类型名称，不要输出任何其他内容。

## 示例
用户输入：今天天气怎么样？
输出：natural_language_query

用户输入：昨天的施工进度如何？质量检查结果是什么？
输出：construction_record_processing

用户输入：明天几点开会？
输出：natural_language_query

用户输入：施工材料的使用情况怎样？
输出：construction_record_processing

用户输入：什么是人工智能？
输出：natural_language_query

用户输入：隐蔽工程验收结果如何？
输出：construction_record_processing

现在开始处理用户输入：
{user_input}
"""
    
    def _call_llm(self, user_input: str) -> Optional[str]:
        """调用LLM进行意图识别"""
        try:
            if not self.use_llm:
                logger.info("未启用LLM，回退到规则路由")
                return None
            
            # 构建完整的提示词
            prompt = self.llm_prompt.format(user_input=user_input)
            
            # 调用OpenAI API
            response = openai.ChatCompletion.create(
                model=self.llm_config['model'],
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config['temperature'],
                max_tokens=self.llm_config['max_tokens']
            )
            
            # 解析响应
            routing_type = response['choices'][0]['message']['content'].strip()
            logger.info(f"LLM识别结果: {routing_type}")
            
            # 验证结果是否有效
            if routing_type in ['natural_language_query', 'construction_record_processing']:
                return routing_type
            else:
                logger.warning(f"LLM返回无效路由类型: {routing_type}")
                return None
                
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return None
    
    def route_request(self, recognition_result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """根据请求类型和上下文进行路由决策"""
        try:
            # 获取请求类型
            request_type = recognition_result['type']
            confidence = recognition_result['confidence']
            
            # 检查置信度，如果置信度太低，使用默认队列
            if confidence < 0.5:
                logger.warning(f"请求类型识别置信度低 ({confidence}), 使用默认队列")
                return self._create_routing_instruction(self.default_queue, priority=3)
            
            # 根据用户输入内容判断具体使用哪个agent
            if request_type == 'query':
                # 获取用户输入内容
                user_input = recognition_result.get('content', '')
                if user_input:
                    # 优先使用LLM进行意图识别
                    llm_routing_type = self._call_llm(user_input)
                    
                    if llm_routing_type:
                        # LLM识别成功，使用LLM的结果
                        request_type = llm_routing_type
                        logger.info(f"LLM识别为{request_type}，路由到对应的agent")
                    else:
                        # LLM识别失败或未启用，回退到规则路由
                        logger.info(f"LLM路由失败，回退到规则路由")
                        # 基于内容判断使用哪个agent
                        if self._is_construction_record_query(user_input):
                            request_type = 'construction_record_processing'
                            logger.info(f"规则识别为施工记录查询，路由到多模态施工记录数据处理agent")
                        else:
                            request_type = 'natural_language_query'
                            logger.info(f"规则识别为自然语言查询，路由到自然语言查询agent")
            
            # 获取基础路由规则
            if request_type in self.routing_rules:
                rule = self.routing_rules[request_type]
                target_queue = rule['target_queue']
                priority = rule['priority']
                
                # 根据队列健康状态调整
                if self._should_adjust_route(target_queue):
                    target_queue = self._find_alternative_queue(request_type)
                    logger.info(f"调整路由，从 {rule['target_queue']} 到 {target_queue}")
            else:
                # 未找到匹配规则，使用默认队列
                logger.warning(f"未找到请求类型 {request_type} 的路由规则，使用默认队列")
                target_queue = self.default_queue
                priority = 3
            
            # 根据上下文调整优先级
            priority = self._adjust_priority(priority, context)
            
            # 创建路由指令
            routing_instruction = self._create_routing_instruction(
                target_queue, priority
            )
            
            logger.info(f"路由决策: {request_type} -> {target_queue} (优先级: {priority})")
            return routing_instruction
            
        except Exception as e:
            logger.error(f"路由决策失败: {e}")
            # 发生错误时使用默认队列
            return self._create_routing_instruction(
                self.default_queue, priority=1
            )
    
    def _should_adjust_route(self, queue_name: str) -> bool:
        """判断是否需要调整路由"""
        if queue_name not in self.queue_health:
            return True
        
        health = self.queue_health[queue_name]
        # 如果队列不健康或负载过高，需要调整
        return not health['healthy'] or health['load'] > 0.8
    
    def _find_alternative_queue(self, request_type: str) -> str:
        """寻找替代队列"""
        # 简单策略：随机选择一个健康且低负载的队列
        healthy_queues = [
            queue for queue, health in self.queue_health.items()
            if health['healthy'] and health['load'] < 0.6
        ]
        
        if healthy_queues:
            return random.choice(healthy_queues)
        else:
            # 如果没有健康队列，使用默认队列
            return self.default_queue
    
    def _is_construction_record_query(self, user_input: str) -> bool:
        """判断用户输入是否为施工记录查询"""
        # 转换为小写进行匹配
        user_input_lower = user_input.lower()
        
        # 1. 检查是否包含明确的施工记录相关关键词
        construction_keywords = [
            '施工记录', '施工进度', '施工质量', '施工验收', '施工现场', '施工材料', 
            '施工安全', '施工检查', '施工测量', '施工图纸', '施工工序', '隐蔽工程', 
            '施工日志', '施工报验', '施工整改', '施工工程量', '施工工时', '施工设备', 
            '施工人员', '施工环境', '文明施工', '工程进度', '工程质量', '工程验收',
            '进度如何', '质量如何', '检查结果', '验收结果', '现场情况', '材料情况'
        ]
        
        for keyword in construction_keywords:
            if keyword in user_input_lower:
                return True
        
        # 2. 检查是否包含施工相关的术语组合
        basic_construction_terms = ['进度', '质量', '验收', '现场', '材料', '安全', '检查']
        for term in basic_construction_terms:
            if term in user_input_lower:
                # 检查是否与施工相关的动词或上下文结合
                if any(context_word in user_input_lower for context_word in ['施工', '工程', '工地', '项目', '现场']):
                    return True
        
        # 3. 特殊情况：质量检查、安全检查等常见施工查询
        common_construction_queries = ['质量检查', '安全检查', '进度检查', '材料检查']
        for query in common_construction_queries:
            if query in user_input_lower:
                return True
        
        # 默认返回False
        return False
    
    def _adjust_priority(self, base_priority: int, context: Dict[str, Any]) -> int:
        """根据上下文调整优先级"""
        priority = base_priority
        
        # 示例：根据用户角色调整优先级
        user_role = context.get('user_role')
        if user_role == 'admin':
            priority = min(10, priority + 2)
        elif user_role == 'guest':
            priority = max(1, priority - 2)
        
        # 示例：根据项目ID调整优先级（特定项目优先处理）
        project_id = context.get('project_id')
        if project_id and project_id in ['project_001', 'project_002']:
            priority = min(10, priority + 1)
        
        return priority
    
    def _create_routing_instruction(self, queue_name: str, priority: int, routing_strategy: str = 'intelligent') -> Dict[str, Any]:
        """创建路由指令"""
        return {
            'target_queue': queue_name,
            'priority': priority,
            'timestamp': self._get_current_timestamp(),
            'routing_strategy': routing_strategy
        }
    
    def update_queue_health(self, queue_name: str, healthy: bool, load: float):
        """更新队列健康状态"""
        self.queue_health[queue_name] = {
            'healthy': healthy,
            'load': load
        }
        logger.info(f"更新队列健康状态: {queue_name} - 健康: {healthy}, 负载: {load}")
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
