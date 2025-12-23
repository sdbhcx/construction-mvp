# gateway_agent.py - 完整的接入与分发Agent
import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uuid
import datetime

from .common.input_recognizer import InputRecognizer
from intelligent_router import IntelligentRouter
from .common.request_standardizer import RequestStandardizer
from .common.session_manager import SessionManager
from .common.message_publisher import MessagePublisher

logger = logging.getLogger(__name__)

class GatewayAgent:
    """接入与分发Agent主类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 初始化组件
        self.recognizer = InputRecognizer()
        self.router = IntelligentRouter(config.get('routing', {}))
        self.standardizer = RequestStandardizer()
        self.session_manager = SessionManager()
        self.publisher = MessagePublisher(config.get('message_queue', {}))
        
        # 指标收集
        self.metrics = {
            'requests_received': 0,
            'requests_processed': 0,
            'errors': 0,
            'by_type': {},
            'avg_processing_time': 0
        }
        
        # 初始化FastAPI应用
        self.app = FastAPI(
            title="施工进度智能记录与查询Agent",
            description="基于多Agent架构的施工记录与查询系统MVP",
            version="1.0.0"
        )
        from fastapi.middleware.cors import CORSMiddleware
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._setup_routes()
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            """中间件：记录请求处理时间"""
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        
        @self.app.post("/api/upload")
        async def upload_endpoint(
            request: Request,
            file: UploadFile = File(...),
            description: str = Form(""),
            project_id: str = Form("project_001")
        ):
            """文件上传接口"""
            return await self.handle_upload(request, file, description, project_id)
        
        @self.app.post("/api/query")
        async def query_endpoint(request: Request):
            """查询接口"""
            return await self.handle_query(request)
    
    async def handle_upload(self, request: Request, file: UploadFile, 
                           description: str, project_id: str):
        """处理上传请求"""
        try:
            # 1. 记录指标
            self.metrics['requests_received'] += 1
            self.metrics['by_type']['upload'] = self.metrics['by_type'].get('upload', 0) + 1
            
            # 2. 识别请求类型
            recognition_result = await self.recognizer.recognize_async(request)
            
            # 3. 获取或创建会话
            session = self.session_manager.get_or_create_session(request)
            
            # 4. 构建上下文
            context = {
                'project_id': project_id,
                'user_id': session.get('user_id'),
                'user_role': session.get('user_role'),
                'session_id': session['session_id']
            }
            
            # 5. 路由决策
            routing_instruction = self.router.route_request(
                recognition_result, context
            )
            
            # 6. 标准化请求
            standardized_message = await self.standardizer.standardize(
                request, recognition_result
            )
            
            # 7. 添加上下文到消息
            standardized_message['context'].update(context)
            
            # 8. 发布到消息队列
            success = await self.publisher.publish_async(
                queue_name=routing_instruction['target_queue'],
                message=standardized_message,
                priority=routing_instruction['priority']
            )
            
            if success:
                # 9. 更新会话
                self.session_manager.update_context(
                    session['session_id'], 
                    'last_upload', 
                    standardized_message['message_id']
                )
                
                # 10. 立即响应（异步处理模式）
                response = {
                    "status": "accepted",
                    "message_id": standardized_message['message_id'],
                    "estimated_time": "30秒",
                    "check_status_url": f"/api/status/{standardized_message['message_id']}"
                }
                
                self.metrics['requests_processed'] += 1
                return JSONResponse(response)
            else:
                return JSONResponse(
                    {"error": "消息队列不可用"},
                    status_code=503
                )
                
        except Exception as e:
            logger.error(f"处理上传请求失败: {e}")
            self.metrics['errors'] += 1
            return JSONResponse(
                {"error": "内部服务器错误", "details": str(e)},
                status_code=500
            )
    
    async def handle_query(self, request: Request):
        """处理查询请求"""
        try:
            # 解析JSON请求体
            body = await request.json()
            question = body.get('question', '').strip()
            
            if not question:
                return JSONResponse(
                    {"error": "问题不能为空"},
                    status_code=400
                )
            
            # 识别为文本请求
            recognition_result = {
                'type': 'text',
                'content': question,
                'confidence': 1.0
            }
            
            # 获取会话
            session = self.session_manager.get_or_create_session(request)
            
            # 构建上下文
            context = {
                'session_id': session['session_id'],
                'query_type': 'natural_language',
                'user_id': session.get('user_id')
            }
            
            # 路由到查询处理队列
            routing_instruction = self.router.route_request(
                recognition_result, context
            )
            
            # 标准化消息
            standardized_message = await self.standardizer.standardize(
                request, recognition_result
            )
            standardized_message['context'].update(context)
            
            # 发布消息
            success = await self.publisher.publish_async(
                queue_name=routing_instruction['target_queue'],
                message=standardized_message,
                priority=9  # 查询请求优先级较高
            )
            
            if success:
                # 对于查询请求，可以等待结果（同步模式）或返回任务ID（异步模式）
                # 这里采用异步模式，立即返回
                response = {
                    "status": "processing",
                    "message_id": standardized_message['message_id'],
                    "estimated_time": "3秒"
                }
                return JSONResponse(response)
            else:
                return JSONResponse(
                    {"error": "系统繁忙，请稍后重试"},
                    status_code=503
                )
                
        except json.JSONDecodeError:
            return JSONResponse(
                {"error": "无效的JSON格式"},
                status_code=400
            )
        except Exception as e:
            logger.error(f"处理查询请求失败: {e}")
            return JSONResponse(
                {"error": "内部服务器错误"},
                status_code=500
            )
    
    async def handle_batch(self, request: Request):
        """处理批量请求"""
        try:
            # 解析批量请求
            batch_request = await request.json()
            operations = batch_request.get('operations', [])
            
            if not operations or len(operations) > 10:  # 限制批量操作数量
                return JSONResponse(
                    {"error": "批量操作数量必须在1-10之间"},
                    status_code=400
                )
            
            # 处理每个操作
            results = []
            for operation in operations:
                try:
                    # 模拟处理每个操作（实际应分发到不同队列）
                    op_result = await self._process_batch_operation(operation)
                    results.append(op_result)
                except Exception as e:
                    results.append({
                        "status": "error",
                        "operation": operation.get('type'),
                        "error": str(e)
                    })
            
            return JSONResponse({
                "batch_id": str(uuid.uuid4()),
                "results": results,
                "total": len(results),
                "successful": sum(1 for r in results if r['status'] == 'success')
            })
            
        except Exception as e:
            logger.error(f"处理批量请求失败: {e}")
            return JSONResponse(
                {"error": "处理批量请求失败"},
                status_code=500
            )
    
    async def _process_batch_operation(self, operation):
        """处理单个批量操作"""
        # 根据操作类型分发
        op_type = operation.get('type')
        
        if op_type == 'upload':
            # 模拟上传处理
            return {
                "status": "success",
                "operation": "upload",
                "message_id": str(uuid.uuid4())
            }
        elif op_type == 'query':
            # 模拟查询处理
            return {
                "status": "success",
                "operation": "query",
                "answer": "模拟回答"
            }
        else:
            raise ValueError(f"未知操作类型: {op_type}")
    
    def start(self, host="0.0.0.0", port=8000):
        """启动网关服务"""
        import uvicorn
        
        logger.info(f"启动网关Agent，监听 {host}:{port}")
        
        # 启动FastAPI应用
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
    
    async def _collect_metrics_periodically(self):
        """定期收集和清理指标"""
        while True:
            await asyncio.sleep(300)  # 每5分钟
            
            # 清理旧会话
            self._cleanup_old_sessions()
            
            # 保存指标快照
            self._save_metrics_snapshot()
    
    def _cleanup_old_sessions(self):
        """清理过期的会话"""
        current_time = datetime.datetime.now()
        expired_sessions = []
        
        for session_id, session in self.session_manager.sessions.items():
            last_activity = session['last_activity']
            if (current_time - last_activity).total_seconds() > 3600:  # 1小时无活动
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_manager.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
    
    def _save_metrics_snapshot(self):
        """保存指标快照"""
        snapshot = {
            'timestamp': datetime.datetime.now().isoformat(),
            'metrics': self.metrics.copy(),
            'active_sessions': len(self.session_manager.sessions)
        }
        
        # 这里可以保存到文件或数据库
        # 暂时只记录日志
        logger.info(f"指标快照: {json.dumps(snapshot, indent=2)}")

# 配置示例
CONFIG = {
    "name": "gateway_agent",
    "version": "1.0.0",
    "message_queue": {
        "type": "memory",  # redis, rabbitmq, kafka
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "routing": {
        "default_queue": "default_processing",
        "queues": {
            "file_processing": ["file_parser_agent_1", "file_parser_agent_2"],
            "speech_processing": ["speech_agent"],
            "query_processing": ["query_agent"],
            "coordinator": ["coordinator_agent"]
        }
    },
    "limits": {
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "max_requests_per_minute": 100,
        "max_concurrent_requests": 50
    }
}

if __name__ == "__main__":
    # 初始化网关Agent
    gateway = GatewayAgent(CONFIG)
    
    # 启动服务
    gateway.start(host="0.0.0.0", port=8000)
