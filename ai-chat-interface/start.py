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
import socket
import psutil

# Windows 및 전역 한글 출력 문제 해결 (강화된 UTF-8 지원)
def setup_korean_encoding():
    """한글 인코딩 환경 완전 설정"""
    import locale

    # 환경 변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    os.environ['PYTHONUTF8'] = '1'
    os.environ['LC_ALL'] = 'ko_KR.UTF-8'

    # Windows 특별 처리
    if sys.platform.startswith('win'):
        try:
            # 콘솔 코드페이지 UTF-8로 설정
            os.system('chcp 65001 > nul')
            os.environ['CHCP'] = '65001'
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
    else:
        # Unix 계열 시스템
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass

    # 로케일 설정 시도
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.65001')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass

    print("✅ 한글 인코딩 환경 설정 완료")
    print(f"🔤 한글 테스트: '한글 출력 테스트 성공'")

# 한글 인코딩 즉시 설정
setup_korean_encoding()

def check_port_available(port):
    """포트 사용 가능 여부 확인"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def find_process_using_port(port):
    """포트를 사용 중인 프로세스 찾기"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None

def prevent_duplicate_execution(port=3000):
    """중복 실행 방지"""
    if not check_port_available(port):
        print(f"⚠️  포트 {port}이 이미 사용 중입니다.")

        # 사용 중인 프로세스 찾기
        process = find_process_using_port(port)
        if process:
            try:
                cmdline = ' '.join(process.cmdline())
                if 'python' in process.name().lower() and ('start.py' in cmdline or 'app.py' in cmdline):
                    print(f"🔍 AI Chat Interface가 이미 실행 중입니다 (PID: {process.pid})")
                    print(f"📍 URL: http://localhost:{port}")
                    print(f"💡 기존 프로세스를 종료하려면: taskkill /F /PID {process.pid}")

                    # 사용자 선택
                    while True:
                        choice = input("\n선택하세요 (k: 기존 프로세스 종료 후 실행, s: 건너뛰기, q: 종료): ").lower()
                        if choice == 'k':
                            try:
                                process.terminate()
                                time.sleep(2)
                                if process.is_running():
                                    process.kill()
                                print("✅ 기존 프로세스를 종료했습니다.")
                                return True
                            except Exception as e:
                                print(f"❌ 프로세스 종료 실패: {e}")
                                return False
                        elif choice == 's':
                            print("🚀 브라우저에서 기존 서버에 접속하세요.")
                            try:
                                import webbrowser
                                webbrowser.open(f'http://localhost:{port}')
                            except:
                                pass
                            return False
                        elif choice == 'q':
                            return False
                        else:
                            print("올바른 선택지를 입력하세요: k, s, q")
                else:
                    print(f"🔍 다른 프로그램이 포트 {port}을 사용 중입니다: {process.name()}")
                    print(f"💡 해당 프로세스를 종료하고 다시 시도하세요 (PID: {process.pid})")
                    return False
            except Exception as e:
                print(f"❌ 프로세스 정보 확인 실패: {e}")
                return False
        else:
            print(f"🔍 포트 {port}을 사용하는 프로세스를 찾을 수 없습니다.")
            return False

    return True

def check_dependencies():
    """필요한 종속성 확인"""
    try:
        import flask
        import flask_cors
        import requests
        import psutil
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

    # 중복 실행 방지 확인
    if not prevent_duplicate_execution(3000):
        print("프로그램을 종료합니다.")
        return

    # 종속성 확인
    if not check_dependencies():
        print("종속성 설치 실패로 인해 서버를 시작할 수 없습니다.")
        return

    # Flask 서버 시작
    try:
        from app import app, socketio # 메인 앱과 socketio 인스턴스 가져오기
        from flask_socketio import join_room, leave_room

        # CrewAI 블루프린트 등록
        # 경로 문제를 피하기 위해 CrewAI 플랫폼 폴더를 sys.path에 추가
        crewai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'CrewAi', 'crewai_platform'))
        if crewai_path not in sys.path:
            sys.path.insert(0, crewai_path)
        from server import crewai_bp
        app.register_blueprint(crewai_bp)

        # CrewAI 실행을 위한 WebSocket 네임스페이스 핸들러 추가
        @socketio.on('join', namespace='/execution')
        def on_join(data):
            room = data['room']
            join_room(room)
            print(f"SocketIO client joined room: {room}")

        print("Flask-SocketIO 서버 시작")
        print("CrewAI Platform이 '/crewai' 경로에 통합되었습니다.")
        socketio.run(
            app,
            host='0.0.0.0',
            port=3000,
            debug=True,
            allow_unsafe_werkzeug=True # debug 모드에서 안정적인 실행을 위해 추가
        )
    except KeyboardInterrupt:
        print("\n서버가 중지되었습니다.")
    except Exception as e:
        print(f"서버 시작 실패: {e}")

if __name__ == '__main__':
    main()