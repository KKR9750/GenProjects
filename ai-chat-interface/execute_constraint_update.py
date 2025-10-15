#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 제약 조건 직접 업데이트 스크립트
Supabase RPC를 사용하여 SQL 실행
"""

import os
import sys
from database import get_database

def execute_constraint_update():
    """데이터베이스 제약 조건 직접 업데이트"""
    try:
        print("데이터베이스 제약 조건 업데이트 시작...")

        # 데이터베이스 인스턴스 가져오기
        db = get_database()

        if not db.is_connected():
            print("ERROR: 데이터베이스 연결 실패")
            return False

        print("OK: 데이터베이스 연결 성공")

        # 1. 기존 제약 조건 제거
        print("   1. 기존 제약 조건 제거...")
        try:
            # 직접 SQL 실행을 위한 raw query 시도
            result1 = db.supabase.postgrest.schema("public").rpc("exec", {
                "sql": "ALTER TABLE project_role_llm_mapping DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;"
            }).execute()
            print("   OK: 기존 제약 조건 제거 완료")
        except Exception as e:
            print(f"   WARNING: 기존 제약 조건 제거 시 오류 (무시 가능): {e}")

        # 2. 새로운 제약 조건 추가
        print("   2. 새로운 제약 조건 추가 (Gemini 2.5 포함)...")
        constraint_sql = """
        ALTER TABLE project_role_llm_mapping
        ADD CONSTRAINT project_role_llm_mapping_llm_model_check
        CHECK (llm_model IN (
            'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
            'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
            'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
        ));
        """

        try:
            result2 = db.supabase.postgrest.schema("public").rpc("exec", {
                "sql": constraint_sql
            }).execute()
            print("   OK: 새로운 제약 조건 추가 완료")
        except Exception as e:
            print(f"   ERROR: 새로운 제약 조건 추가 실패: {e}")
            print("   다른 방법을 시도합니다...")

            # 대안: 테이블 직접 조작
            print("   대안: 수동으로 모델명 변환 로직 확인...")

            # 현재 데이터베이스의 제약 조건 확인
            try:
                result = db.supabase.table('project_role_llm_mapping').select('*').limit(1).execute()
                print(f"   INFO: 현재 테이블 접근 가능함 - 행 수: {len(result.data) if result.data else 0}")

                # gemini-2.5-flash 데이터 삽입 테스트
                test_data = {
                    "projects_project_id": "test_project_00001",
                    "role_name": "Researcher",
                    "llm_model": "gemini-2.5-flash",
                    "is_active": True
                }

                print("   테스트: gemini-2.5-flash 모델 삽입 시도...")
                test_result = db.supabase.table('project_role_llm_mapping').insert(test_data).execute()

                if test_result.data:
                    print("   SUCCESS: gemini-2.5-flash 모델이 이미 허용됨!")
                    # 테스트 데이터 삭제
                    db.supabase.table('project_role_llm_mapping').delete().eq('projects_project_id', 'test_project_00001').execute()
                    return True

            except Exception as test_e:
                if "violates check constraint" in str(test_e):
                    print(f"   CONFIRMED: 제약 조건 위반 확인됨 - {test_e}")
                    print("   수동 업데이트가 필요합니다.")
                else:
                    print(f"   ERROR: 예상치 못한 오류: {test_e}")

        # 3. 변경 사항 확인
        print("   3. 변경 사항 확인...")
        try:
            # 간접적인 방법으로 확인
            print("   INFO: 제약 조건 확인 완료 (수동 확인 필요)")
        except Exception as e:
            print(f"   WARNING: 제약 조건 확인 실패: {e}")

        print("WARNING: 제약 조건 업데이트가 완전히 성공하지 못했습니다.")
        print("수동으로 Supabase 콘솔에서 다음 SQL을 실행하세요:")
        print("=" * 60)
        print("-- 1. 기존 제약 조건 제거")
        print("ALTER TABLE project_role_llm_mapping")
        print("DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;")
        print()
        print("-- 2. 새로운 제약 조건 추가")
        print("ALTER TABLE project_role_llm_mapping")
        print("ADD CONSTRAINT project_role_llm_mapping_llm_model_check")
        print("CHECK (llm_model IN (")
        print("    'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',")
        print("    'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',")
        print("    'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'")
        print("));")
        print("=" * 60)

        return False

    except Exception as e:
        print(f"ERROR: 데이터베이스 업데이트 실패: {e}")
        return False

if __name__ == "__main__":
    success = execute_constraint_update()
    sys.exit(0 if success else 1)