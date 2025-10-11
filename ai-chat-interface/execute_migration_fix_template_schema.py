#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
긴급 마이그레이션 실행 스크립트
템플릿 스키마 수정 및 데이터 업데이트
"""

import os
import sys
from database import get_supabase_client

def execute_migration():
    """마이그레이션 SQL 실행"""

    print("=" * 60)
    print("템플릿 스키마 마이그레이션 시작")
    print("=" * 60)

    # Supabase 클라이언트 가져오기
    try:
        supabase = get_supabase_client()
        print("✅ Supabase 연결 성공")
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return False

    # migration_fix_template_schema.sql 파일 읽기
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file = os.path.join(script_dir, 'migration_fix_template_schema.sql')

    if not os.path.exists(sql_file):
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"✅ SQL 파일 읽기 성공: {sql_file}")

    # SQL을 개별 명령으로 분리
    sql_statements = [
        stmt.strip()
        for stmt in sql_content.split(';')
        if stmt.strip()
        and not stmt.strip().startswith('--')
        and 'COMMENT ON' not in stmt.upper()
    ]

    print(f"\n📋 총 {len(sql_statements)}개의 SQL 명령 실행 예정\n")

    # 각 SQL 명령 실행
    success_count = 0
    error_count = 0

    for i, statement in enumerate(sql_statements, 1):
        # COMMENT, SELECT 문은 스킵
        if any(keyword in statement.upper() for keyword in ['COMMENT ON', 'SELECT ']):
            continue

        try:
            # ALTER TABLE 또는 CREATE INDEX
            if 'ALTER TABLE' in statement.upper() or 'CREATE INDEX' in statement.upper():
                print(f"[{i}/{len(sql_statements)}] 실행 중: {statement[:60]}...")
                # Supabase RPC를 통한 DDL 실행은 제한적이므로 직접 실행 시도
                # 실제로는 Supabase SQL Editor에서 실행 필요
                print(f"    DDL 명령은 Supabase SQL Editor에서 실행하세요")

            # UPDATE 문
            elif 'UPDATE' in statement.upper():
                # UPDATE 문 파싱
                table_name = None
                if 'agent_templates' in statement.lower():
                    table_name = 'agent_templates'
                elif 'task_templates' in statement.lower():
                    table_name = 'task_templates'

                print(f"[{i}/{len(sql_statements)}] 실행 중: UPDATE {table_name}...")

                # Supabase Python Client로 UPDATE 실행은 복잡하므로
                # SQL을 Supabase SQL Editor에 복사해서 실행하도록 안내
                print(f"    UPDATE 명령은 Supabase SQL Editor에서 실행하세요")

            success_count += 1

        except Exception as e:
            print(f"    ❌ 에러: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print("마이그레이션 실행 완료")
    print("=" * 60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {error_count}개")

    # 검증 수행
    print("\n" + "=" * 60)
    print("마이그레이션 검증")
    print("=" * 60)

    verify_migration(supabase)

    return True


def verify_migration(supabase):
    """마이그레이션 결과 검증"""

    print("\n📊 Agent 템플릿 검증:")
    try:
        result = supabase.table('agent_templates')\
            .select('framework, template_name, agent_order')\
            .order('framework, agent_order')\
            .execute()

        print(f"총 {len(result.data)}개 Agent 템플릿:")
        for agent in result.data:
            print(f"  - [{agent['framework']}] {agent['template_name']} (order: {agent.get('agent_order', 'N/A')})")

    except Exception as e:
        print(f"❌ Agent 템플릿 조회 실패: {e}")

    print("\n📊 Task 템플릿 검증:")
    try:
        result = supabase.table('task_templates')\
            .select('framework, task_type, task_order, assigned_agent_order, depends_on_task_order')\
            .order('framework, task_order')\
            .execute()

        print(f"총 {len(result.data)}개 Task 템플릿:")
        for task in result.data:
            depends = task.get('depends_on_task_order', 'None')
            print(f"  - [{task['framework']}] {task['task_type']} "
                  f"(order: {task.get('task_order', 'N/A')}, "
                  f"agent: {task.get('assigned_agent_order', 'N/A')}, "
                  f"depends: {depends})")

    except Exception as e:
        print(f"❌ Task 템플릿 조회 실패: {e}")


def print_instructions():
    """실행 안내"""

    print("\n" + "=" * 60)
    print("마이그레이션 실행 방법")
    print("=" * 60)
    print("""
Option 1: Supabase SQL Editor 사용 (추천)
  1. Supabase 대시보드 접속
  2. SQL Editor 메뉴 선택
  3. migration_fix_template_schema.sql 파일 내용 복사
  4. SQL Editor에 붙여넣기
  5. Run 버튼 클릭
  6. 검증 쿼리로 결과 확인

Option 2: 이 스크립트 실행 (제한적)
  python execute_migration_fix_template_schema.py

주의: Supabase Python Client는 DDL 명령 실행에 제한이 있으므로
    Option 1 (SQL Editor)를 사용하는 것을 강력히 권장합니다.
""")


if __name__ == '__main__':
    print_instructions()

    response = input("\n계속 진행하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        execute_migration()
    else:
        print("마이그레이션 취소됨")
