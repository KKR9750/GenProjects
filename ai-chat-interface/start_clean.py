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

# Load environment variables from .env file with override
load_dotenv(override=True)

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