#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
한글 요청 완전 처리 테스트
주식 투자 분석 보고서 생성 테스트
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

# UTF-8 인코딩 설정
def setup_encoding():
    import io
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    os.environ['PYTHONUTF8'] = '1'

    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul')
        except:
            pass

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

setup_encoding()

def test_korean_crewai_request():
    """한글 CrewAI 요청 테스트"""
    print("🚀 한글 CrewAI 요청 테스트 시작...")
    print("=" * 60)

    # 서버 상태 확인
    print("\n🔍 1. 서버 상태 확인")
    try:
        health_response = requests.get('http://localhost:3000/api/health', timeout=5)
        print(f"   서버 상태: {health_response.status_code}")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   데이터베이스: {health_data.get('database', {}).get('message', 'Unknown')}")
        else:
            print("   ❌ 서버가 응답하지 않습니다.")
            return False
    except Exception as e:
        print(f"   ❌ 서버 연결 실패: {e}")
        return False

    # CrewAI 요청 준비
    print("\n📝 2. CrewAI 요청 준비")
    korean_request = {
        "requirement": "삼성전자와 애플 주식의 최근 3개월 성과를 분석하고 향후 6개월 투자 전망을 제시하는 상세한 보고서를 작성해주세요. 기술적 분석, 재무 분석, 시장 동향을 포함하여 한국어로 작성해주세요.",
        "selectedModels": {
            "planner": "gpt-4",
            "researcher": "gpt-4",
            "writer": "gpt-4"
        }
    }

    print(f"   요청 내용: {korean_request['requirement'][:50]}...")
    print(f"   선택된 모델: {korean_request['selectedModels']}")

    # CrewAI 요청 전송
    print("\n🎯 3. CrewAI 요청 전송")
    try:
        response = requests.post(
            'http://localhost:3000/api/crewai',
            json=korean_request,
            headers={
                'Content-Type': 'application/json; charset=utf-8'
            },
            timeout=30
        )

        print(f"   응답 상태 코드: {response.status_code}")
        print(f"   응답 헤더: {dict(response.headers)}")

        if response.status_code == 200:
            response_data = response.json()
            print("   ✅ 요청 성공!")

            # 응답 내용 분석
            print("\n📊 4. 응답 내용 분석")
            if 'execution_id' in response_data:
                print(f"   실행 ID: {response_data['execution_id']}")
            if 'project_path' in response_data:
                print(f"   프로젝트 경로: {response_data['project_path']}")
            if 'result' in response_data:
                print(f"   결과 메시지: {response_data['result'][:100]}...")
            if 'files_created' in response_data:
                print(f"   생성된 파일: {response_data['files_created']}")

            # 프로젝트 디렉토리 확인
            if 'project_path' in response_data:
                project_path = response_data['project_path']
                print(f"\n📁 5. 생성된 프로젝트 확인: {project_path}")

                if os.path.exists(project_path):
                    print("   ✅ 프로젝트 디렉토리 존재")

                    # 파일 목록 확인
                    files = os.listdir(project_path)
                    print(f"   파일 개수: {len(files)}")
                    for file in files:
                        file_path = os.path.join(project_path, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            print(f"     📄 {file} ({size} bytes)")

                    # 한글 파일 내용 확인
                    for file in files:
                        if file.endswith(('.py', '.md', '.txt')):
                            file_path = os.path.join(project_path, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read(500)  # 처음 500자만
                                    korean_chars = sum(1 for c in content if ord(c) > 127)
                                    print(f"     🔤 {file}: 한글 문자 {korean_chars}개 포함")
                                    if '한글' in content or 'CrewAI' in content:
                                        print(f"       ✅ 한글 텍스트 올바르게 저장됨")
                            except Exception as e:
                                print(f"     ❌ {file} 읽기 실패: {e}")
                else:
                    print("   ❌ 프로젝트 디렉토리가 존재하지 않음")

            return True
        else:
            print(f"   ❌ 요청 실패: {response.status_code}")
            print(f"   오류 내용: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("   ⏱️ 요청 시간 초과 (30초)")
        return False
    except Exception as e:
        print(f"   ❌ 요청 실패: {e}")
        return False

def wait_for_execution_completion(execution_id, max_wait=60):
    """실행 완료 대기"""
    print(f"\n⏳ 실행 완료 대기 (최대 {max_wait}초)...")

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            # 실행 상태 확인 (만약 API가 있다면)
            time.sleep(5)
            print(f"   📊 대기 중... ({int(time.time() - start_time)}초 경과)")

            # 여기서 실제로는 로그 파일이나 상태 API를 확인할 수 있음

        except KeyboardInterrupt:
            print("\n   ⚠️ 사용자가 중단했습니다.")
            break
        except Exception as e:
            print(f"   ⚠️ 상태 확인 중 오류: {e}")
            break

    print("   ⏰ 대기 시간 종료")

if __name__ == '__main__':
    print("🧪 한글 요청 완전 처리 테스트")
    print("📋 주식 투자 분석 보고서 생성 테스트")
    print("=" * 60)

    success = test_korean_crewai_request()

    if success:
        print("\n🎉 테스트 성공!")
        print("💡 CrewAI가 백그라운드에서 실행 중입니다.")
        print("🔍 생성된 프로젝트 디렉토리에서 결과를 확인하세요.")
    else:
        print("\n❌ 테스트 실패!")
        print("🔧 서버 상태와 설정을 확인하세요.")

    print("\n🏁 테스트 완료")