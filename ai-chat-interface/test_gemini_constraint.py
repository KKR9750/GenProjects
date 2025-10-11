#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 2.5 모델 제약 조건 테스트
"""

import os
import sys
from database import get_database

def test_gemini_model():
    """Gemini 2.5 모델 제약 조건 테스트"""
    try:
        print("Gemini 2.5 모델 제약 조건 테스트 시작...")

        # 데이터베이스 인스턴스 가져오기
        db = get_database()

        if not db.is_connected():
            print("ERROR: 데이터베이스 연결 실패")
            return False

        print("OK: 데이터베이스 연결 성공")

        # 유효한 프로젝트 ID 형식 사용 (13자리 제한)
        test_project_id = "project_00001"  # 13자리

        # 1. 기존 모델 테스트 (gemini-flash)
        print("   1. 기존 모델 (gemini-flash) 테스트...")
        test_data_old = {
            "projects_project_id": test_project_id,
            "role_name": "Researcher",
            "llm_model": "gemini-flash",
            "is_active": True
        }

        try:
            result_old = db.supabase.table('project_role_llm_mapping').insert(test_data_old).execute()
            if result_old.data:
                print("   OK: gemini-flash 모델 허용됨")
                # 테스트 데이터 삭제
                db.supabase.table('project_role_llm_mapping').delete().eq('projects_project_id', test_project_id).eq('role_name', 'Researcher').execute()
            else:
                print("   ERROR: gemini-flash 모델 삽입 실패")
        except Exception as e:
            print(f"   ERROR: gemini-flash 테스트 실패: {e}")

        # 2. 새로운 모델 테스트 (gemini-2.5-flash)
        print("   2. 새로운 모델 (gemini-2.5-flash) 테스트...")
        test_data_new = {
            "projects_project_id": test_project_id,
            "role_name": "Writer",
            "llm_model": "gemini-2.5-flash",
            "is_active": True
        }

        try:
            result_new = db.supabase.table('project_role_llm_mapping').insert(test_data_new).execute()
            if result_new.data:
                print("   SUCCESS: gemini-2.5-flash 모델이 이미 허용됨!")
                # 테스트 데이터 삭제
                db.supabase.table('project_role_llm_mapping').delete().eq('projects_project_id', test_project_id).eq('role_name', 'Writer').execute()
                return True
            else:
                print("   ERROR: gemini-2.5-flash 모델 삽입 실패")
                return False
        except Exception as e:
            if "violates check constraint" in str(e):
                print(f"   CONFIRMED: 제약 조건 위반 - {e}")
                print("   gemini-2.5-flash 모델이 허용되지 않음")
                return False
            else:
                print(f"   ERROR: 예상치 못한 오류: {e}")
                return False

    except Exception as e:
        print(f"ERROR: 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_model()
    if success:
        print("결론: 데이터베이스 제약 조건이 이미 업데이트되어 있습니다!")
    else:
        print("결론: 데이터베이스 제약 조건 업데이트가 필요합니다.")
    sys.exit(0 if success else 1)