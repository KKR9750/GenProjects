#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Database Connection Test
실제 데이터베이스 연결 및 데이터 삽입 테스트
"""

import os
import sys
import json
from datetime import datetime

# 직접 환경 변수 설정
os.environ['SUPABASE_URL'] = 'https://vpbkitxgisxbqtxrwjvo.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwYmtpdHhnaXN4YnF0eHJ3anZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgxNzM5NzUsImV4cCI6MjA3Mzc0OTk3NX0._db0ajX3GQVBUdxl7OJ0ykt14Jb7FSRbUNsEnnqDtp8'

try:
    from supabase import create_client

    print("=" * 60)
    print("Real Database Operations Test")
    print("=" * 60)

    # Supabase 클라이언트 생성
    supabase = create_client(
        os.environ['SUPABASE_URL'],
        os.environ['SUPABASE_ANON_KEY']
    )
    print("SUCCESS: Supabase 클라이언트 생성 성공")

    # 1. 기존 프로젝트 조회
    print("\n1. 기존 프로젝트 조회:")
    try:
        result = supabase.table('projects').select('*').execute()
        print(f"SUCCESS: {len(result.data)}개의 프로젝트가 있습니다")
        for project in result.data:
            print(f"  - {project['name']} ({project['selected_ai']})")
    except Exception as e:
        print(f"INFO: 프로젝트 조회 실패: {e}")

    # 2. 새 프로젝트 생성
    print("\n2. 새 프로젝트 생성:")
    try:
        new_project = {
            'name': 'Test Project from Python',
            'description': 'CrewAI database integration successful test',
            'selected_ai': 'crew-ai',
            'project_type': 'web_app',
            'status': 'planning',
            'current_stage': 'requirement',
            'progress_percentage': 0
        }

        result = supabase.table('projects').insert(new_project).execute()
        if result.data:
            project_id = result.data[0]['id']
            print(f"SUCCESS: 프로젝트 생성 성공! ID: {project_id}")
            print(f"프로젝트명: {result.data[0]['name']}")
        else:
            print("ERROR: 프로젝트 생성 실패")
    except Exception as e:
        print(f"ERROR: 프로젝트 생성 실패: {e}")

    # 3. 전체 프로젝트 목록 다시 조회
    print("\n3. 최종 프로젝트 목록:")
    try:
        result = supabase.table('projects').select('*').order('created_at', desc=True).execute()
        print(f"SUCCESS: 총 {len(result.data)}개의 프로젝트")
        for i, project in enumerate(result.data[:3]):  # 최신 3개만 표시
            print(f"  {i+1}. {project['name']} - {project['status']} ({project['created_at'][:10]})")
    except Exception as e:
        print(f"ERROR: 프로젝트 목록 조회 실패: {e}")

    print("\n" + "=" * 60)
    print("Real Database Test Complete!")
    print("=" * 60)

except Exception as e:
    print(f"ERROR: 데이터베이스 연결 실패: {e}")
    print("\n해결 방법:")
    print("1. 환경 변수 확인")
    print("2. Supabase 프로젝트 상태 확인")
    print("3. API 키 권한 확인")