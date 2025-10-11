#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 매니저 - 실시간 알림 기능
프로젝트 완성 알림 및 실시간 상태 업데이트
"""

from flask_socketio import SocketIO, emit
from typing import Optional
import json
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.socketio: Optional[SocketIO] = None
        self.connected_clients = set()

    def init_socketio(self, socketio: SocketIO):
        """SocketIO 인스턴스 초기화"""
        self.socketio = socketio
        self._register_events()

    def _register_events(self):
        """WebSocket 이벤트 등록"""
        if not self.socketio:
            return

        @self.socketio.on('connect')
        def handle_connect():
            print(f"🔗 클라이언트 연결됨")
            self.connected_clients.add(request.sid if 'request' in globals() else 'unknown')

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"🔌 클라이언트 연결 해제됨")
            if 'request' in globals():
                self.connected_clients.discard(request.sid)

    def emit_project_completion(self, project_id: str, project_name: str, result_path: str):
        """프로젝트 완성 알림 전송"""
        if not self.socketio:
            print("⚠️ SocketIO가 초기화되지 않음")
            return

        completion_data = {
            'type': 'project_completion',
            'project_id': project_id,
            'project_name': project_name,
            'result_path': result_path,
            'timestamp': datetime.now().isoformat(),
            'message': f"🎉 프로젝트 '{project_name}'가 성공적으로 완성되었습니다!",
            'details': {
                'completion_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'result_location': result_path
            }
        }

        try:
            self.socketio.emit('project_notification', completion_data, broadcast=True)
            print(f"✅ 프로젝트 완성 알림 전송: {project_name}")
        except Exception as e:
            print(f"❌ 알림 전송 실패: {e}")

    def emit_log_update(self, project_id: str, message: str, level: str = "info"):
        """로그 업데이트 전송"""
        if not self.socketio:
            return

        log_data = {
            'type': 'log_update',
            'project_id': project_id,
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }

        try:
            self.socketio.emit('log_message', log_data, broadcast=True)
        except Exception as e:
            print(f"❌ 로그 전송 실패: {e}")

    def emit_status_update(self, project_id: str, status: str, progress: int = 0):
        """상태 업데이트 전송"""
        if not self.socketio:
            return

        status_data = {
            'type': 'status_update',
            'project_id': project_id,
            'status': status,
            'progress': progress,
            'timestamp': datetime.now().isoformat()
        }

        try:
            self.socketio.emit('status_update', status_data, broadcast=True)
        except Exception as e:
            print(f"❌ 상태 업데이트 전송 실패: {e}")

    def emit_error_notification(self, project_id: str, error_message: str):
        """에러 알림 전송"""
        if not self.socketio:
            return

        error_data = {
            'type': 'error_notification',
            'project_id': project_id,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat()
        }

        try:
            self.socketio.emit('error_notification', error_data, broadcast=True)
            print(f"⚠️ 에러 알림 전송: {error_message}")
        except Exception as e:
            print(f"❌ 에러 알림 전송 실패: {e}")

# 전역 WebSocket 매니저 인스턴스
_websocket_manager = WebSocketManager()

def init_websocket_manager(socketio: SocketIO):
    """WebSocket 매니저 초기화"""
    global _websocket_manager
    _websocket_manager.init_socketio(socketio)
    print("✅ WebSocket 매니저 초기화 완료")

def get_websocket_manager() -> WebSocketManager:
    """WebSocket 매니저 인스턴스 반환"""
    return _websocket_manager
