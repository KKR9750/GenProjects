# -*- coding: utf-8 -*-
"""
CrewAI Enhanced Logging System
CrewAI 프로그램 생성 및 실행 로직 강화된 로깅 시스템
"""

import logging
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ExecutionPhase(Enum):
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    PREPARATION = "preparation"
    DIRECTORY_CREATION = "directory_creation"
    FILE_GENERATION = "file_generation"
    ENVIRONMENT_SETUP = "environment_setup"
    API_REQUEST = "api_request"
    SUBPROCESS_LAUNCH = "subprocess_launch"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    OUTPUT_PROCESSING = "output_processing"
    RESULT_VALIDATION = "result_validation"
    COMPLETION = "completion"
    ERROR_HANDLING = "error_handling"

@dataclass
class LogEntry:
    timestamp: str
    execution_id: str
    crew_id: str
    phase: ExecutionPhase
    level: LogLevel
    message: str
    details: Dict[str, Any] = None
    duration_ms: Optional[int] = None
    memory_usage: Optional[int] = None

    def to_dict(self):
        return asdict(self)

class CrewAILogger:
    """CrewAI 전용 강화된 로깅 시스템"""

    def __init__(self):
        self.setup_logger()
        self.execution_logs: Dict[str, List[LogEntry]] = {}
        self.phase_timers: Dict[str, Dict[ExecutionPhase, float]] = {}
        self.step_counters: Dict[str, int] = {}  # 실행별 단계 카운터
        self.current_steps: Dict[str, str] = {}  # 현재 진행 중인 단계
        self.websocket_manager = None

    def setup_logger(self):
        """로거 초기 설정"""
        # 로그 디렉토리 생성
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # 파일 핸들러 설정
        log_file = os.path.join(log_dir, f'crewai_{datetime.now().strftime("%Y%m%d")}.log')

        # 포매터 설정
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # 콘솔 핸들러 (UTF-8 인코딩 명시적 설정)
        import sys
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Windows 환경에서 UTF-8 출력 보장
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except:
                pass

        # 로거 설정
        self.logger = logging.getLogger('CrewAI')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # 중복 로그 방지
        self.logger.propagate = False

    def set_websocket_manager(self, websocket_manager):
        """WebSocket 매니저 설정"""
        self.websocket_manager = websocket_manager

    def start_execution_logging(self, execution_id: str, crew_id: str, inputs: Dict[str, Any]):
        """실행 로깅 시작"""
        self.execution_logs[execution_id] = []
        self.phase_timers[execution_id] = {}

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.INITIALIZATION,
            level=LogLevel.INFO,
            message=f"CrewAI 실행 시작 - execution_id: {execution_id}",
            details={
                "crew_id": crew_id,
                "inputs": inputs,
                "start_time": datetime.now().isoformat()
            }
        )

    def start_phase(self, execution_id: str, crew_id: str, phase: ExecutionPhase):
        """단계 시작 로깅"""
        self.phase_timers[execution_id][phase] = time.time()

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=phase,
            level=LogLevel.INFO,
            message=f"단계 시작: {phase.value}",
            details={"phase_start_time": datetime.now().isoformat()}
        )

    def end_phase(self, execution_id: str, crew_id: str, phase: ExecutionPhase, success: bool = True, details: Dict[str, Any] = None):
        """단계 완료 로깅"""
        start_time = self.phase_timers[execution_id].get(phase)
        duration_ms = int((time.time() - start_time) * 1000) if start_time else None

        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "완료" if success else "실패"

        log_details = {
            "phase_end_time": datetime.now().isoformat(),
            "success": success,
            "duration_ms": duration_ms
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=phase,
            level=level,
            message=f"단계 {status}: {phase.value} ({duration_ms}ms)",
            details=log_details,
            duration_ms=duration_ms
        )

    def log_validation(self, execution_id: str, crew_id: str, validation_type: str, result: bool, details: Dict[str, Any] = None):
        """검증 로깅"""
        level = LogLevel.INFO if result else LogLevel.WARNING
        status = "성공" if result else "실패"

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.VALIDATION,
            level=level,
            message=f"{validation_type} 검증 {status}",
            details=details or {}
        )

    def log_file_operation(self, execution_id: str, crew_id: str, operation: str, file_path: str, success: bool, details: Dict[str, Any] = None):
        """파일 작업 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "operation": operation,
            "file_path": file_path,
            "file_exists": os.path.exists(file_path) if file_path else False
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.PREPARATION,
            level=level,
            message=f"파일 작업 {status}: {operation} - {file_path}",
            details=log_details
        )

    def log_subprocess_start(self, execution_id: str, crew_id: str, script_path: str, env_vars: Dict[str, str]):
        """서브프로세스 시작 로깅"""
        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.EXECUTION,
            level=LogLevel.INFO,
            message=f"CrewAI 스크립트 실행 시작: {script_path}",
            details={
                "script_path": script_path,
                "environment_variables": {k: v for k, v in env_vars.items() if 'CREWAI_' in k},
                "python_executable": "python -u"
            }
        )

    def log_subprocess_output(self, execution_id: str, crew_id: str, output_type: str, content: str):
        """서브프로세스 출력 로깅"""
        level = LogLevel.INFO if output_type == "stdout" else LogLevel.WARNING

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.MONITORING,
            level=level,
            message=f"프로그램 출력 ({output_type}): {content[:100]}{'...' if len(content) > 100 else ''}",
            details={
                "output_type": output_type,
                "full_content": content,
                "content_length": len(content)
            }
        )

    def log_crewai_role_execution(self, execution_id: str, crew_id: str, role: str, status: str, details: Dict[str, Any] = None):
        """CrewAI 역할별 실행 로깅 (올바른 순서: Planner → Researcher → Writer)"""
        role_order = {"Planner": 1, "Researcher": 2, "Writer": 3}
        role_icons = {"Planner": "📋", "Researcher": "🔍", "Writer": "✍️"}

        log_details = {
            "role": role,
            "role_order": role_order.get(role, 0),
            "role_icon": role_icons.get(role, "🤖"),
            "status": status,
            "workflow_position": f"{role_order.get(role, 0)}/3",
            **(details or {})
        }

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.EXECUTION,
            level=LogLevel.INFO,
            message=f"{role_icons.get(role, '🤖')} {role} {status} (단계 {role_order.get(role, 0)}/3)",
            details=log_details
        )

    def log_progress_update(self, execution_id: str, crew_id: str, progress: int, message: str, details: Dict[str, Any] = None):
        """진행 상황 업데이트 로깅"""
        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.MONITORING,
            level=LogLevel.INFO,
            message=f"진행률 {progress}%: {message}",
            details={
                "progress_percentage": progress,
                "status_message": message,
                **(details or {})
            }
        )

    def log_error(self, execution_id: str, crew_id: str, error: Exception, context: str = "", details: Dict[str, Any] = None):
        """에러 로깅"""
        import traceback

        log_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.ERROR_HANDLING,
            level=LogLevel.ERROR,
            message=f"오류 발생: {type(error).__name__} - {str(error)}",
            details=log_details
        )

    def log_directory_operation(self, execution_id: str, crew_id: str, operation: str, path: str, success: bool, details: Dict[str, Any] = None):
        """디렉토리 작업 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "operation": operation,
            "directory_path": path,
            "absolute_path": os.path.abspath(path) if path else None,
            "exists_before": os.path.exists(path) if path else False,
            "exists_after": os.path.exists(path) if path and success else False,
            "parent_directory": os.path.dirname(path) if path else None
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.DIRECTORY_CREATION,
            level=level,
            message=f"📁 디렉토리 작업 {status}: {operation} - {path}",
            details=log_details
        )

    def log_api_request(self, execution_id: str, crew_id: str, api_name: str, endpoint: str, method: str, success: bool, details: Dict[str, Any] = None):
        """API 요청 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "api_name": api_name,
            "endpoint": endpoint,
            "http_method": method,
            "request_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.API_REQUEST,
            level=level,
            message=f"🌐 API 요청 {status}: {api_name} {method} {endpoint}",
            details=log_details
        )

    def log_environment_setup(self, execution_id: str, crew_id: str, env_vars: Dict[str, str], success: bool, details: Dict[str, Any] = None):
        """환경 변수 설정 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        # 민감한 정보 마스킹
        safe_env_vars = {}
        for key, value in env_vars.items():
            if 'KEY' in key.upper() or 'TOKEN' in key.upper() or 'PASSWORD' in key.upper():
                safe_env_vars[key] = '***MASKED***'
            else:
                safe_env_vars[key] = value

        log_details = {
            "environment_variables": safe_env_vars,
            "variable_count": len(env_vars),
            "setup_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.ENVIRONMENT_SETUP,
            level=level,
            message=f"⚙️ 환경 설정 {status}: {len(env_vars)}개 변수 설정",
            details=log_details
        )

    def log_project_initialization(self, execution_id: str, crew_id: str, project_name: str, project_path: str, template_type: str, success: bool, details: Dict[str, Any] = None):
        """프로젝트 초기화 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "project_name": project_name,
            "project_path": project_path,
            "template_type": template_type,
            "absolute_path": os.path.abspath(project_path) if project_path else None,
            "directory_created": os.path.exists(project_path) if project_path else False,
            "initialization_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.INITIALIZATION,
            level=level,
            message=f"🚀 프로젝트 초기화 {status}: {project_name} ({template_type})",
            details=log_details
        )

    def log_file_generation(self, execution_id: str, crew_id: str, file_path: str, file_type: str, content_length: int, success: bool, details: Dict[str, Any] = None):
        """파일 생성 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "file_path": file_path,
            "file_type": file_type,
            "content_length": content_length,
            "file_exists": os.path.exists(file_path) if file_path else False,
            "file_size_bytes": os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0,
            "generation_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.FILE_GENERATION,
            level=level,
            message=f"📄 파일 생성 {status}: {os.path.basename(file_path) if file_path else 'Unknown'} ({content_length} chars)",
            details=log_details
        )

    def log_subprocess_execution(self, execution_id: str, crew_id: str, command: str, working_dir: str, success: bool, exit_code: int = None, details: Dict[str, Any] = None):
        """서브프로세스 실행 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "command": command,
            "working_directory": working_dir,
            "exit_code": exit_code,
            "execution_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.SUBPROCESS_LAUNCH,
            level=level,
            message=f"⚡ 서브프로세스 실행 {status}: {command[:50]}... (exit: {exit_code})",
            details=log_details
        )

    def log_output_processing(self, execution_id: str, crew_id: str, output_type: str, content: str, processed_lines: int, success: bool, details: Dict[str, Any] = None):
        """출력 처리 상세 로깅"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        status = "완료" if success else "실패"

        log_details = {
            "output_type": output_type,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "total_content_length": len(content),
            "processed_lines": processed_lines,
            "processing_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.OUTPUT_PROCESSING,
            level=level,
            message=f"📥 출력 처리 {status}: {output_type} ({processed_lines} lines, {len(content)} chars)",
            details=log_details
        )

    def log_detailed_step(self, execution_id: str, crew_id: str, step_name: str, step_description: str, phase: ExecutionPhase, success: bool = True, details: Dict[str, Any] = None):
        """세부 단계 로깅 (일반적인 진행 상황 추적용)"""
        level = LogLevel.INFO if success else LogLevel.WARNING
        status = "진행중" if success else "문제발생"

        log_details = {
            "step_name": step_name,
            "step_description": step_description,
            "step_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=phase,
            level=level,
            message=f"🔄 단계 {status}: {step_name} - {step_description}",
            details=log_details
        )

    def log_korean_encoding_test(self, execution_id: str, crew_id: str, test_string: str, encoding_type: str, success: bool, details: Dict[str, Any] = None):
        """한글 인코딩 테스트 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        log_details = {
            "test_string": test_string,
            "encoding_type": encoding_type,
            "string_length": len(test_string),
            "byte_length": len(test_string.encode('utf-8')),
            "test_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.VALIDATION,
            level=level,
            message=f"🔤 한글 인코딩 테스트 {status}: {encoding_type} - '{test_string[:30]}...'",
            details=log_details
        )

    def log_completion(self, execution_id: str, crew_id: str, success: bool, total_duration: int, final_details: Dict[str, Any] = None):
        """실행 완료 로깅"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "성공" if success else "실패"

        # 단계별 소요 시간 계산
        phase_durations = {}
        for phase, start_time in self.phase_timers.get(execution_id, {}).items():
            # 완료된 단계만 계산 (현재 시간 기준)
            phase_durations[phase.value] = int((time.time() - start_time) * 1000)

        log_details = {
            "final_status": status,
            "total_duration_ms": total_duration,
            "phase_durations": phase_durations,
            "total_log_entries": len(self.execution_logs.get(execution_id, [])),
            "completion_time": datetime.now().isoformat()
        }

        if final_details:
            log_details.update(final_details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.COMPLETION,
            level=level,
            message=f"🏁 CrewAI 실행 {status} - 총 소요시간: {total_duration}ms (단계: {self.step_counters.get(execution_id, 0)}개 완료)",
            details=log_details,
            duration_ms=total_duration
        )

        # 실행 완료 후 추적 데이터 정리
        self.cleanup_execution_tracking(execution_id)

    def log(self, execution_id: str, crew_id: str, phase: ExecutionPhase, level: LogLevel,
            message: str, details: Dict[str, Any] = None, duration_ms: Optional[int] = None):
        """통합 로깅 메서드"""

        # 메모리 사용량 측정 (선택적)
        memory_usage = None
        try:
            import psutil
            process = psutil.Process()
            memory_usage = process.memory_info().rss // 1024 // 1024  # MB
        except:
            pass

        # 로그 엔트리 생성
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            execution_id=execution_id,
            crew_id=crew_id,
            phase=phase,
            level=level,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
            memory_usage=memory_usage
        )

        # 실행별 로그 저장
        if execution_id not in self.execution_logs:
            self.execution_logs[execution_id] = []
        self.execution_logs[execution_id].append(log_entry)

        # 파일 로깅
        log_message = f"[{execution_id[:8]}] [{crew_id}] [{phase.value}] {message}"
        if details:
            log_message += f" | Details: {json.dumps(details, ensure_ascii=False)}"

        getattr(self.logger, level.value.lower())(log_message)

        # WebSocket으로 실시간 전송
        if self.websocket_manager:
            try:
                self.websocket_manager.broadcast_to_room(
                    room=f"execution_{execution_id}",
                    event="log_update",
                    data=log_entry.to_dict()
                )
            except Exception as e:
                self.logger.warning(f"WebSocket 로그 전송 실패: {e}")

    def get_execution_logs(self, execution_id: str) -> List[Dict[str, Any]]:
        """특정 실행의 모든 로그 조회"""
        logs = self.execution_logs.get(execution_id, [])
        return [log.to_dict() for log in logs]

    def get_execution_summary(self, execution_id: str) -> Dict[str, Any]:
        """실행 요약 정보"""
        logs = self.execution_logs.get(execution_id, [])
        if not logs:
            return {}

        phases = {}
        for log in logs:
            phase = log.phase.value
            if phase not in phases:
                phases[phase] = {"count": 0, "errors": 0, "warnings": 0}
            phases[phase]["count"] += 1
            if log.level == LogLevel.ERROR:
                phases[phase]["errors"] += 1
            elif log.level == LogLevel.WARNING:
                phases[phase]["warnings"] += 1

        return {
            "execution_id": execution_id,
            "total_logs": len(logs),
            "start_time": logs[0].timestamp if logs else None,
            "end_time": logs[-1].timestamp if logs else None,
            "phases": phases,
            "has_errors": any(log.level == LogLevel.ERROR for log in logs),
            "has_warnings": any(log.level == LogLevel.WARNING for log in logs)
        }

    def cleanup_old_logs(self, max_executions: int = 100):
        """오래된 로그 정리"""
        if len(self.execution_logs) > max_executions:
            # 가장 오래된 실행 로그부터 삭제
            sorted_executions = sorted(
                self.execution_logs.keys(),
                key=lambda x: self.execution_logs[x][0].timestamp if self.execution_logs[x] else ""
            )

            for execution_id in sorted_executions[:-max_executions]:
                del self.execution_logs[execution_id]
                if execution_id in self.phase_timers:
                    del self.phase_timers[execution_id]

    def start_step_tracking(self, execution_id: str, crew_id: str, total_steps: int = None):
        """단계별 추적 시작"""
        self.step_counters[execution_id] = 0
        self.current_steps[execution_id] = "시작"

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.INITIALIZATION,
            level=LogLevel.INFO,
            message=f"📊 단계별 추적 시작 - 총 {total_steps or '미정'} 단계 예정",
            details={
                "total_estimated_steps": total_steps,
                "tracking_start_time": datetime.now().isoformat()
            }
        )

    def advance_step(self, execution_id: str, crew_id: str, step_name: str, step_description: str = "", phase: ExecutionPhase = ExecutionPhase.EXECUTION):
        """다음 단계로 진행"""
        if execution_id not in self.step_counters:
            self.step_counters[execution_id] = 0

        self.step_counters[execution_id] += 1
        self.current_steps[execution_id] = step_name

        step_number = self.step_counters[execution_id]

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=phase,
            level=LogLevel.INFO,
            message=f"➡️ 단계 {step_number}: {step_name} {step_description}",
            details={
                "step_number": step_number,
                "step_name": step_name,
                "step_description": step_description,
                "previous_step": self.current_steps.get(execution_id, "없음"),
                "step_time": datetime.now().isoformat()
            }
        )

    def log_system_check(self, execution_id: str, crew_id: str, check_name: str, result: bool, details: Dict[str, Any] = None):
        """시스템 상태 체크 로깅"""
        level = LogLevel.INFO if result else LogLevel.WARNING
        status = "정상" if result else "문제"
        icon = "✅" if result else "⚠️"

        log_details = {
            "check_name": check_name,
            "check_result": result,
            "check_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.VALIDATION,
            level=level,
            message=f"{icon} 시스템 체크 {status}: {check_name}",
            details=log_details
        )

    def log_realtime_status(self, execution_id: str, crew_id: str, status_message: str, progress_percent: int = None, details: Dict[str, Any] = None):
        """실시간 상태 업데이트 로깅 (WebSocket 우선)"""
        current_step = self.current_steps.get(execution_id, "알 수 없음")
        step_number = self.step_counters.get(execution_id, 0)

        log_details = {
            "status_message": status_message,
            "progress_percent": progress_percent,
            "current_step": current_step,
            "step_number": step_number,
            "realtime_update": True,
            "update_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        # 진행률 표시 포맷
        progress_display = f" ({progress_percent}%)" if progress_percent is not None else ""

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.MONITORING,
            level=LogLevel.INFO,
            message=f"🔄 실시간 상태: {status_message}{progress_display} [단계 {step_number}: {current_step}]",
            details=log_details
        )

    def log_websocket_status(self, execution_id: str, crew_id: str, connected: bool, room_name: str = None, details: Dict[str, Any] = None):
        """WebSocket 연결 상태 로깅"""
        level = LogLevel.INFO if connected else LogLevel.WARNING
        status = "연결됨" if connected else "연결 끊김"
        icon = "🔗" if connected else "🔌"

        log_details = {
            "websocket_connected": connected,
            "room_name": room_name or f"execution_{execution_id}",
            "connection_time": datetime.now().isoformat()
        }

        if details:
            log_details.update(details)

        self.log(
            execution_id=execution_id,
            crew_id=crew_id,
            phase=ExecutionPhase.MONITORING,
            level=level,
            message=f"{icon} WebSocket {status}: {room_name or f'execution_{execution_id}'}",
            details=log_details
        )

    def cleanup_execution_tracking(self, execution_id: str):
        """실행 완료 후 추적 데이터 정리"""
        if execution_id in self.step_counters:
            del self.step_counters[execution_id]
        if execution_id in self.current_steps:
            del self.current_steps[execution_id]

# 글로벌 로거 인스턴스
crewai_logger = CrewAILogger()