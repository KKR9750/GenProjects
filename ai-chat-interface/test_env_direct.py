#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Environment Variable Test
환경 변수를 직접 설정하여 Supabase 연결 테스트
"""

import os
import sys

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("Direct Environment Variable Test")
print("=" * 60)

# 환경 변수 확인
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

print(f"SUPABASE_URL: {supabase_url}")
print(f"SUPABASE_ANON_KEY: {supabase_key[:20]}...")

try:
    from supabase import create_client

    # Supabase 클라이언트 생성
    supabase = create_client(supabase_url, supabase_key)
    print("SUCCESS: Supabase 클라이언트 생성 성공")

    # 연결 테스트
    try:
        # 기본 테이블 목록 조회 시도
        result = supabase.table('projects').select('count').limit(1).execute()
        print("SUCCESS: 데이터베이스 연결 성공!")
        print("Projects 테이블이 존재하고 접근 가능합니다.")

    except Exception as query_error:
        print(f"WARNING: 테이블 쿼리 실패: {query_error}")
        print("NOTE: 아직 테이블이 생성되지 않았을 수 있습니다.")
        print("Supabase SQL 편집기에서 setup_database.sql을 실행하세요.")

except Exception as e:
    print(f"ERROR: Supabase 연결 실패: {e}")
    print("\n해결 방법:")
    print("1. SUPABASE_URL이 올바른지 확인")
    print("2. SUPABASE_ANON_KEY가 올바른지 확인")
    print("3. Supabase 프로젝트가 활성화되어 있는지 확인")

print("=" * 60)