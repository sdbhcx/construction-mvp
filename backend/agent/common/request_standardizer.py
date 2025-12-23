# request_standardizer.py - 请求标准化组件
import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

class RequestStandardizer:
    """请求标准化组件，将不同类型的请求转换为统一格式"""
    
    def __init__(self):
        self.message_counter = 0
    
    async def standardize(self, request: Request, recognition_result: Dict[str, Any]) -> Dict[str, Any]:
        """标准化请求，转换为统一格式"""
        try:
            # 基本请求信息
            request_info = {
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers),
                'client_ip': self._get_client_ip(request),
                'user_agent': self._get_user_agent(request)
            }
            
            # 生成唯一消息ID
            message_id = str(uuid.uuid4())
            
            # 根据请求类型标准化内容
            request_type = recognition_result['type']
            standardized_content = await self._standardize_content(request, request_type)
            
            # 构建标准化消息
            standardized_message = {
                'message_id': message_id,
                'timestamp': datetime.now().isoformat(),
                'request_info': request_info,
                'recognition_result': recognition_result,
                'content': standardized_content,
                'context': {
                    'request_id': self._generate_request_id(),
                    'trace_id': self._get_trace_id(request),
                    'processing_stage': 'standardized'
                }
            }
            
            logger.info(f"标准化请求: {message_id} - {request_type}")
            return standardized_message
            
        except Exception as e:
            logger.error(f"标准化请求失败: {e}")
            # 即使出错，也返回基本标准化消息
            return {
                'message_id': str(uuid.uuid4()),
                'timestamp': datetime.now().isoformat(),
                'request_info': {
                    'method': request.method if hasattr(request, 'method') else 'unknown',
                    'path': request.url.path if hasattr(request, 'url') else 'unknown'
                },
                'recognition_result': recognition_result,
                'content': {'error': str(e)},
                'context': {
                    'request_id': self._generate_request_id(),
                    'processing_stage': 'error'
                }
            }
    
    async def _standardize_content(self, request: Request, request_type: str) -> Dict[str, Any]:
        """根据请求类型标准化内容"""
        try:
            if request_type == 'upload':
                return await self._standardize_upload_request(request)
            elif request_type == 'query':
                return await self._standardize_query_request(request)
            elif request_type == 'batch':
                return await self._standardize_batch_request(request)
            elif request_type == 'status_check':
                return await self._standardize_status_request(request)
            else:
                # 默认情况，尝试从请求体获取内容
                try:
                    return await request.json()
                except Exception:
                    try:
                        return dict(await request.form())
                    except Exception:
                        return {'raw': '无法解析请求内容'}
        except Exception as e:
            logger.error(f"标准化请求内容失败: {e}")
            return {'error': str(e)}
    
    async def _standardize_upload_request(self, request: Request) -> Dict[str, Any]:
        """标准化上传请求"""
        form_data = await request.form()
        
        # 提取文件信息
        file = form_data.get('file')
        file_info = {
            'filename': file.filename if file else None,
            'content_type': file.content_type if file else None,
            'size': len(await file.read()) if file else 0
        }
        
        # 重置文件指针
        if file:
            await file.seek(0)
        
        return {
            'file_info': file_info,
            'description': form_data.get('description', ''),
            'project_id': form_data.get('project_id', 'default'),
            'metadata': {
                'upload_time': datetime.now().isoformat()
            }
        }
    
    async def _standardize_query_request(self, request: Request) -> Dict[str, Any]:
        """标准化查询请求"""
        body = await request.json()
        return {
            'question': body.get('question', ''),
            'query_type': body.get('query_type', 'natural_language'),
            'context': body.get('context', {}),
            'expected_format': body.get('expected_format', 'json')
        }
    
    async def _standardize_batch_request(self, request: Request) -> Dict[str, Any]:
        """标准化批量请求"""
        body = await request.json()
        return {
            'operations': body.get('operations', []),
            'batch_id': body.get('batch_id', str(uuid.uuid4())),
            'max_concurrent': body.get('max_concurrent', 5),
            'timeout': body.get('timeout', 300)
        }
    
    async def _standardize_status_request(self, request: Request) -> Dict[str, Any]:
        """标准化状态查询请求"""
        path = request.url.path
        message_id = path.split('/')[-1] if path else ''
        return {
            'message_id': message_id,
            'requested_fields': request.query_params.getlist('fields', ['status', 'progress', 'result'])
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        try:
            # 尝试从X-Forwarded-For头获取（如果有代理）
            x_forwarded_for = request.headers.get('X-Forwarded-For')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0].strip()
            # 直接获取客户端IP
            client = request.client
            if client and client.host:
                return client.host
        except Exception:
            pass
        return 'unknown'
    
    def _get_user_agent(self, request: Request) -> str:
        """获取用户代理"""
        try:
            return request.headers.get('User-Agent', 'unknown')
        except Exception:
            return 'unknown'
    
    def _get_trace_id(self, request: Request) -> str:
        """获取跟踪ID"""
        try:
            # 尝试从各种跟踪头获取
            trace_headers = ['X-Trace-ID', 'Trace-ID', 'X-Request-ID']
            for header in trace_headers:
                if header in request.headers:
                    return request.headers[header]
        except Exception:
            pass
        # 生成新的跟踪ID
        return str(uuid.uuid4())
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        self.message_counter += 1
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"req_{timestamp}_{self.message_counter:06d}"
