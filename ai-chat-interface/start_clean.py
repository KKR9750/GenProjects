#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Environment Start Script
환경 변수를 강제로 재설정하고 서버 시작
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# 기존 환경 변수 제거
if 'SUPABASE_URL' in os.environ:
    del os.environ['SUPABASE_URL']
if 'SUPABASE_ANON_KEY' in os.environ:
    del os.environ['SUPABASE_ANON_KEY']

# .env 파일에서 새로 로드
load_dotenv(override=True)

# 환경 변수 강제 설정
os.environ['SUPABASE_URL'] = 'https://vpbkitxgisxbqtxrwjvo.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwYmtpdHhnaXN4YnF0eHJ3anZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxNzM5NzUsImV4cCI6MjA3Mzc0OTk3NX0._db0ajX3GQVBUdxl7OJ0ykt14Jb7FSRbUNsEnnqDtp8'

print("=" * 60)
print("Clean Environment Start")
print("=" * 60)
print(f"SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
print(f"SUPABASE_ANON_KEY: {os.getenv('SUPABASE_ANON_KEY')[:20]}...")

# app.py 실행
print("\nFlask 서버 시작...")
try:
    from app import app
    print("SUCCESS: Flask 앱 로드 성공")
    app.run(host='0.0.0.0', port=3000, debug=True)
except Exception as e:
    print(f"ERROR: Flask 서버 시작 실패: {e}")
    sys.exit(1)