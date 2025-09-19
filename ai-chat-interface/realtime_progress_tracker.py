# -*- coding: utf-8 -*-
"""
Real-time Progress Tracker for AI Agents
AI 에이전트 실시간 진행 상황 추적기
"""

import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import json
from websocket_manager import get_websocket_manager

@dataclass
class ProgressUpdate:
    """진행 상황 업데이트 구조체"""
    project_id: str
    stage: str
    role: str
    progress: int  # 0-100
    message: str
    details: Dict[str, Any] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}

class RealtimeProgressTracker:
    """실시간 AI 진행 상황 추적기"""

    def __init__(self):
        self.active_projects = {}  # project_id -> ProjectProgress
        self.progress_callbacks = []  # List of callback functions
        self.websocket_manager = None
        self._lock = threading.Lock()

    def set_websocket_manager(self, manager):
        """WebSocket 매니저 설정"""
        self.websocket_manager = manager

    def start_project_tracking(self, project_id: str, total_stages: int, stage_names: List[str]):
        """프로젝트 추적 시작"""
        with self._lock:
            self.active_projects[project_id] = {
                'total_stages': total_stages,
                'stage_names': stage_names,
                'current_stage_index': 0,
                'stage_progress': {},  # stage_name -> progress
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'status': 'running',
                'messages': []
            }

        # WebSocket을 통해 프로젝트 시작 알림
        if self.websocket_manager:
            self.websocket_manager.broadcast_project_update(
                project_id,
                'project_started',
                {
                    'total_stages': total_stages,
                    'stage_names': stage_names,
                    'start_time': datetime.now().isoformat()
                }
            )

    def update_progress(self, project_id: str, stage: str, role: str, progress: int,
                       message: str = "", details: Dict[str, Any] = None):
        """진행 상황 업데이트"""
        update = ProgressUpdate(
            project_id=project_id,
            stage=stage,
            role=role,
            progress=progress,
            message=message,
            details=details or {}
        )

        with self._lock:
            if project_id in self.active_projects:
                project = self.active_projects[project_id]
                project['stage_progress'][stage] = progress
                project['last_update'] = datetime.now()
                project['messages'].append({
                    'timestamp': update.timestamp,
                    'stage': stage,
                    'role': role,
                    'message': message,
                    'progress': progress
                })

                # 최근 10개 메시지만 유지
                if len(project['messages']) > 10:
                    project['messages'] = project['messages'][-10:]

        # WebSocket을 통해 실시간 업데이트
        if self.websocket_manager:
            self.websocket_manager.broadcast_project_update(
                project_id,
                'progress_update',
                asdict(update)
            )

        # 등록된 콜백 함수들 호출
        for callback in self.progress_callbacks:
            try:
                callback(update)
            except Exception as e:
                print(f"Progress callback error: {e}")

    def complete_stage(self, project_id: str, stage: str, deliverables: List[Dict] = None):
        """단계 완료 처리"""
        with self._lock:
            if project_id in self.active_projects:
                project = self.active_projects[project_id]
                project['stage_progress'][stage] = 100

                # 다음 단계로 이동
                if stage in project['stage_names']:
                    current_index = project['stage_names'].index(stage)
                    if current_index < len(project['stage_names']) - 1:
                        project['current_stage_index'] = current_index + 1
                    else:
                        # 모든 단계 완료
                        project['status'] = 'completed'

        # WebSocket을 통해 단계 완료 알림
        if self.websocket_manager:
            self.websocket_manager.broadcast_project_update(
                project_id,
                'stage_completed',
                {
                    'stage': stage,
                    'deliverables': deliverables or [],
                    'timestamp': datetime.now().isoformat()
                }
            )

    def report_error(self, project_id: str, error_type: str, error_message: str,
                    stage: str = "", role: str = ""):
        """오류 보고"""
        with self._lock:
            if project_id in self.active_projects:
                project = self.active_projects[project_id]
                project['status'] = 'error'
                project['error'] = {
                    'type': error_type,
                    'message': error_message,
                    'stage': stage,
                    'role': role,
                    'timestamp': datetime.now().isoformat()
                }

        # WebSocket을 통해 오류 알림
        if self.websocket_manager:
            self.websocket_manager.broadcast_project_update(
                project_id,
                'error_occurred',
                {
                    'error_type': error_type,
                    'message': error_message,
                    'stage': stage,
                    'role': role,
                    'timestamp': datetime.now().isoformat()
                }
            )

    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """프로젝트 현재 상태 조회"""
        with self._lock:
            if project_id not in self.active_projects:
                return None

            project = self.active_projects[project_id]

            # 전체 진행률 계산
            total_progress = 0
            completed_stages = 0
            for stage_name in project['stage_names']:
                stage_progress = project['stage_progress'].get(stage_name, 0)
                total_progress += stage_progress
                if stage_progress == 100:
                    completed_stages += 1

            overall_progress = total_progress / len(project['stage_names']) if project['stage_names'] else 0

            return {
                'project_id': project_id,
                'status': project['status'],
                'overall_progress': round(overall_progress, 1),
                'completed_stages': completed_stages,
                'total_stages': project['total_stages'],
                'current_stage': project['stage_names'][project['current_stage_index']]
                               if project['current_stage_index'] < len(project['stage_names']) else None,
                'stage_progress': project['stage_progress'],
                'start_time': project['start_time'].isoformat(),
                'last_update': project['last_update'].isoformat(),
                'recent_messages': project['messages'][-5:],  # 최근 5개 메시지
                'error': project.get('error')
            }

    def add_progress_callback(self, callback: Callable[[ProgressUpdate], None]):
        """진행 상황 콜백 함수 추가"""
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: Callable[[ProgressUpdate], None]):
        """진행 상황 콜백 함수 제거"""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)

    def stop_project_tracking(self, project_id: str):
        """프로젝트 추적 중지"""
        with self._lock:
            if project_id in self.active_projects:
                del self.active_projects[project_id]

        # WebSocket을 통해 추적 중지 알림
        if self.websocket_manager:
            self.websocket_manager.broadcast_project_update(
                project_id,
                'tracking_stopped',
                {'timestamp': datetime.now().isoformat()}
            )

# 전역 진행 상황 추적기 인스턴스
global_progress_tracker = RealtimeProgressTracker()

# AI 프레임워크별 진행 상황 추적 헬퍼 클래스들
class MetaGPTProgressHelper:
    """MetaGPT 진행 상황 추적 헬퍼"""

    @staticmethod
    def start_project(project_id: str):
        """MetaGPT 프로젝트 시작"""
        stage_names = [
            "Product Manager Analysis",
            "Architecture Design",
            "Project Planning",
            "Code Development",
            "Quality Assurance"
        ]
        global_progress_tracker.start_project_tracking(project_id, 5, stage_names)

    @staticmethod
    def update_pm_progress(project_id: str, progress: int, message: str = ""):
        """Product Manager 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Product Manager Analysis", "Product Manager",
            progress, message
        )

    @staticmethod
    def update_architect_progress(project_id: str, progress: int, message: str = ""):
        """Architect 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Architecture Design", "Architect",
            progress, message
        )

    @staticmethod
    def update_engineer_progress(project_id: str, progress: int, message: str = ""):
        """Engineer 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Code Development", "Engineer",
            progress, message
        )

    @staticmethod
    def update_qa_progress(project_id: str, progress: int, message: str = ""):
        """QA Engineer 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Quality Assurance", "QA Engineer",
            progress, message
        )

class CrewAIProgressHelper:
    """CrewAI 진행 상황 추적 헬퍼"""

    @staticmethod
    def start_project(project_id: str):
        """CrewAI 프로젝트 시작"""
        stage_names = [
            "Research Phase",
            "Writing Phase",
            "Planning Phase"
        ]
        global_progress_tracker.start_project_tracking(project_id, 3, stage_names)

    @staticmethod
    def update_researcher_progress(project_id: str, progress: int, message: str = ""):
        """Researcher 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Research Phase", "Researcher",
            progress, message
        )

    @staticmethod
    def update_writer_progress(project_id: str, progress: int, message: str = ""):
        """Writer 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Writing Phase", "Writer",
            progress, message
        )

    @staticmethod
    def update_planner_progress(project_id: str, progress: int, message: str = ""):
        """Planner 진행 상황"""
        global_progress_tracker.update_progress(
            project_id, "Planning Phase", "Planner",
            progress, message
        )