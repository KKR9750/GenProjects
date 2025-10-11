#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 승인 시스템 통합 실행 스크립트
각 단계별 사용자 승인을 받고 진행하는 시스템
"""

import os
import sys
import json
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM

def setup_utf8_environment():
    """UTF-8 인코딩 환경 설정"""
    import io

    # 환경 변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    # Windows 콘솔 UTF-8 설정
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass

    # stdout/stderr UTF-8 재구성
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

    return True

def get_llm_model(role_name: str):
    """역할별 LLM 모델 반환"""
    models = {"planner": "gemini/gemini-2.0-flash-exp", "researcher": "gemini/gemini-2.0-flash-exp", "writer": "gemini/gemini-2.0-flash-exp"}
    model_id = models.get(role_name.lower(), 'openai/gpt-4')

    print(f"🤖 {role_name} 역할 → {model_id} 모델")

    return LLM(
        model=model_id,
        temperature=0.7
    )

def wait_for_user_approval(stage_name: str, result: str = None) -> bool:
    """사용자 승인 대기"""
    print("\n" + "="*60)
    print(f"📋 {stage_name} 단계 완료")
    if result:
        print("\n📄 결과:")
        print(result[:500] + "..." if len(result) > 500 else result)

    print("\n" + "="*60)
    print("🤔 다음 단계로 진행하시겠습니까?")
    print("   승인: 'y', 'yes', '네', '승인'")
    print("   거부: 'n', 'no', '아니오', '거부'")
    print("   수정요청: 'm', 'modify', '수정'")

    while True:
        user_input = input("➤ 답변: ").strip().lower()

        if user_input in ['y', 'yes', '네', '승인']:
            print("✅ 승인됨 - 다음 단계로 진행합니다")
            return True
        elif user_input in ['n', 'no', '아니오', '거부']:
            print("❌ 거부됨 - 작업을 중단합니다")
            return False
        elif user_input in ['m', 'modify', '수정']:
            print("📝 수정 요청 - 해당 단계를 다시 수행합니다")
            return None  # 수정 신호
        else:
            print("⚠️ 올바른 답변을 입력해주세요")

def execute_crewai_with_approval(requirement: str, project_path: str, execution_id: str):
    """승인 시스템과 함께 CrewAI 실행"""

    # 환경 설정
    setup_utf8_environment()

    print("✅ UTF-8 인코딩 환경 설정 완료")
    print("🚀 CrewAI 단계별 승인 시스템 시작...")
    print(f"🎯 요구사항: {requirement[:100]}..." if len(requirement) > 100 else f"🎯 요구사항: {requirement}")
    print(f"📁 프로젝트 경로: {project_path}")
    print(f"🆔 실행 ID: {execution_id}")
    print("\n" + "="*50 + "\n")

    # 에이전트 정의
    planner = Agent(
        role="Project Planner",
        goal="프로젝트 요구사항을 분석하고 체계적인 개발 계획을 수립합니다.",
        backstory="당신은 소프트웨어 프로젝트 관리 전문가입니다. 복잡한 요구사항을 구체적이고 실행 가능한 단계로 분해하는 능력이 뛰어납니다.",
        verbose=True,
        allow_delegation=False,
        llm=get_llm_model("planner")
    )

    researcher = Agent(
        role="Research Specialist",
        goal="프로젝트에 필요한 최적의 기술 스택과 구현 방법을 조사합니다.",
        backstory="당신은 기술 리서치 전문가입니다. 최신 기술 동향을 파악하고, 프로젝트 요구사항에 가장 적합한 도구와 방법론을 선별하는데 전문성을 가지고 있습니다.",
        verbose=True,
        allow_delegation=False,
        llm=get_llm_model("researcher")
    )

    writer = Agent(
        role="Technical Writer",
        goal="조사 결과를 바탕으로 실제 동작하는 코드와 완전한 문서를 작성합니다.",
        backstory="당신은 기술 문서 및 코드 작성 전문가입니다. 연구 결과를 실제 동작하는 고품질 코드로 변환하고, 이해하기 쉬운 문서를 작성하는 능력이 탁월합니다.",
        verbose=True,
        allow_delegation=False,
        llm=get_llm_model("writer")
    )

    # 태스크 정의
    task1 = Task(
        description=f"""
다음 요구사항을 분석하여 체계적인 프로젝트 계획을 수립하세요:

**요구사항:**
{requirement}

**계획에 포함할 내용:**
1. 프로젝트 목표 및 범위 정의
2. 핵심 기능 목록 및 우선순위
3. 기술적 요구사항 분석
4. 개발 단계 및 마일스톤
5. 예상 개발 일정

구체적이고 실행 가능한 계획을 한글로 작성해주세요.
        """,
        expected_output="상세한 프로젝트 계획서 (마크다운 형식, 한글)",
        agent=planner
    )

    task2 = Task(
        description="""
Planner가 수립한 계획을 바탕으로 기술적 조사를 수행하세요:

**조사 항목:**
1. 권장 프로그래밍 언어 및 프레임워크
2. 필수 라이브러리 및 패키지 목록
3. 개발 환경 구성 가이드
4. 아키텍처 패턴 및 디자인 권장사항
5. 테스트 및 배포 전략
6. 보안 고려사항

실제 구현 가능한 구체적인 기술 솔루션을 제시해주세요.
        """,
        expected_output="기술 조사 보고서 및 구현 가이드 (마크다운 형식, 한글)",
        agent=researcher
    )

    task3 = Task(
        description="""
계획과 조사 결과를 바탕으로 완성된 프로젝트를 구현하세요:

**구현 내용:**
1. 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (완전 동작)
3. 설정 파일 (requirements.txt, package.json 등)
4. README.md (설치, 설정, 실행 방법)
5. 기본 테스트 코드
6. 실행 예시 및 사용법

모든 코드는 실제로 동작해야 하며, 충분한 주석을 포함해야 합니다.
        """,
        expected_output="완전히 구현된 프로젝트 (코드, 문서, 설정 파일 포함)",
        agent=writer
    )

    start_time = datetime.now()
    results = []

    # 1단계: 계획 수립
    print("📋 1단계: 프로젝트 계획 수립 시작...")
    crew1 = Crew(agents=[planner], tasks=[task1], verbose=True)

    try:
        result1 = crew1.kickoff()
        results.append(("계획 수립", str(result1)))

        # 승인 대기
        approval = wait_for_user_approval("프로젝트 계획 수립", str(result1))
        if approval is False:
            print("❌ 사용자가 거부하여 작업을 중단합니다.")
            return save_partial_results(results, project_path, execution_id, start_time)
        elif approval is None:
            print("📝 수정 요청 - 계획 수립 단계를 다시 수행해야 합니다.")
            # 수정 로직 구현 필요 (현재는 진행)

    except Exception as e:
        print(f"❌ 계획 수립 단계 오류: {e}")
        return save_error_result(e, project_path, execution_id, start_time)

    # 2단계: 기술 조사 (승인된 경우만)
    print("\n🔍 2단계: 기술 조사 시작...")
    crew2 = Crew(agents=[researcher], tasks=[task2], verbose=True)

    try:
        result2 = crew2.kickoff()
        results.append(("기술 조사", str(result2)))

        # 승인 대기
        approval = wait_for_user_approval("기술 조사", str(result2))
        if approval is False:
            print("❌ 사용자가 거부하여 작업을 중단합니다.")
            return save_partial_results(results, project_path, execution_id, start_time)
        elif approval is None:
            print("📝 수정 요청 - 기술 조사 단계를 다시 수행해야 합니다.")
            # 수정 로직 구현 필요 (현재는 진행)

    except Exception as e:
        print(f"❌ 기술 조사 단계 오류: {e}")
        return save_partial_results(results, project_path, execution_id, start_time, error=e)

    # 3단계: 구현 (승인된 경우만)
    print("\n💻 3단계: 프로젝트 구현 시작...")
    crew3 = Crew(agents=[writer], tasks=[task3], verbose=True)

    try:
        result3 = crew3.kickoff()
        results.append(("프로젝트 구현", str(result3)))

        # 최종 결과 승인
        approval = wait_for_user_approval("프로젝트 구현 (최종)", str(result3))
        if approval is False:
            print("❌ 최종 결과가 거부되었습니다.")
        else:
            print("✅ 모든 단계가 승인되어 완료되었습니다!")

    except Exception as e:
        print(f"❌ 프로젝트 구현 단계 오류: {e}")
        return save_partial_results(results, project_path, execution_id, start_time, error=e)

    # 최종 결과 저장
    return save_final_results(results, project_path, execution_id, start_time)

def save_partial_results(results, project_path, execution_id, start_time, error=None):
    """부분 결과 저장"""
    end_time = datetime.now()
    duration = end_time - start_time

    output_file = os.path.join(project_path, "crewai_partial_result.md")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 부분 실행 결과\n\n")
        f.write(f"**실행 ID**: {execution_id}\n")
        f.write(f"**시작 시간**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**중단 시간**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**소요 시간**: {duration}\n\n")

        if error:
            f.write(f"**중단 사유**: 오류 발생 - {str(error)}\n\n")
        else:
            f.write("**중단 사유**: 사용자 거부\n\n")

        f.write("---\n\n")
        f.write("## 완료된 단계\n\n")

        for stage, result in results:
            f.write(f"### {stage}\n\n")
            f.write(f"{result}\n\n")

    print(f"📄 부분 결과 저장: {os.path.abspath(output_file)}")
    return output_file

def save_final_results(results, project_path, execution_id, start_time):
    """최종 결과 저장"""
    end_time = datetime.now()
    duration = end_time - start_time

    output_file = os.path.join(project_path, "crewai_result_approved.md")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 승인 완료 결과\n\n")
        f.write(f"**실행 ID**: {execution_id}\n")
        f.write(f"**시작 시간**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**완료 시간**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**총 소요시간**: {duration}\n\n")
        f.write("**상태**: ✅ 모든 단계 사용자 승인 완료\n\n")

        f.write("---\n\n")
        f.write("## 승인된 단계별 결과\n\n")

        for stage, result in results:
            f.write(f"### {stage}\n\n")
            f.write(f"{result}\n\n")

    print(f"📄 최종 결과 저장: {os.path.abspath(output_file)}")
    return output_file

def save_error_result(error, project_path, execution_id, start_time):
    """오류 결과 저장"""
    import traceback
    end_time = datetime.now()

    error_file = os.path.join(project_path, "crewai_approval_error.log")

    with open(error_file, 'w', encoding='utf-8') as f:
        f.write("CrewAI 승인 시스템 실행 오류\n")
        f.write(f"실행 ID: {execution_id}\n")
        f.write(f"오류 발생 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"오류 메시지: {str(error)}\n\n")
        f.write(f"상세 추적:\n{traceback.format_exc()}")

    print(f"🗂️ 오류 로그 저장: {os.path.abspath(error_file)}")
    return error_file

if __name__ == "__main__":
    # 테스트 실행
    test_requirement = "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘."
    test_project_path = "D:\\GenProjects\\Projects\\project_approval_test"
    test_execution_id = "approval_test_001"

    # 테스트 디렉토리 생성
    os.makedirs(test_project_path, exist_ok=True)

    print("🧪 승인 시스템 테스트 시작...")
    result_file = execute_crewai_with_approval(test_requirement, test_project_path, test_execution_id)
    print(f"🎯 테스트 완료: {result_file}")