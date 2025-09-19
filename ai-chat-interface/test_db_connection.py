#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Connection Test Script
Supabase 연결 테스트 및 스키마 검증
"""

import os
import sys
from dotenv import load_dotenv

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables
load_dotenv()

from database import db

def test_connection():
    """데이터베이스 연결 테스트"""
    print(">> Supabase 연결 테스트 중...")

    # 기본 연결 확인
    result = db.test_connection()

    if result['connected']:
        print(f"SUCCESS: {result['message']}")
        return True
    else:
        print(f"ERROR: {result['message']}")
        if 'error' in result:
            print(f"   오류 세부사항: {result['error']}")

        if result.get('simulation_mode'):
            print("INFO: 시뮬레이션 모드로 계속 진행합니다.")
            return False
        return False

def test_basic_operations():
    """기본 데이터베이스 작업 테스트"""
    print("\n>> 기본 데이터베이스 작업 테스트...")

    # 1. 프로젝트 목록 조회 테스트
    print("1. 프로젝트 목록 조회 테스트")
    projects_result = db.get_projects()
    if projects_result['success']:
        print(f"   SUCCESS: 프로젝트 {projects_result['count']}개 조회 성공")
        if projects_result.get('simulation'):
            print("   INFO: 시뮬레이션 데이터입니다.")
    else:
        print(f"   ERROR: 프로젝트 조회 실패: {projects_result['error']}")

    # 2. 테스트 프로젝트 생성
    print("\n2. 테스트 프로젝트 생성")
    test_project_data = {
        "name": "테스트 프로젝트",
        "description": "데이터베이스 연결 테스트용 프로젝트",
        "selected_ai": "crew-ai",
        "project_type": "web_app"
    }

    create_result = db.create_project(test_project_data)
    if create_result['success']:
        print(f"   SUCCESS: 프로젝트 생성 성공: {create_result['project']['name']}")
        project_id = create_result['project']['id']

        # 3. 역할-LLM 매핑 테스트
        print("\n3. 역할-LLM 매핑 설정 테스트")
        test_mappings = [
            {"role_name": "Researcher", "llm_model": "gpt-4"},
            {"role_name": "Writer", "llm_model": "claude-3"},
            {"role_name": "Planner", "llm_model": "gemini-pro"}
        ]

        mapping_result = db.set_project_role_llm_mapping(project_id, test_mappings)
        if mapping_result['success']:
            print(f"   SUCCESS: LLM 매핑 설정 성공: {len(mapping_result['mappings'])}개 매핑")
        else:
            print(f"   ERROR: LLM 매핑 설정 실패: {mapping_result['error']}")

        # 4. 매핑 조회 테스트
        print("\n4. LLM 매핑 조회 테스트")
        get_mapping_result = db.get_project_role_llm_mapping(project_id)
        if get_mapping_result['success']:
            print(f"   SUCCESS: LLM 매핑 조회 성공: {len(get_mapping_result['mappings'])}개 매핑")
            for mapping in get_mapping_result['mappings']:
                print(f"      - {mapping['role_name']}: {mapping['llm_model']}")
        else:
            print(f"   ERROR: LLM 매핑 조회 실패: {get_mapping_result['error']}")

    else:
        print(f"   ERROR: 프로젝트 생성 실패: {create_result['error']}")

def check_environment():
    """환경 변수 확인"""
    print(">> 환경 변수 확인...")

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'JWT_SECRET_KEY'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-'):
            missing_vars.append(var)
        else:
            print(f"   SUCCESS: {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '****'}")

    if missing_vars:
        print(f"\nWARNING: 다음 환경 변수를 설정해야 합니다:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nNOTE: .env 파일을 편집하여 실제 값으로 변경하세요:")
        print("   1. Supabase 프로젝트 생성 (https://supabase.com)")
        print("   2. Project Settings > API에서 URL과 API 키 복사")
        print("   3. .env 파일에 실제 값 입력")
        return False

    return True

def display_next_steps():
    """다음 단계 안내"""
    print("\n>> 다음 단계:")
    print("1. Supabase 프로젝트에서 SQL 편집기 열기")
    print("2. setup_database.sql 파일 내용을 실행하여 테이블 생성")
    print("3. 다시 이 스크립트를 실행하여 연결 테스트")
    print("\n>> 파일 위치:")
    print(f"   - 데이터베이스 스키마: {os.path.join(current_dir, 'setup_database.sql')}")
    print(f"   - 환경 변수 설정: {os.path.join(current_dir, '.env')}")

def main():
    """메인 함수"""
    print("=" * 60)
    print("AI Chat Interface - 데이터베이스 연결 테스트")
    print("=" * 60)

    # 환경 변수 확인
    env_ok = check_environment()

    if not env_ok:
        print("\nERROR: 환경 변수 설정이 필요합니다.")
        display_next_steps()
        return

    # 연결 테스트
    connected = test_connection()

    if not connected and not db.is_connected():
        print("\nERROR: 데이터베이스 연결 실패. 환경 변수를 확인하세요.")
        display_next_steps()
        return

    # 기본 작업 테스트
    test_basic_operations()

    print("\n" + "=" * 60)
    if connected:
        print("SUCCESS: 데이터베이스 연결 및 기본 작업 테스트 완료!")
    else:
        print("INFO: 시뮬레이션 모드에서 기본 작업 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()