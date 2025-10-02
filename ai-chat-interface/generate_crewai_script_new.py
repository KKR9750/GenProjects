#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 CrewAI 스크립트 생성 함수
핵심 정보만 표시하는 웹 승인 시스템 통합
"""

def generate_crewai_execution_script_with_approval(
    requirement: str,
    selected_models: dict,
    project_path: str,
    execution_id: str,
    review_iterations: int = 3,
    selected_tools: list = None,
    api_keys: dict = None
) -> str:
    """
    개선된 승인 시스템이 통합된 CrewAI 실행 스크립트 생성
    핵심 정보만 표시하여 사용자 승인을 받고 진행하는 시스템
    project_00055 수준의 고품질 에이전트 구성 자동 생성

    Args:
        requirement: 사용자 요구사항
        selected_models: 역할별 LLM 모델 딕셔너리
        project_path: 프로젝트 저장 경로
        execution_id: 실행 ID
        review_iterations: 검토-재작성 반복 횟수 (0-3)
        selected_tools: 선택된 MCP/도구 ID 리스트
        api_keys: 도구별 API 키 딕셔너리
    """
    import json
    from datetime import datetime
    from mcp_manager import MCPManager

    # 요구사항 분석을 통한 전문 에이전트 구성 결정
    def analyze_requirement_for_agents(requirement: str) -> dict:
        """요구사항을 분석하여 최적의 전문 에이전트 구성을 결정"""
        requirement_lower = requirement.lower()

        # 키워드 기반 도메인 분석
        if any(keyword in requirement_lower for keyword in ['데이터', 'data', '분석', 'analysis', '통계', '차트', 'visualization']):
            return {
                'domain': 'data_analysis',
                'agents': {
                    'data_scientist': {'role': 'Senior Data Scientist', 'goal': 'Extract insights from data using advanced analytics and machine learning', 'model_preference': 'gpt-4'},
                    'data_engineer': {'role': 'Senior Data Engineer', 'goal': 'Build robust data pipelines and infrastructure for data processing', 'model_preference': 'deepseek-coder'},
                    'visualization_specialist': {'role': 'Data Visualization Specialist', 'goal': 'Create compelling and insightful data visualizations', 'model_preference': 'gemini-flash'},
                    'quality_assurance': {'role': 'Quality Assurance Expert', 'goal': 'Ensure high-quality deliverables and comprehensive testing', 'model_preference': 'claude-3-sonnet'}
                }
            }
        elif any(keyword in requirement_lower for keyword in ['웹', 'web', 'api', '서버', 'server', 'backend', 'frontend']):
            return {
                'domain': 'web_development',
                'agents': {
                    'architect': {'role': 'Software Architect', 'goal': 'Design scalable and maintainable software architecture', 'model_preference': 'gpt-4'},
                    'backend_developer': {'role': 'Backend Developer', 'goal': 'Develop robust server-side applications and APIs', 'model_preference': 'deepseek-coder'},
                    'frontend_developer': {'role': 'Frontend Developer', 'goal': 'Create engaging and responsive user interfaces', 'model_preference': 'gemini-flash'},
                    'devops_engineer': {'role': 'DevOps Engineer', 'goal': 'Ensure reliable deployment and infrastructure management', 'model_preference': 'claude-3-sonnet'}
                }
            }
        elif any(keyword in requirement_lower for keyword in ['뉴스', 'news', '정보수집', '크롤링', 'crawling', 'scraping']):
            return {
                'domain': 'information_processing',
                'agents': {
                    'information_analyst': {'role': 'Information Research Analyst', 'goal': 'Gather and analyze comprehensive information from various sources', 'model_preference': 'gpt-4'},
                    'data_processor': {'role': 'Data Processing Specialist', 'goal': 'Process and structure collected information efficiently', 'model_preference': 'deepseek-coder'},
                    'content_synthesizer': {'role': 'Content Synthesis Expert', 'goal': 'Transform processed data into meaningful insights and reports', 'model_preference': 'gemini-flash'},
                    'quality_validator': {'role': 'Quality Validation Expert', 'goal': 'Ensure accuracy and reliability of processed information', 'model_preference': 'claude-3-sonnet'}
                }
            }
        else:
            # 기본 고품질 구성
            return {
                'domain': 'general_purpose',
                'agents': {
                    'senior_analyst': {'role': 'Senior Business Analyst', 'goal': 'Analyze requirements and design optimal solutions', 'model_preference': 'gpt-4'},
                    'technical_specialist': {'role': 'Technical Implementation Specialist', 'goal': 'Implement robust and efficient technical solutions', 'model_preference': 'deepseek-coder'},
                    'integration_expert': {'role': 'System Integration Expert', 'goal': 'Ensure seamless integration and optimal performance', 'model_preference': 'gemini-flash'},
                    'quality_assurance': {'role': 'Quality Assurance Director', 'goal': 'Guarantee highest quality standards and comprehensive testing', 'model_preference': 'claude-3-sonnet'}
                }
            }

    # 안전한 텍스트 처리 함수
    def safe_text_escape(text: str, max_length: int = 400) -> str:
        if len(text) > max_length:
            text = text[:max_length] + '...'
        text = text.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'")
        text = text.replace('\\n', '\\\\n').replace('\\r', '\\\\r')
        return text

    def safe_path_escape(path: str) -> str:
        return path.replace('\\\\', '\\\\\\\\')

    # 요구사항 분석 및 전문 에이전트 구성 결정
    agent_config = analyze_requirement_for_agents(requirement)

    # 안전한 매개변수 준비
    safe_requirement = safe_text_escape(requirement)
    safe_project_path = safe_path_escape(project_path)
    models_json_escaped = json.dumps(selected_models, ensure_ascii=False).replace('"', '\\\\"')
    agent_config_json = json.dumps(agent_config, ensure_ascii=False, indent=2)

    # 순수 CrewAI 실행 스크립트 템플릿 (4개 전문 에이전트 + 동적 검토-재작성 반복)
    clean_crewai_script_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템
실행 ID: {execution_id}
생성 시간: {generation_time}
요구사항: {original_requirement}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew
from langchain_litellm import ChatLiteLLM
{tools_import}

# 시스템 환경 변수 사용 (별도 .env 파일 로드 없음)

# UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

print("🚀 CrewAI 전문 에이전트 협업 시스템 시작")
print(f"📋 프로젝트: {original_requirement}")
print(f"⏰ 시작 시간: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")

# API 키 확인
missing_keys = []
if not os.getenv("GOOGLE_API_KEY"):
    missing_keys.append("GOOGLE_API_KEY")

if missing_keys:
    print(f"⚠️  경고: 다음 환경변수가 설정되지 않았습니다: {{', '.join(missing_keys)}}", file=sys.stderr)
    print("   .env 파일에 해당 키를 추가하거나 시스템 환경변수를 설정해주세요.", file=sys.stderr)

# LLM 모델 설정 함수
def get_model(model_name: str):
    """LLM 모델 인스턴스 반환 (ChatLiteLLM 사용)"""

    # 모델 ID → LiteLLM 이름 매핑 (model_config.json과 동기화)
    MODEL_ID_TO_LITELLM = {{
        "ollama-gemma2-2b": "ollama/gemma2:2b",
        "ollama-deepseek-coder-6.7b": "ollama/deepseek-coder:6.7b",
        "ollama-llama3.1": "ollama/llama3.1:latest",
        "ollama-qwen3-coder-30b": "ollama/qwen3-coder:30b"
    }}

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
        model_name = f"ollama/{{model_name}}"

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
            model_name = f"openai/{{model_name}}"
    elif "claude" in model_name.lower():
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not model_name.startswith("anthropic/"):
            model_name = f"anthropic/{{model_name}}"
    elif "deepseek" in model_name.lower():
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not model_name.startswith("deepseek/"):
            model_name = f"deepseek/{{model_name}}"
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
                model_name = f"gemini/{{model_name}}"

    return ChatLiteLLM(
        model=model_name,
        api_key=api_key,
        temperature=0.7
    )

{tools_init}

# 4개 전문 에이전트 정의 (사전 분석 결과 기반)
print("\\n👥 전문 에이전트 구성 중...")

# Pre-Analyzer: 사전 분석 처리
pre_analyzer = Agent(
    role="Pre-Analysis Specialist",
    goal="{pre_analyzer_goal}",
    backstory="{pre_analyzer_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{pre_analyzer_model}")
)

# Planner: 프로젝트 계획 수립 + Writer 산출물 검토
planner = Agent(
    role="Project Planner & Quality Reviewer",
    goal="{planner_goal}",
    backstory="{planner_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{planner_model}")
)

# Researcher: 기술 조사 및 분석 (도구 활용)
researcher = Agent(
    role="Technical Researcher",
    goal="{researcher_goal}",
    backstory="{researcher_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{researcher_model}"),
    {researcher_tools}
)

# Writer: 구현 및 문서 작성 + Planner 피드백 반영
writer = Agent(
    role="Technical Writer & Implementer",
    goal="{writer_goal}",
    backstory="{writer_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{writer_model}")
)

print("✅ 4개 전문 에이전트 구성 완료")

# 태스크 구성
print("\\n📋 태스크 구성 중...")

# 1. Pre-Analysis Task
task1 = Task(
    description="""{pre_analysis_task_description}""",
    expected_output="""요구사항 분석 보고서 (마크다운 형식, 구체적 기능 명세 포함)""",
    agent=pre_analyzer
)

# 2. Planning Task
task2 = Task(
    description="""{planning_task_description}""",
    expected_output="""프로젝트 개발 계획서 (마크다운 형식, 실행 가능한 단계별 가이드)""",
    agent=planner
)

# 3. Research Task
task3 = Task(
    description="""{research_task_description}""",
    expected_output="""기술 조사 보고서 (마크다운 형식, 기술 선택 근거 포함)""",
    agent=researcher
)

# 4. Initial Writing Task
task4 = Task(
    description="""{initial_writing_task_description}""",
    expected_output="""완전한 프로젝트 구현체 (실행 가능한 코드, 문서, 설정 파일 포함)""",
    agent=writer
)

{review_revision_tasks}

print("✅ 총 {{len([task1, task2, task3, task4] + review_tasks + revision_tasks)}}개 태스크 구성 완료")

# CrewAI 실행
print("\\n🚀 CrewAI 전문 에이전트 협업 시작...")

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

    print(f"\\n🎉 CrewAI 전문 에이전트 협업 완료!")
    print(f"⏰ 총 소요시간: {{duration}}")

    # 결과 저장
    output_file = os.path.join("{project_path}", "crewai_result.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 전문 에이전트 협업 시스템 결과\\\\n\\\\n")
        f.write(f"**실행 ID**: {execution_id}\\\\n")
        f.write(f"**요구사항**: {original_requirement}\\\\n")
        f.write(f"**시작 시간**: {{start_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
        f.write(f"**완료 시간**: {{end_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
        f.write(f"**총 소요시간**: {{duration}}\\\\n\\\\n")
        f.write("## 최종 결과\\\\n\\\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {{os.path.abspath(output_file)}}")

    # README.md 생성
    readme_file = os.path.join("{project_path}", "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{' '.join('{original_requirement}'.split()[:3])}}\\\\n\\\\n")
        f.write(f"CrewAI 전문 에이전트 협업으로 개발된 프로젝트입니다.\\\\n\\\\n")
        f.write(f"## 프로젝트 개요\\\\n")
        f.write(f"**요구사항**: {original_requirement}\\\\n")
        f.write(f"**개발 완료**: {{end_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n\\\\n")
        f.write(f"## 개발 과정\\\\n")
        f.write(f"1. Pre-Analysis: 사전 분석\\\\n")
        f.write(f"2. Planning: 프로젝트 계획 수립\\\\n")
        f.write(f"3. Research: 기술 조사\\\\n")
        f.write(f"4. Implementation: 구현 ({review_iterations}회 검토-재작성 반복)\\\\n\\\\n")
        f.write(f"상세 결과는 `crewai_result.md` 파일을 참조하세요.\\\\n")

    print(f"📄 README.md 생성: {{os.path.abspath(readme_file)}}")

except Exception as e:
    print(f"\\n❌ 실행 중 오류 발생: {{str(e)}}")
    import traceback
    print(f"상세 오류:\\\\n{{traceback.format_exc()}}")
    sys.exit(1)
'''

    # Dynamic review-revision task generation logic will be added in template_vars preparation below

    # MCP/도구 관리자 초기화 및 코드 생성
    tools_import = ""
    tools_init = ""
    researcher_tools = ""

    if selected_tools:
        try:
            mcp_manager = MCPManager()
            tools_import = mcp_manager.generate_tool_imports(selected_tools)
            tools_init = mcp_manager.generate_tool_initialization(selected_tools, api_keys or {})
            researcher_tools = mcp_manager.get_agent_tools_list(selected_tools)

            tool_names = mcp_manager.get_tool_names(selected_tools)
            print(f"🛠️ 선택된 도구: {', '.join(tool_names)}")
        except Exception as e:
            print(f"⚠️ MCP 도구 처리 중 오류: {str(e)}")
            # 오류 발생 시 빈 값으로 처리
            tools_import = ""
            tools_init = ""
            researcher_tools = ""

    # 사전 분석 결과 기반 템플릿 변수 값 준비
    template_vars = {
        'execution_id': execution_id,
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_requirement': requirement,
        'project_path': safe_project_path,
        'review_iterations': review_iterations,
        'models_json': models_json_escaped,

        # MCP/도구 관련 변수
        'tools_import': tools_import,
        'tools_init': tools_init,
        'researcher_tools': researcher_tools,

        # 4개 전문 에이전트 정의 (사전 분석 결과 기반)
        'pre_analyzer_goal': f"사전 분석을 통해 {requirement}에 대한 핵심 요구사항과 기술적 제약사항을 명확히 정의합니다.",
        'pre_analyzer_backstory': f"당신은 요구사항 분석 전문가입니다. {requirement} 프로젝트의 본질을 파악하고 성공을 위한 핵심 요소들을 식별하는 전문성을 가지고 있습니다.",
        'pre_analyzer_model': list(selected_models.values())[0] if selected_models else "gemini-2.5-flash",

        'planner_goal': f"Pre-Analyzer의 분석을 바탕으로 {requirement} 프로젝트의 체계적인 개발 계획을 수립하고, Writer의 산출물을 {review_iterations}회 검토하여 최고 품질을 보장합니다.",
        'planner_backstory': f"당신은 프로젝트 관리 및 품질 보증 전문가입니다. {requirement} 같은 프로젝트의 성공적인 실행 계획 수립과 지속적인 품질 개선에 전문성을 가지고 있습니다.",
        'planner_model': list(selected_models.values())[1] if len(selected_models) > 1 else "gemini-2.5-flash",

        'researcher_goal': f"Planner의 계획을 바탕으로 {requirement} 구현에 필요한 최적의 기술 스택, 도구, 방법론을 조사하고 제안합니다.",
        'researcher_backstory': f"당신은 기술 리서치 전문가입니다. {requirement}와 같은 프로젝트에 최적화된 기술 솔루션을 찾아내고 검증하는 전문성을 가지고 있습니다.",
        'researcher_model': list(selected_models.values())[2] if len(selected_models) > 2 else "gemini-2.5-flash",

        'writer_goal': f"연구 결과를 바탕으로 {requirement}를 완전히 구현하고, Planner의 피드백을 반영하여 지속적으로 개선합니다.",
        'writer_backstory': f"당신은 기술 구현 및 문서화 전문가입니다. {requirement} 프로젝트를 실제 동작하는 고품질 코드로 구현하고 피드백을 통해 지속적으로 개선하는 전문성을 가지고 있습니다.",
        'writer_model': list(selected_models.values())[-1] if selected_models else "gemini-2.5-flash",

        # 10개 태스크 정의 (검토-재작성 3회 반복)
        'pre_analysis_task_description': f'''
다음 요구사항에 대한 포괄적인 사전 분석을 수행하세요:

**요구사항**: {requirement}

**분석 내용**:
1. 프로젝트 목표 및 핵심 가치 정의
2. 주요 기능 요구사항 도출
3. 기술적 제약사항 및 고려사항
4. 성공 기준 및 평가 지표
5. 잠재적 리스크 및 대응 방안

구체적이고 실행 가능한 분석 결과를 제시하세요.
        ''',
        'pre_analysis_expected_output': "요구사항 분석 보고서 (마크다운 형식, 구체적 기능 명세 포함)",

        'planning_task_description': '''
Pre-Analyzer의 분석 결과를 바탕으로 체계적인 프로젝트 개발 계획을 수립하세요:

**계획 수립 내용**:
1. 개발 단계별 로드맵
2. 기능별 우선순위 매트릭스
3. 기술 스택 선정 가이드라인
4. 개발 일정 및 마일스톤
5. 품질 보증 체크포인트

실무진이 바로 실행할 수 있는 상세한 계획을 작성하세요.
        ''',
        'planning_expected_output': "프로젝트 개발 계획서 (마크다운 형식, 실행 가능한 단계별 가이드)",

        'research_task_description': '''
Planner의 계획을 바탕으로 기술적 조사를 수행하세요:

**조사 항목**:
1. 권장 기술 스택 및 라이브러리
2. 아키텍처 패턴 및 설계 원칙
3. 개발 도구 및 환경 설정
4. 보안 고려사항 및 베스트 프랙티스
5. 성능 최적화 방안
6. 테스트 및 배포 전략

각 기술 선택의 근거와 대안을 명시하세요.
        ''',
        'research_expected_output': "기술 조사 보고서 (마크다운 형식, 기술 선택 근거 포함)",

        'initial_writing_task_description': '''
분석과 계획, 조사 결과를 바탕으로 초기 프로젝트를 구현하세요:

**구현 내용**:
1. 완전한 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (실제 동작)
3. 설정 파일 및 의존성 관리
4. 상세한 README.md 및 사용법
5. 기본 테스트 코드
6. 실행 및 배포 가이드

모든 코드는 실제로 동작해야 하며 충분한 주석을 포함하세요.
        ''',
        'initial_writing_expected_output': "완전한 프로젝트 구현체 (실행 가능한 코드, 문서, 설정 파일 포함)",

        'review_task_1_description': '''
Writer가 작성한 초기 구현체를 검토하고 개선사항을 도출하세요:

**검토 항목**:
1. 요구사항 충족도 평가
2. 코드 품질 및 구조 분석
3. 기능 완성도 점검
4. 문서화 수준 평가
5. 테스트 커버리지 검토
6. 사용성 및 접근성 평가

구체적인 개선 방향과 우선순위를 제시하세요.
        ''',
        'review_task_1_expected_output': "1차 검토 보고서 및 개선 지시사항 (구체적 수정 항목 포함)",

        'revision_task_1_description': '''
Planner의 1차 검토 피드백을 바탕으로 프로젝트를 개선하세요:

**개선 작업**:
1. 검토에서 지적된 문제점 해결
2. 코드 품질 향상 및 구조 개선
3. 기능 완성도 제고
4. 문서화 보완 및 명확화
5. 테스트 코드 강화
6. 사용성 개선

모든 피드백을 반영하여 한 단계 발전된 버전을 제작하세요.
        ''',
        'revision_task_1_expected_output': "1차 개선된 프로젝트 구현체 (피드백 반영 완료)",

        'review_task_2_description': '''
Writer의 1차 개선 결과를 2차 검토하고 추가 개선사항을 도출하세요:

**심화 검토 항목**:
1. 1차 피드백 반영 수준 평가
2. 새로운 개선 기회 식별
3. 성능 및 보안 검토
4. 확장성 및 유지보수성 평가
5. 사용자 경험 최적화 방안
6. 배포 준비 상태 점검

더욱 엄격한 기준으로 품질을 평가하세요.
        ''',
        'review_task_2_expected_output': "2차 검토 보고서 및 고도화 지시사항 (심화 개선 항목 포함)",

        'revision_task_2_description': '''
Planner의 2차 검토 피드백을 바탕으로 프로젝트를 고도화하세요:

**고도화 작업**:
1. 심화 검토 지적사항 해결
2. 성능 최적화 및 보안 강화
3. 확장성 및 유지보수성 향상
4. 사용자 경험 개선
5. 배포 및 운영 준비
6. 종합적 품질 향상

전문가 수준의 완성도를 목표로 개선하세요.
        ''',
        'revision_task_2_expected_output': "2차 고도화된 프로젝트 구현체 (전문가 수준 품질)",

        'review_task_3_description': '''
Writer의 2차 고도화 결과에 대한 최종 검토를 수행하세요:

**최종 검토 항목**:
1. 모든 요구사항 완벽 충족 여부
2. 코드 품질의 전문가 수준 달성 여부
3. 완전한 기능 동작 및 안정성
4. 문서화 완성도 및 사용 편의성
5. 배포 준비 완료 상태
6. 프로덕션 레벨 품질 보장

최고 수준의 기준으로 최종 평가하세요.
        ''',
        'review_task_3_expected_output': "최종 검토 보고서 및 완성 확인서 (프로덕션 레벨 품질 인증)",

        'final_revision_task_description': '''
Planner의 최종 검토를 바탕으로 완벽한 최종 버전을 완성하세요:

**최종 완성 작업**:
1. 모든 검토 지적사항의 완벽한 해결
2. 최고 수준의 코드 품질 달성
3. 완전한 기능 구현 및 검증
4. 완벽한 문서화 및 사용 가이드
5. 프로덕션 배포 준비 완료
6. 최종 품질 보증

업계 최고 수준의 완성된 프로젝트를 제작하세요.
        ''',
        'final_revision_expected_output': "최종 완성된 프로젝트 (업계 최고 수준, 즉시 배포 가능)"
    }

    # 동적 검토-재작성 태스크 생성 (review_iterations에 따라 0~3회)
    review_revision_code_parts = []

    for i in range(review_iterations):
        iteration_num = i + 1
        is_final = (i == review_iterations - 1)

        if is_final:
            # 마지막 반복 - 최종 검토 및 완성
            review_revision_code_parts.append(f'''
# {iteration_num*2-1}. Review Task {iteration_num} (Final)
task{4+iteration_num*2-1} = Task(
    description="""
Writer의 {"" if iteration_num == 1 else f"{iteration_num-1}차 "}{"초기 구현" if iteration_num == 1 else "고도화"} 결과에 대한 최종 검토를 수행하세요:

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

# {iteration_num*2}. Final Revision Task
task{4+iteration_num*2} = Task(
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
''')
        else:
            # 중간 반복 - 일반 검토 및 개선
            if iteration_num == 1:
                prev_stage = "초기 구현체"
                improvement_level = "기본"
            else:
                prev_stage = f"{iteration_num-1}차 개선 결과"
                improvement_level = "심화"

            review_revision_code_parts.append(f'''
# {iteration_num*2-1}. Review Task {iteration_num}
task{4+iteration_num*2-1} = Task(
    description="""
Writer가 작성한 {prev_stage}를 검토하고 개선사항을 도출하세요:

**검토 항목**:
1. {"요구사항 충족도 평가" if iteration_num == 1 else f"{iteration_num-1}차 피드백 반영 수준 평가"}
2. {"코드 품질 및 구조 분석" if iteration_num == 1 else "새로운 개선 기회 식별"}
3. {"기능 완성도 점검" if iteration_num == 1 else "성능 및 보안 검토"}
4. {"문서화 수준 평가" if iteration_num == 1 else "확장성 및 유지보수성 평가"}
5. {"테스트 커버리지 검토" if iteration_num == 1 else "사용자 경험 최적화 방안"}
6. {"사용성 및 접근성 평가" if iteration_num == 1 else "배포 준비 상태 점검"}

{"구체적인 개선 방향과 우선순위를 제시하세요." if iteration_num == 1 else "더욱 엄격한 기준으로 품질을 평가하세요."}
        """,
    expected_output="""{iteration_num}차 검토 보고서 및 {"개선" if iteration_num == 1 else "고도화"} 지시사항 ({"구체적 수정 항목" if iteration_num == 1 else "심화 개선 항목"} 포함)""",
    agent=planner
)

# {iteration_num*2}. Revision Task {iteration_num}
task{4+iteration_num*2} = Task(
    description="""
Planner의 {iteration_num}차 검토 피드백을 바탕으로 프로젝트를 {"개선" if iteration_num == 1 else "고도화"}하세요:

**{improvement_level} {"개선" if iteration_num == 1 else "고도화"} 작업**:
1. {"검토에서 지적된 문제점 해결" if iteration_num == 1 else "심화 검토 지적사항 해결"}
2. {"코드 품질 향상 및 구조 개선" if iteration_num == 1 else "성능 최적화 및 보안 강화"}
3. {"기능 완성도 제고" if iteration_num == 1 else "확장성 및 유지보수성 향상"}
4. {"문서화 보완 및 명확화" if iteration_num == 1 else "사용자 경험 개선"}
5. {"테스트 코드 강화" if iteration_num == 1 else "배포 및 운영 준비"}
6. {"사용성 개선" if iteration_num == 1 else "종합적 품질 향상"}

{"모든 피드백을 반영하여 한 단계 발전된 버전을 제작하세요." if iteration_num == 1 else "전문가 수준의 완성도를 목표로 개선하세요."}
        """,
    expected_output="""{iteration_num}차 {"개선된" if iteration_num == 1 else "고도화된"} 프로젝트 구현체 ({"피드백 반영 완료" if iteration_num == 1 else "전문가 수준 품질"})""",
    agent=writer
)
''')

    # 생성된 태스크 코드 결합
    review_revision_tasks_code = ''.join(review_revision_code_parts)

    # 동적으로 생성된 태스크 리스트 빌드
    if review_iterations > 0:
        review_task_list = ', '.join([f'task{4+i+1}' for i in range(review_iterations * 2)])
        dynamic_tasks_append = f'''
review_tasks = [{', '.join([f'task{4+i*2+1}' for i in range(review_iterations)])}]
revision_tasks = [{', '.join([f'task{4+i*2+2}' for i in range(review_iterations)])}]
'''
    else:
        dynamic_tasks_append = '''
review_tasks = []
revision_tasks = []
'''

    # 템플릿 변수에 동적 코드 추가
    template_vars['review_revision_tasks'] = review_revision_tasks_code + dynamic_tasks_append

    # 새로운 순수 CrewAI 스크립트 생성
    try:
        # 새로운 템플릿에 변수 적용
        script_content = clean_crewai_script_template.format(**template_vars)
        return script_content

    except Exception as e:
        # 새로운 템플릿 처리 오류 시 간단한 fallback
        print(f"템플릿 처리 오류: {str(e)}")
        fallback_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템 (Fallback)
실행 ID: {execution_id}
오류: {str(e)}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, LLM

print("⚠️ 템플릿 처리 오류 발생")
print(f"요구사항: {requirement}")
print(f"실행 ID: {execution_id}")
print(f"오류: {str(e)}")
print("\\n기본 3개 에이전트로 fallback 실행...")

# 기본 에이전트들
planner = Agent(role="Planner", goal="프로젝트 계획 수립", backstory="계획 전문가", llm=LLM(model="gemini-2.5-flash"))
researcher = Agent(role="Researcher", goal="기술 조사", backstory="기술 전문가", llm=LLM(model="gemini-2.5-flash"))
writer = Agent(role="Writer", goal="코드 구현", backstory="개발 전문가", llm=LLM(model="gemini-2.5-flash"))

# 기본 태스크들
task1 = Task(description="프로젝트 계획 수립", expected_output="계획서", agent=planner)
task2 = Task(description="기술 조사", expected_output="조사 보고서", agent=researcher)
task3 = Task(description="코드 구현", expected_output="완성된 프로젝트", agent=writer)

# 실행
crew = Crew(agents=[planner, researcher, writer], tasks=[task1, task2, task3])
result = crew.kickoff()

print("Fallback 실행 완료")
'''
        return fallback_script

def generate_crewai_execution_script(requirement: str, selected_models: dict, project_path: str, execution_id: str, review_iterations: int = 3) -> str:
    """
    CrewAI 실행 스크립트 생성 - 새로운 전문 에이전트 시스템을 기본값으로 사용
    """
    # 새로운 전문 에이전트 시스템을 기본값으로 사용
    return generate_crewai_execution_script_with_approval(requirement, selected_models, project_path, execution_id, review_iterations)

if __name__ == "__main__":
    # 테스트
    test_req = "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘."
    test_models = {"planner": "gpt-4", "researcher": "claude-3", "writer": "gpt-4"}
    test_path = "D:\\GenProjects\\Projects\\test_project"
    test_id = "test_12345"

    result = generate_crewai_execution_script(test_req, test_models, test_path, test_id)
    print("✅ 전문 에이전트 시스템 스크립트 생성 테스트 성공")
    print(f"스크립트 길이: {len(result)} 문자")
    print("첫 100자:", result[:100])
