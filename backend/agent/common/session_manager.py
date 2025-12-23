# session_manager.py - 会话管理组件
import logging
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

class SessionManager:
    """会话管理组件，用于管理用户会话和上下文"""
    
    def __init__(self):
        # 存储所有会话
        self.sessions: Dict[str, Dict[str, Any]] = {}
        # 会话超时时间（秒）
        self.session_timeout = 3600  # 1小时
    
    def get_or_create_session(self, request: Request) -> Dict[str, Any]:
        """获取或创建会话"""
        try:
            # 尝试从cookie获取会话ID
            session_id = self._get_session_id_from_cookie(request)
            
            # 如果会话存在且未过期，更新最后活动时间并返回
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                if not self._is_session_expired(session):
                    self._update_session_activity(session_id)
                    logger.info(f"使用现有会话: {session_id}")
                    return session
            
            # 创建新会话
            new_session = self._create_new_session(request)
            logger.info(f"创建新会话: {new_session['session_id']}")
            return new_session
            
        except Exception as e:
            logger.error(f"获取或创建会话失败: {e}")
            # 即使出错，也返回新会话
            return self._create_new_session(request)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """根据会话ID获取会话"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if not self._is_session_expired(session):
                    self._update_session_activity(session_id)
                    return session
                else:
                    # 会话已过期，删除
                    del self.sessions[session_id]
                    logger.info(f"删除过期会话: {session_id}")
            return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def update_context(self, session_id: str, key: str, value: Any):
        """更新会话上下文"""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                # 更新上下文
                if 'context' not in session:
                    session['context'] = {}
                session['context'][key] = value
                # 更新最后活动时间
                self._update_session_activity(session_id)
                logger.debug(f"更新会话上下文: {session_id} - {key} = {value}")
        except Exception as e:
            logger.error(f"更新会话上下文失败: {e}")
    
    def remove_session(self, session_id: str):
        """删除会话"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"删除会话: {session_id}")
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
    
    def _create_new_session(self, request: Request) -> Dict[str, Any]:
        """创建新会话"""
        # 生成唯一会话ID
        session_id = str(uuid.uuid4())
        
        # 从请求中提取用户信息（模拟）
        user_info = self._extract_user_info(request)
        
        # 创建会话对象
        session = {
            'session_id': session_id,
            'user_id': user_info.get('user_id', 'anonymous'),
            'user_role': user_info.get('user_role', 'guest'),
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'context': {},
            'ip_address': self._get_client_ip(request),
            'user_agent': self._get_user_agent(request)
        }
        
        # 存储会话
        self.sessions[session_id] = session
        return session
    
    def _update_session_activity(self, session_id: str):
        """更新会话最后活动时间"""
        if session_id in self.sessions:
            self.sessions[session_id]['last_activity'] = datetime.now()
    
    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """检查会话是否过期"""
        last_activity = session['last_activity']
        current_time = datetime.now()
        return (current_time - last_activity).total_seconds() > self.session_timeout
    
    def _get_session_id_from_cookie(self, request: Request) -> Optional[str]:
        """从cookie获取会话ID"""
        try:
            if hasattr(request, 'cookies'):
                return request.cookies.get('session_id')
        except Exception:
            pass
        return None
    
    def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """从请求中提取用户信息（模拟实现）"""
        # 在实际应用中，这应该从认证系统获取
        try:
            # 尝试从请求头获取用户信息（示例）
            if 'X-User-ID' in request.headers:
                return {
                    'user_id': request.headers.get('X-User-ID', 'anonymous'),
                    'user_role': request.headers.get('X-User-Role', 'guest')
                }
        except Exception:
            pass
        
        # 默认匿名用户
        return {
            'user_id': 'anonymous',
            'user_role': 'guest'
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        try:
            x_forwarded_for = request.headers.get('X-Forwarded-For')
            if x_forwarded_for:
                return x_forwarded_for.split(',')[0].strip()
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
            pass
        return 'unknown'
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        # 清理过期会话
        self._cleanup_expired_sessions()
        return len(self.sessions)
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        # 删除过期会话
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
