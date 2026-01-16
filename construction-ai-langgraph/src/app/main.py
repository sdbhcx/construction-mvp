"""
FastAPI主应用
集成LangGraph智能体
"""
import os
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

from src.graphs.construction_graph import ConstructionGraph
from src.agents.orchestrator import ConstructionOrchestrator
from src.utils.logger import setup_logger, logger
from src.utils.metrics import setup_metrics
from src.app.config import settings

# 配置日志
setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("启动施工记录AI服务...")
    
    # 初始化图
    app.state.construction_graph = ConstructionGraph(settings.graph_config)
    app.state.construction_graph.build_graph()
    
    # 初始化调度器
    app.state.orchestrator = ConstructionOrchestrator(settings.agent_config)
    
    # 设置监控
    if settings.monitoring.enabled:
        setup_metrics()
    
    logger.info("施工记录AI服务启动完成")
    
    yield
    
    # 关闭时
    logger.info("关闭施工记录AI服务...")
    await app.state.orchestrator.cleanup()
    logger.info("施工记录AI服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="施工记录AI服务 (LangGraph)",
    description="基于LangGraph和智能体的施工记录多模态处理服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ProcessRequest(BaseModel):
    """处理请求"""
    config: Optional[Dict[str, Any]] = None
    enable_cache: bool = True
    timeout_seconds: int = 120

class ProcessResponse(BaseModel):
    """处理响应"""
    success: bool
    request_id: str
    file_hash: str
    processing_time: float
    extracted_data: Dict[str, Any]
    confidence_scores: Dict[str, float]
    warnings: List[str] = []
    error: Optional[str] = None
    graph_visualization: Optional[str] = None

class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    file_paths: List[str]
    config: Optional[Dict[str, Any]] = None
    enable_cache: bool = True
    timeout_seconds: int = 120
    parallel: bool = True

class BatchProcessResponse(BaseModel):
    """批量处理响应"""
    success: bool
    request_id: str
    total_files: int
    successful_files: int
    processing_time: float
    results: List[Dict[str, Any]]

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "construction-ai-langgraph",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/ready")
async def readiness_check():
    """就绪检查"""
    try:
        # 检查图是否初始化
        if not hasattr(app.state, 'construction_graph') or not app.state.construction_graph.compiled_graph:
            return JSONResponse(
                content={"status": "not ready", "reason": "graph not initialized"},
                status_code=503
            )
        
        # 检查调度器
        if not hasattr(app.state, 'orchestrator'):
            return JSONResponse(
                content={"status": "not ready", "reason": "orchestrator not initialized"},
                status_code=503
            )
        
        return {
            "status": "ready",
            "graph_initialized": True,
            "orchestrator_initialized": True
        }
    except Exception as e:
        return JSONResponse(
            content={"status": "not ready", "reason": str(e)},
            status_code=503
        )

# 处理端点
@app.post("/api/v1/process", response_model=ProcessResponse)
async def process_document(
    file: UploadFile = File(...),
    config: Optional[Dict[str, Any]] = None,
    enable_cache: bool = True,
    timeout_seconds: int = 120
):
    """处理单个文档"""
    request_id = f"req_{int(time.time() * 1000)}"
    start_time = time.time()
    
    logger.info(f"收到处理请求: {request_id}, 文件: {file.filename}")
    
    try:
        # 保存上传的文件
        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        try:
            # 使用图处理
            graph = app.state.construction_graph
            
            # 合并配置
            processing_config = config or {}
            processing_config.update({
                "enable_cache": enable_cache,
                "timeout_seconds": timeout_seconds
            })
            
            # 处理文档
            document = await graph.process_document(temp_path, processing_config)
            
            # 生成可视化
            visualization = graph.visualize()
            
            # 构建响应
            response = ProcessResponse(
                success=document.metadata.get("status") == "completed",
                request_id=request_id,
                file_hash=document.file_hash,
                processing_time=document.metadata.get("processing_time", 0),
                extracted_data=document.structured_data,
                confidence_scores=document.confidence_scores,
                warnings=document.metadata.get("warnings", []),
                error=document.metadata.get("error"),
                graph_visualization=visualization
            )
            
            logger.info(f"处理完成: {request_id}, 耗时: {response.processing_time:.2f}s")
            
            return response
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        logger.error(f"{request_id}: {error_msg}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.post("/api/v1/process/batch", response_model=BatchProcessResponse)
async def process_batch(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks
):
    """批量处理文档"""
    request_id = f"batch_{int(time.time() * 1000)}"
    start_time = time.time()
    
    logger.info(f"收到批量处理请求: {request_id}, 文件数: {len(request.file_paths)}")
    
    try:
        results = []
        successful = 0
        
        # 顺序处理
        for file_path in request.file_paths:
            try:
                # 使用图处理
                graph = app.state.construction_graph
                
                # 合并配置
                processing_config = request.config or {}
                processing_config.update({
                    "enable_cache": request.enable_cache,
                    "timeout_seconds": request.timeout_seconds
                })
                
                # 处理文档
                document = await graph.process_document(file_path, processing_config)
                
                results.append({
                    "file_path": file_path,
                    "success": document.metadata.get("status") == "completed",
                    "processing_time": document.metadata.get("processing_time", 0),
                    "extracted_data": document.structured_data,
                    "confidence_scores": document.confidence_scores,
                    "error": document.metadata.get("error")
                })
                
                if document.metadata.get("status") == "completed":
                    successful += 1
                    
            except Exception as e:
                logger.error(f"文件处理失败 {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        # 构建响应
        response = BatchProcessResponse(
            success=successful == len(request.file_paths),
            request_id=request_id,
            total_files=len(request.file_paths),
            successful_files=successful,
            processing_time=time.time() - start_time,
            results=results
        )
        
        logger.info(f"批量处理完成: {request_id}, 成功: {successful}/{len(request.file_paths)}")
        
        return response
    
    except Exception as e:
        error_msg = f"批量处理失败: {str(e)}"
        logger.error(f"{request_id}: {error_msg}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/api/v1/visualize")
async def visualize_graph():
    """可视化处理图"""
    try:
        graph = app.state.construction_graph
        mermaid_code = graph.visualize()
        
        return {
            "mermaid": mermaid_code,
            "html": f'<div class="mermaid">{mermaid_code}</div>'
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"图可视化失败: {str(e)}"
        )

@app.get("/api/v1/status")
async def get_status():
    """获取服务状态"""
    try:
        graph = app.state.construction_graph
        orchestrator = app.state.orchestrator
        
        return {
            "graph": {
                "initialized": graph.compiled_graph is not None,
                "node_count": len(graph.graph.nodes) if graph.graph else 0
            },
            "orchestrator": {
                "agents": orchestrator.get_agent_status() if hasattr(orchestrator, 'get_agent_status') else {},
                "initialized": hasattr(orchestrator, 'agents')
            },
            "memory": {
                "graph_memory": graph.graph.memory if hasattr(graph.graph, 'memory') else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"状态获取失败: {str(e)}"
        )

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "施工记录AI服务 (LangGraph)",
        "version": "1.0.0",
        "endpoints": {
            "process": "/api/v1/process",
            "batch_process": "/api/v1/process/batch",
            "visualize": "/api/v1/visualize",
            "status": "/api/v1/status",
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs"
        }
    }

# 运行应用
if __name__ == "__main__":
    uvicorn.run(
        "src.app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.server.log_level.lower()
    )