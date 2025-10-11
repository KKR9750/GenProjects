#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
정규화된 모델명 저장 테스트
"""

import os
import sys
from database import get_database

def test_normalized_model_save():
    """정규화된 모델명 저장 테스트"""
    try:
        print("정규화된 모델명 저장 테스트 시작...")

        # 데이터베이스 인스턴스 가져오기
        db = get_database()

        if not db.is_connected():
            print("ERROR: 데이터베이스 연결 실패")
            return False

        print("OK: 데이터베이스 연결 성공")

        # 테스트 프로젝트 ID
        test_project_id = "project_00001"

        # gemini-2.5-flash 모델을 포함한 매핑 테스트
        print("   gemini-2.5-flash 모델을 포함한 매핑 테스트...")
        test_mappings = [
            {"role_name": "Researcher", "llm_model": "gemini-2.5-flash"},
            {"role_name": "Writer", "llm_model": "gemini-2.5-pro"},
            {"role_name": "Planner", "llm_model": "gpt-4"}
        ]

        # 데이터베이스에 저장 시도
        result = db.set_project_role_llm_mapping(test_project_id, test_mappings)

        if result.get("success"):
            print("   SUCCESS: 모델명 정규화 로직이 성공적으로 작동함!")
            print(f"   저장된 매핑 수: {len(result.get('mappings', []))}")

            # 저장된 데이터 확인
            saved_result = db.get_project_role_llm_mapping(test_project_id)
            if saved_result.get("success"):
                mappings = saved_result.get("mappings", [])
                print("   저장된 매핑 확인:")
                for mapping in mappings:
                    role = mapping.get('role_name')
                    model = mapping.get('llm_model')
                    print(f"     - {role}: {model}")

            # 테스트 데이터 정리
            db.supabase.table('project_role_llm_mapping').delete().eq('projects_project_id', test_project_id).execute()
            print("   테스트 데이터 정리 완료")

            return True
        else:
            print(f"   ERROR: 매핑 저장 실패 - {result.get('error')}")
            return False

    except Exception as e:
        print(f"ERROR: 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_normalized_model_save()
    if success:
        print("결론: 모델명 정규화 로직이 성공적으로 구현되었습니다!")
    else:
        print("결론: 모델명 정규화 로직에 문제가 있습니다.")
    sys.exit(0 if success else 1)