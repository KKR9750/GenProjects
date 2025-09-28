#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 CrewAI 실행기
- 단계별 승인 시스템
- 작업 중단/재개 지원
- 요구사항 보존
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

# 프로젝트 상태 관리자 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from project_state_manager import ProjectStateManager, ProjectStatus, AgentStatus

# UTF-8 인코딩 보장
import locale
import io

# 환경 변수 강제 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'

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

print("✅ UTF-8 인코딩 환경 설정 완료")

class EnhancedCrewAIExecutor:
    """강화된 CrewAI 실행기"""

    def __init__(self, project_path: str, original_requirements: str,
                 project_name: str = "", description: str = ""):
        self.project_path = project_path
        self.original_requirements = original_requirements
        self.project_name = project_name
        self.description = description

        # 프로젝트 상태 관리자 초기화
        self.state_manager = ProjectStateManager(project_path)

        # 결과 파일 경로
        self.planner_result_file = os.path.join(project_path, "planner_result.md")
        self.researcher_result_file = os.path.join(project_path, "researcher_result.md")
        self.writer_result_file = os.path.join(project_path, "writer_result.md")
        self.final_result_file = os.path.join(project_path, "final_result.md")

    def initialize_project(self):
        """프로젝트 초기화"""
        print("📋 프로젝트 초기화 중...")

        # 요구사항 저장
        self.state_manager.save_original_requirements(self.original_requirements, {
            "project_name": self.project_name,
            "description": self.description
        })

        # 프로젝트 상태 초기화
        self.state_manager.initialize_project_status(self.project_name, self.description)

        print(f"✅ 프로젝트 '{self.project_name}' 초기화 완료")
        print(f"📁 프로젝트 경로: {self.project_path}")

    def get_llm_model(self, role_name: str) -> ChatOpenAI:
        """LLM 모델 반환"""
        models = {
            'planner': 'gpt-4',
            'researcher': 'gpt-4',
            'writer': 'gpt-4'
        }
        model_id = models.get(role_name.lower(), 'gpt-4')
        print(f"🤖 {role_name} 역할 LLM: {model_id}")

        return ChatOpenAI(
            model=model_id,
            temperature=0.7,
            max_tokens=3000
        )

    def create_agents(self) -> Dict[str, Agent]:
        """에이전트 생성"""
        print("👥 에이전트 생성 중...")

        agents = {}

        # Planner 에이전트
        agents['planner'] = Agent(
            role="Project Planner",
            goal="사용자 요구사항을 분석하고 체계적인 실행 계획을 수립",
            backstory="당신은 프로젝트 관리 전문가로, 복잡한 요구사항을 실행 가능한 단계로 나누어 정리하는 데 능숙합니다. 사용자의 승인을 받을 수 있도록 명확하고 구체적인 계획을 작성합니다.",
            verbose=True,
            allow_delegation=False,
            llm=self.get_llm_model("planner")
        )

        # Researcher 에이전트
        agents['researcher'] = Agent(
            role="Research Specialist",
            goal="프로젝트 실행에 필요한 기술, 도구, 방법론을 조사",
            backstory="당신은 기술 조사 전문가로, 최신 도구와 방법론을 연구하여 프로젝트에 최적의 솔루션을 제안합니다. Planner의 계획을 바탕으로 실제 구현 방법을 연구합니다.",
            verbose=True,
            allow_delegation=False,
            llm=self.get_llm_model("researcher")
        )

        # Writer 에이전트
        agents['writer'] = Agent(
            role="Technical Implementation Specialist",
            goal="계획과 연구 결과를 바탕으로 실제 코드와 문서를 작성",
            backstory="당신은 기술 구현 전문가로, 계획과 연구 결과를 실제 동작하는 코드와 문서로 변환할 수 있습니다. 모든 코드는 실행 가능하고 완성도 높은 상태여야 합니다.",
            verbose=True,
            allow_delegation=False,
            llm=self.get_llm_model("writer")
        )

        print("✅ 에이전트 생성 완료")
        return agents

    def create_planner_task(self, agents: Dict[str, Agent]) -> Task:
        """Planner 태스크 생성"""
        return Task(
            description=f"""
            다음 요구사항을 분석하고 체계적인 실행 계획을 수립하세요:

            === 원본 요구사항 ===
            {self.original_requirements}

            다음 사항들을 포함한 상세한 계획을 작성하세요:
            1. 요구사항 분석 및 핵심 목표 정리
            2. 주요 기능 및 구성요소 식별
            3. 필요한 기술 스택 및 도구 예상
            4. 구체적인 구현 단계 (순서별)
            5. 예상 산출물 및 결과물
            6. 리스크 요소 및 고려사항

            **중요**: 이 계획은 사용자의 승인을 받을 예정이므로, 명확하고 이해하기 쉽게 작성해주세요.
            """,
            expected_output="구체적이고 실행 가능한 프로젝트 계획서 (한글로 작성)",
            agent=agents['planner']
        )

    def create_researcher_task(self, agents: Dict[str, Agent]) -> Task:
        """Researcher 태스크 생성"""
        return Task(
            description=f"""
            승인된 Planner의 계획을 바탕으로 다음 사항들을 상세히 조사하세요:

            1. 추천 기술 스택 및 프레임워크 (구체적 버전 포함)
            2. 필요한 라이브러리 및 패키지 목록
            3. 개발 환경 설정 방법
            4. 구현 방법론 및 베스트 프랙티스
            5. 테스트 전략 및 도구
            6. 배포 및 운영 방안
            7. 참고할 수 있는 예제 코드나 문서

            모든 조사 결과는 실제 구현에 바로 적용할 수 있도록 구체적이어야 합니다.

            === 참조할 원본 요구사항 ===
            {self.original_requirements}
            """,
            expected_output="상세한 기술 조사 보고서 및 구현 가이드 (한글로 작성)",
            agent=agents['researcher']
        )

    def create_writer_task(self, agents: Dict[str, Agent]) -> Task:
        """Writer 태스크 생성"""
        return Task(
            description=f"""
            Planner의 계획과 Researcher의 조사 결과를 바탕으로 다음을 구현하세요:

            1. 완전한 프로젝트 구조 및 파일 구성
            2. 실행 가능한 코드 (모든 주요 기능 포함)
            3. 상세한 설치 및 실행 가이드
            4. README.md 파일
            5. 의존성 파일 (requirements.txt, package.json 등)
            6. 테스트 코드 (기본적인 테스트 포함)
            7. 사용자 가이드 및 예시

            **핵심 요구사항**:
            - 모든 코드는 실제로 동작해야 함
            - 한글 주석 포함
            - 에러 처리 포함
            - 사용자가 바로 실행할 수 있는 완성도

            === 원본 요구사항 참조 ===
            {self.original_requirements}
            """,
            expected_output="완성된 프로젝트 코드와 문서 (즉시 실행 가능한 형태)",
            agent=agents['writer']
        )

    def execute_planner(self, agents: Dict[str, Agent]) -> bool:
        """Planner 단계 실행"""
        print("\n" + "="*60)
        print("📋 STEP 1: 프로젝트 계획 수립")
        print("="*60)

        self.state_manager.update_project_status(ProjectStatus.PLANNING)
        self.state_manager.update_agent_status("planner", AgentStatus.RUNNING, 0)

        try:
            # Planner 태스크 생성 및 실행
            planner_task = self.create_planner_task(agents)

            crew = Crew(
                agents=[agents['planner']],
                tasks=[planner_task],
                verbose=2,
                process=Process.sequential
            )

            result = crew.kickoff()

            # 결과 저장
            with open(self.planner_result_file, 'w', encoding='utf-8') as f:
                f.write("# Planner 결과\n\n")
                f.write(f"**실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## 계획 내용\n\n")
                f.write(str(result))

            # 상태 업데이트
            self.state_manager.update_agent_status("planner", AgentStatus.COMPLETED, 100, self.planner_result_file)
            self.state_manager.update_project_status(ProjectStatus.PLANNER_APPROVAL_PENDING, 33)

            print(f"\n✅ Planner 완료! 결과 파일: {self.planner_result_file}")
            print("\n" + "⏸️ "*20)
            print("🔔 사용자 승인 대기 중...")
            print("📄 계획서를 검토하신 후 승인/거부를 결정해주세요.")
            print("⏸️ "*20)

            return True

        except Exception as e:
            print(f"❌ Planner 실행 오류: {str(e)}")
            self.state_manager.update_agent_status("planner", AgentStatus.ERROR)
            self.state_manager.update_project_status(ProjectStatus.ERROR)
            return False

    def wait_for_approval(self, agent_name: str) -> bool:
        """승인 대기"""
        print(f"\n⏳ {agent_name} 결과 승인 대기 중...")

        # 승인 파일 경로
        approval_file = os.path.join(self.project_path, f"{agent_name}_approval.json")

        # 주기적으로 승인 파일 확인
        while True:
            if os.path.exists(approval_file):
                try:
                    with open(approval_file, 'r', encoding='utf-8') as f:
                        approval_data = json.load(f)

                    if approval_data.get("decision") == "approved":
                        print(f"✅ {agent_name} 승인됨!")
                        self.state_manager.mark_approval_granted(agent_name)
                        # 승인 파일 삭제
                        os.remove(approval_file)
                        return True

                    elif approval_data.get("decision") == "rejected":
                        print(f"❌ {agent_name} 거부됨")
                        reason = approval_data.get("reason", "")
                        if reason:
                            print(f"거부 사유: {reason}")
                        self.state_manager.mark_approval_rejected(agent_name, reason)
                        # 승인 파일 삭제
                        os.remove(approval_file)
                        return False

                except Exception as e:
                    print(f"승인 파일 읽기 오류: {e}")

            time.sleep(2)  # 2초마다 확인

    def execute_researcher(self, agents: Dict[str, Agent]) -> bool:
        """Researcher 단계 실행"""
        print("\n" + "="*60)
        print("🔍 STEP 2: 기술 조사 및 연구")
        print("="*60)

        self.state_manager.update_project_status(ProjectStatus.RESEARCHING)
        self.state_manager.update_agent_status("researcher", AgentStatus.RUNNING, 0)

        try:
            researcher_task = self.create_researcher_task(agents)

            crew = Crew(
                agents=[agents['researcher']],
                tasks=[researcher_task],
                verbose=2,
                process=Process.sequential
            )

            result = crew.kickoff()

            # 결과 저장
            with open(self.researcher_result_file, 'w', encoding='utf-8') as f:
                f.write("# Researcher 결과\n\n")
                f.write(f"**실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## 조사 내용\n\n")
                f.write(str(result))

            self.state_manager.update_agent_status("researcher", AgentStatus.COMPLETED, 100, self.researcher_result_file)
            self.state_manager.update_project_status(ProjectStatus.WRITING, 66)

            print(f"\n✅ Researcher 완료! 결과 파일: {self.researcher_result_file}")
            return True

        except Exception as e:
            print(f"❌ Researcher 실행 오류: {str(e)}")
            self.state_manager.update_agent_status("researcher", AgentStatus.ERROR)
            return False

    def execute_writer(self, agents: Dict[str, Agent]) -> bool:
        """Writer 단계 실행"""
        print("\n" + "="*60)
        print("✍️ STEP 3: 코드 구현 및 문서 작성")
        print("="*60)

        self.state_manager.update_agent_status("writer", AgentStatus.RUNNING, 0)

        try:
            writer_task = self.create_writer_task(agents)

            crew = Crew(
                agents=[agents['writer']],
                tasks=[writer_task],
                verbose=2,
                process=Process.sequential
            )

            result = crew.kickoff()

            # 결과 저장
            with open(self.writer_result_file, 'w', encoding='utf-8') as f:
                f.write("# Writer 결과\n\n")
                f.write(f"**실행 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## 구현 내용\n\n")
                f.write(str(result))

            self.state_manager.update_agent_status("writer", AgentStatus.COMPLETED, 100, self.writer_result_file)
            self.state_manager.update_project_status(ProjectStatus.COMPLETED, 100)

            print(f"\n✅ Writer 완료! 결과 파일: {self.writer_result_file}")
            return True

        except Exception as e:
            print(f"❌ Writer 실행 오류: {str(e)}")
            self.state_manager.update_agent_status("writer", AgentStatus.ERROR)
            return False

    def execute(self, resume_from: str = None):
        """전체 실행 (재개 지점 지원)"""
        start_time = datetime.now()
        print(f"🚀 강화된 CrewAI 실행 시작 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 에이전트 생성
        agents = self.create_agents()

        try:
            # 재개 지점에 따른 실행
            if not resume_from or resume_from == "planning":
                # Step 1: Planner 실행
                if not self.execute_planner(agents):
                    return False

                # 승인 대기
                if not self.wait_for_approval("planner"):
                    print("❌ Planner 승인 거부로 실행 중단")
                    return False

            if not resume_from or resume_from in ["planning", "researching"]:
                # Step 2: Researcher 실행
                if not self.execute_researcher(agents):
                    return False

            if not resume_from or resume_from in ["planning", "researching", "writing"]:
                # Step 3: Writer 실행
                if not self.execute_writer(agents):
                    return False

            # 최종 완료
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "🎉"*30)
            print("✅ 모든 단계 완료!")
            print(f"⏱️ 총 소요시간: {duration}")
            print(f"📁 프로젝트 경로: {self.project_path}")
            print("🎉"*30)

            return True

        except Exception as e:
            print(f"\n❌ 실행 중 오류 발생: {str(e)}")
            self.state_manager.update_project_status(ProjectStatus.ERROR)
            return False

def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='강화된 CrewAI 실행기')
    parser.add_argument('--project-path', required=True, help='프로젝트 경로')
    parser.add_argument('--requirements', required=True, help='원본 요구사항')
    parser.add_argument('--project-name', default='', help='프로젝트 이름')
    parser.add_argument('--description', default='', help='프로젝트 설명')
    parser.add_argument('--resume-from', help='재개 지점 (planning/researching/writing)')

    args = parser.parse_args()

    # 실행기 생성 및 실행
    executor = EnhancedCrewAIExecutor(
        project_path=args.project_path,
        original_requirements=args.requirements,
        project_name=args.project_name,
        description=args.description
    )

    # 새 프로젝트인 경우 초기화
    if not args.resume_from:
        executor.initialize_project()

    # 실행
    success = executor.execute(resume_from=args.resume_from)

    if success:
        print("\n🎯 실행 성공!")
    else:
        print("\n💥 실행 실패!")
        sys.exit(1)

if __name__ == "__main__":
    main()