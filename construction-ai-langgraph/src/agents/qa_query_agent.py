#!/usr/bin/env python3
# qa_query_agent.py - 问答与查询智能体

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class QAQueryAgent:
    """问答与查询智能体，负责处理自然语言查询"""
    
    def __init__(self, sql_tool: Any = None, vector_tool: Any = None, llm_tool: Any = None):
        """初始化问答与查询智能体
        
        Args:
            sql_tool: SQL工具实例，用于生成和执行SQL查询
            vector_tool: 向量搜索工具实例，用于语义搜索
            llm_tool: LLM工具实例，用于生成回答
        """
        logger.info("初始化问答与查询智能体")
        self.sql_tool = sql_tool
        self.vector_tool = vector_tool
        self.llm_tool = llm_tool
        self.message_queue = self._init_message_queue()
        self._running = False
    
    def _init_message_queue(self):
        """初始化消息队列客户端"""
        from .orchestrator import MockMessageQueue
        logger.info("初始化消息队列客户端")
        return MockMessageQueue()
    
    def process_query(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理查询请求
        
        Args:
            task: 任务信息，包含查询文本、用户ID等
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            logger.info(f"开始处理查询: {task.get('payload', {}).get('query_text', '未知查询')}")
            
            # 1. 解析任务信息
            payload = task.get('payload', {})
            query_text = payload.get('query_text')
            user_id = payload.get('user_id')
            project_id = payload.get('project_id')
            
            if not query_text:
                logger.error("任务缺少查询文本")
                raise ValueError("任务缺少查询文本")
            
            # 2. 使用问答查询图处理查询
            from src.graphs.qa_query_graph import QAQueryGraph
            
            # 创建图实例
            graph = QAQueryGraph()
            
            # 构建图
            graph.build_graph()
            
            # 异步运行图
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(graph.process_query(query_text, user_id, project_id))
            loop.close()
            
            # 3. 保存查询历史
            self._save_query_history(query_text, result.get('answer', ''), user_id, project_id, result.get('intent', 'unknown'))
            
            logger.info(f"成功处理查询: {query_text}")
            
            return {
                'status': 'success',
                'message': '查询处理成功',
                'query_text': query_text,
                'intent': result.get('intent', 'unknown'),
                'answer': result.get('answer', ''),
                'result_data': result,
                'timestamp': datetime.now().isoformat(),
                'confidence': result.get('confidence', 0.0),
                'processing_time': result.get('processing_time', 0.0)
            }
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            return {
                'status': 'error',
                'message': f'查询处理失败: {str(e)}',
                'query_text': task.get('payload', {}).get('query_text', '未知查询'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _identify_intent(self, query_text: str) -> str:
        """识别查询意图
        
        Args:
            query_text: 查询文本
            
        Returns:
            str: 查询意图，如'sql_query'、'vector_search'或'hybrid'
        """
        logger.info(f"识别查询意图: {query_text}")
        
        # 简单的意图识别逻辑，实际项目中可以使用LLM或专门的意图识别模型
        structured_keywords = [
            '多少', '数量', '统计', '总', '平均', '计数', '完成', '进度', '工时', '成本'
        ]
        
        unstructured_keywords = [
            '什么', '如何', '为什么', '原因', '说明', '解释', '定义', '文档', '记录', '报告'
        ]
        
        query_lower = query_text.lower()
        
        has_structured = any(keyword in query_lower for keyword in structured_keywords)
        has_unstructured = any(keyword in query_lower for keyword in unstructured_keywords)
        
        if has_structured and has_unstructured:
            return 'hybrid'
        elif has_structured:
            return 'sql_query'
        else:
            return 'vector_search'
    
    def _handle_sql_query(self, query_text: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """处理结构化查询
        
        Args:
            query_text: 查询文本
            project_id: 项目ID，用于过滤数据
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        logger.info(f"处理结构化查询: {query_text}")
        
        try:
            if self.sql_tool:
                # 生成SQL
                sql = self.sql_tool.generate_sql(query_text, project_id)
                logger.info(f"生成SQL: {sql}")
                
                # 执行SQL
                results = self.sql_tool.execute_sql(sql)
                logger.info(f"SQL执行结果: {len(results)} 条记录")
                
                return {
                    'type': 'sql',
                    'sql': sql,
                    'results': results,
                    'count': len(results)
                }
            else:
                # 模拟SQL查询结果
                logger.info("使用模拟SQL查询结果")
                return self._get_mock_sql_results(query_text)
        
        except Exception as e:
            logger.error(f"SQL查询失败: {e}")
            # 降级为向量搜索
            logger.info("SQL查询失败，降级为向量搜索")
            return self._handle_vector_search(query_text, project_id)
    
    def _handle_vector_search(self, query_text: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """处理非结构化查询
        
        Args:
            query_text: 查询文本
            project_id: 项目ID，用于过滤数据
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        logger.info(f"处理非结构化查询: {query_text}")
        
        try:
            if self.vector_tool:
                # 执行向量搜索
                results = self.vector_tool.search(query_text, project_id)
                logger.info(f"向量搜索结果: {len(results)} 条记录")
                
                return {
                    'type': 'vector',
                    'results': results,
                    'count': len(results)
                }
            else:
                # 模拟向量搜索结果
                logger.info("使用模拟向量搜索结果")
                return self._get_mock_vector_results(query_text)
        
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return {
                'type': 'vector',
                'results': [],
                'count': 0,
                'error': str(e)
            }
    
    def _handle_hybrid_query(self, query_text: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """处理混合查询
        
        Args:
            query_text: 查询文本
            project_id: 项目ID，用于过滤数据
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        logger.info(f"处理混合查询: {query_text}")
        
        # 同时执行SQL查询和向量搜索
        sql_results = self._handle_sql_query(query_text, project_id)
        vector_results = self._handle_vector_search(query_text, project_id)
        
        return {
            'type': 'hybrid',
            'sql_results': sql_results,
            'vector_results': vector_results,
            'total_count': sql_results.get('count', 0) + vector_results.get('count', 0)
        }
    
    def _synthesize_answer(self, result: Dict[str, Any], query_text: str, intent: str) -> str:
        """合成最终回答
        
        Args:
            result: 查询结果
            query_text: 查询文本
            intent: 查询意图
            
        Returns:
            str: 合成的回答
        """
        logger.info("合成最终回答")
        
        if self.llm_tool:
            # 使用LLM合成回答
            return self.llm_tool.generate_answer(result, query_text, intent)
        else:
            # 简单的模板回答
            if result.get('type') == 'sql':
                count = result.get('count', 0)
                results = result.get('results', [])
                
                if count == 0:
                    return f"没有找到与'{query_text}'相关的结构化数据。"
                elif count == 1:
                    return f"查询结果: {results[0]}"
                else:
                    return f"找到了 {count} 条相关记录: {results[:3]}..."
            
            elif result.get('type') == 'vector':
                count = result.get('count', 0)
                results = result.get('results', [])
                
                if count == 0:
                    return f"没有找到与'{query_text}'相关的非结构化数据。"
                elif count == 1:
                    return f"相关文档: {results[0].get('content', '')[:100]}..."
                else:
                    return f"找到了 {count} 条相关文档。"
            
            elif result.get('type') == 'hybrid':
                sql_count = result.get('sql_results', {}).get('count', 0)
                vector_count = result.get('vector_results', {}).get('count', 0)
                
                return f"结构化数据找到 {sql_count} 条记录，非结构化数据找到 {vector_count} 条文档。"
            
            else:
                return f"查询完成，结果: {result}"
    
    def _save_query_history(self, query_text: str, answer: str, user_id: Optional[str], project_id: Optional[str], intent: str):
        """保存查询历史
        
        Args:
            query_text: 查询文本
            answer: 回答
            user_id: 用户ID
            project_id: 项目ID
            intent: 查询意图
        """
        logger.info(f"保存查询历史: 用户 {user_id} - 查询: {query_text[:30]}...")
        # 实际项目中，这里应该将查询历史保存到数据库
        # 这里使用日志模拟保存
    
    def _get_mock_sql_results(self, query_text: str) -> Dict[str, Any]:
        """获取模拟的SQL查询结果
        
        Args:
            query_text: 查询文本
            
        Returns:
            Dict[str, Any]: 模拟的SQL查询结果
        """
        # 根据查询文本生成不同的模拟结果
        query_lower = query_text.lower()
        
        if '安全隐患' in query_lower:
            return {
                'type': 'sql',
                'sql': f"SELECT * FROM safety_hazards WHERE description LIKE '%{query_lower}%'",
                'results': [
                    {
                        'id': 'haz_001',
                        'location': 'B区1号楼',
                        'description': '脚手架未固定',
                        'severity': 'high',
                        'date': '2024-03-10',
                        'status': 'resolved'
                    },
                    {
                        'id': 'haz_002',
                        'location': 'B区2号楼',
                        'description': '安全网破损',
                        'severity': 'medium',
                        'date': '2024-03-12',
                        'status': 'pending'
                    }
                ],
                'count': 2
            }
        elif '完成量' in query_lower or '进度' in query_lower:
            return {
                'type': 'sql',
                'sql': f"SELECT workpoint, process, SUM(quantity) as total_quantity FROM construction_records GROUP BY workpoint, process",
                'results': [
                    {
                        'workpoint': 'B区1号楼',
                        'process': '混凝土浇筑',
                        'total_quantity': '500m³'
                    },
                    {
                        'workpoint': 'B区2号楼',
                        'process': '钢筋绑扎',
                        'total_quantity': '300t'
                    }
                ],
                'count': 2
            }
        else:
            return {
                'type': 'sql',
                'sql': f"SELECT * FROM construction_records WHERE description LIKE '%{query_lower}%'",
                'results': [],
                'count': 0
            }
    
    def _get_mock_vector_results(self, query_text: str) -> Dict[str, Any]:
        """获取模拟的向量搜索结果
        
        Args:
            query_text: 查询文本
            
        Returns:
            Dict[str, Any]: 模拟的向量搜索结果
        """
        return {
            'type': 'vector',
            'results': [
                {
                    'id': 'doc_001',
                    'title': 'B区施工记录报告',
                    'content': '2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组...',
                    'score': 0.95
                },
                {
                    'id': 'doc_002',
                    'title': 'B区安全检查记录',
                    'content': '2024年3月10日，B区1号楼脚手架未固定，已要求整改...',
                    'score': 0.88
                }
            ],
            'count': 2
        }
    
    def consume_task(self):
        """从消息队列消费任务"""
        logger.info("从消息队列消费任务")
        task = self.message_queue.consume('query_processing')
        if task:
            logger.info(f"接收到任务: {task.get('type')}")
            result = self.process_query(task)
            logger.info(f"任务处理结果: {result.get('status')}")
        else:
            logger.info("没有新任务")
    
    def start(self):
        """启动问答与查询智能体"""
        logger.info("启动问答与查询智能体")
        self._running = True
        
    def stop(self):
        """停止问答与查询智能体"""
        logger.info("停止问答与查询智能体")
        self._running = False


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    agent = QAQueryAgent()
    agent.start()
    
    # 测试查询处理
    test_task = {
        'type': 'query',
        'priority': 7,
        'payload': {
            'query_text': '上个月B区有哪些安全隐患？',
            'user_id': 'user_789',
            'project_id': 'proj_456'
        },
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'query_processing',
            'user_id': 'user_789'
        }
    }
    
    try:
        result = agent.process_query(test_task)
        logger.info(f"查询处理测试成功: {result}")
    except Exception as e:
        logger.error(f"查询处理测试失败: {e}")
    
    agent.stop()
