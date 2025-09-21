#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 테이블 설정 테스트 스크립트
"""

import os
import bcrypt
from datetime import datetime
from database import db

def create_admin_user():
    """기본 관리자 계정 생성"""
    try:
        # 비밀번호 해시 생성
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        admin_data = {
            'user_id': 'admin',
            'email': 'admin@genprojects.com',
            'display_name': '시스템 관리자',
            'password_hash': password_hash,
            'role': 'admin',
            'is_active': True
        }

        result = db.create_user(admin_data)

        if result['success']:
            print("관리자 계정 생성 성공")
            print(f"   사용자 ID: admin")
            print(f"   비밀번호: admin123")
            print(f"   이메일: admin@genprojects.com")
        else:
            print(f"❌ 관리자 계정 생성 실패: {result.get('error')}")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("데이터베이스 연결 테스트...")

    if not db.is_connected():
        print("Supabase 연결 실패")
        print("   환경 변수를 확인하세요:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_ANON_KEY")
        return False

    connection_test = db.test_connection()
    if connection_test['connected']:
        print("Supabase 연결 성공")
        return True
    else:
        print(f"연결 실패: {connection_test['message']}")
        return False

def test_users_table():
    """Users 테이블 테스트"""
    print("\n👥 Users 테이블 테스트...")

    try:
        # 사용자 목록 조회 테스트
        result = db.get_users()

        if result['success']:
            users = result['users']
            print(f"✅ Users 테이블 접근 성공 (사용자 수: {len(users)})")

            if users:
                print("   등록된 사용자:")
                for user in users[:3]:  # 최대 3명만 표시
                    print(f"   - {user['user_id']} ({user['role']}) - {user.get('display_name', 'N/A')}")
            else:
                print("   등록된 사용자가 없습니다")

        else:
            print(f"❌ Users 테이블 접근 실패: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Users 테이블 테스트 실패: {str(e)}")
        return False

    return True

def test_projects_table():
    """Projects 테이블 테스트"""
    print("\n📁 Projects 테이블 테스트...")

    try:
        result = db.get_projects(limit=5)

        if result['success']:
            projects = result['projects']
            print(f"✅ Projects 테이블 접근 성공 (프로젝트 수: {len(projects)})")

            if projects:
                print("   최근 프로젝트:")
                for project in projects[:3]:
                    owner = project.get('created_by_user_id', 'N/A')
                    print(f"   - {project['name']} (소유자: {owner})")
            else:
                print("   등록된 프로젝트가 없습니다")

        else:
            print(f"❌ Projects 테이블 접근 실패: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Projects 테이블 테스트 실패: {str(e)}")
        return False

    return True

def main():
    """메인 실행 함수"""
    print("GenProjects Supabase 설정 테스트")
    print("=" * 50)

    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        return

    # 2. Users 테이블 테스트
    if not test_users_table():
        print("\n⚠️  Users 테이블이 없을 수 있습니다.")
        print("   Supabase SQL Editor에서 다음 파일을 실행하세요:")
        print("   📄 create_users_table.sql")
        return

    # 3. Projects 테이블 테스트
    test_projects_table()

    # 4. 관리자 계정 생성 (이미 있으면 무시)
    print("\n👑 관리자 계정 설정...")
    create_admin_user()

    print("\n🎉 설정 테스트 완료!")
    print("\n📋 다음 단계:")
    print("1. 웹 브라우저에서 http://localhost:3000 접속")
    print("2. 로그인 정보:")
    print("   - 사용자 ID: admin")
    print("   - 비밀번호: admin123")
    print("3. 관리자 대시보드에서 사용자 및 프로젝트 관리")

if __name__ == '__main__':
    main()