#!/usr/bin/env python3
# information_extraction_graph.py - 信息抽取图，用于从文档中提取结构化信息

from typing import Dict, Any, Optional, List, TypedDict, Annotated
from datetime import datetime
import asyncio
import time

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator

from src.schemas.state import ExtractionState
from src.nodes.input_nodes import load_document_node, validate_document_node
from src.nodes.ocr_nodes import run_ocr_node, postprocess_ocr_node
from src.nodes.ner_nodes import run_ner_node, link_entities_node
from src.nodes.table_nodes import detect_tables_node, extract_table_content_node
from src.nodes.vlm_nodes import run_vlm_node, parse_vlm_response_node
from src.nodes.validation_nodes import validate_extraction_node, calculate_confidence_node
from src.nodes.output_nodes import format_output_node, save_results_node
from src.utils.logger import logger
from src.utils.metrics import record_metric


class InformationExtractionGraph:
    """信息抽取图，负责从各种文档中提取结构化信息"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化信息抽取图
        
        Args:
            config: 图配置
        """
        self.config = config or {}
        self.graph = None
        self.compiled_graph = None
    
    def build_graph(self):
        """构建信息抽取图"""
        logger.info("构建信息抽取图...")
        
        # 创建工作流
        workflow = StateGraph(ExtractionState)
        
        # 添加节点
        workflow.add_node("load_document", self._wrap_node(load_document_node))
        workflow.add_node("validate_document", self._wrap_node(validate_document_node))
        workflow.add_node("run_ocr", self._wrap_node(run_ocr_node))
        workflow.add_node("postprocess_ocr", self._wrap_node(postprocess_ocr_node))
        workflow.add_node("run_ner", self._wrap_node(run_ner_node))
        workflow.add_node("link_entities", self._wrap_node(link_entities_node))
        workflow.add_node("detect_tables", self._wrap_node(detect_tables_node))
        workflow.add_node("extract_table_content", self._wrap_node(extract_table_content_node))
        workflow.add_node("run_vlm", self._wrap_node(run_vlm_node))
        workflow.add_node("parse_vlm_response", self._wrap_node(parse_vlm_response_node))
        workflow.add_node("validate_extraction", self._wrap_node(validate_extraction_node))
        workflow.add_node("calculate_confidence", self._wrap_node(calculate_confidence_node))
        workflow.add_node("format_output", self._wrap_node(format_output_node))
        workflow.add_node("save_results", self._wrap_node(save_results_node))
        
        # 设置边
        workflow.set_entry_point("load_document")
        
        # 主流程
        workflow.add_edge("load_document", "validate_document")
        
        # 条件路由：根据文档类型选择处理路径
        workflow.add_conditional_edges(
            "validate_document",
            self._route_after_document_validation,
            {
                "image_ocr": "run_ocr",
                "pdf_processing": "detect_tables",
                "text_processing": "run_ner",
                "direct_vlm": "run_vlm"
            }
        )
        
        # OCR分支
        workflow.add_edge("run_ocr", "postprocess_ocr")
        workflow.add_edge("postprocess_ocr", "run_ner")
        
        # 表格分支
        workflow.add_edge("detect_tables", "extract_table_content")
        workflow.add_edge("extract_table_content", "link_entities")
        
        # NER分支
        workflow.add_edge("run_ner", "link_entities")
        
        # VLM分支
        workflow.add_edge("run_vlm", "parse_vlm_response")
        workflow.add_edge("parse_vlm_response", "validate_extraction")
        
        # 实体链接后处理
        workflow.add_conditional_edges(
            "link_entities",
            self._route_after_entity_linking,
            {
                "need_vlm_refinement": "run_vlm",
                "ready_for_validation": "validate_extraction"
            }
        )
        
        # 验证后流程
        workflow.add_edge("validate_extraction", "calculate_confidence")
        workflow.add_edge("calculate_confidence", "format_output")
        workflow.add_edge("format_output", "save_results")
        workflow.add_edge("save_results", END)
        
        # 编译图
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("信息抽取图构建完成")
        return self.compiled_graph
    
    def _wrap_node(self, node_func):
        """包装节点函数，添加监控和错误处理"""
        async def wrapped_node(state: ExtractionState):
            start_time = time.time()
            step_name = node_func.__name__
            
            try:
                logger.info(f"信息抽取图 - 执行节点: {step_name}")
                
                # 更新状态
                state["current_step"] = step_name
                state["status"] = "processing"
                
                # 执行节点
                result = await node_func(state)
                
                # 记录执行时间
                duration = time.time() - start_time
                record_metric(f"extraction_node_{step_name}_duration_seconds", duration)
                
                logger.info(f"信息抽取图 - 节点完成: {step_name}, 耗时: {duration:.2f}s")
                
                return result
                
            except Exception as e:
                error_msg = f"信息抽取图 - 节点执行失败: {step_name}, 错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # 记录失败指标
                record_metric(f"extraction_node_{step_name}_failures_total", 1)
                
                # 更新状态
                state["status"] = "failed"
                state["error"] = error_msg
                state["current_step"] = step_name
                
                return state
        
        return wrapped_node
    
    def _route_after_document_validation(self, state: ExtractionState) -> str:
        """文档验证后的路由逻辑
        
        Args:
            state: 提取状态
            
        Returns:
            str: 下一个节点名称
        """
        file_type = state.get("file_type", "").lower()
        
        if file_type in ["jpg", "jpeg", "png", "bmp", "tiff"]:
            return "image_ocr"
        elif file_type == "pdf":
            return "pdf_processing"
        elif file_type == "txt" or file_type == "md":
            return "text_processing"
        else:
            return "direct_vlm"
    
    def _route_after_entity_linking(self, state: ExtractionState) -> str:
        """实体链接后的路由逻辑
        
        Args:
            state: 提取状态
            
        Returns:
            str: 下一个节点名称
        """
        # 简单的路由逻辑，根据实体链接结果决定是否需要VLM细化
        ner_results = state.get("ner_results", {})
        entities = ner_results.get("entities", [])
        
        # 如果实体数量少于5个，或者实体置信度低于阈值，则需要VLM细化
        if len(entities) < 5:
            return "need_vlm_refinement"
        
        avg_confidence = sum(entity.get("confidence", 0) for entity in entities) / len(entities) if entities else 0
        if avg_confidence < 0.8:
            return "need_vlm_refinement"
        
        return "ready_for_validation"
    
    async def extract_information(self, file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """提取文档中的信息
        
        Args:
            file_path: 文件路径
            file_type: 文件类型
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        if not self.compiled_graph:
            self.build_graph()
        
        logger.info(f"开始信息抽取: {file_path}")
        
        # 初始化状态
        initial_state = ExtractionState(
            file_path=file_path,
            file_type=file_type or self._get_file_type(file_path),
            current_step="start",
            status="pending",
            error=None,
            ocr_results={},
            extracted_text="",
            ner_results={},
            table_results={},
            vlm_response={},
            extracted_data={},
            confidence_scores={},
            validation_results={},
            formatted_output={},
            start_time=datetime.now(),
            end_time=None,
            processing_time=None,
            warnings=[],
            messages=[]
        )
        
        try:
            # 执行图
            start_time = time.time()
            final_state = await self.compiled_graph.ainvoke(initial_state)
            total_time = time.time() - start_time
            
            logger.info(f"信息抽取完成: {file_path}, 耗时: {total_time:.2f}s")
            record_metric("information_extraction_duration_seconds", total_time)
            
            return {
                "status": final_state.get("status", "success"),
                "extracted_data": final_state.get("extracted_data", {}),
                "formatted_output": final_state.get("formatted_output", {}),
                "confidence": final_state.get("confidence_scores", {}).get("overall", 0),
                "processing_time": total_time,
                "warnings": final_state.get("warnings", [])
            }
            
        except Exception as e:
            error_msg = f"信息抽取失败: {file_path}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            record_metric("information_extraction_failures_total", 1)
            raise
    
    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件类型
        """
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')
    
    def visualize(self, output_path: Optional[str] = None) -> Optional[str]:
        """可视化图结构
        
        Args:
            output_path: 输出路径
            
        Returns:
            Optional[str]: 可视化结果
        """
        if not self.graph:
            self.build_graph()
        
        try:
            mermaid_graph = self.graph.get_graph().draw_mermaid()
            
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(mermaid_graph)
                logger.info(f"信息抽取图已保存到: {output_path}")
            
            return mermaid_graph
            
        except Exception as e:
            logger.warning(f"信息抽取图可视化失败: {str(e)}")
            return None
