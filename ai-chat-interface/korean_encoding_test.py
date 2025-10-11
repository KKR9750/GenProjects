#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 인코딩 전체 파이프라인 테스트
모든 UTF-8 설정이 올바르게 작동하는지 검증
"""

import os
import sys
import subprocess
import tempfile
import json
from datetime import datetime
import io
import locale

# UTF-8 인코딩 즉시 설정 (한글 출력 오류 방지)
def setup_encoding():
    # 환경 변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    os.environ['PYTHONUTF8'] = '1'

    # Windows 콘솔 UTF-8 설정
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul')
        except:
            pass

    # stdout/stderr UTF-8 재구성
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 인코딩 설정 즉시 실행
setup_encoding()

def test_korean_encoding():
    """한글 인코딩 종합 테스트"""
    print("🔍 한글 인코딩 테스트 시작...")
    print("=" * 60)

    results = {}

    # 1. 기본 환경 변수 확인
    print("\n📋 1. 환경 변수 확인")
    env_vars = ['PYTHONIOENCODING', 'PYTHONLEGACYWINDOWSSTDIO', 'PYTHONUTF8', 'LC_ALL', 'CHCP']
    for var in env_vars:
        value = os.environ.get(var, 'Not Set')
        print(f"   {var}: {value}")
        results[f'env_{var}'] = value

    # 2. 콘솔 출력 테스트
    print("\n🖥️ 2. 콘솔 출력 테스트")
    test_strings = [
        "한글 테스트 문자열",
        "CrewAI 프로젝트 생성",
        "주식 투자 분석 보고서",
        "특수문자: ①②③④⑤ ★☆♠♥♦♣",
        "이모지: 🚀🎯📊💡🔍✍️"
    ]

    for i, test_str in enumerate(test_strings):
        try:
            print(f"   테스트 {i+1}: {test_str}")
            results[f'console_test_{i+1}'] = True
        except Exception as e:
            print(f"   테스트 {i+1}: 실패 - {e}")
            results[f'console_test_{i+1}'] = False

    # 3. 파일 입출력 테스트
    print("\n📄 3. 파일 입출력 테스트")
    temp_dir = tempfile.mkdtemp(prefix='korean_test_')
    test_files = {
        'test_korean.txt': "한글 파일 테스트\n프로젝트: CrewAI 분석\n결과: 성공적으로 한글이 저장됨",
        'test_json.json': json.dumps({
            "프로젝트명": "CrewAI 테스트",
            "상태": "진행중",
            "결과": ["성공", "한글처리완료", "UTF-8지원"]
        }, ensure_ascii=False, indent=2),
        'test_markdown.md': """# 한글 마크다운 테스트

## 프로젝트 개요
- **이름**: CrewAI 한글 지원 테스트
- **목적**: UTF-8 인코딩 검증
- **결과**: 성공적으로 한글이 표시됨

### 특수 문자
★☆♠♥♦♣ ①②③④⑤

### 이모지
🚀🎯📊💡🔍✍️
"""
    }

    for filename, content in test_files.items():
        try:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)

            # 파일 읽기 테스트
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                read_content = f.read()

            success = content == read_content
            print(f"   {filename}: {'✅ 성공' if success else '❌ 실패'}")
            results[f'file_test_{filename}'] = success

        except Exception as e:
            print(f"   {filename}: ❌ 실패 - {e}")
            results[f'file_test_{filename}'] = False

    # 4. 서브프로세스 테스트 (Python 스크립트 실행)
    print("\n🔄 4. 서브프로세스 한글 처리 테스트")
    test_script = os.path.join(temp_dir, 'subprocess_test.py')
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("한글 서브프로세스 테스트 성공")
print("프로젝트: CrewAI")
print("결과: UTF-8 지원 완료")
'''

    try:
        with open(test_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 강화된 환경 변수로 서브프로세스 실행
        env = os.environ.copy()
        env.update({
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONLEGACYWINDOWSSTDIO': '0',
            'PYTHONUTF8': '1'
        })

        if sys.platform.startswith('win'):
            cmd = [sys.executable, '-X', 'utf8', test_script]
        else:
            cmd = [sys.executable, test_script]

        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        success = result.returncode == 0 and '한글' in result.stdout
        print(f"   서브프로세스 실행: {'✅ 성공' if success else '❌ 실패'}")
        if result.stdout:
            print(f"   출력: {result.stdout.strip()}")
        if result.stderr:
            print(f"   오류: {result.stderr.strip()}")

        results['subprocess_test'] = success

    except Exception as e:
        print(f"   서브프로세스 실행: ❌ 실패 - {e}")
        results['subprocess_test'] = False

    # 5. 시스템 정보
    print("\n🖥️ 5. 시스템 정보")
    import locale
    import platform

    system_info = {
        'platform': platform.platform(),
        'python_version': sys.version,
        'encoding_default': sys.getdefaultencoding(),
        'filesystem_encoding': sys.getfilesystemencoding(),
        'locale': locale.getlocale(),
        'preferred_encoding': locale.getpreferredencoding()
    }

    for key, value in system_info.items():
        print(f"   {key}: {value}")
        results[f'system_{key}'] = str(value)

    # 결과 요약
    print("\n" + "=" * 60)
    print("🎯 테스트 결과 요약")
    print("=" * 60)

    total_tests = len([k for k in results.keys() if k.startswith(('console_test_', 'file_test_', 'subprocess_test'))])
    passed_tests = len([k for k, v in results.items() if k.startswith(('console_test_', 'file_test_', 'subprocess_test')) and v])

    print(f"📊 총 테스트: {total_tests}")
    print(f"✅ 성공: {passed_tests}")
    print(f"❌ 실패: {total_tests - passed_tests}")
    print(f"📈 성공률: {(passed_tests/total_tests)*100:.1f}%")

    # 결과 파일 저장
    results_file = os.path.join(temp_dir, 'korean_encoding_test_results.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'results': results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 상세 결과가 저장되었습니다: {results_file}")

    # 임시 디렉토리 정보
    print(f"🗂️ 테스트 파일 경로: {temp_dir}")

    # 전체 성공 여부 반환
    return passed_tests == total_tests

if __name__ == '__main__':
    success = test_korean_encoding()
    print(f"\n🏁 전체 테스트 {'✅ 성공' if success else '❌ 실패'}")
    sys.exit(0 if success else 1)