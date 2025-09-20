#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MetaGPT Bridge for Web Interface with Real-time Progress Tracking
웹 인터페이스와 MetaGPT를 연결하는 브릿지 스크립트 (실시간 진행 상황 추적 포함)
"""

import sys
import os
import json
import asyncio
import uuid
from pathlib import Path
from datetime import datetime
import threading
import time

# MetaGPT 경로 추가 (상대 경로로 수정)
current_dir = os.path.dirname(os.path.abspath(__file__))
metagpt_path = os.path.join(os.path.dirname(current_dir), 'MetaGPT')
sys.path.append(metagpt_path)

try:
    from metagpt.software_company import SoftwareCompany
    from metagpt.roles import ProductManager, Architect, ProjectManager, Engineer, QaEngineer
    from metagpt.logs import logger
    from metagpt.schema import Message
except ImportError as e:
    print(json.dumps({"error": f"MetaGPT import failed: {str(e)}"}))
    sys.exit(1)

# 실시간 진행 상황 추적기 import
try:
    from realtime_progress_tracker import MetaGPTProgressHelper, global_progress_tracker
except ImportError:
    print("Warning: 실시간 진행 상황 추적기를 사용할 수 없습니다.")
    MetaGPTProgressHelper = None
    global_progress_tracker = None

class MetaGPTBridgeWithProgress:
    def __init__(self):
        self.company = None
        self.project_id = None
        self.progress_tracker = MetaGPTProgressHelper
        self.current_stage = 0
        self.total_stages = 5
        self.stage_names = [
            "Product Manager Analysis",
            "Architecture Design",
            "Project Planning",
            "Code Development",
            "Quality Assurance"
        ]

    def set_project_id(self, project_id: str):
        """프로젝트 ID 설정"""
        self.project_id = project_id
        if self.progress_tracker:
            self.progress_tracker.start_project(project_id)

    def track_progress(self, stage: str, role: str, progress: int, message: str = ""):
        """진행 상황 추적"""
        if self.progress_tracker and self.project_id:
            if role == "Product Manager":
                self.progress_tracker.update_pm_progress(self.project_id, progress, message)
            elif role == "Architect":
                self.progress_tracker.update_architect_progress(self.project_id, progress, message)
            elif role == "Engineer":
                self.progress_tracker.update_engineer_progress(self.project_id, progress, message)
            elif role == "QA Engineer":
                self.progress_tracker.update_qa_progress(self.project_id, progress, message)

        # 콘솔 로그도 출력
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {role}: {message} ({progress}%)")

    def complete_stage(self, stage: str, deliverables: list = None):
        """단계 완료 처리"""
        if self.progress_tracker and self.project_id:
            global_progress_tracker.complete_stage(self.project_id, stage, deliverables)

    def report_error(self, error_type: str, error_message: str, stage: str = "", role: str = ""):
        """오류 보고"""
        if self.progress_tracker and self.project_id:
            global_progress_tracker.report_error(self.project_id, error_type, error_message, stage, role)

    async def initialize_company(self, requirement):
        """MetaGPT 회사 초기화"""
        try:
            self.track_progress("초기화", "System", 10, "MetaGPT 회사 초기화 중...")

            self.company = SoftwareCompany()

            # 역할들을 추가
            self.company.hire([
                ProductManager(),
                Architect(),
                ProjectManager(),
                Engineer(),
                QaEngineer()
            ])

            self.track_progress("초기화", "System", 100, "MetaGPT 회사 초기화 완료")
            return True
        except Exception as e:
            self.report_error("initialization_error", f"Company initialization failed: {e}")
            logger.error(f"Company initialization failed: {e}")
            return False

    async def process_requirement(self, requirement, selected_models=None):
        """요구사항 처리"""
        try:
            # 회사 초기화
            if not await self.initialize_company(requirement):
                return {"error": "Failed to initialize MetaGPT company"}

            # 요구사항을 회사에 투입
            self.company.invest(investment=3.0)
            self.company.start_project(requirement)

            # 실행
            result = await self.company.run(n_round=3)  # 3라운드 실행

            # 결과 포맷팅
            return {
                "success": True,
                "requirement": requirement,
                "result": str(result),
                "models_used": selected_models or {},
                "agents_involved": [
                    "ProductManager",
                    "Architect",
                    "ProjectManager",
                    "Engineer",
                    "QaEngineer"
                ]
            }

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return {"error": f"MetaGPT processing failed: {str(e)}"}

async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python metagpt_bridge.py 'requirement' [models_json]"}))
        return

    requirement = sys.argv[1]
    selected_models = {}

    if len(sys.argv) >= 3:
        try:
            selected_models = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            pass

    bridge = MetaGPTBridge()
    result = await bridge.process_requirement(requirement, selected_models)

    # JSON으로 결과 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    # 이벤트 루프 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(json.dumps({"error": "Process interrupted"}))
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}))