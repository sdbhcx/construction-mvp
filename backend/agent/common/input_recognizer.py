# input_recognizer.py - 请求类型识别组件
import logging
from typing import Dict, Any, Optional
from fastapi import Request

logger = logging.getLogger(__name__)

class InputRecognizer:
    """识别请求类型的组件"""
    
    def __init__(self):
        self.supported_types = [
            'upload',          # 文件上传（图片、PDF等）
            'query',           # 自然语言查询
            'batch',           # 批量操作
            'status_check',    # 状态查询
            'system_command'   # 系统命令
        ]
    
    async def recognize_async(self, request: Request) -> Dict[str, Any]:
        """异步识别请求类型"""
        try:
            # 获取请求方法和路径
            method = request.method
            path = request.url.path
            
            # 根据路径判断请求类型
            if path.endswith('/upload') and method == 'POST':
                return self._create_recognition_result('upload', confidence=0.95)
            elif path.endswith('/query') and method == 'POST':
                return self._create_recognition_result('query', confidence=0.95)
            elif path.endswith('/batch') and method == 'POST':
                return self._create_recognition_result('batch', confidence=0.95)
            elif path.startswith('/status/') and method == 'GET':
                return self._create_recognition_result('status_check', confidence=0.95)
            elif path.startswith('/system/'):
                return self._create_recognition_result('system_command', confidence=0.9)
            else:
                # 默认情况，尝试从请求体识别
                try:
                    body = await request.json()
                    if 'question' in body:
                        return self._create_recognition_result('query', confidence=0.9)
                    elif 'operations' in body:
                        return self._create_recognition_result('batch', confidence=0.9)
                except Exception:
                    pass
                
                # 最后尝试从表单数据识别
                try:
                    form = await request.form()
                    if 'file' in form:
                        return self._create_recognition_result('upload', confidence=0.85)
                except Exception:
                    pass
            
            # 无法识别的请求类型
            logger.warning(f"无法识别请求类型: {method} {path}")
            return self._create_recognition_result('unknown', confidence=0.1)
            
        except Exception as e:
            logger.error(f"识别请求类型失败: {e}")
            return self._create_recognition_result('error', confidence=0.0)
    
    def recognize_sync(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步识别请求类型（用于测试或批量处理）"""
        try:
            if 'file' in request_data:
                return self._create_recognition_result('upload', confidence=0.9)
            elif 'question' in request_data:
                return self._create_recognition_result('query', confidence=0.9)
            elif 'operations' in request_data:
                return self._create_recognition_result('batch', confidence=0.9)
            elif 'status_id' in request_data:
                return self._create_recognition_result('status_check', confidence=0.9)
            elif 'command' in request_data:
                return self._create_recognition_result('system_command', confidence=0.9)
            else:
                return self._create_recognition_result('unknown', confidence=0.1)
        except Exception as e:
            logger.error(f"同步识别请求类型失败: {e}")
            return self._create_recognition_result('error', confidence=0.0)
    
    def _create_recognition_result(self, request_type: str, confidence: float) -> Dict[str, Any]:
        """创建识别结果"""
        return {
            'type': request_type,
            'confidence': confidence,
            'supported': request_type in self.supported_types,
            'timestamp': self._get_current_timestamp()
        }
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
