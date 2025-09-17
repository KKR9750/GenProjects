#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Chat Interface 시작 스크립트
Flask 기반 통합 서버 실행
"""

import os
import sys
import io
import subprocess
import time

# Windows에서 한글 출력 문제 해결
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_dependencies():
    """필요한 종속성 확인"""
    try:
        import flask
        import flask_cors
        import requests
        print("모든 종속성이 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"종속성 누락: {e}")
        print("종속성을 설치합니다...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("종속성 설치 완료")
            return True
        except subprocess.CalledProcessError:
            print("종속성 설치 실패")
            return False

def main():
    """메인 실행 함수"""
    print("AI Chat Interface 시작 중...")

    # 종속성 확인
    if not check_dependencies():
        print("종속성 설치 실패로 인해 서버를 시작할 수 없습니다.")
        return

    # Flask 서버 시작
    try:
        from app import app
        print("Flask 서버 시작")
        app.run(host='0.0.0.0', port=3000, debug=True)
    except KeyboardInterrupt:
        print("\n서버가 중지되었습니다.")
    except Exception as e:
        print(f"서버 시작 실패: {e}")

if __name__ == '__main__':
    main()