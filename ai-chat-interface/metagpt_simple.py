#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple MetaGPT Bridge
간단한 MetaGPT 브릿지 - 명령어로 호출 가능
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# MetaGPT 경로 추가
sys.path.append('D:/MetaGPT')

# 환경 변수 설정 (불필요한 provider 비활성화)
os.environ['DISABLE_ARK'] = '1'
os.environ['DISABLE_DASHSCOPE'] = '1'
os.environ['DISABLE_VOLCENGINE'] = '1'
os.environ['DISABLE_QIANFAN'] = '1'
os.environ['DISABLE_AZURE'] = '1'

try:
    from metagpt.team import Team
    from metagpt.roles import ProductManager, Architect, Engineer, ProjectManager, QaEngineer
    from metagpt.logs import logger
except ImportError as e:
    print(json.dumps({"error": f"MetaGPT import failed: {str(e)}", "success": False}))
    sys.exit(1)

async def run_metagpt(requirement):
    """MetaGPT 실행"""
    try:
        # 팀 생성
        team = Team()

        # 역할들 추가
        team.hire([
            ProductManager(),
            Architect(),
            ProjectManager(),
            Engineer(),
            QaEngineer()
        ])

        # 투자 및 프로젝트 시작
        team.invest(investment=3.0)
        team.run_project(idea=requirement)

        # 실행
        await team.run(n_round=1)  # 1라운드만 실행 (빠른 응답을 위해)

        return {
            "success": True,
            "requirement": requirement,
            "message": "MetaGPT 팀이 프로젝트를 성공적으로 실행했습니다.",
            "agents": ["ProductManager", "Architect", "ProjectManager", "Engineer", "QaEngineer"],
            "process": "문서 기반 개발 프로세스 완료"
        }

    except Exception as e:
        logger.error(f"MetaGPT execution failed: {e}")
        return {
            "success": False,
            "error": f"MetaGPT 실행 실패: {str(e)}"
        }

def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "사용법: python metagpt_simple.py '요구사항'"
        }))
        return

    requirement = sys.argv[1]

    try:
        # 비동기 실행
        result = asyncio.run(run_metagpt(requirement))
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except KeyboardInterrupt:
        print(json.dumps({
            "success": False,
            "error": "사용자에 의해 중단됨"
        }))
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"예상치 못한 오류: {str(e)}"
        }))

if __name__ == "__main__":
    main()