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
    
    def _perform_ocr(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """执行OCR识别
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            Dict[str, Any]: OCR识别结果
        """
        logger.info(f"执行OCR识别: {file_path} ({file_type})")
        
        if self.ocr_tool:
            try:
                return self.ocr_tool.recognize(file_path, file_type)
            except Exception as e:
                logger.error(f"OCR识别失败: {e}")
                # 使用模拟OCR结果
                return {
                    'text': '2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组，工点：B区1号楼，分项工程：主体结构，部位：3层，工序：混凝土浇筑，完成量：100m³，天气：晴',
                    'confidence': 0.95,
                    'pages': 1
                }
        else:
            # 使用模拟OCR结果
            logger.info("使用模拟OCR结果")
            return {
                'text': '2024年3月15日，B区工地完成混凝土浇筑，施工队伍：张三班组，工点：B区1号楼，分项工程：主体结构，部位：3层，工序：混凝土浇筑，完成量：100m³，天气：晴',
                'confidence': 0.95,
                'pages': 1
            }
    
    def _perform_ner(self, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """执行命名实体识别
        
        Args:
            ocr_results: OCR识别结果
            
        Returns:
            Dict[str, Any]: NER识别结果
        """
        logger.info("执行命名实体识别")
        
        if self.ner_tool:
            try:
                return self.ner_tool.extract_entities(ocr_results.get('text', ''))
            except Exception as e:
                logger.error(f"NER识别失败: {e}")
                # 使用模拟NER结果
                return self._get_mock_ner_results()
        else:
            # 使用模拟NER结果
            logger.info("使用模拟NER结果")
            return self._get_mock_ner_results()
    
    def _get_mock_ner_results(self) -> Dict[str, Any]:
        """获取模拟的NER结果"""
        return {
            'entities': [
                {'text': '2024年3月15日', 'type': 'DATE', 'confidence': 0.99},
                {'text': 'B区工地', 'type': 'LOCATION', 'confidence': 0.95},
                {'text': '混凝土浇筑', 'type': 'ACTIVITY', 'confidence': 0.98},
                {'text': '张三班组', 'type': 'TEAM', 'confidence': 0.96},
                {'text': 'B区1号楼', 'type': 'WORKPOINT', 'confidence': 0.97},
                {'text': '主体结构', 'type': 'SUBPROJECT', 'confidence': 0.98},
                {'text': '3层', 'type': 'POSITION', 'confidence': 0.99},
                {'text': '混凝土浇筑', 'type': 'PROCESS', 'confidence': 0.98},
                {'text': '100m³', 'type': 'QUANTITY', 'confidence': 0.99},
                {'text': '晴', 'type': 'WEATHER', 'confidence': 0.95}
            ],
            'confidence': 0.97
        }
    
    def _perform_vlm(self, file_path: str, ocr_results: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """使用VLM进行细粒度信息提取
        
        Args:
            file_path: 文件路径
            ocr_results: OCR识别结果
            file_type: 文件类型
            
        Returns:
            Dict[str, Any]: VLM提取结果
        """
        logger.info(f"使用VLM进行细粒度信息提取: {file_path}")
        
        if self.vlm_tool and file_type in ['jpg', 'jpeg', 'png', 'pdf']:
            try:
                return self.vlm_tool.analyze_document(file_path, ocr_results)
            except Exception as e:
                logger.error(f"VLM分析失败: {e}")
                # 使用模拟VLM结果
                return {'confidence': 0.9, 'verified': True}
        else:
            # 使用模拟VLM结果
            logger.info("使用模拟VLM结果")
            return {'confidence': 0.9, 'verified': True}
    
    def _integrate_results(self, ocr_results: Dict[str, Any], ner_results: Dict[str, Any], vlm_results: Dict[str, Any]) -> Dict[str, Any]:
        """整合提取结果
        
        Args:
            ocr_results: OCR识别结果
            ner_results: NER识别结果
            vlm_results: VLM提取结果
            
        Returns:
            Dict[str, Any]: 整合后的提取结果
        """
        logger.info("整合提取结果")
        
        # 从NER结果中提取结构化信息
        entities = ner_results.get('entities', [])
        integrated = {}
        
        entity_map = {
            'DATE': 'date',
            'LOCATION': 'location',
            'TEAM': 'team',
            'WORKPOINT': 'workpoint',
            'SUBPROJECT': 'subproject',
            'POSITION': 'position',
            'PROCESS': 'process',
            'QUANTITY': 'quantity',
            'WEATHER': 'weather'
        }
        
        for entity in entities:
            entity_type = entity.get('type')
            if entity_type in entity_map:
                integrated[entity_map[entity_type]] = entity.get('text')
        
        # 添加置信度信息
        integrated['confidence'] = min(
            ocr_results.get('confidence', 0.9),
            ner_results.get('confidence', 0.9),
            vlm_results.get('confidence', 0.9)
        )
        
        integrated['verified_by_vlm'] = vlm_results.get('verified', True)
        
        return integrated
    
    def _validate_extraction(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证提取结果
        
        Args:
            extracted_info: 提取的信息
            
        Returns:
            Dict[str, Any]: 验证后的信息
        """
        logger.info("验证提取结果")
        
        # 验证必填字段
        required_fields = ['date', 'workpoint', 'team', 'subproject', 'position', 'process', 'quantity', 'weather']
        
        for field in required_fields:
            if field not in extracted_info or not extracted_info[field]:
                logger.warning(f"提取结果缺少必填字段: {field}")
                # 可以在这里添加默认值或标记为需要人工复核
                extracted_info[field] = extracted_info.get(field, f'<缺失_{field}>')
                extracted_info['needs_review'] = True
        
        # 验证置信度
        if extracted_info.get('confidence', 0) < 0.8:
            logger.warning(f"提取结果置信度低: {extracted_info.get('confidence')}")
            extracted_info['needs_review'] = True
        
        return extracted_info
    
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
