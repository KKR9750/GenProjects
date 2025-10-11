# -*- coding: utf-8 -*-
"""
Ollama 로컬 모델을 위한 데이터베이스 제약 조건 업데이트
Supabase의 project_role_llm_mapping 테이블에 Ollama 모델 4개 추가
"""

import os
import sys
import io

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from supabase import create_client, Client

def update_llm_constraint():
    """데이터베이스 제약 조건 업데이트"""

    # Supabase 연결
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_key:
        print("❌ 오류: SUPABASE_ANON_KEY 환경 변수가 설정되지 않았습니다")
        return False

    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"✅ Supabase 연결 성공: {supabase_url}")

        # SQL 명령어
        sql_commands = [
            # 1. 기존 제약 조건 제거
            """
            ALTER TABLE project_role_llm_mapping
            DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;
            """,

            # 2. 새로운 제약 조건 추가 (Ollama 모델 포함)
            """
            ALTER TABLE project_role_llm_mapping
            ADD CONSTRAINT project_role_llm_mapping_llm_model_check
            CHECK (llm_model IN (
                'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
                'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
                'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama',
                'ollama-gemma2-2b', 'ollama-deepseek-coder-6.7b', 'ollama-llama3.1', 'ollama-qwen3-coder-30b'
            ));
            """
        ]

        # SQL 실행
        for i, sql in enumerate(sql_commands, 1):
            print(f"\n📝 SQL 명령어 {i} 실행 중...")
            print(sql.strip())

            try:
                result = supabase.rpc('exec_sql', {'query': sql}).execute()
                print(f"✅ SQL 명령어 {i} 실행 성공")
            except Exception as e:
                error_msg = str(e)

                # RPC 함수가 없는 경우 대안 안내
                if 'exec_sql' in error_msg or 'function' in error_msg.lower():
                    print("⚠️ Supabase RPC 함수가 없습니다.")
                    print("\n📋 수동 실행 방법:")
                    print("1. Supabase 대시보드 접속: https://supabase.com/dashboard")
                    print("2. 프로젝트 선택")
                    print("3. SQL Editor 메뉴 선택")
                    print("4. 아래 SQL을 복사하여 실행:")
                    print("\n--- SQL 시작 ---")
                    for sql_cmd in sql_commands:
                        print(sql_cmd.strip())
                    print("--- SQL 끝 ---\n")
                    return False
                else:
                    print(f"❌ SQL 실행 실패: {error_msg}")
                    return False

        # 3. 변경 사항 확인
        print("\n🔍 변경 사항 확인 중...")
        verify_sql = """
        SELECT constraint_name, check_clause
        FROM information_schema.check_constraints
        WHERE constraint_name = 'project_role_llm_mapping_llm_model_check';
        """

        try:
            result = supabase.rpc('exec_sql', {'query': verify_sql}).execute()
            print("✅ 제약 조건 업데이트 완료!")
            print(f"결과: {result.data}")
        except:
            print("⚠️ 확인 쿼리 실패 (업데이트는 성공했을 수 있음)")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Ollama 로컬 모델 - 데이터베이스 제약 조건 업데이트")
    print("=" * 60)

    success = update_llm_constraint()

    if success:
        print("\n✅ 업데이트 성공!")
        print("\n추가된 Ollama 모델:")
        print("  - ollama-gemma2-2b")
        print("  - ollama-deepseek-coder-6.7b")
        print("  - ollama-llama3.1")
        print("  - ollama-qwen3-coder-30b")
    else:
        print("\n⚠️ 수동 업데이트가 필요합니다.")
        print("위의 안내를 따라 Supabase 대시보드에서 SQL을 실행하세요.")

    sys.exit(0 if success else 1)
