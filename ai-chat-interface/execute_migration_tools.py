#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tools 지원 마이그레이션 실행 스크립트
"""

import os
from database import get_supabase_client

def execute_migration():
    """마이그레이션 SQL 실행"""
    print("=" * 70)
    print("Tools 지원 마이그레이션 시작")
    print("=" * 70)

    # SQL 파일 읽기
    sql_file = os.path.join(os.path.dirname(__file__), 'migration_add_tools_support.sql')

    if not os.path.exists(sql_file):
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"\n✅ SQL 파일 로드 완료: {sql_file}")
    print(f"   파일 크기: {len(sql_content)} bytes")

    # Supabase 연결
    try:
        supabase = get_supabase_client()
        print("\n✅ Supabase 연결 성공")
    except Exception as e:
        print(f"\n❌ Supabase 연결 실패: {e}")
        return False

    # SQL 실행
    try:
        # Supabase는 직접 SQL 실행을 지원하지 않으므로,
        # rpc 또는 REST API를 사용해야 합니다.
        # 대신 Supabase 대시보드 SQL 에디터에서 실행하도록 안내

        print("\n" + "=" * 70)
        print("⚠️  Supabase는 Python에서 직접 DDL을 실행할 수 없습니다")
        print("=" * 70)
        print("\n다음 단계를 따라 수동으로 마이그레이션을 실행하세요:\n")
        print("1. Supabase Dashboard 열기:")
        print("   https://supabase.com/dashboard/project/vpbkitxgisxbqtxrwjvo/sql\n")
        print("2. 'SQL Editor' 탭으로 이동\n")
        print("3. 다음 SQL을 복사하여 실행:\n")
        print("-" * 70)
        print(sql_content)
        print("-" * 70)
        print("\n4. 'Run' 버튼 클릭\n")
        print("=" * 70)

        # 또는 파일 경로 출력
        print(f"\n또는 다음 파일의 내용을 직접 복사하세요:")
        print(f"   {os.path.abspath(sql_file)}")
        print("\n" + "=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = execute_migration()

    if success:
        print("\n✅ 마이그레이션 준비 완료!")
        print("   Supabase Dashboard에서 SQL을 실행하세요.")
    else:
        print("\n❌ 마이그레이션 실패")
        exit(1)
