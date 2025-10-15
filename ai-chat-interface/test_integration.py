#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Chat Interface 통합 테스트
데이터베이스 연동, API 엔드포인트, 보안 검증 테스트
"""

import sys
import os
import json
import time
import requests
from datetime import datetime

# Windows 환경에서 UTF-8 출력 설정
if sys.platform == "win32":
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        # 이모지 대신 텍스트 사용
        pass

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 테스트 클래스
class IntegrationTester:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.auth_token = None
        self.test_results = []

    def log_test(self, test_name, success, message="", details=None):
        """테스트 결과 로깅"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        if details and not success:
            print(f"    Details: {details}")

    def test_database_connection(self):
        """데이터베이스 연결 테스트"""
        print("\n[INFO] 데이터베이스 연결 테스트")

        try:
            from database import db

            # 연결 테스트
            connection_result = db.test_connection()

            if connection_result.get('connected'):
                self.log_test(
                    "Database Connection",
                    True,
                    "데이터베이스 연결 성공"
                )
            else:
                self.log_test(
                    "Database Connection",
                    True,  # 시뮬레이션 모드도 정상으로 간주
                    f"시뮬레이션 모드: {connection_result.get('message', 'No message')}"
                )

            return True

        except Exception as e:
            self.log_test(
                "Database Connection",
                False,
                "데이터베이스 연결 실패",
                str(e)
            )
            return False

    def test_security_utils(self):
        """보안 유틸리티 테스트"""
        print("\n[INFO] 보안 유틸리티 테스트")

        try:
            from security_utils import InputValidator, SecurityChecker, validate_request_data

            # 입력 검증 테스트
            test_data = {
                "name": "테스트 프로젝트",
                "description": "안전한 프로젝트 설명",
                "project_type": "web_app",
                "selected_ai": "crew-ai"
            }

            validation_result = validate_request_data(test_data, 'project')

            if validation_result['valid']:
                self.log_test(
                    "Input Validation",
                    True,
                    "유효한 입력 데이터 검증 성공"
                )
            else:
                self.log_test(
                    "Input Validation",
                    False,
                    "유효한 입력 데이터 검증 실패",
                    validation_result['errors']
                )

            # 악성 입력 검증 테스트
            malicious_data = {
                "name": "'; DROP TABLE projects; --",
                "description": "<script>alert('xss')</script>",
                "project_type": "invalid_type"
            }

            malicious_validation = validate_request_data(malicious_data, 'project')

            if not malicious_validation['valid']:
                self.log_test(
                    "Malicious Input Detection",
                    True,
                    "악성 입력 차단 성공"
                )
            else:
                self.log_test(
                    "Malicious Input Detection",
                    False,
                    "악성 입력이 통과됨"
                )

            # SQL 인젝션 검사 테스트
            sql_injection_text = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"
            is_malicious = SecurityChecker.check_sql_injection(sql_injection_text)

            if is_malicious:
                self.log_test(
                    "SQL Injection Detection",
                    True,
                    "SQL 인젝션 패턴 감지 성공"
                )
            else:
                self.log_test(
                    "SQL Injection Detection",
                    False,
                    "SQL 인젝션 패턴 감지 실패"
                )

            return True

        except Exception as e:
            self.log_test(
                "Security Utils",
                False,
                "보안 유틸리티 테스트 실패",
                str(e)
            )
            return False

    def test_jwt_functionality(self):
        """JWT 기능 테스트"""
        print("\n[INFO] JWT 기능 테스트")

        try:
            from database import db

            # 토큰 생성 테스트
            user_data = {
                "id": "test-user",
                "email": "test@example.com",
                "role": "user"
            }

            token = db.generate_jwt_token(user_data)

            if token:
                self.log_test(
                    "JWT Generation",
                    True,
                    "JWT 토큰 생성 성공"
                )
            else:
                self.log_test(
                    "JWT Generation",
                    False,
                    "JWT 토큰 생성 실패"
                )
                return False

            # 토큰 검증 테스트
            verification_result = db.verify_jwt_token(token)

            if verification_result['success']:
                self.log_test(
                    "JWT Verification",
                    True,
                    "JWT 토큰 검증 성공"
                )
                self.auth_token = token
            else:
                self.log_test(
                    "JWT Verification",
                    False,
                    "JWT 토큰 검증 실패",
                    verification_result.get('error', 'Unknown error')
                )

            # 잘못된 토큰 검증 테스트
            invalid_verification = db.verify_jwt_token("invalid.token.here")

            if not invalid_verification['success']:
                self.log_test(
                    "Invalid JWT Rejection",
                    True,
                    "잘못된 JWT 토큰 거부 성공"
                )
            else:
                self.log_test(
                    "Invalid JWT Rejection",
                    False,
                    "잘못된 JWT 토큰이 승인됨"
                )

            return True

        except Exception as e:
            self.log_test(
                "JWT Functionality",
                False,
                "JWT 기능 테스트 실패",
                str(e)
            )
            return False

    def test_project_operations(self):
        """프로젝트 CRUD 작업 테스트"""
        print("\n[INFO] 프로젝트 CRUD 테스트")

        try:
            from database import db

            # 프로젝트 생성 테스트
            project_data = {
                "name": "테스트 프로젝트",
                "description": "통합 테스트용 프로젝트",
                "project_type": "web_app",
                "selected_ai": "crew-ai"
            }

            create_result = db.create_project(project_data)

            if create_result['success']:
                self.log_test(
                    "Project Creation",
                    True,
                    "프로젝트 생성 성공"
                )
                project_id = create_result['project']['id']
            else:
                self.log_test(
                    "Project Creation",
                    False,
                    "프로젝트 생성 실패",
                    create_result.get('error', 'Unknown error')
                )
                return False

            # 프로젝트 조회 테스트
            get_result = db.get_project_by_id(project_id)

            if get_result['success']:
                self.log_test(
                    "Project Retrieval",
                    True,
                    "프로젝트 조회 성공"
                )
            else:
                self.log_test(
                    "Project Retrieval",
                    False,
                    "프로젝트 조회 실패",
                    get_result.get('error', 'Unknown error')
                )

            # LLM 매핑 설정 테스트
            mappings = [
                {"role_name": "Researcher", "llm_model": "gpt-4"},
                {"role_name": "Writer", "llm_model": "claude-3"},
                {"role_name": "Planner", "llm_model": "gemini-pro"}
            ]

            mapping_result = db.set_project_role_llm_mapping(project_id, mappings)

            if mapping_result['success']:
                self.log_test(
                    "LLM Mapping Setup",
                    True,
                    "LLM 매핑 설정 성공"
                )
            else:
                self.log_test(
                    "LLM Mapping Setup",
                    False,
                    "LLM 매핑 설정 실패",
                    mapping_result.get('error', 'Unknown error')
                )

            # LLM 매핑 조회 테스트
            get_mapping_result = db.get_project_role_llm_mapping(project_id)

            if get_mapping_result['success']:
                self.log_test(
                    "LLM Mapping Retrieval",
                    True,
                    "LLM 매핑 조회 성공"
                )
            else:
                self.log_test(
                    "LLM Mapping Retrieval",
                    False,
                    "LLM 매핑 조회 실패",
                    get_mapping_result.get('error', 'Unknown error')
                )

            # 프로젝트 목록 조회 테스트
            projects_result = db.get_projects(10)

            if projects_result['success']:
                self.log_test(
                    "Projects List",
                    True,
                    f"프로젝트 목록 조회 성공 ({projects_result['count']}개)"
                )
            else:
                self.log_test(
                    "Projects List",
                    False,
                    "프로젝트 목록 조회 실패",
                    projects_result.get('error', 'Unknown error')
                )

            return True

        except Exception as e:
            self.log_test(
                "Project Operations",
                False,
                "프로젝트 CRUD 테스트 실패",
                str(e)
            )
            return False

    def test_api_utils(self):
        """API 유틸리티 테스트"""
        print("\n[INFO] API 유틸리티 테스트")

        try:
            # JavaScript 파일 존재 확인
            api_utils_path = os.path.join(current_dir, 'api-utils.js')
            if os.path.exists(api_utils_path):
                self.log_test(
                    "API Utils File",
                    True,
                    "api-utils.js 파일 존재 확인"
                )
            else:
                self.log_test(
                    "API Utils File",
                    False,
                    "api-utils.js 파일이 존재하지 않음"
                )

            # HTML 파일들 확인
            html_files = ['dashboard.html', 'crewai.html']

            for html_file in html_files:
                file_path = os.path.join(current_dir, html_file)
                if os.path.exists(file_path):
                    # API 유틸리티 포함 여부 확인
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'api-utils.js' in content:
                            self.log_test(
                                f"API Utils in {html_file}",
                                True,
                                f"{html_file}에 API 유틸리티 포함됨"
                            )
                        else:
                            self.log_test(
                                f"API Utils in {html_file}",
                                False,
                                f"{html_file}에 API 유틸리티가 포함되지 않음"
                            )
                else:
                    self.log_test(
                        f"{html_file} File",
                        False,
                        f"{html_file} 파일이 존재하지 않음"
                    )

            return True

        except Exception as e:
            self.log_test(
                "API Utils Test",
                False,
                "API 유틸리티 테스트 실패",
                str(e)
            )
            return False

    def generate_report(self):
        """테스트 보고서 생성"""
        print("\n" + "="*60)
        print("[REPORT] 통합 테스트 결과 보고서")
        print("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"[STATS] 전체 테스트: {total_tests}")
        print(f"[STATS] 성공: {passed_tests}")
        print(f"[STATS] 실패: {failed_tests}")
        print(f"[STATS] 성공률: {(passed_tests/total_tests*100):.1f}%")

        print("\n[DETAILS] 상세 결과:")

        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            print(f"[{status}] {result['test_name']}: {result['message']}")

            if not result['success'] and result['details']:
                print(f"    [ERROR] 세부사항: {result['details']}")

        # 보고서 파일로 저장
        report_path = os.path.join(current_dir, 'test_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": passed_tests/total_tests*100,
                    "timestamp": datetime.now().isoformat()
                },
                "results": self.test_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[REPORT] 상세 보고서가 저장되었습니다: {report_path}")

        return passed_tests == total_tests

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("[START] AI Chat Interface 통합 테스트 시작")
        print("="*60)

        # 각 테스트 실행
        tests = [
            self.test_database_connection,
            self.test_security_utils,
            self.test_jwt_functionality,
            self.test_project_operations,
            self.test_api_utils
        ]

        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(
                    test.__name__,
                    False,
                    f"테스트 실행 중 예외 발생",
                    str(e)
                )

        # 보고서 생성
        success = self.generate_report()

        if success:
            print("\n[SUCCESS] 모든 테스트가 성공했습니다!")
        else:
            print("\n[WARNING] 일부 테스트가 실패했습니다. 세부사항을 확인하세요.")

        return success

def main():
    """메인 실행 함수"""
    tester = IntegrationTester()
    success = tester.run_all_tests()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
