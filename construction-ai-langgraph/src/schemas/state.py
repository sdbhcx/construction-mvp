"""
LangGraph状态定义
"""
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
from pydantic import BaseModel, Field
from langgraph.graph import add_messages
import operator

class ConstructionState(TypedDict):
    """施工记录处理状态"""
    # 输入
    file_path: str
    file_hash: str
    file_type: str
    
    # 处理状态
    current_step: str
    status: str  # pending, processing, completed, failed
    error: Optional[str]
    
    # 中间结果
    raw_image: Optional[Any]
    ocr_results: Dict[str, Any]
    extracted_text: str
    ner_results: Dict[str, Any]
    table_results: Dict[str, Any]
    vlm_response: Dict[str, Any]
    
    # 最终结果
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    validation_results: Dict[str, Any]
    formatted_output: Dict[str, Any]
    
    # 元数据
    start_time: datetime
    end_time: Optional[datetime]
    processing_time: Optional[float]
    warnings: List[str]
    
    # 消息历史
    messages: Annotated[List[Any], add_messages]

class ConstructionDocument(BaseModel):
    """施工记录文档模型"""
    id: str = Field(description="文档ID")
    file_hash: str = Field(description="文件哈希")
    file_type: str = Field(description="文件类型")
    
    # 原始内容
    raw_content: Optional[Dict] = Field(default=None, description="原始内容")
    
    # 解析结果
    parsed_text: str = Field(default="", description="解析后的文本")
    ocr_confidence: float = Field(default=0.0, description="OCR置信度")
    layout_info: Dict[str, Any] = Field(default_factory=dict, description="布局信息")
    
    # 结构化数据
    structured_data: Dict[str, Any] = Field(default_factory=dict, description="结构化数据")
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="置信度分数")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    processing_history: List[Dict] = Field(default_factory=list, description="处理历史")
    
    class Config:
        arbitrary_types_allowed = True

class ProcessingStep(BaseModel):
    """处理步骤"""
    step_name: str = Field(description="步骤名称")
    step_type: str = Field(description="步骤类型")
    status: str = Field(description="状态")
    start_time: datetime = Field(description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    duration: Optional[float] = Field(default=None, description="持续时间")
    result: Optional[Dict] = Field(default=None, description="结果")
    error: Optional[str] = Field(default=None, description="错误信息")


class ExtractionState(TypedDict):
    """信息抽取处理状态"""
    # 输入
    file_path: str
    file_type: str
    file_size: Optional[int] = None
    file_mtime: Optional[str] = None
    file_exists: bool = False
    
    # 处理状态
    current_step: str = "start"
    status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None
    
    # 中间结果
    raw_image: Optional[Any] = None
    ocr_results: Dict[str, Any] = {}  # 默认空字典
    extracted_text: str = ""
    ner_results: Dict[str, Any] = {}  # 默认空字典
    table_results: Dict[str, Any] = {}  # 默认空字典
    vlm_response: Dict[str, Any] = {}  # 默认空字典
    
    # 最终结果
    extracted_data: Dict[str, Any] = {}  # 默认空字典
    confidence_scores: Dict[str, float] = {}  # 默认空字典
    validation_results: Dict[str, Any] = {}  # 默认空字典
    formatted_output: Dict[str, Any] = {}  # 默认空字典
    
    # 元数据
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    warnings: List[str] = []  # 默认空列表
    
    # 额外信息
    vlm_confidence: float = 0.0
    vlm_verified: bool = False
    additional_info: Dict[str, Any] = {}  # 默认空字典
    vlm_validation: Dict[str, Any] = {}  # 默认空字典
    entities_linked: bool = False
    ocr_postprocessed: bool = False
    ocr_confidence: float = 0.0
    
    # 复核信息
    needs_review: bool = False
    review_reasons: List[str] = []  # 默认空列表
    review_task_id: Optional[str] = None
    added_to_review_queue: bool = False
    review_approved: Optional[bool] = None
    review_feedback: str = ""
    reviewer_id: Optional[str] = None
    review_completed: bool = False
    
    # 记录信息
    record_id: Optional[str] = None
    record_saved: bool = False
    record_updated: bool = False
    reference_data_linked: bool = False


class QueryState(TypedDict):
    """查询处理状态"""
    # 输入
    query_text: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    
    # 处理状态
    current_step: str = "start"
    status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None
    
    # 预处理结果
    preprocessed_query: str = ""
    query_length: int = 0
    query_valid: bool = False
    validation_results: Dict[str, Any] = {}  # 默认空字典
    
    # 意图识别
    intent: str = "unknown"
    intent_confidence: float = 0.0
    
    # SQL查询
    sql_query: str = ""
    sql_results: List[Dict[str, Any]] = []  # 默认空列表
    sql_executed: bool = False
    sql_result_count: int = 0
    formatted_sql_results: List[Dict[str, Any]] = []  # 默认空列表
    sql_formatted: bool = False
    sql_valid: bool = False
    sql_generated: bool = False
    sql_validation_error: Optional[str] = None
    
    # 向量搜索
    vector_results: List[Dict[str, Any]] = []  # 默认空列表
    reranked_results: List[Dict[str, Any]] = []  # 默认空列表
    relevant_passages: List[Dict[str, Any]] = []  # 默认空列表
    vector_search_completed: bool = False
    vector_result_count: int = 0
    rerank_completed: bool = False
    reranked_result_count: int = 0
    passage_extraction_completed: bool = False
    formatted_vector_results: List[Dict[str, Any]] = []  # 默认空列表
    vector_formatted: bool = False
    
    # 回答合成
    synthesized_answer: str = ""
    answer_confidence: float = 0.0
    answer_synthesized: bool = False
    answer_valid: bool = False
    answer_validation: Dict[str, Any] = {}  # 默认空字典
    answer_validation_completed: bool = False
    answer_validation_error: Optional[str] = None
    formatted_answer: str = ""
    answer_formatted: bool = False
    
    # 最终结果
    formatted_output: Dict[str, Any] = {}  # 默认空字典
    result_saved: bool = False
    result_path: Optional[str] = None
    query_result_saved: bool = False
    query_result_path: Optional[str] = None
    
    # 元数据
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    context: Dict[str, Any] = {}  # 默认空字典