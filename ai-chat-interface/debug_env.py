#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Variables Debug
환경 변수 디버깅 및 확인
"""

import os
from dotenv import load_dotenv

print("=" * 60)
print("Environment Variables Debug")
print("=" * 60)

# .env 파일 로드 전
print("1. 로드 전 환경 변수:")
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY', 'NOT SET')[:20]}...")

# .env 파일 로드
print(f"\n2. .env 파일 로드 시도...")
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f".env 파일 경로: {env_path}")
print(f".env 파일 존재: {os.path.exists(env_path)}")

load_dotenv()

# .env 파일 로드 후
print(f"\n3. 로드 후 환경 변수:")
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_ANON_KEY')

print(f"SUPABASE_URL: {supabase_url}")
if supabase_key:
    print(f"SUPABASE_ANON_KEY: {supabase_key[:20]}...")
else:
    print("SUPABASE_ANON_KEY: NOT SET")

# .env 파일 내용 직접 읽기
print(f"\n4. .env 파일 내용 직접 확인:")
try:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        for line in lines[:10]:  # 처음 10줄만
            if line.strip() and not line.startswith('#'):
                if 'SUPABASE_URL' in line:
                    print(f"  {line}")
                elif 'SUPABASE_ANON_KEY' in line:
                    key_part = line.split('=')[1] if '=' in line else ''
                    print(f"  SUPABASE_ANON_KEY={key_part[:20]}...")
except Exception as e:
    print(f"ERROR reading .env: {e}")

# 연결 테스트
print(f"\n5. 연결 테스트:")
if supabase_url and supabase_key and not supabase_key.startswith('your-'):
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        print("SUCCESS: Supabase 클라이언트 생성 성공")

        # 간단한 테이블 조회
        result = supabase.table('projects').select('count').limit(1).execute()
        print("SUCCESS: 데이터베이스 연결 성공!")

    except Exception as e:
        print(f"ERROR: 연결 실패: {e}")
else:
    print("ERROR: 환경 변수가 올바르게 설정되지 않았습니다")

print("=" * 60)