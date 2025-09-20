#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Supabase Connection Test
실제 Supabase 연결 테스트를 위한 간단한 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Supabase 연결 테스트"""

    # 환경 변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    print("=" * 60)
    print("Supabase 연결 테스트")
    print("=" * 60)

    if not supabase_url or supabase_url.startswith('your-'):
        print("ERROR: SUPABASE_URL이 설정되지 않았습니다.")
        return False

    if not supabase_key or supabase_key.startswith('your-'):
        print("ERROR: SUPABASE_ANON_KEY가 설정되지 않았습니다.")
        return False

    print(f"SUPABASE_URL: {supabase_url}")
    print(f"SUPABASE_ANON_KEY: {supabase_key[:20]}...")

    try:
        from supabase import create_client

        # Supabase 클라이언트 생성
        supabase = create_client(supabase_url, supabase_key)
        print("SUCCESS: Supabase 클라이언트 생성 성공")

        # 기본 연결 테스트 (빈 쿼리)
        try:
            result = supabase.table('projects').select('count').limit(1).execute()
            print("SUCCESS: 데이터베이스 연결 성공!")
            print(f"Projects 테이블 접근 가능")
            return True

        except Exception as query_error:
            print(f"WARNING: 테이블 쿼리 실패: {query_error}")
            print("NOTE: 아직 테이블이 생성되지 않았을 수 있습니다.")
            print("Supabase SQL 편집기에서 setup_database.sql을 실행하세요.")
            return True  # 연결은 성공했지만 테이블이 없음

    except Exception as e:
        print(f"ERROR: Supabase 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. SUPABASE_URL이 올바른지 확인")
        print("2. SUPABASE_ANON_KEY가 올바른지 확인")
        print("3. Supabase 프로젝트가 활성화되어 있는지 확인")
        return False

def test_with_database_module():
    """database.py 모듈을 통한 테스트"""
    try:
        from database import db

        print("\n" + "=" * 60)
        print("Database 모듈 테스트")
        print("=" * 60)

        if db.is_connected():
            print("SUCCESS: Database 모듈 연결 성공")

            # 연결 테스트
            result = db.test_connection()
            print(f"연결 테스트 결과: {result}")

            # 프로젝트 목록 조회 테스트
            projects_result = db.get_projects()
            if projects_result['success']:
                print(f"SUCCESS: 프로젝트 목록 조회 성공 ({projects_result['count']}개)")
            else:
                print(f"INFO: {projects_result['error']}")

        else:
            print("INFO: Database 모듈이 시뮬레이션 모드로 실행 중")

    except Exception as e:
        print(f"ERROR: Database 모듈 테스트 실패: {e}")

def main():
    """메인 함수"""

    # 직접 연결 테스트
    connection_ok = test_supabase_connection()

    # Database 모듈 테스트
    test_with_database_module()

    print("\n" + "=" * 60)
    if connection_ok:
        print("SUCCESS: Supabase 연결 테스트 완료!")
        print("\n다음 단계:")
        print("1. Supabase SQL 편집기에서 setup_database.sql 실행")
        print("2. Flask 서버 재시작")
        print("3. API 테스트")
    else:
        print("ERROR: Supabase 연결 실패")
        print("\n문제 해결:")
        print("1. .env 파일에서 SUPABASE_URL과 SUPABASE_ANON_KEY 확인")
        print("2. Supabase 프로젝트 상태 확인")
    print("=" * 60)

if __name__ == "__main__":
    main()