#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3단계 승인 시스템 직접 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pre_analysis_service import pre_analysis_service
from approval_workflow import approval_workflow_manager

def test_full_workflow():
    """전체 워크플로우 테스트"""

    print("=== 3단계 승인 시스템 테스트 ===\n")

    # 1단계: 사전 분석
    print("1. 사전 분석 단계")
    user_request = "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램을 생성해주세요. 개인정보는 정확하게 추출하고, 누락된 데이터는 비워두세요."

    analysis_result = pre_analysis_service.analyze_user_request(
        user_request=user_request,
        framework="crewai",
        model="gemini-flash"
    )

    if analysis_result.get('status') == 'error':
        print(f"FAIL 사전 분석 실패: {analysis_result.get('error')}")
        return

    print("OK 사전 분석 완료")
    print(f"   - 분석 ID: {analysis_result.get('analysis_id')}")
    print(f"   - 프로젝트 요약: {analysis_result.get('analysis', {}).get('project_summary', 'N/A')}")
    print(f"   - 에이전트 수: {len(analysis_result.get('analysis', {}).get('agents', []))}")

    # 디버깅용 출력
    analysis_data = analysis_result.get('analysis', {})
    if 'agents' in analysis_data:
        print(f"   - 에이전트 목록:")
        for agent in analysis_data['agents']:
            print(f"     * {agent.get('role', 'Unknown')}: {agent.get('expertise', 'N/A')}")
    else:
        print(f"   - 분석 데이터 키들: {list(analysis_data.keys())}")
    print()

    # 2단계: 승인 요청 생성
    print("2. 승인 요청 생성")
    approval_id = approval_workflow_manager.create_approval_request(
        analysis_result=analysis_result,
        project_id="test-project-001",
        requester="test_user"
    )

    print(f"OK 승인 요청 생성 완료")
    print(f"   - 승인 ID: {approval_id}")
    print()

    # 승인 요청 조회
    print("3. 승인 요청 조회")
    approval_request = approval_workflow_manager.get_approval_request(approval_id)

    if approval_request:
        print("OK 승인 요청 조회 성공")
        print(f"   - 상태: {approval_request.get('status')}")
        print(f"   - 생성시간: {approval_request.get('created_at')}")
        print(f"   - 예상완료시간: {approval_request.get('metadata', {}).get('estimated_completion_time')}")
    else:
        print("FAIL 승인 요청 조회 실패")
        return
    print()

    # 4단계: 승인 처리 (자동 승인)
    print("4. 승인 처리")
    approval_response = approval_workflow_manager.process_approval_response(
        approval_id=approval_id,
        action="approve",
        feedback="테스트 자동 승인"
    )

    if approval_response.get('success'):
        print("OK 승인 처리 완료")
        print(f"   - 상태: {approval_response.get('status')}")
        print(f"   - 메시지: {approval_response.get('message')}")
        print(f"   - 다음 단계: {approval_response.get('next_steps', [])}")
    else:
        print(f"FAIL 승인 처리 실패: {approval_response.get('error')}")
    print()

    # 5단계: 대기 중인 승인 목록 확인
    print("5. 대기 중인 승인 목록 확인")
    pending_approvals = approval_workflow_manager.get_pending_approvals()
    print(f"   - 대기 중인 승인 수: {len(pending_approvals)}")

    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_full_workflow()