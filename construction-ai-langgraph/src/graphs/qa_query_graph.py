#!/usr/bin/env python3
# qa_query_graph.py - 问答查询图，用于处理自然语言查询

from typing import Dict, Any, Optional, List, TypedDict, Annotated
from datetime import datetime
import asyncio
import time

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator

from src.schemas.state import QueryState
from src.nodes.input_nodes import validate_query_node, preprocess_query_node
from src.nodes.intent_nodes import recognize_intent_node
from src.nodes.sql_query_nodes import generate_sql_node, execute_sql_node, format_sql_result_node
from src.nodes.vector_search_nodes import vector_search_node, rerank_results_node
from src.nodes.answer_synthesis_nodes import synthesize_answer_node, validate_answer_node
from src.nodes.output_nodes import format_query_output_node, save_query_results_node
from src.utils.logger import logger
from src.utils.metrics import record_metric


class QAQueryGraph:
    """问答查询图，负责处理自然语言查询"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化问答查询图
        
        Args:
            config: 图配置
        """
        self.config = config or {}
        self.graph = None
        self.compiled_graph = None
    
    def build_graph(self):
        """构建问答查询图"""
        logger.info("构建问答查询图...")
        
        # 创建工作流
        workflow = StateGraph(QueryState)
        
        # 添加节点
        workflow.add_node("validate_query", self._wrap_node(validate_query_node))
        workflow.add_node("preprocess_query", self._wrap_node(preprocess_query_node))
        workflow.add_node("recognize_intent", self._wrap_node(recognize_intent_node))
        workflow.add_node("generate_sql", self._wrap_node(generate_sql_node))
        workflow.add_node("execute_sql", self._wrap_node(execute_sql_node))
        workflow.add_node("format_sql_result", self._wrap_node(format_sql_result_node))
        workflow.add_node("vector_search", self._wrap_node(vector_search_node))
        workflow.add_node("rerank_results", self._wrap_node(rerank_results_node))
        workflow.add_node("synthesize_answer", self._wrap_node(synthesize_answer_node))
        workflow.add_node("validate_answer", self._wrap_node(validate_answer_node))
        workflow.add_node("format_query_output", self._wrap_node(format_query_output_node))
        workflow.add_node("save_query_results", self._wrap_node(save_query_results_node))
        
        # 设置边
        workflow.set_entry_point("validate_query")
        
        # 主流程
        workflow.add_edge("validate_query", "preprocess_query")
        workflow.add_edge("preprocess_query", "recognize_intent")
        
        # 意图路由：根据查询意图选择处理路径
        workflow.add_conditional_edges(
            "recognize_intent",
            self._route_after_intent_recognition,
            {
                "structured_query": "generate_sql",
                "unstructured_query": "vector_search",
                "hybrid_query": "generate_sql",  # 混合查询先执行结构化查询
                "unknown": "vector_search"  # 未知意图默认走向量搜索
            }
        )
        
        # 结构化查询分支
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "format_sql_result")
        
        # 非结构化查询分支
        workflow.add_edge("vector_search", "rerank_results")
        
        # 混合查询处理：结构化查询结果出来后，需要执行向量搜索
        workflow.add_conditional_edges(
            "format_sql_result",
            self._route_after_sql_processing,
            {
                "need_vector_search": "vector_search",
                "ready_for_synthesis": "synthesize_answer"
            }
        )
        
        # 向量搜索结果处理
        workflow.add_edge("rerank_results", "synthesize_answer")
        
        # 回答合成与验证
        workflow.add_edge("synthesize_answer", "validate_answer")
        workflow.add_edge("validate_answer", "format_query_output")
        workflow.add_edge("format_query_output", "save_query_results")
        workflow.add_edge("save_query_results", END)
        
        # 编译图
        self.graph = workflow
        self.compiled_graph = workflow.compile()
        
        logger.info("问答查询图构建完成")
        return self.compiled_graph
    
    def _wrap_node(self, node_func):
        """包装节点函数，添加监控和错误处理"""
        async def wrapped_node(state: QueryState):
            start_time = time.time()
            step_name = node_func.__name__
            
            try:
                logger.info(f"问答查询图 - 执行节点: {step_name}")
                
                # 更新状态
                state["current_step"] = step_name
                state["status"] = "processing"
                
                # 执行节点
                result = await node_func(state)
                
                # 记录执行时间
                duration = time.time() - start_time
                record_metric(f"query_node_{step_name}_duration_seconds", duration)
                
                logger.info(f"问答查询图 - 节点完成: {step_name}, 耗时: {duration:.2f}s")
                
                return result
                
            except Exception as e:
                error_msg = f"问答查询图 - 节点执行失败: {step_name}, 错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                # 记录失败指标
                record_metric(f"query_node_{step_name}_failures_total", 1)
                
                # 更新状态
                state["status"] = "failed"
                state["error"] = error_msg
                state["current_step"] = step_name
                
                return state
        
        return wrapped_node
    
    def _route_after_intent_recognition(self, state: QueryState) -> str:
        """意图识别后的路由逻辑
        
        Args:
            state: 查询状态
            
        Returns:
            str: 下一个节点名称
        """
        intent = state.get("intent", "unknown")
        
        if intent == "structured_query":
            return "structured_query"
        elif intent == "unstructured_query":
            return "unstructured_query"
        elif intent == "hybrid_query":
            return "hybrid_query"
        else:
            return "unknown"
    
    def _route_after_sql_processing(self, state: QueryState) -> str:
        """SQL处理后的路由逻辑
        
        Args:
            state: 查询状态
            
        Returns:
            str: 下一个节点名称
        """
        # 检查意图是否为混合查询
        intent = state.get("intent", "structured_query")
        if intent == "hybrid_query":
            return "need_vector_search"
        
        # 检查SQL结果是否为空
        sql_results = state.get("sql_results", [])
        if not sql_results:
            # SQL结果为空，尝试向量搜索
            return "need_vector_search"
        
        return "ready_for_synthesis"
    
    async def process_query(self, query_text: str, user_id: Optional[str] = None, project_id: Optional[str] = None) -> Dict[str, Any]:
        """处理自然语言查询
        
        Args:
            query_text: 查询文本
            user_id: 用户ID
            project_id: 项目ID
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        if not self.compiled_graph:
            self.build_graph()
        
        logger.info(f"开始处理查询: {query_text}")
        
        # 初始化状态
        initial_state = QueryState(
            query_text=query_text,
            user_id=user_id,
            project_id=project_id,
            current_step="start",
            status="pending",
            error=None,
            preprocessed_query="",
            intent="unknown",
            sql_query="",
            sql_results=[],
            formatted_sql_results={},
            vector_results=[],
            reranked_results=[],
            synthesized_answer="",
            answer_confidence=0.0,
            formatted_output={},
            start_time=datetime.now(),
            end_time=None,
            processing_time=None,
            context={}
        )
        
        try:
            # 执行图
            start_time = time.time()
            final_state = await self.compiled_graph.ainvoke(initial_state)
            total_time = time.time() - start_time
            
            logger.info(f"查询处理完成: {query_text}, 耗时: {total_time:.2f}s")
            record_metric("query_processing_duration_seconds", total_time)
            
            return {
                "status": final_state.get("status", "success"),
                "query_text": query_text,
                "intent": final_state.get("intent", "unknown"),
                "answer": final_state.get("synthesized_answer", ""),
                "confidence": final_state.get("answer_confidence", 0.0),
                "sql_results": final_state.get("sql_results", []),
                "vector_results": final_state.get("vector_results", []),
                "processing_time": total_time,
                "formatted_output": final_state.get("formatted_output", {})
            }
            
        except Exception as e:
            error_msg = f"查询处理失败: {query_text}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            record_metric("query_processing_failures_total", 1)
            raise
    
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
                logger.info(f"问答查询图已保存到: {output_path}")
            
            return mermaid_graph
            
        except Exception as e:
            logger.warning(f"问答查询图可视化失败: {str(e)}")
            return None
