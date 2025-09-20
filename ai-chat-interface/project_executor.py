# -*- coding: utf-8 -*-
"""
Project Executor
생성된 프로젝트 자동 실행 시스템
"""

import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from project_initializer import project_initializer
from realtime_progress_tracker import global_progress_tracker
from websocket_manager import get_websocket_manager

class ExecutionStatus(Enum):
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExecutionResult:
    project_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    output: List[str] = None
    error: Optional[str] = None
    deliverables: List[Dict[str, Any]] = None

class ProjectExecutor:
    """프로젝트 자동 실행 및 관리 시스템"""

    def __init__(self):
        self.executions = {}  # project_id -> ExecutionResult
        self.running_processes = {}  # project_id -> subprocess.Popen
        self.execution_threads = {}  # project_id -> Thread

        # 실행 환경 설정
        self.crewai_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'CrewAi')
        self.metagpt_base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MetaGPT')

    def execute_project(self, project_id: str, auto_start: bool = True) -> Dict[str, Any]:
        """프로젝트 실행 시작"""
        try:
            # 프로젝트 상태 조회
            project_status = project_initializer.get_project_status(project_id)
            if not project_status:
                raise ValueError(f"프로젝트를 찾을 수 없습니다: {project_id}")

            # 실행 결과 초기화
            execution_result = ExecutionResult(
                project_id=project_id,
                status=ExecutionStatus.PENDING,
                start_time=datetime.now(),
                output=[],
                deliverables=[]
            )
            self.executions[project_id] = execution_result

            # 실시간 진행 상황 추적 시작
            framework = project_status['framework']
            if framework == 'crew_ai':
                stages = ['Research', 'Planning', 'Writing']
            else:  # meta_gpt
                stages = ['Product Manager', 'Architect', 'Engineer', 'QA Engineer', 'Review']

            global_progress_tracker.start_project_tracking(
                project_id, len(stages), stages
            )

            # 백그라운드에서 실행
            if auto_start:
                execution_thread = threading.Thread(
                    target=self._execute_project_background,
                    args=(project_id, project_status),
                    daemon=True
                )
                execution_thread.start()
                self.execution_threads[project_id] = execution_thread

            return {
                'success': True,
                'project_id': project_id,
                'status': execution_result.status.value,
                'message': '프로젝트 실행이 시작되었습니다'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_project_background(self, project_id: str, project_status: Dict[str, Any]):
        """백그라운드에서 프로젝트 실행"""
        execution_result = self.executions[project_id]

        try:
            execution_result.status = ExecutionStatus.STARTING
            self._broadcast_status_update(project_id, execution_result)

            framework = project_status['framework']

            if framework == 'crew_ai':
                self._execute_crewai_project(project_id, project_status)
            elif framework == 'meta_gpt':
                self._execute_metagpt_project(project_id, project_status)
            else:
                raise ValueError(f"지원하지 않는 프레임워크: {framework}")

            execution_result.status = ExecutionStatus.COMPLETED
            execution_result.end_time = datetime.now()

        except Exception as e:
            execution_result.status = ExecutionStatus.FAILED
            execution_result.error = str(e)
            execution_result.end_time = datetime.now()

        finally:
            global_progress_tracker.complete_project(project_id)
            self._broadcast_status_update(project_id, execution_result)

    def _execute_crewai_project(self, project_id: str, project_status: Dict[str, Any]):
        """CrewAI 프로젝트 실행"""
        execution_result = self.executions[project_id]
        execution_result.status = ExecutionStatus.RUNNING

        # CrewAI 실행 시뮬레이션 (실제 구현에서는 CrewAI API 호출)
        stages = ['Research', 'Planning', 'Writing']

        for i, stage in enumerate(stages):
            self._log_output(project_id, f"=== {stage} 단계 시작 ===")

            # 단계별 진행 상황 업데이트
            for progress in range(0, 101, 20):
                global_progress_tracker.update_progress(
                    project_id, stage, 'AI Agent', progress,
                    f"{stage} 작업 진행 중... {progress}%"
                )
                time.sleep(0.5)  # 실제로는 AI 작업 시간

            # 단계 완료 및 산출물 생성
            deliverable = {
                'stage': stage,
                'type': stage.lower().replace(' ', '_'),
                'title': f"{stage} 결과물",
                'content': f"{stage} 단계에서 생성된 결과물입니다.",
                'created_at': datetime.now().isoformat()
            }

            execution_result.deliverables.append(deliverable)
            global_progress_tracker.complete_stage(project_id, stage, [deliverable])

            self._log_output(project_id, f"=== {stage} 단계 완료 ===")

    def _execute_metagpt_project(self, project_id: str, project_status: Dict[str, Any]):
        """MetaGPT 프로젝트 실행"""
        execution_result = self.executions[project_id]
        execution_result.status = ExecutionStatus.RUNNING

        # MetaGPT 실행 시뮬레이션
        stages = ['Product Manager', 'Architect', 'Engineer', 'QA Engineer', 'Review']

        for i, stage in enumerate(stages):
            self._log_output(project_id, f"=== {stage} 역할 시작 ===")

            # LLM 매핑 정보 가져오기
            llm_model = self._get_llm_for_role(project_status, stage)

            # 단계별 진행 상황 업데이트
            for progress in range(0, 101, 25):
                global_progress_tracker.update_progress(
                    project_id, stage, llm_model, progress,
                    f"{stage}가 {llm_model}로 작업 중... {progress}%"
                )
                time.sleep(0.8)  # 실제로는 LLM 처리 시간

            # 단계 완료 및 산출물 생성
            deliverable = {
                'stage': stage,
                'type': self._get_deliverable_type(stage),
                'title': f"{stage} 산출물",
                'content': f"{stage}가 {llm_model}를 사용하여 생성한 결과물입니다.",
                'llm_model': llm_model,
                'created_at': datetime.now().isoformat()
            }

            execution_result.deliverables.append(deliverable)
            global_progress_tracker.complete_stage(project_id, stage, [deliverable])

            self._log_output(project_id, f"=== {stage} 역할 완료 ===")

    def _get_llm_for_role(self, project_status: Dict[str, Any], role: str) -> str:
        """역할별 LLM 모델 조회"""
        llm_mappings = project_status.get('llm_mappings', [])
        for mapping in llm_mappings:
            if mapping['role'] == role:
                return mapping['llm_model']
        return 'gpt-4'  # 기본값

    def _get_deliverable_type(self, stage: str) -> str:
        """단계별 산출물 타입 반환"""
        deliverable_types = {
            'Product Manager': 'prd_document',
            'Architect': 'system_design',
            'Engineer': 'source_code',
            'QA Engineer': 'test_plan',
            'Review': 'final_report'
        }
        return deliverable_types.get(stage, 'document')

    def _log_output(self, project_id: str, message: str):
        """실행 로그 기록"""
        if project_id in self.executions:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}"
            self.executions[project_id].output.append(log_message)
            print(log_message)  # 콘솔 출력

    def _broadcast_status_update(self, project_id: str, execution_result: ExecutionResult):
        """WebSocket으로 상태 업데이트 브로드캐스트"""
        try:
            ws_manager = get_websocket_manager()
            if ws_manager:
                update_data = {
                    'type': 'execution_status_update',
                    'project_id': project_id,
                    'status': execution_result.status.value,
                    'progress': len(execution_result.deliverables),
                    'timestamp': datetime.now().isoformat()
                }
                ws_manager.emit_to_room(f'project_{project_id}', 'project_update', update_data)
        except Exception as e:
            print(f"WebSocket 브로드캐스트 오류: {e}")

    def get_execution_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """프로젝트 실행 상태 조회"""
        if project_id not in self.executions:
            return None

        execution_result = self.executions[project_id]
        return {
            'project_id': project_id,
            'status': execution_result.status.value,
            'start_time': execution_result.start_time.isoformat(),
            'end_time': execution_result.end_time.isoformat() if execution_result.end_time else None,
            'output': execution_result.output[-10:] if execution_result.output else [],  # 최근 10개
            'error': execution_result.error,
            'deliverables_count': len(execution_result.deliverables),
            'deliverables': execution_result.deliverables
        }

    def cancel_execution(self, project_id: str) -> Dict[str, Any]:
        """프로젝트 실행 취소"""
        try:
            if project_id in self.executions:
                execution_result = self.executions[project_id]

                if execution_result.status in [ExecutionStatus.PENDING, ExecutionStatus.STARTING, ExecutionStatus.RUNNING]:
                    execution_result.status = ExecutionStatus.CANCELLED
                    execution_result.end_time = datetime.now()

                    # 실행 중인 프로세스 종료
                    if project_id in self.running_processes:
                        process = self.running_processes[project_id]
                        process.terminate()
                        del self.running_processes[project_id]

                    # 진행 상황 추적 종료
                    global_progress_tracker.cancel_project(project_id)

                    self._broadcast_status_update(project_id, execution_result)

                    return {
                        'success': True,
                        'message': '프로젝트 실행이 취소되었습니다'
                    }
                else:
                    return {
                        'success': False,
                        'message': '취소할 수 없는 상태입니다'
                    }
            else:
                return {
                    'success': False,
                    'message': '실행 중인 프로젝트를 찾을 수 없습니다'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def list_executions(self) -> List[Dict[str, Any]]:
        """모든 실행 상태 목록 조회"""
        executions = []
        for project_id, execution_result in self.executions.items():
            executions.append({
                'project_id': project_id,
                'status': execution_result.status.value,
                'start_time': execution_result.start_time.isoformat(),
                'end_time': execution_result.end_time.isoformat() if execution_result.end_time else None,
                'deliverables_count': len(execution_result.deliverables),
                'has_error': execution_result.error is not None
            })

        return sorted(executions, key=lambda x: x['start_time'], reverse=True)

    def cleanup_completed_executions(self, older_than_hours: int = 24):
        """완료된 실행 결과 정리"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)

        to_remove = []
        for project_id, execution_result in self.executions.items():
            if (execution_result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
                and execution_result.end_time
                and execution_result.end_time.timestamp() < cutoff_time):
                to_remove.append(project_id)

        for project_id in to_remove:
            del self.executions[project_id]
            if project_id in self.execution_threads:
                del self.execution_threads[project_id]

        return len(to_remove)

# 글로벌 인스턴스
project_executor = ProjectExecutor()