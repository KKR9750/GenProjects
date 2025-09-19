# -*- coding: utf-8 -*-
"""
WebSocket Event Manager
실시간 데이터 동기화를 위한 WebSocket 이벤트 관리
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json
from typing import Dict, List, Any, Optional

class WebSocketManager:
    """WebSocket 이벤트 관리 클래스"""

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connected_clients = {}  # session_id -> client_info
        self.project_rooms = {}      # project_id -> set of session_ids
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """WebSocket 이벤트 핸들러 설정"""

        @self.socketio.on('connect')
        def handle_connect():
            """클라이언트 연결"""
            from flask import request
            session_id = request.sid

            self.connected_clients[session_id] = {
                'connected_at': datetime.now().isoformat(),
                'projects': set(),
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            }

            print(f"클라이언트 연결: {session_id}")
            emit('connection_established', {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'status': 'connected'
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """클라이언트 연결 해제"""
            from flask import request
            session_id = request.sid

            if session_id in self.connected_clients:
                # 프로젝트 룸에서 제거
                client_info = self.connected_clients[session_id]
                for project_id in client_info['projects']:
                    if project_id in self.project_rooms:
                        self.project_rooms[project_id].discard(session_id)
                        if not self.project_rooms[project_id]:
                            del self.project_rooms[project_id]

                del self.connected_clients[session_id]
                print(f"클라이언트 연결 해제: {session_id}")

        @self.socketio.on('join_project')
        def handle_join_project(data):
            """프로젝트 룸 참가"""
            from flask import request
            session_id = request.sid
            project_id = data.get('project_id')

            if not project_id:
                emit('error', {'message': 'project_id가 필요합니다'})
                return

            # 프로젝트 룸 참가
            join_room(f"project_{project_id}")

            # 클라이언트 정보 업데이트
            if session_id in self.connected_clients:
                self.connected_clients[session_id]['projects'].add(project_id)

            # 프로젝트 룸 추적
            if project_id not in self.project_rooms:
                self.project_rooms[project_id] = set()
            self.project_rooms[project_id].add(session_id)

            emit('joined_project', {
                'project_id': project_id,
                'timestamp': datetime.now().isoformat()
            })

            print(f"클라이언트 {session_id}가 프로젝트 {project_id} 룸에 참가")

        @self.socketio.on('leave_project')
        def handle_leave_project(data):
            """프로젝트 룸 나가기"""
            from flask import request
            session_id = request.sid
            project_id = data.get('project_id')

            if not project_id:
                emit('error', {'message': 'project_id가 필요합니다'})
                return

            # 프로젝트 룸 나가기
            leave_room(f"project_{project_id}")

            # 클라이언트 정보 업데이트
            if session_id in self.connected_clients:
                self.connected_clients[session_id]['projects'].discard(project_id)

            # 프로젝트 룸 추적 업데이트
            if project_id in self.project_rooms:
                self.project_rooms[project_id].discard(session_id)
                if not self.project_rooms[project_id]:
                    del self.project_rooms[project_id]

            emit('left_project', {
                'project_id': project_id,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('ping')
        def handle_ping():
            """연결 상태 확인"""
            emit('pong', {
                'timestamp': datetime.now().isoformat()
            })

    def broadcast_project_update(self, project_id: str, update_type: str, data: Dict[str, Any]):
        """프로젝트 업데이트 브로드캐스트"""
        message = {
            'type': update_type,
            'project_id': project_id,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        self.socketio.emit('project_update', message, room=f"project_{project_id}")
        print(f"프로젝트 {project_id} 업데이트 브로드캐스트: {update_type}")

    def broadcast_llm_status_update(self, llm_data: Dict[str, Any]):
        """LLM 상태 업데이트 브로드캐스트"""
        message = {
            'type': 'llm_status_update',
            'data': llm_data,
            'timestamp': datetime.now().isoformat()
        }

        self.socketio.emit('llm_status_update', message)
        print(f"LLM 상태 업데이트 브로드캐스트: {len(llm_data.get('models', []))}개 모델")

    def broadcast_system_notification(self, notification_type: str, message: str, data: Optional[Dict] = None):
        """시스템 알림 브로드캐스트"""
        notification = {
            'type': notification_type,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }

        self.socketio.emit('system_notification', notification)
        print(f"시스템 알림 브로드캐스트: {notification_type} - {message}")

    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계 정보"""
        return {
            'total_connections': len(self.connected_clients),
            'active_projects': len(self.project_rooms),
            'project_connections': {
                project_id: len(sessions)
                for project_id, sessions in self.project_rooms.items()
            },
            'timestamp': datetime.now().isoformat()
        }

    def send_to_session(self, session_id: str, event: str, data: Dict[str, Any]):
        """특정 세션에 메시지 전송"""
        if session_id in self.connected_clients:
            self.socketio.emit(event, data, room=session_id)
            return True
        return False

# 전역 WebSocket 매니저 인스턴스 (app.py에서 초기화됨)
websocket_manager = None

def init_websocket_manager(socketio: SocketIO):
    """WebSocket 매니저 초기화"""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    return websocket_manager

def get_websocket_manager() -> Optional[WebSocketManager]:
    """WebSocket 매니저 인스턴스 반환"""
    return websocket_manager