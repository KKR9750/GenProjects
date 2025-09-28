#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 상태 관리 시스템
- 요구사항 보존
- 진행 상태 추적
- 중단/재개 지원
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

class ProjectStatus(Enum):
    """프로젝트 상태 열거형"""
    CREATED = "created"
    PLANNING = "planning"
    PLANNER_APPROVAL_PENDING = "planner_approval_pending"
    RESEARCHING = "researching"
    WRITING = "writing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"

class AgentStatus(Enum):
    """에이전트 상태 열거형"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    APPROVAL_PENDING = "approval_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ERROR = "error"

class ProjectStateManager:
    """프로젝트 상태 관리 클래스"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.requirements_file = os.path.join(project_path, "original_requirements.json")
        self.status_file = os.path.join(project_path, "project_status.json")
        self.execution_log_file = os.path.join(project_path, "execution_log.json")

        # 디렉토리가 없으면 생성
        os.makedirs(project_path, exist_ok=True)

    def save_original_requirements(self, requirements: str, additional_info: Dict[str, Any] = None):
        """원본 요구사항 저장"""
        requirements_data = {
            "original_request": requirements,
            "created_at": datetime.now().isoformat(),
            "project_id": os.path.basename(self.project_path),
            "additional_info": additional_info or {}
        }

        with open(self.requirements_file, 'w', encoding='utf-8') as f:
            json.dump(requirements_data, f, ensure_ascii=False, indent=2)

        return requirements_data

    def load_original_requirements(self) -> Optional[Dict[str, Any]]:
        """원본 요구사항 로드"""
        try:
            if os.path.exists(self.requirements_file):
                with open(self.requirements_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"요구사항 로드 실패: {e}")
        return None

    def initialize_project_status(self, project_name: str, description: str = ""):
        """프로젝트 상태 초기화"""
        status_data = {
            "project_id": os.path.basename(self.project_path),
            "project_name": project_name,
            "description": description,
            "status": ProjectStatus.CREATED.value,
            "progress_percentage": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "agents": {
                "planner": {
                    "status": AgentStatus.PENDING.value,
                    "progress": 0,
                    "result_file": None,
                    "started_at": None,
                    "completed_at": None
                },
                "researcher": {
                    "status": AgentStatus.PENDING.value,
                    "progress": 0,
                    "result_file": None,
                    "started_at": None,
                    "completed_at": None
                },
                "writer": {
                    "status": AgentStatus.PENDING.value,
                    "progress": 0,
                    "result_file": None,
                    "started_at": None,
                    "completed_at": None
                }
            },
            "current_step": "planning",
            "can_resume": False,
            "resume_point": None,
            "execution_id": str(uuid.uuid4())
        }

        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        # 실행 로그 초기화
        self.log_execution_event("project_initialized", {
            "project_name": project_name,
            "description": description
        })

        return status_data

    def update_project_status(self, status: ProjectStatus, progress: int = None):
        """프로젝트 전체 상태 업데이트"""
        status_data = self.load_project_status()
        if not status_data:
            return False

        status_data["status"] = status.value
        status_data["updated_at"] = datetime.now().isoformat()

        if progress is not None:
            status_data["progress_percentage"] = progress

        # 특정 상태에서 재개 가능 설정
        if status.value in ["planner_approval_pending", "researching", "writing", "reviewing"]:
            status_data["can_resume"] = True
            status_data["resume_point"] = status.value

        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        return True

    def update_agent_status(self, agent_name: str, status: AgentStatus,
                          progress: int = None, result_file: str = None):
        """개별 에이전트 상태 업데이트"""
        status_data = self.load_project_status()
        if not status_data or agent_name not in status_data["agents"]:
            return False

        agent_data = status_data["agents"][agent_name]
        agent_data["status"] = status.value

        if progress is not None:
            agent_data["progress"] = progress

        if result_file:
            agent_data["result_file"] = result_file

        # 시작/완료 시간 기록
        if status == AgentStatus.RUNNING and not agent_data["started_at"]:
            agent_data["started_at"] = datetime.now().isoformat()
        elif status in [AgentStatus.COMPLETED, AgentStatus.APPROVAL_PENDING]:
            agent_data["completed_at"] = datetime.now().isoformat()

        status_data["updated_at"] = datetime.now().isoformat()

        # 전체 진행률 계산
        total_progress = sum(agent["progress"] for agent in status_data["agents"].values()) // 3
        status_data["progress_percentage"] = total_progress

        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        return True

    def load_project_status(self) -> Optional[Dict[str, Any]]:
        """프로젝트 상태 로드"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"프로젝트 상태 로드 실패: {e}")
        return None

    def log_execution_event(self, event_type: str, data: Dict[str, Any]):
        """실행 로그 기록"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }

        # 기존 로그 로드
        execution_log = []
        try:
            if os.path.exists(self.execution_log_file):
                with open(self.execution_log_file, 'r', encoding='utf-8') as f:
                    execution_log = json.load(f)
        except:
            execution_log = []

        # 새 로그 추가
        execution_log.append(log_entry)

        # 로그 저장 (최대 1000개 유지)
        execution_log = execution_log[-1000:]

        with open(self.execution_log_file, 'w', encoding='utf-8') as f:
            json.dump(execution_log, f, ensure_ascii=False, indent=2)

    def can_resume(self) -> bool:
        """재개 가능 여부 확인"""
        status_data = self.load_project_status()
        return status_data and status_data.get("can_resume", False)

    def get_resume_point(self) -> Optional[str]:
        """재개 지점 반환"""
        status_data = self.load_project_status()
        if status_data and status_data.get("can_resume", False):
            return status_data.get("resume_point")
        return None

    def mark_approval_granted(self, agent_name: str):
        """승인 처리"""
        self.update_agent_status(agent_name, AgentStatus.APPROVED)
        self.log_execution_event("approval_granted", {"agent": agent_name})

        # 다음 단계로 진행
        if agent_name == "planner":
            self.update_project_status(ProjectStatus.RESEARCHING)
            self.update_agent_status("researcher", AgentStatus.RUNNING)

    def mark_approval_rejected(self, agent_name: str, reason: str = ""):
        """승인 거부 처리"""
        self.update_agent_status(agent_name, AgentStatus.REJECTED)
        self.log_execution_event("approval_rejected", {
            "agent": agent_name,
            "reason": reason
        })

        # 해당 단계를 다시 실행할 수 있도록 상태 변경
        if agent_name == "planner":
            self.update_project_status(ProjectStatus.PLANNING)
            self.update_agent_status("planner", AgentStatus.PENDING)

def get_project_state_manager(project_path: str) -> ProjectStateManager:
    """프로젝트 상태 관리자 인스턴스 반환"""
    return ProjectStateManager(project_path)

# 사용 예시
if __name__ == "__main__":
    # 테스트
    manager = ProjectStateManager("D:\\GenProjects\\Projects\\test_project")

    # 요구사항 저장
    manager.save_original_requirements(
        "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘.",
        {
            "additional_instructions": [
                "이력서 데이터가 누락된 경우 해당 필드는 비워두세요.",
                "이력서에 없는 정보는 유추하거나 생성하지 마세요.",
                "개인정보(이름, 이메일, 전화번호)는 정확하게 추출해야 합니다.",
                "원본 이력서 데이터를 함께 제공하지 마세요. 오직 JSON 형식의 결과만 출력하세요"
            ]
        }
    )

    # 프로젝트 상태 초기화
    manager.initialize_project_status("이력서통합", "여러 포맷의 이력서를 JSON으로 통합")

    print("프로젝트 상태 관리 시스템 테스트 완료")