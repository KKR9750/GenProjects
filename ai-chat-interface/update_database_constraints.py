#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 제약 조건 업데이트 스크립트
Gemini 2.5 모델을 위한 제약 조건 추가
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def update_database_constraints():
    """데이터베이스 제약 조건 업데이트"""
    try:
        # Supabase 클라이언트 초기화
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_ANON_KEY가 설정되지 않았습니다")

        supabase: Client = create_client(url, key)

        print("데이터베이스 제약 조건 업데이트 시작...")

        # 1. 기존 제약 조건 제거
        print("   1. 기존 제약 조건 제거...")
        try:
            supabase.rpc('execute_sql', {
                'sql': '''
                ALTER TABLE project_role_llm_mapping
                DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;
                '''
            }).execute()
            print("   OK: 기존 제약 조건 제거 완료")
        except Exception as e:
            print(f"   WARNING: 기존 제약 조건 제거 시 오류 (무시 가능): {e}")

        # 2. 새로운 제약 조건 추가
        print("   2. 새로운 제약 조건 추가 (Gemini 2.5 포함)...")
        supabase.rpc('execute_sql', {
            'sql': '''
            ALTER TABLE project_role_llm_mapping
            ADD CONSTRAINT project_role_llm_mapping_llm_model_check
            CHECK (llm_model IN (
                'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
                'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
                'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
            ));
            '''
        }).execute()
        print("   OK: 새로운 제약 조건 추가 완료")

        # 3. 변경 사항 확인
        print("   3. 변경 사항 확인...")
        result = supabase.rpc('execute_sql', {
            'sql': '''
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_name = 'project_role_llm_mapping_llm_model_check';
            '''
        }).execute()

        if result.data:
            print("   OK: 제약 조건 확인 완료")
            print(f"   INFO: 제약 조건: {result.data[0].get('check_clause', 'N/A')}")
        else:
            print("   WARNING: 제약 조건 확인 실패")

        print("SUCCESS: 데이터베이스 제약 조건 업데이트 완료!")
        return True

    except Exception as e:
        print(f"ERROR: 데이터베이스 업데이트 실패: {e}")
        return False

if __name__ == "__main__":
    success = update_database_constraints()
    sys.exit(0 if success else 1)