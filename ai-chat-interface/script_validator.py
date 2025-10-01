#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 스크립트 검증 시스템
생성된 스크립트의 문법, Import, 환경변수 등을 검증합니다.
"""

import os
import ast
import sys
from typing import Dict, List, Optional
from datetime import datetime


class ScriptValidator:
    """생성된 CrewAI 스크립트 검증 클래스"""

    def __init__(self, script_path: str):
        """
        Args:
            script_path: 검증할 Python 스크립트 파일 경로
        """
        self.script_path = script_path
        self.script_content = None
        self.validation_results = {
            'overall_valid': True,
            'checks': [],
            'errors': [],
            'warnings': [],
            'validated_at': datetime.now().isoformat()
        }

    def _read_script(self) -> bool:
        """스크립트 파일 읽기"""
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                self.script_content = f.read()
            return True
        except Exception as e:
            self.validation_results['overall_valid'] = False
            self.validation_results['errors'].append({
                'level': 'file_read',
                'error': str(e),
                'message': f'파일을 읽을 수 없습니다: {e}'
            })
            return False

    def validate_syntax(self) -> Dict:
        """
        Python 문법 검증

        Returns:
            dict: {
                'valid': bool,
                'level': 'syntax',
                'message': str,
                'line': int (오류 시),
                'error': str (오류 시)
            }
        """
        if self.script_content is None:
            if not self._read_script():
                return self.validation_results['errors'][0]

        try:
            # compile() 함수로 바이트코드 컴파일 시도
            compile(self.script_content, self.script_path, 'exec')

            result = {
                'valid': True,
                'level': 'syntax',
                'message': '✅ 문법 검증 통과'
            }
            self.validation_results['checks'].append(result)
            return result

        except SyntaxError as e:
            result = {
                'valid': False,
                'level': 'syntax',
                'error': str(e),
                'line': e.lineno,
                'offset': e.offset,
                'text': e.text.strip() if e.text else '',
                'message': f'❌ Line {e.lineno}: {e.msg}'
            }
            self.validation_results['overall_valid'] = False
            self.validation_results['errors'].append(result)
            self.validation_results['checks'].append(result)
            return result

        except Exception as e:
            result = {
                'valid': False,
                'level': 'syntax',
                'error': str(e),
                'message': f'❌ 예상치 못한 오류: {e}'
            }
            self.validation_results['overall_valid'] = False
            self.validation_results['errors'].append(result)
            self.validation_results['checks'].append(result)
            return result

    def validate_imports(self) -> Dict:
        """
        Import 문 검증 (필수 라이브러리 설치 여부)

        Returns:
            dict: {
                'valid': bool,
                'level': 'imports',
                'missing_modules': List[str],
                'message': str
            }
        """
        if self.script_content is None:
            if not self._read_script():
                return self.validation_results['errors'][0]

        try:
            tree = ast.parse(self.script_content)
        except SyntaxError:
            # 문법 오류가 있으면 import 검증 불가
            result = {
                'valid': False,
                'level': 'imports',
                'message': '⚠️ 문법 오류로 인해 Import 검증 불가',
                'skipped': True
            }
            self.validation_results['checks'].append(result)
            return result

        # Import 문 추출
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # 필수 모듈 확인
        missing_modules = []
        for module in imports:
            # 하위 모듈은 최상위 모듈만 확인
            top_module = module.split('.')[0]
            try:
                __import__(top_module)
            except ImportError:
                missing_modules.append(module)

        if missing_modules:
            result = {
                'valid': False,
                'level': 'imports',
                'missing_modules': missing_modules,
                'message': f'⚠️ 설치되지 않은 모듈: {", ".join(missing_modules)}'
            }
            self.validation_results['warnings'].append(result)
        else:
            result = {
                'valid': True,
                'level': 'imports',
                'missing_modules': [],
                'message': '✅ Import 검증 통과'
            }

        self.validation_results['checks'].append(result)
        return result

    def validate_environment(self) -> Dict:
        """
        환경변수 검증 (API 키 등)

        Returns:
            dict: {
                'valid': bool,
                'level': 'environment',
                'missing_keys': List[str],
                'message': str
            }
        """
        # 일반적으로 필요한 API 키들
        common_keys = [
            'GOOGLE_API_KEY',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'DEEPSEEK_API_KEY'
        ]

        missing_keys = []
        for key in common_keys:
            if not os.getenv(key):
                missing_keys.append(key)

        if missing_keys:
            result = {
                'valid': True,  # 경고만, 실패는 아님
                'level': 'environment',
                'missing_keys': missing_keys,
                'message': f'⚠️ 미설정 환경변수: {", ".join(missing_keys)}'
            }
            self.validation_results['warnings'].append(result)
        else:
            result = {
                'valid': True,
                'level': 'environment',
                'missing_keys': [],
                'message': '✅ 환경변수 검증 통과'
            }

        self.validation_results['checks'].append(result)
        return result

    def validate_all(self, quick_mode: bool = True) -> Dict:
        """
        모든 검증 수행

        Args:
            quick_mode: True이면 문법 오류 발견 시 즉시 중단

        Returns:
            dict: 전체 검증 결과
        """
        # 1. 문법 검증 (가장 중요)
        syntax_result = self.validate_syntax()

        if not syntax_result['valid'] and quick_mode:
            # 문법 오류 발견 시 즉시 중단
            return self.validation_results

        # 2. Import 검증 (문법 통과 시에만)
        if syntax_result['valid']:
            self.validate_imports()

            # 3. 환경변수 검증
            self.validate_environment()

        return self.validation_results

    def get_summary(self) -> str:
        """검증 결과 요약 문자열 생성"""
        results = self.validation_results

        summary_lines = [
            f"📋 스크립트 검증 결과: {os.path.basename(self.script_path)}",
            f"{'='*60}"
        ]

        if results['overall_valid']:
            summary_lines.append("✅ 전체 검증 통과")
        else:
            summary_lines.append("❌ 검증 실패")

        # 개별 검증 결과
        for check in results['checks']:
            summary_lines.append(f"  {check['message']}")

        # 경고 사항
        if results['warnings']:
            summary_lines.append("\n⚠️ 경고:")
            for warning in results['warnings']:
                summary_lines.append(f"  - {warning['message']}")

        # 오류 상세
        if results['errors']:
            summary_lines.append("\n❌ 오류:")
            for error in results['errors']:
                summary_lines.append(f"  - {error['message']}")
                if 'line' in error:
                    summary_lines.append(f"    위치: Line {error['line']}")
                    if 'text' in error and error['text']:
                        summary_lines.append(f"    코드: {error['text']}")

        summary_lines.append(f"{'='*60}")

        return '\n'.join(summary_lines)


def validate_script_file(script_path: str, quick_mode: bool = True) -> Dict:
    """
    스크립트 파일 검증 (편의 함수)

    Args:
        script_path: 검증할 스크립트 파일 경로
        quick_mode: 문법 오류 시 즉시 중단 여부

    Returns:
        dict: 검증 결과
    """
    validator = ScriptValidator(script_path)
    return validator.validate_all(quick_mode=quick_mode)


if __name__ == '__main__':
    # UTF-8 출력 설정
    if sys.platform.startswith('win'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 테스트 코드
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        validator = ScriptValidator(script_path)
        results = validator.validate_all(quick_mode=False)

        print(validator.get_summary())

        sys.exit(0 if results['overall_valid'] else 1)
    else:
        print("사용법: python script_validator.py <script_path>")
        sys.exit(1)