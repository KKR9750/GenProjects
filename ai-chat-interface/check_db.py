#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import db

def main():
    print("=== Supabase 상태 확인 ===")

    # 연결 테스트
    if not db.is_connected():
        print("Supabase 연결 실패")
        return

    print("Supabase 연결 성공")

    # Users 테이블 테스트
    try:
        result = db.get_users()
        if result['success']:
            print(f"Users 테이블 OK - 사용자 수: {len(result['users'])}")
        else:
            print(f"Users 테이블 오류: {result['error']}")
    except Exception as e:
        print(f"Users 테이블 없음: {str(e)}")

    # Projects 테이블 테스트
    try:
        result = db.get_projects()
        if result['success']:
            print(f"Projects 테이블 OK - 프로젝트 수: {len(result['projects'])}")
        else:
            print(f"Projects 테이블 오류: {result['error']}")
    except Exception as e:
        print(f"Projects 테이블 오류: {str(e)}")

if __name__ == '__main__':
    main()