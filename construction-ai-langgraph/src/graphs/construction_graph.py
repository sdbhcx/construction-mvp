"""
施工记录处理主图
使用LangGraph构建智能处理流水线
"""
from typing import Dict, Any, Optional, List, TypedDict, Annotated
from datetime import datetime
import asyncio
import time

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator

from src.schemas.state import ConstructionState, ConstructionDocument
from src.nodes.input_nodes import load_document_node, validate_document_node
from src.nodes.ocr_nodes import run_ocr_node, postprocess_ocr_node
from src.nodes.ner_nodes import run_ner_node, link_entities_node
from src.nodes.table_nodes import detect_tables_node, extract_table_content_node
from src.nodes.vlm_nodes import run_vlm_node, parse_vlm_response_node
from src.nodes.validation_nodes import validate_extraction_node, calculate_confidence_node
from src.nodes.output_nodes import format_output_node, save_results_node
from src.utils.logger import logger
from src.utils.metrics import record_metric

class ConstructionGraph:
    """施工记录处理图"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = None
        self.compiled_graph = None
        
    def build_graph(self):
        """构建处理图"""
        logger.info("构建施工记录处理图...")
        
        # 创建工作流
        workflow = StateGraph(ConstructionState)
        
        # 添加节点
        # 1. 输入处理阶段
        workflow.add_node("load_document", self._wrap_node(load_document_node))
        workflow.add_node("validate_document", self._wrap_node(validate_document_node))
        
        # 2. 解析阶段
        workflow.add_node("run_ocr", self._wrap_node(run_ocr_node))
        workflow.add_node("postprocess_ocr", self._wrap_node(postprocess_ocr_node))
        workflow.add_node("detect_tables", self._wrap_node(detect_tables_node))
        workflow.add_node("extract_table_content", self._wrap_node(extract_table_content_node))
        
        # 3. 理解阶段
        workflow.add_node("run_ner", self._wrap_node(run_ner_node))
        workflow.add_node("link_entities", self._wrap_node(link_entities_node))
        
        # 4. 提取阶段
        workflow.add_node("run_vlm", self._wrap_node(run_vlm_node))
        workflow.add_node("parse_vlm_response", self._wrap_node(parse_vlm_response_node))
        
        # 5. 验证阶段
        workflow.add_node("validate_extraction", self._wrap_node(validate_extraction_node))
        workflow.add_node("calculate_confidence", self._wrap_node(calculate_confidence_node))
        
        # 6. 输出阶段
        workflow.add_node("format_output", self._wrap_node(format_output_node))
        workflow.add_node("save_results", self._wrap_node(save_results_node))
        
        # 设置边
        # 开始 -> 加载文档
        workflow.set_entry_point("load_document")
        
        # 输入处理流程
        workflow.add_edge("load_document", "validate_document")
        
        # 解析分支
        workflow.add_conditional_edges(
            "validate_document",
            self._route_after_validation,
            {
                "ocr_required": "run_ocr",
                "tables_required": "detect_tables",
                "direct_vlm": "run_vlm"
            }
        )
        
        # OCR处理流程
        workflow.add_edge("run_ocr", "postprocess_ocr")
        workflow.add_edge("postprocess_ocr", "run_ner")
        
        # 表格处理流程
        workflow.add_edge("detect_tables", "extract_table_content")
        workflow.add_edge("extract_table_content", "run_ner")
        
        # 理解阶段
        workflow.add_edge("run_ner", "link_entities")
        workflow.add_edge("link_entities", "run_vlm")
        
        # 提取阶段
        workflow.add_edge("run_vlm", "parse_vlm_response")
        
        # 验证阶段
        workflow.add_edge("parse_vlm_response", "validate_extraction")
        workflow.add_edge("validate_extraction", "calculate_confidence")
        
        # 输出阶段
        workflow.add_edge("calculate_confidence", "format_output")
        workflow.add_edge("format_output", "save_results")
        workflow.add_edge("save_results", END)
        
        # 编译图
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("施工记录处理图构建完成")
        return self.compiled_graph
    
    def _wrap_node(self, node_func):
        """包装节点函数，添加监控和错误处理"""
        async def wrapped_node(state: ConstructionState):
            start_time = time.time()
            step_name = node_func.__name__
            
            try:
                logger.info(f"开始执行节点: {step_name}")
                
                # 更新状态
                state["current_step"] = step_name
                state["status"] = "processing"
                
                # 执行节点
                result = await node_func(state)
                
                # 记录执行时间
                duration = time.time() - start_time
                record_metric(f"node_{step_name}_duration_seconds", duration)
                
                logger.info(f"节点完成: {step_name}, 耗时: {duration:.2f}s")
                
                return result
                
            except Exception as e:
                error_msg = f"节点执行失败: {step_name}, 错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # 记录失败指标
                record_metric(f"node_{step_name}_failures_total", 1)
                
                # 更新状态
                state["status"] = "failed"
                state["error"] = error_msg
                state["current_step"] = step_name
                
                # 直接跳到结束
                return {"__end__": True}
        
        return wrapped_node
    
    def _route_after_validation(self, state: ConstructionState) -> str:
        """验证后的路由逻辑"""
        file_type = state.get("file_type", "").lower()
        
        # 如果是图片，需要OCR
        if file_type in ["jpg", "jpeg", "png", "bmp", "tiff"]:
            return "ocr_required"
        
        # 如果是PDF，检查是否需要表格处理
        elif file_type == "pdf":
            # 这里可以添加更复杂的逻辑，比如检查PDF是否包含表格
            return "tables_required"
        
        # 如果是纯文本，直接进入VLM
        elif file_type == "txt":
            return "direct_vlm"
        
        # 默认走OCR流程
        return "ocr_required"
    
    async def process_document(self, file_path: str, config: Optional[Dict] = None) -> ConstructionDocument:
        """处理文档"""
        if not self.compiled_graph:
            self.build_graph()
        
        logger.info(f"开始处理文档: {file_path}")
        
        # 初始化状态
        initial_state = ConstructionState(
            file_path=file_path,
            file_hash="",  # 将在load_document节点计算
            file_type=self._get_file_type(file_path),
            current_step="start",
            status="pending",
            error=None,
            raw_image=None,
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
        
        # 添加配置
        if config:
            initial_state["config"] = config
        
        try:
            # 执行图
            start_time = time.time()
            final_state = await self.compiled_graph.ainvoke(initial_state)
            total_time = time.time() - start_time
            
            # 构建结果文档
            document = ConstructionDocument(
                id=final_state.get("file_hash", ""),
                file_hash=final_state.get("file_hash", ""),
                file_type=final_state.get("file_type", ""),
                raw_content=final_state.get("ocr_results", {}),
                parsed_text=final_state.get("extracted_text", ""),
                ocr_confidence=final_state.get("ocr_results", {}).get("confidence", 0.0),
                layout_info=final_state.get("ocr_results", {}).get("layout", {}),
                structured_data=final_state.get("formatted_output", {}).get("data", {}),
                confidence_scores=final_state.get("formatted_output", {}).get("confidences", {}),
                metadata={
                    "processing_time": total_time,
                    "status": final_state.get("status", ""),
                    "error": final_state.get("error"),
                    "warnings": final_state.get("warnings", []),
                    "steps": self._extract_processing_steps(final_state)
                }
            )
            
            logger.info(f"文档处理完成: {file_path}, 耗时: {total_time:.2f}s")
            record_metric("document_processing_duration_seconds", total_time)
            
            return document
            
        except Exception as e:
            error_msg = f"文档处理失败: {file_path}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise
    
    def _get_file_type(self, file_path: str) -> str:
        """获取文件类型"""
        import os
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')
    
    def _extract_processing_steps(self, state: ConstructionState) -> List[Dict]:
        """从状态中提取处理步骤"""
        # 这里可以从state中提取处理历史
        # 简化实现
        return [
            {
                "step": state.get("current_step", "unknown"),
                "status": state.get("status", "unknown")
            }
        ]
    
    def visualize(self, output_path: Optional[str] = None):
        """可视化图结构"""
        if not self.graph:
            self.build_graph()
        
        try:
            # 生成Mermaid图
            mermaid_graph = self.graph.get_graph().draw_mermaid()
            
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(mermaid_graph)
                logger.info(f"图已保存到: {output_path}")
            
            return mermaid_graph
            
        except Exception as e:
            logger.warning(f"图可视化失败: {str(e)}")
            return None