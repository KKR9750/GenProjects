#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MetaGPT Bridge for Web Interface
웹 인터페이스와 MetaGPT를 연결하는 브릿지 스크립트
"""

import sys
import os
import json
import asyncio
from pathlib import Path

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

class MetaGPTBridge:
    def __init__(self):
        self.company = None

    async def initialize_company(self, requirement):
        """MetaGPT 회사 초기화"""
        try:
            self.company = SoftwareCompany()

            # 역할들을 추가
            self.company.hire([
                ProductManager(),
                Architect(),
                ProjectManager(),
                Engineer(),
                QaEngineer()
            ])

            return True
        except Exception as e:
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