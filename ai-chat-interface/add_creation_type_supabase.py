#!/usr/bin/env python3
"""
Supabase REST API를 사용하여 creation_type 컬럼 추가
"""

import os
import requests
from supabase import create_client, Client

def add_creation_type_via_supabase():
    """Supabase 클라이언트를 통해 creation_type 컬럼 추가"""

    # Supabase 설정
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_key:
        print("❌ SUPABASE_ANON_KEY 환경 변수가 설정되지 않았습니다.")
        print("다음과 같이 설정하세요:")
        print('  set SUPABASE_ANON_KEY="your_anon_key_here"  (Windows)')
        print('  export SUPABASE_ANON_KEY="your_anon_key_here"  (Linux/Mac)')
        return

    print(f"Supabase URL: {supabase_url}")

    # Supabase 클라이언트 생성
    supabase: Client = create_client(supabase_url, supabase_key)

    try:
        # SQL 실행 (Supabase RPC를 사용)
        # 먼저 컬럼이 존재하는지 확인
        print("\n1️⃣ 현재 projects 테이블 구조 확인 중...")

        # 테스트: projects 테이블 조회
        result = supabase.table('projects').select('*').limit(1).execute()
        print(f"✅ Projects 테이블 접근 성공 (레코드 수: {len(result.data)})")

        if result.data and len(result.data) > 0:
            columns = result.data[0].keys()
            print(f"   현재 컬럼: {', '.join(columns)}")

            if 'creation_type' in columns:
                print("\n✅ creation_type 컬럼이 이미 존재합니다!")

                # creation_type 값 확인
                all_projects = supabase.table('projects').select('project_id, creation_type').execute()
                dynamic_count = sum(1 for p in all_projects.data if p.get('creation_type') == 'dynamic')
                template_count = sum(1 for p in all_projects.data if p.get('creation_type') == 'template')
                null_count = sum(1 for p in all_projects.data if not p.get('creation_type'))

                print(f"   - Dynamic 프로젝트: {dynamic_count}개")
                print(f"   - Template 프로젝트: {template_count}개")
                print(f"   - NULL 프로젝트: {null_count}개")

                if null_count > 0:
                    print("\n2️⃣ NULL 값을 'template'로 업데이트 중...")
                    # NULL인 프로젝트들을 template로 업데이트
                    for project in all_projects.data:
                        if not project.get('creation_type'):
                            supabase.table('projects').update({
                                'creation_type': 'template'
                            }).eq('project_id', project['project_id']).execute()
                    print(f"✅ {null_count}개 프로젝트를 'template'로 업데이트했습니다.")
            else:
                print("\n⚠️ creation_type 컬럼이 없습니다.")
                print("⚠️ Supabase 대시보드에서 수동으로 추가해야 합니다.")
                print("\n다음 SQL을 Supabase SQL Editor에서 실행하세요:")
                print("=" * 60)
                print("""
ALTER TABLE projects
ADD COLUMN creation_type VARCHAR(20) DEFAULT 'template';

UPDATE projects
SET creation_type = 'template'
WHERE creation_type IS NULL;
                """)
                print("=" * 60)
                print("\nSupabase 대시보드: https://supabase.com/dashboard/project/vpbkitxgisxbqtxrwjvo/editor")
        else:
            print("⚠️ projects 테이블이 비어있습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_creation_type_via_supabase()
