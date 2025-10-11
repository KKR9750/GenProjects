#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템
실행 ID: test-final
생성 시간: 2025-10-02 12:31:17
요구사항: 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew
from langchain_litellm import ChatLiteLLM

# 시스템 환경 변수 사용 (별도 .env 파일 로드 없음)

# UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

print("🚀 CrewAI 전문 에이전트 협업 시스템 시작")
print(f"📋 프로젝트: 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘")
print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# API 키 확인
missing_keys = []
if not os.getenv("GOOGLE_API_KEY"):
    missing_keys.append("GOOGLE_API_KEY")

if missing_keys:
    print(f"⚠️  경고: 다음 환경변수가 설정되지 않았습니다: {', '.join(missing_keys)}", file=sys.stderr)
    print("   .env 파일에 해당 키를 추가하거나 시스템 환경변수를 설정해주세요.", file=sys.stderr)

# LLM 모델 설정 함수
def get_model(model_name: str):
    """LLM 모델 인스턴스 반환 (ChatLiteLLM 사용)"""

    # 모델 ID → LiteLLM 이름 매핑 (model_config.json과 동기화)
    MODEL_ID_TO_LITELLM = {
        "ollama-gemma2-2b": "ollama/gemma2:2b",
        "ollama-deepseek-coder-6.7b": "ollama/deepseek-coder:6.7b",
        "ollama-llama3.1": "ollama/llama3.1:latest",
        "ollama-qwen3-coder-30b": "ollama/qwen3-coder:30b"
    }

    # ID를 LiteLLM 이름으로 변환
    if model_name in MODEL_ID_TO_LITELLM:
        model_name = MODEL_ID_TO_LITELLM[model_name]

    # Ollama 로컬 모델 감지 (최우선 처리)
    ollama_models = ["llama", "gemma", "qwen", "gpt-oss"]
    is_ollama = any(ollama_model in model_name.lower() for ollama_model in ollama_models)

    # deepseek-coder는 API와 로컬 모두 가능하므로 'ollama/' 프리픽스로 구분
    if "deepseek-coder" in model_name.lower() and model_name.startswith("ollama/"):
        is_ollama = True

    if is_ollama and not model_name.startswith("ollama/"):
        model_name = f"ollama/{model_name}"

    if model_name.startswith("ollama/"):
        # Ollama 로컬 모델 처리
        return ChatLiteLLM(
            model=model_name,
            api_base="http://localhost:11434",
            temperature=0.7
        )

    # Provider prefix 자동 추가 및 모델명 정규화
    if "gpt" in model_name.lower():
        api_key = os.getenv("OPENAI_API_KEY")
        if not model_name.startswith("openai/"):
            model_name = f"openai/{model_name}"
    elif "claude" in model_name.lower():
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not model_name.startswith("anthropic/"):
            model_name = f"anthropic/{model_name}"
    elif "deepseek" in model_name.lower():
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not model_name.startswith("deepseek/"):
            model_name = f"deepseek/{model_name}"
    else:
        # 기본값: Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not model_name.startswith("gemini/"):
            # 모델명 정규화: gemini-flash → gemini-2.5-flash
            if model_name in ["gemini-flash", "gemini-2.5-flash", "gemini-2.0-flash"]:
                model_name = "gemini/gemini-2.5-flash"
            elif model_name in ["gemini-pro", "gemini-2.5-pro"]:
                model_name = "gemini/gemini-2.5-pro"
            else:
                model_name = f"gemini/{model_name}"

    return ChatLiteLLM(
        model=model_name,
        api_key=api_key,
        temperature=0.7
    )

# 4개 전문 에이전트 정의 (사전 분석 결과 기반)
print("\n👥 전문 에이전트 구성 중...")

# Pre-Analyzer: 사전 분석 처리
pre_analyzer = Agent(
    role="Pre-Analysis Specialist",
    goal="사전 분석을 통해 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘에 대한 핵심 요구사항과 기술적 제약사항을 명확히 정의합니다.",
    backstory="당신은 요구사항 분석 전문가입니다. 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘 프로젝트의 본질을 파악하고 성공을 위한 핵심 요소들을 식별하는 전문성을 가지고 있습니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_model("gemini-2.5-flash")
)

# Planner: 프로젝트 계획 수립 + Writer 산출물 검토
planner = Agent(
    role="Project Planner & Quality Reviewer",
    goal="Pre-Analyzer의 분석을 바탕으로 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘 프로젝트의 체계적인 개발 계획을 수립하고, Writer의 산출물을 2회 검토하여 최고 품질을 보장합니다.",
    backstory="당신은 프로젝트 관리 및 품질 보증 전문가입니다. 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘 같은 프로젝트의 성공적인 실행 계획 수립과 지속적인 품질 개선에 전문성을 가지고 있습니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_model("gemini-2.5-flash")
)

# Researcher: 기술 조사 및 분석
researcher = Agent(
    role="Technical Researcher",
    goal="Planner의 계획을 바탕으로 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘 구현에 필요한 최적의 기술 스택, 도구, 방법론을 조사하고 제안합니다.",
    backstory="당신은 기술 리서치 전문가입니다. 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘와 같은 프로젝트에 최적화된 기술 솔루션을 찾아내고 검증하는 전문성을 가지고 있습니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_model("gemini-2.5-flash")
)

# Writer: 구현 및 문서 작성 + Planner 피드백 반영
writer = Agent(
    role="Technical Writer & Implementer",
    goal="연구 결과를 바탕으로 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘를 완전히 구현하고, Planner의 피드백을 반영하여 지속적으로 개선합니다.",
    backstory="당신은 기술 구현 및 문서화 전문가입니다. 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘 프로젝트를 실제 동작하는 고품질 코드로 구현하고 피드백을 통해 지속적으로 개선하는 전문성을 가지고 있습니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_model("gemini-2.5-flash")
)

print("✅ 4개 전문 에이전트 구성 완료")

# 태스크 구성
print("\n📋 태스크 구성 중...")

# 1. Pre-Analysis Task
task1 = Task(
    description="""
다음 요구사항에 대한 포괄적인 사전 분석을 수행하세요:

**요구사항**: 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘

**분석 내용**:
1. 프로젝트 목표 및 핵심 가치 정의
2. 주요 기능 요구사항 도출
3. 기술적 제약사항 및 고려사항
4. 성공 기준 및 평가 지표
5. 잠재적 리스크 및 대응 방안

구체적이고 실행 가능한 분석 결과를 제시하세요.
        """,
    expected_output="""요구사항 분석 보고서 (마크다운 형식, 구체적 기능 명세 포함)""",
    agent=pre_analyzer
)

# 2. Planning Task
task2 = Task(
    description="""
Pre-Analyzer의 분석 결과를 바탕으로 체계적인 프로젝트 개발 계획을 수립하세요:

**계획 수립 내용**:
1. 개발 단계별 로드맵
2. 기능별 우선순위 매트릭스
3. 기술 스택 선정 가이드라인
4. 개발 일정 및 마일스톤
5. 품질 보증 체크포인트

실무진이 바로 실행할 수 있는 상세한 계획을 작성하세요.
        """,
    expected_output="""프로젝트 개발 계획서 (마크다운 형식, 실행 가능한 단계별 가이드)""",
    agent=planner
)

# 3. Research Task
task3 = Task(
    description="""
Planner의 계획을 바탕으로 기술적 조사를 수행하세요:

**조사 항목**:
1. 권장 기술 스택 및 라이브러리
2. 아키텍처 패턴 및 설계 원칙
3. 개발 도구 및 환경 설정
4. 보안 고려사항 및 베스트 프랙티스
5. 성능 최적화 방안
6. 테스트 및 배포 전략

각 기술 선택의 근거와 대안을 명시하세요.
        """,
    expected_output="""기술 조사 보고서 (마크다운 형식, 기술 선택 근거 포함)""",
    agent=researcher
)

# 4. Initial Writing Task
task4 = Task(
    description="""
분석과 계획, 조사 결과를 바탕으로 초기 프로젝트를 구현하세요:

**구현 내용**:
1. 완전한 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (실제 동작)
3. 설정 파일 및 의존성 관리
4. 상세한 README.md 및 사용법
5. 기본 테스트 코드
6. 실행 및 배포 가이드

모든 코드는 실제로 동작해야 하며 충분한 주석을 포함하세요.
        """,
    expected_output="""완전한 프로젝트 구현체 (실행 가능한 코드, 문서, 설정 파일 포함)""",
    agent=writer
)


# 1. Review Task 1
task5 = Task(
    description="""
Writer가 작성한 초기 구현체를 검토하고 개선사항을 도출하세요:

**검토 항목**:
1. 요구사항 충족도 평가
2. 코드 품질 및 구조 분석
3. 기능 완성도 점검
4. 문서화 수준 평가
5. 테스트 커버리지 검토
6. 사용성 및 접근성 평가

구체적인 개선 방향과 우선순위를 제시하세요.
        """,
    expected_output="""1차 검토 보고서 및 개선 지시사항 (구체적 수정 항목 포함)""",
    agent=planner
)

# 2. Revision Task 1
task6 = Task(
    description="""
Planner의 1차 검토 피드백을 바탕으로 프로젝트를 개선하세요:

**기본 개선 작업**:
1. 검토에서 지적된 문제점 해결
2. 코드 품질 향상 및 구조 개선
3. 기능 완성도 제고
4. 문서화 보완 및 명확화
5. 테스트 코드 강화
6. 사용성 개선

모든 피드백을 반영하여 한 단계 발전된 버전을 제작하세요.
        """,
    expected_output="""1차 개선된 프로젝트 구현체 (피드백 반영 완료)""",
    agent=writer
)

# 3. Review Task 2 (Final)
task7 = Task(
    description="""
Writer의 1차 고도화 결과에 대한 최종 검토를 수행하세요:

**최종 검토 항목**:
1. 모든 요구사항 완벽 충족 여부
2. 코드 품질의 전문가 수준 달성 여부
3. 완전한 기능 동작 및 안정성
4. 문서화 완성도 및 사용 편의성
5. 배포 준비 완료 상태
6. 프로덕션 레벨 품질 보장

최고 수준의 기준으로 최종 평가하세요.
        """,
    expected_output="""최종 검토 보고서 및 완성 확인서 (프로덕션 레벨 품질 인증)""",
    agent=planner
)

# 4. Final Revision Task
task8 = Task(
    description="""
Planner의 최종 검토를 바탕으로 완벽한 최종 버전을 완성하세요:

**최종 완성 작업**:
1. 모든 검토 지적사항의 완벽한 해결
2. 최고 수준의 코드 품질 달성
3. 완전한 기능 구현 및 검증
4. 완벽한 문서화 및 사용 가이드
5. 프로덕션 배포 준비 완료
6. 최종 품질 보증

업계 최고 수준의 완성된 프로젝트를 제작하세요.
        """,
    expected_output="""최종 완성된 프로젝트 (업계 최고 수준, 즉시 배포 가능)""",
    agent=writer
)

review_tasks = [task5, task7]
revision_tasks = [task6, task8]


print("✅ 총 {len([task1, task2, task3, task4] + review_tasks + revision_tasks)}개 태스크 구성 완료")

# CrewAI 실행
print("\n🚀 CrewAI 전문 에이전트 협업 시작...")

all_tasks = [task1, task2, task3, task4] + review_tasks + revision_tasks

crew = Crew(
    agents=[pre_analyzer, planner, researcher, writer],
    tasks=all_tasks,
    verbose=True
)

# 실행 및 결과 저장
start_time = datetime.now()
try:
    result = crew.kickoff()
    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\n🎉 CrewAI 전문 에이전트 협업 완료!")
    print(f"⏰ 총 소요시간: {duration}")

    # 결과 저장
    output_file = os.path.join("D:\GenProjects\Projects	est_project", "crewai_result.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 전문 에이전트 협업 시스템 결과\\n\\n")
        f.write(f"**실행 ID**: test-final\\n")
        f.write(f"**요구사항**: 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘\\n")
        f.write(f"**시작 시간**: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"**완료 시간**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"**총 소요시간**: {duration}\\n\\n")
        f.write("## 최종 결과\\n\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {os.path.abspath(output_file)}")

    # README.md 생성
    readme_file = os.path.join("D:\GenProjects\Projects	est_project", "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"# {' '.join('금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘'.split()[:3])}\\n\\n")
        f.write(f"CrewAI 전문 에이전트 협업으로 개발된 프로젝트입니다.\\n\\n")
        f.write(f"## 프로젝트 개요\\n")
        f.write(f"**요구사항**: 금일 구글 뉴스를 검색해서 10개내외 요약해서 알려줘\\n")
        f.write(f"**개발 완료**: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        f.write(f"## 개발 과정\\n")
        f.write(f"1. Pre-Analysis: 사전 분석\\n")
        f.write(f"2. Planning: 프로젝트 계획 수립\\n")
        f.write(f"3. Research: 기술 조사\\n")
        f.write(f"4. Implementation: 구현 (2회 검토-재작성 반복)\\n\\n")
        f.write(f"상세 결과는 `crewai_result.md` 파일을 참조하세요.\\n")

    print(f"📄 README.md 생성: {os.path.abspath(readme_file)}")

except Exception as e:
    print(f"\n❌ 실행 중 오류 발생: {str(e)}")
    import traceback
    print(f"상세 오류:\\n{traceback.format_exc()}")
    sys.exit(1)
