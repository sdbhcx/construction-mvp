#!/usr/bin/env python3
# information_extraction_agent.py - 信息抽取智能体

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InformationExtractionAgent:
    """信息抽取智能体，负责从文档中提取结构化信息"""
    
    def __init__(self, ocr_tool: Any = None, ner_tool: Any = None, vlm_tool: Any = None):
        """初始化信息抽取智能体
        
        Args:
            ocr_tool: OCR工具实例
            ner_tool: NER工具实例
            vlm_tool: VLM工具实例
        """
        logger.info("初始化信息抽取智能体")
        self.ocr_tool = ocr_tool
        self.ner_tool = ner_tool
        self.vlm_tool = vlm_tool
        self.message_queue = self._init_message_queue()
        self._running = False
    
    def _init_message_queue(self):
        """初始化消息队列客户端"""
        from .orchestrator import MockMessageQueue
        logger.info("初始化消息队列客户端")
        return MockMessageQueue()
    
    def process_document(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理文档，提取结构化信息
        
        Args:
            task: 任务信息，包含文档路径、类型等
            
        Returns:
            Dict[str, Any]: 提取的结构化信息
        """
        try:
            logger.info(f"开始处理文档: {task.get('payload', {}).get('file_path', '未知文件')}")
            
            # 1. 解析任务信息
            payload = task.get('payload', {})
            file_path = payload.get('file_path')
            file_type = payload.get('file_type')
            
            if not file_path:
                logger.error("任务缺少文件路径")
                raise ValueError("任务缺少文件路径")
            
            # 2. 使用信息抽取图处理文档
            from src.graphs.information_extraction_graph import InformationExtractionGraph
            
            # 创建图实例
            graph = InformationExtractionGraph()
            
            # 构建图
            graph.build_graph()
            
            # 异步运行图
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(graph.extract_information(file_path, file_type))
            loop.close()
            
            logger.info(f"成功处理文档: {file_path}")
            
            return {
                'status': 'success',
                'message': '文档处理成功',
                'construction_record': result.get('extracted_data', {}),
                'timestamp': datetime.now().isoformat(),
                'confidence': result.get('confidence', 0.0),
                'processing_time': result.get('processing_time', 0.0),
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            logger.error(f"处理文档失败: {e}")
            return {
                'status': 'error',
                'message': f'文档处理失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_construction_record(self, validated_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成施工记录
        
        Args:
            validated_info: 验证后的信息
            
        Returns:
            Dict[str, Any]: 施工记录
        """
        logger.info("生成施工记录")
        
        # 模拟匹配生产进度系统中的工点、队伍、分项、部位、工序ID
        # 实际项目中，这里应该调用生产进度系统的API或数据库查询来获取真实ID
        record = {
            'date': validated_info.get('date'),
            'weather': validated_info.get('weather'),
            'workpoint': validated_info.get('workpoint'),
            'workpoint_id': f"wp_{hash(validated_info.get('workpoint', '')) % 1000:03d}",
            'team': validated_info.get('team'),
            'team_id': f"team_{hash(validated_info.get('team', '')) % 1000:03d}",
            'subproject': validated_info.get('subproject'),
            'subproject_id': f"sp_{hash(validated_info.get('subproject', '')) % 1000:03d}",
            'position': validated_info.get('position'),
            'position_id': f"pos_{hash(validated_info.get('position', '')) % 1000:03d}",
            'process': validated_info.get('process'),
            'process_id': f"proc_{hash(validated_info.get('process', '')) % 1000:03d}",
            'quantity': validated_info.get('quantity'),
            'confidence': validated_info.get('confidence'),
            'needs_review': validated_info.get('needs_review', False),
            'created_at': datetime.now().isoformat(),
            'verified_by_vlm': validated_info.get('verified_by_vlm', True)
        }
        
        return record
    
    def _save_results(self, construction_record: Dict[str, Any]):
        """保存提取结果
        
        Args:
            construction_record: 施工记录
        """
        logger.info(f"保存施工记录: {construction_record.get('workpoint')} - {construction_record.get('date')}")
        # 实际项目中，这里应该将施工记录保存到数据库或发送到生产进度系统
        # 这里使用日志模拟保存
    
    def consume_task(self):
        """从消息队列消费任务"""
        logger.info("从消息队列消费任务")
        task = self.message_queue.consume('document_processing')
        if task:
            logger.info(f"接收到任务: {task.get('type')}")
            result = self.process_document(task)
            logger.info(f"任务处理结果: {result.get('status')}")
        else:
            logger.info("没有新任务")
    
    def start(self):
        """启动信息抽取智能体"""
        logger.info("启动信息抽取智能体")
        self._running = True
        
    def stop(self):
        """停止信息抽取智能体"""
        logger.info("停止信息抽取智能体")
        self._running = False


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    agent = InformationExtractionAgent()
    agent.start()
    
    # 测试文档处理
    test_task = {
        'type': 'extraction',
        'priority': 8,
        'payload': {
            'file_path': '/path/to/test.pdf',
            'file_type': 'pdf',
            'file_size': 1024,
            'uploader_id': 'user_123',
            'project_id': 'proj_456'
        },
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'task_type': 'document_processing',
            'file_type': 'pdf'
        }
    }
    
    try:
        result = agent.process_document(test_task)
        logger.info(f"文档处理测试成功: {result}")
    except Exception as e:
        logger.error(f"文档处理测试失败: {e}")
    
    agent.stop()
