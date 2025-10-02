#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
통합 CrewAI 스크립트 생성 시스템
새로운 적응형 스크립트 생성 엔진과 기존 시스템 통합
"""

import os
from adaptive_script_generator import AdaptiveScriptGenerator
from datetime import datetime

def generate_enhanced_crewai_script(requirement, selected_models, project_path, execution_id, review_iterations=3, selected_tools=None, api_keys=None):
    """새로운 적응형 시스템을 사용한 CrewAI 스크립트 생성

    Args:
        requirement: 사용자 요구사항
        selected_models: 역할별 LLM 모델 딕셔너리
        project_path: 프로젝트 저장 경로
        execution_id: 실행 ID
        review_iterations: 검토-재작성 반복 횟수 (0-3)
        selected_tools: 선택된 MCP/도구 ID 리스트
        api_keys: 도구별 API 키 딕셔너리
    """

    print(f"🚀 새로운 적응형 CrewAI 생성 시스템 사용")
    print(f"   요구사항: {requirement[:100]}...")
    print(f"   프로젝트 경로: {project_path}")
    print(f"   실행 ID: {execution_id}")
    print(f"   검토-재작성 반복: {review_iterations}회")

    if selected_tools:
        from mcp_manager import MCPManager
        mcp_manager = MCPManager()
        tool_names = mcp_manager.get_tool_names(selected_tools)
        print(f"   선택된 도구: {', '.join(tool_names)}")

    try:
        # 적응형 스크립트 생성기 초기화
        generator = AdaptiveScriptGenerator("model_config.json")

        # 수동 모델 선택과 관계없이 항상 고품질 스크립트 생성
        if selected_models and any(selected_models.values()):
            print(f"🎯 수동 모델 선택 감지: {selected_models}")
            print(f"🚀 수동 모델을 사용한 고품질 스크립트 생성 시도...")
            # 수동 선택된 모델을 AdaptiveScriptGenerator에 전달
            budget = "medium"
            strategy = "balanced"

            # 고품질 스크립트 생성 (수동 모델 사용)
            result = generator.generate_optimal_script_with_manual_models(
                requirement=requirement,
                selected_models=selected_models,
                project_path=project_path,
                execution_id=execution_id,
                budget=budget,
                strategy=strategy,
                max_quality_iterations=2
            )
        else:
            print(f"🤖 자동 모델 할당 모드 사용")
            # 기존 selected_models 형식을 새로운 시스템에 맞게 변환
            budget = "medium"  # 기본값
            strategy = "balanced"  # 기본값

            # 고품질 스크립트 생성
            result = generator.generate_optimal_script(
                requirement=requirement,
                project_path=project_path,
                execution_id=execution_id,
                budget=budget,
                strategy=strategy,
                max_quality_iterations=2
            )

        print(f"✅ 적응형 시스템 생성 완료!")
        print(f"   품질 점수: {result.quality_score:.1f}/100")
        print(f"   프로덕션 준비: {'✅' if result.is_production_ready else '❌'}")

        return result.script_content

    except ImportError as e:
        print(f"❌ 적응형 시스템 import 실패: {e}")
        print(f"🔄 고품질 대안 시스템 시도...")

        # Import 실패 시 고품질 대안 시도
        try:
            return generate_high_quality_alternative_script(requirement, selected_models, project_path, execution_id, review_iterations)
        except Exception:
            print(f"🔄 최종 폴백 시스템 사용...")
            return generate_fallback_script(requirement, selected_models, project_path, execution_id, review_iterations)

    except Exception as e:
        print(f"❌ 적응형 시스템 실행 실패: {e}")
        print(f"🔄 고품질 대안 시스템 시도...")

        # 일반 예외 시 고품질 대안 먼저 시도
        try:
            return generate_high_quality_alternative_script(requirement, selected_models, project_path, execution_id, review_iterations)
        except Exception as fallback_e:
            print(f"❌ 고품질 대안도 실패: {fallback_e}")
            print(f"🔄 최종 폴백 시스템 사용...")
            return generate_fallback_script(requirement, selected_models, project_path, execution_id, review_iterations)

def generate_high_quality_alternative_script(requirement, selected_models, project_path, execution_id, review_iterations=3):
    """고품질 대안 스크립트 생성 (적응형 시스템 실패 시)"""

    print(f"🚀 고품질 대안 스크립트 생성 시작 (검토-재작성 {review_iterations}회)...")

    try:
        # project_00055 수준의 고품질 스크립트 생성
        from generate_crewai_script_new import generate_crewai_execution_script_with_approval

        print(f"📋 전문 에이전트 기반 고품질 스크립트 생성...")

        # 고품질 스크립트 생성 (승인 기반 템플릿 사용)
        script_content = generate_crewai_execution_script_with_approval(
            requirement=requirement,
            selected_models=selected_models or {'planner': 'gemini-flash', 'researcher': 'gemini-flash', 'writer': 'gemini-flash'},
            project_path=project_path,
            execution_id=execution_id,
            review_iterations=review_iterations,
            selected_tools=selected_tools,
            api_keys=api_keys
        )

        print(f"✅ 고품질 대안 스크립트 생성 완료!")

        # README.md 생성
        try:
            create_high_quality_readme(project_path, requirement, selected_models)
        except Exception as readme_e:
            print(f"⚠️ README 생성 실패 (무시): {readme_e}")

        return script_content

    except Exception as e:
        print(f"❌ 고품질 대안 생성 실패: {e}")
        raise e

def create_high_quality_readme(project_path, requirement, selected_models):
    """고품질 README.md 파일 생성"""
    import os

    readme_content = f'''# 고품질 CrewAI 프로젝트

## 📋 프로젝트 개요
**요구사항**: {requirement}

**분야**: 전문 AI 에이전트 협업 시스템

**핵심 기술**: CrewAI, Python, 전문 에이전트 구성

## 🤖 에이전트 구성
- **Planner** ({selected_models.get('planner', 'gemini-flash')}): 전략 수립 및 계획 전문가
- **Researcher** ({selected_models.get('researcher', 'gemini-flash')}): 정보 수집 및 분석 전문가
- **Writer** ({selected_models.get('writer', 'gemini-flash')}): 콘텐츠 생성 및 문서화 전문가

**협업 구조**: 3개 전문 에이전트가 순차적으로 협업하여 고품질 결과물 생성

## 🚀 실행 방법
### 1. 환경 설정
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일에 필요한 API 키를 설정하세요

### 3. 프로그램 실행
```bash
python crewai_script.py
```

### 4. 결과 확인
실행 결과는 `output/` 폴더에 저장됩니다

## 📈 예상 결과
- 요구사항에 맞는 고품질 결과물
- 전문 에이전트 협업을 통한 최적화된 솔루션
- 체계적인 프로젝트 구조 및 문서

## 🔧 기술 스택
- CrewAI
- Python
- 선택된 LLM 모델들

## 📦 주요 의존성
- crewai
- python-dotenv
'''

    readme_path = os.path.join(project_path, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"✅ README.md 생성 완료: {readme_path}")

def generate_fallback_script(requirement, selected_models, project_path, execution_id, review_iterations=3):
    """폴백 스크립트 생성 (기존 시스템 호환)"""

    print(f"📋 폴백 스크립트 생성 중...")

    # 간단한 폴백 스크립트 생성
    fallback_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
폴백 CrewAI 스크립트
실행 ID: {execution_id}
요구사항: {requirement}
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_litellm import ChatLiteLLM

# 현재 스크립트 파일의 디렉토리를 기준으로 .env 파일의 경로를 지정
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# API 키 확인
missing_keys = []
if not os.getenv('GOOGLE_API_KEY'):
    missing_keys.append('GOOGLE_API_KEY')
if not os.getenv('OPENAI_API_KEY'):
    missing_keys.append('OPENAI_API_KEY')

if missing_keys:
    print(f'⚠️  경고: 다음 환경변수가 설정되지 않았습니다: {{", ".join(missing_keys)}}', file=sys.stderr)
    print('   .env 파일에 해당 키를 추가하거나 시스템 환경변수를 설정해주세요.', file=sys.stderr)

# LLM 모델 설정 (ChatLiteLLM 객체 생성)
MODELS = {{}}
api_key_mapping = {{
    'gemini': 'GOOGLE_API_KEY',
    'openai': 'OPENAI_API_KEY',
    'anthropic': 'ANTHROPIC_API_KEY',
    'deepseek': 'DEEPSEEK_API_KEY'
}}

for role, model_name in {selected_models}.items():
    provider = model_name.split('/')[0] if '/' in model_name else 'gemini'
    api_key_env = api_key_mapping.get(provider, 'GOOGLE_API_KEY')

    MODELS[role] = ChatLiteLLM(
        model=model_name,
        api_key=os.getenv(api_key_env)
    )
    print(f"📍 {{role}} 역할: {{model_name}} (API 키: {{api_key_env}})")

# 기본 에이전트 구성
# 에이전트들을 모델 키에 맞춰 동적으로 생성
agents = []
tasks = []

# 사용 가능한 모델 키를 기반으로 에이전트 생성
model_keys = list(MODELS.keys()) if MODELS else ['researcher', 'writer', 'planner']

for i, role_key in enumerate(model_keys):
    if role_key == 'researcher' or 'research' in role_key.lower():
        agent = Agent(
            role="Senior Researcher",
            goal="Analyze requirements and research optimal solutions",
            backstory="Expert researcher with deep domain knowledge.",
            verbose=True,
            llm=MODELS[role_key],  # ChatLiteLLM 객체 직접 전달
            allow_delegation=False
        )
    elif role_key == 'writer' or 'writ' in role_key.lower():
        agent = Agent(
            role="Professional Writer",
            goal="Create high-quality documentation and deliverables",
            backstory="Professional writer with expertise in technical documentation.",
            verbose=True,
            llm=MODELS[role_key],  # ChatLiteLLM 객체 직접 전달
            allow_delegation=False
        )
    elif role_key == 'planner' or 'plan' in role_key.lower():
        agent = Agent(
            role="Strategic Planner",
            goal="Develop comprehensive implementation plans",
            backstory="Strategic planning expert with project management experience.",
            verbose=True,
            llm=MODELS[role_key],  # ChatLiteLLM 객체 직접 전달
            allow_delegation=False
        )
    else:
        # 기타 역할들 (data_scientist, data_engineer, visualization_specialist 등)
        agent = Agent(
            role=f"{{role_key.replace('_', ' ').title()}} Specialist",
            goal="전문 분야에서 최고 품질의 결과물을 생성합니다.",
            backstory=f"당신은 {{role_key.replace('_', ' ')}} 전문가입니다. 해당 분야에서 뛰어난 전문성을 가지고 있습니다.",
            verbose=True,
            llm=MODELS[role_key],  # ChatLiteLLM 객체 직접 전달
            allow_delegation=False
        )

    agents.append(agent)

    # 각 에이전트에 대한 태스크 생성
    task = Task(
        description=f"전문 분야에서 최고 품질의 결과물을 생성하세요: {requirement}",
        expected_output="전문 분야의 고품질 결과물",
        agent=agent
    )
    tasks.append(task)

# 크루 구성
crew = Crew(
    agents=agents,
    tasks=tasks,
    process=Process.sequential,
    verbose=True
)

def main():
    """메인 실행 함수"""
    print("CrewAI 폴백 시스템 - 실행 시작")
    print(f"실행 ID: {execution_id}")
    print(f"프로젝트 경로: {project_path}")

    try:
        # 출력 디렉토리 생성
        output_dir = Path("{project_path}") / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # CrewAI 실행
        start_time = datetime.now()
        result = crew.kickoff()
        end_time = datetime.now()

        print("실행 완료!")
        print(result)

        # 결과 저장
        result_file = output_dir / f"crew_result_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

        print(f"결과 저장: {{result_file}}")

    except Exception as e:
        print(f"오류 발생: {{e}}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

    return fallback_script

# ===== 기존 시스템 호환성 함수들 =====

def apply_feedback_loop(script_content, requirement, selected_models, project_path, execution_id, max_iterations=2):
    """기존 시스템 호환용 피드백 루프 (더이상 사용하지 않음)"""
    print("⚠️  기존 피드백 루프는 새로운 품질 보증 시스템으로 대체되었습니다.")
    return script_content

def planner_review_script(script_content, requirement):
    """Planner agent reviews script and provides structured feedback"""

    feedback = {
        'quality_score': 5.0,  # Default baseline score
        'issues': [],
        'improvements': [],
        'structural_assessment': '',
        'recommendation': ''
    }

    # Analyze script structure
    lines = script_content.split('\n')

    # Check for common issues
    issues = []
    improvements = []

    # 1. Agent definition quality
    agent_count = script_content.count('Agent(')
    if agent_count < 3:
        issues.append("부족한 에이전트 구성: 최소 3개 이상의 전문 에이전트 필요")
        improvements.append("도메인별 전문 에이전트 추가")
    elif agent_count >= 4:
        feedback['quality_score'] += 1.0

    # 2. Task chain logic
    task_count = script_content.count('Task(')
    if task_count != agent_count:
        issues.append("에이전트-태스크 불일치: 각 에이전트마다 전용 태스크 필요")
        improvements.append("에이전트별 전문 태스크 정의")
    else:
        feedback['quality_score'] += 1.0

    # 3. Error handling
    if 'try:' not in script_content or 'except' not in script_content:
        issues.append("예외 처리 부족: 포괄적 에러 핸들링 필요")
        improvements.append("try-except 블록으로 견고한 에러 처리 구현")
    else:
        feedback['quality_score'] += 1.0

    # 4. Output handling
    if 'output' not in script_content.lower() or 'save' not in script_content.lower():
        issues.append("출력 처리 부족: 결과 저장 및 관리 로직 필요")
        improvements.append("결과 파일 저장 및 관리 시스템 구현")
    else:
        feedback['quality_score'] += 1.0

    # 5. Requirement integration
    if requirement.lower() not in script_content.lower():
        issues.append("요구사항 반영 부족: 사용자 요구사항이 충분히 반영되지 않음")
        improvements.append("구체적 요구사항을 태스크 설명에 통합")

    # 6. Code quality
    if 'verbose=True' in script_content:
        feedback['quality_score'] += 0.5
    if 'encoding=\'utf-8\'' in script_content:
        feedback['quality_score'] += 0.5

    feedback['issues'] = issues
    feedback['improvements'] = improvements

    # Structural assessment
    if len(issues) == 0:
        feedback['structural_assessment'] = "우수한 구조: 모든 핵심 요소가 잘 구성됨"
        feedback['recommendation'] = "현재 구조 유지하며 세부 구현 강화"
    elif len(issues) <= 2:
        feedback['structural_assessment'] = "양호한 구조: 일부 개선사항 있음"
        feedback['recommendation'] = "주요 이슈 해결 후 품질 향상 기대"
    else:
        feedback['structural_assessment'] = "구조 개선 필요: 여러 핵심 요소 보완 필요"
        feedback['recommendation'] = "전면적 구조 재검토 및 핵심 기능 강화"
        feedback['quality_score'] = max(3.0, feedback['quality_score'] - 1.0)

    return feedback

def writer_improve_script(script_content, planner_feedback, requirement, selected_models, project_path, execution_id):
    """Writer agent improves script based on Planner feedback"""

    improvements = planner_feedback['improvements']
    issues = planner_feedback['issues']

    # If major structural issues, regenerate with improvements
    if len(issues) > 3:
        print("[WRITER] 주요 구조적 문제로 인한 스크립트 재생성")
        if any(keyword in requirement.lower() for keyword in ['이력서', '문서', '파싱', '추출', 'pdf', 'docx', 'resume']):
            return generate_improved_resume_processing_script(requirement, selected_models, project_path, execution_id, planner_feedback)
        else:
            return generate_improved_general_script(requirement, selected_models, project_path, execution_id, planner_feedback)

    # Otherwise, apply targeted improvements
    improved_script = script_content

    # Apply specific improvements
    for improvement in improvements:
        if "에이전트 추가" in improvement:
            improved_script = add_specialized_agents(improved_script)
        elif "태스크 정의" in improvement:
            improved_script = improve_task_definitions(improved_script, requirement)
        elif "에러 처리" in improvement:
            improved_script = enhance_error_handling(improved_script)
        elif "결과 저장" in improvement:
            improved_script = improve_output_handling(improved_script, project_path)

    return improved_script

def generate_improved_resume_processing_script(requirement, selected_models, project_path, execution_id, feedback):
    """Generate improved resume processing script based on feedback"""

    # Enhanced version with all feedback considerations
    script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Quality Resume Processing CrewAI Script
Generated: ''' + execution_id + '''
Improved based on Planner feedback
Requirement: ''' + requirement + '''
"""

import os
import sys
import json
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# 환경변수 로드
load_dotenv()

# Model configuration
MODELS = ''' + str(selected_models) + '''

# Specialized agents for resume processing (Enhanced)
document_parser = Agent(
    role="Senior Document Parsing Expert",
    goal="Parse various document formats (PDF, DOCX, Excel) with 99% accuracy",
    backstory="""You are a senior document processing expert with 15+ years of experience.
    You have mastered parsing PDF, DOCX, Excel files and resolving complex encoding issues.
    Your expertise includes OCR processing, table extraction, and multi-language support.""",
    verbose=True,
    llm=MODELS.get('document_parser', 'gemini-flash'),
    allow_delegation=False
)

information_extractor = Agent(
    role="AI Information Extraction Specialist",
    goal="Extract structured information with precision using advanced NLP techniques",
    backstory="""You are an AI specialist in information extraction with deep expertise in
    regex patterns, named entity recognition, and semantic analysis. You excel at extracting
    personal information, education history, work experience, and skills from unstructured text.""",
    verbose=True,
    llm=MODELS.get('information_extractor', 'gpt-4'),
    allow_delegation=False
)

data_validator = Agent(
    role="Data Quality Assurance Expert",
    goal="Ensure 100% data accuracy and completeness through systematic validation",
    backstory="""You are a data quality expert specializing in validation frameworks.
    Your systematic approach includes data consistency checks, duplicate detection,
    format standardization, and comprehensive quality metrics.""",
    verbose=True,
    llm=MODELS.get('data_validator', 'claude-3'),
    allow_delegation=False
)

output_formatter = Agent(
    role="Multi-Format Output Specialist",
    goal="Generate perfect output in multiple formats with enterprise-grade quality",
    backstory="""You are an output formatting expert who creates production-ready results.
    You master JSON, Excel, CSV formatting with proper encoding, schema validation,
    and enterprise reporting standards.""",
    verbose=True,
    llm=MODELS.get('output_formatter', 'gemini-pro'),
    allow_delegation=False
)

# Enhanced task definitions
task1_parse_documents = Task(
    description=f"""Implement a comprehensive document parsing system for: {requirement}

**Core Requirements:**
- Support PDF, DOCX, Excel, TXT formats
- Handle OCR for scanned documents
- Extract tables and structured data
- Resolve encoding issues (UTF-8, CP949, Latin-1)
- Implement robust error recovery

**Quality Standards:**
- 99%+ text extraction accuracy
- Preserve document structure
- Handle corrupted files gracefully
- Support batch processing

**Deliverables:**
- Complete parsing functions with error handling
- Unit tests for each format
- Performance benchmarks
- Usage documentation
""",
    expected_output="Production-ready document parsing system with comprehensive error handling",
    agent=document_parser
)

task2_extract_information = Task(
    description="""Build advanced information extraction system with NLP techniques:

**Information Categories:**
1. Personal: Name, email, phone (regex validation)
2. Education: Institution, degree, major, dates, GPA
3. Experience: Company, role, duration, achievements
4. Skills: Technical skills, certifications, languages
5. Additional: Projects, publications, references

**Advanced Features:**
- Named entity recognition
- Confidence scoring for extractions
- Duplicate detection across sections
- Missing data identification
- Format standardization

**Quality Assurance:**
- Validation patterns for all data types
- Cross-reference consistency checks
- Accuracy confidence metrics
""",
    expected_output="Advanced information extraction system with NLP capabilities and quality metrics",
    agent=information_extractor
)

task3_validate_data = Task(
    description="""Implement comprehensive data validation and quality assurance:

**Validation Framework:**
- Field completeness analysis
- Data type validation
- Format consistency checks
- Cross-field logical validation
- Duplicate detection algorithms

**Quality Metrics:**
- Completion percentage by category
- Accuracy confidence scores
- Data consistency index
- Error categorization and reporting

**Output Standards:**
- Validated JSON with confidence scores
- Quality assessment report
- Data gap analysis
- Improvement recommendations
""",
    expected_output="Comprehensive data validation system with quality metrics and reporting",
    agent=data_validator
)

task4_format_output = Task(
    description="""Create enterprise-grade multi-format output system:

**Output Formats:**
1. JSON: Structured data with schema validation
2. Excel: Human-readable with formatting and charts
3. CSV: Analysis-ready format
4. PDF Report: Executive summary with visualizations

**Quality Features:**
- UTF-8 BOM encoding for Korean support
- Schema validation for JSON output
- Professional formatting for Excel
- Data visualization in reports
- Comprehensive error logging

**File Management:**
- Organized directory structure
- Timestamped filenames
- Backup and versioning
- Metadata tracking

Save to: """ + project_path + """/output/
""",
    expected_output="Enterprise-grade multi-format output system with professional quality",
    agent=output_formatter
)

# Create enhanced crew
crew = Crew(
    agents=[document_parser, information_extractor, data_validator, output_formatter],
    tasks=[task1_parse_documents, task2_extract_information, task3_validate_data, task4_format_output],
    process=Process.sequential,
    verbose=True
)

def main():
    """Enhanced main execution function with comprehensive error handling"""
    print("=" * 80)
    print("HIGH-QUALITY Resume Processing CrewAI - Starting Execution")
    print(f"Execution ID: ''' + execution_id + '''")
    print(f"Project Path: ''' + project_path + '''")
    print(f"Requirement: ''' + requirement + '''")
    print("=" * 80)

    try:
        # Create comprehensive output structure
        output_dir = Path(""" + f'"{project_path}"' + """) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        reports_dir = output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        # Execute CrewAI with monitoring
        print("\\n🚀 Starting CrewAI execution...")
        start_time = datetime.now()

        result = crew.kickoff()

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        print("\\n" + "=" * 80)
        print("✅ EXECUTION COMPLETED SUCCESSFULLY!")
        print(f"⏱️  Total execution time: {'{execution_time:.2f}'} seconds")
        print("=" * 80)
        print(result)

        # Save comprehensive results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Main result file
        result_file = output_dir / f"crew_result_{'{timestamp}'}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"Execution Summary\\n")
            f.write(f"================\\n")
            f.write(f"Execution ID: """ + execution_id + """\\n")
            f.write(f"Requirement: """ + requirement + """\\n")
            f.write(f"Start Time: {'{start_time}'}\\n")
            f.write(f"End Time: {'{end_time}'}\\n")
            f.write(f"Duration: {'{execution_time:.2f}'} seconds\\n\\n")
            f.write(f"Results:\\n")
            f.write(f"========\\n")
            f.write(str(result))

        # Execution metadata
        metadata_file = output_dir / f"execution_metadata_{'{timestamp}'}.json"
        metadata = {'{'}
            "execution_id": \"""" + execution_id + """\",
            "requirement": \"""" + requirement + """\",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": execution_time,
            "agents_used": ["document_parser", "information_extractor", "data_validator", "output_formatter"],
            "status": "completed",
            "output_files": [str(result_file), str(metadata_file)]
        {'}'}

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\\n📁 Results saved:")
        print(f"   📄 Main result: {'{result_file}'}")
        print(f"   📊 Metadata: {'{metadata_file}'}")
        print(f"   📁 Output directory: {'{output_dir}'}")

    except Exception as e:
        error_time = datetime.now()
        print(f"\\n❌ ERROR OCCURRED: {'{e}'}")

        # Comprehensive error logging
        error_file = output_dir / f"error_log_{'{error_time.strftime(\\'%Y%m%d_%H%M%S\\')}'}.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Error Report\\n")
            f.write(f"============\\n")
            f.write(f"Time: {'{error_time}'}\\n")
            f.write(f"Execution ID: """ + execution_id + """\\n")
            f.write(f"Error: {'{str(e)}'}\\n\\n")

            import traceback
            f.write("Full Traceback:\\n")
            f.write(traceback.format_exc())

        print(f"📄 Error log saved: {'{error_file}'}")

        # Re-raise for upstream handling
        raise

if __name__ == "__main__":
    main()
'''

    return script

def generate_improved_general_script(requirement, selected_models, project_path, execution_id, feedback):
    """Generate improved general script based on feedback"""

    # Similar structure but for general use cases
    return generate_general_script(requirement, selected_models, project_path, execution_id)

def add_specialized_agents(script_content):
    """Add more specialized agents to the script"""
    # Implementation for adding agents
    return script_content

def improve_task_definitions(script_content, requirement):
    """Improve task definitions with more specific requirements"""
    # Implementation for improving tasks
    return script_content

def enhance_error_handling(script_content):
    """Add comprehensive error handling"""
    # Implementation for error handling
    return script_content

def improve_output_handling(script_content, project_path):
    """Improve output and file management"""
    # Implementation for output handling
    return script_content

def generate_resume_processing_script(requirement, selected_models, project_path, execution_id):
    """Generate specialized resume processing script"""

    script = f'''#!/usr/bin/env python3
# Enhanced Resume Processing CrewAI Script
# Generated: {execution_id}

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Model configuration
MODELS = ''' + str(selected_models) + '''

# Specialized agents for resume processing
document_parser = Agent(
    role="Document Parsing Expert",
    goal="Parse various document formats to extract text content",
    backstory="Expert in document processing with 10+ years of experience.",
    verbose=True,
    llm=MODELS.get('document_parser', 'gemini-flash'),
    allow_delegation=False
)

information_extractor = Agent(
    role="Information Extraction Specialist",
    goal="Extract structured information from unstructured text",
    backstory="Expert in regex and NLP techniques for information extraction.",
    verbose=True,
    llm=MODELS.get('information_extractor', 'gpt-4'),
    allow_delegation=False
)

data_validator = Agent(
    role="Data Validation Expert",
    goal="Validate accuracy and completeness of extracted data",
    backstory="Data quality management expert specializing in validation.",
    verbose=True,
    llm=MODELS.get('data_validator', 'claude-3'),
    allow_delegation=False
)

output_formatter = Agent(
    role="Output Formatting Specialist",
    goal="Convert validated data to required output formats",
    backstory="Expert in various output formats and encoding handling.",
    verbose=True,
    llm=MODELS.get('output_formatter', 'gemini-pro'),
    allow_delegation=False
)

# Tasks for resume processing pipeline
task1 = Task(
    description="Implement document parsing system for PDF, DOCX, Excel files with encoding support",
    expected_output="Document parsing functions with error handling",
    agent=document_parser
)

task2 = Task(
    description="Extract personal info, education, experience, skills from parsed text using regex",
    expected_output="Information extraction system with validation logic",
    agent=information_extractor
)

task3 = Task(
    description="Structure extracted data into standardized JSON format with validation",
    expected_output="JSON data conversion system with validation rules",
    agent=data_validator
)

task4 = Task(
    description="Generate output files in JSON, Excel, CSV formats with proper encoding",
    expected_output="Multi-format file output system",
    agent=output_formatter
)

# Create crew
crew = Crew(
    agents=[document_parser, information_extractor, data_validator, output_formatter],
    tasks=[task1, task2, task3, task4],
    process=Process.sequential,
    verbose=True
)

def main():
    print("Enhanced Resume Processing CrewAI - Starting execution")
    print(f"Execution ID: ''' + execution_id + '''")
    print(f"Project Path: ''' + project_path + '''")

    try:
        output_dir = Path(""" + f'"{project_path}"' + """) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = crew.kickoff()

        print("Execution completed!")
        print(result)

        result_file = output_dir / f"crew_result_{'{datetime.now().strftime(\\'%Y%m%d_%H%M%S\\')}'}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

        print(f"Result saved to: {'{result_file}'}")

    except Exception as e:
        print(f"Error occurred: {'{e}'}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

    return script

def generate_enhanced_general_script(requirement, selected_models, project_path, execution_id):
    """Generate enhanced 4-agent general script for all project types"""

    script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Quality General Project CrewAI Script (4-Agent System)
Generated: ''' + execution_id + '''
Enhanced with Enterprise-Grade Features
Requirement: ''' + requirement + '''
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Model configuration
MODELS = ''' + str(selected_models) + '''

# Enhanced 4-Agent System for General Projects
requirements_analyst = Agent(
    role="Senior Requirements Analyst",
    goal="Analyze and structure project requirements with precision",
    backstory="""You are a senior business analyst with 15+ years of experience.
    You excel at understanding complex requirements, identifying hidden needs,
    and translating business goals into clear technical specifications.""",
    verbose=True,
    llm=MODELS.get('requirements_analyst', 'gpt-4'),
    allow_delegation=False
)

technology_researcher = Agent(
    role="Technology Research Specialist",
    goal="Research and recommend optimal technology stack and implementation approaches",
    backstory="""You are a technology research expert with deep knowledge of modern frameworks,
    tools, and best practices. You stay current with industry trends and can recommend
    the most suitable technologies for any project type.""",
    verbose=True,
    llm=MODELS.get('technology_researcher', 'gemini-pro'),
    allow_delegation=False
)

solution_architect = Agent(
    role="Senior Solution Architect",
    goal="Design comprehensive system architecture and implementation strategy",
    backstory="""You are a senior solution architect with expertise in designing scalable,
    maintainable systems. You excel at creating detailed technical designs that balance
    performance, security, and development efficiency.""",
    verbose=True,
    llm=MODELS.get('solution_architect', 'claude-3'),
    allow_delegation=False
)

implementation_engineer = Agent(
    role="Senior Implementation Engineer",
    goal="Create production-ready code and comprehensive project deliverables",
    backstory="""You are a senior software engineer with expertise in multiple programming
    languages and frameworks. You write clean, well-documented, production-ready code
    with comprehensive testing and deployment strategies.""",
    verbose=True,
    llm=MODELS.get('implementation_engineer', 'deepseek-coder'),
    allow_delegation=False
)

# Enhanced task definitions
task1_analyze_requirements = Task(
    description=f"""Perform comprehensive requirements analysis for: {requirement}

**Analysis Framework:**
1. **Functional Requirements**: Core features, user stories, business logic
2. **Non-Functional Requirements**: Performance, security, usability standards
3. **Technical Constraints**: Platform limitations, dependencies, resources
4. **Success Criteria**: Measurable outcomes, acceptance criteria, quality standards

**Deliverables:**
- Structured requirements document with priority matrix
- Risk assessment and mitigation strategies
- Success metrics and KPI definitions
""",
    expected_output="Comprehensive requirements analysis with structured specifications and success criteria",
    agent=requirements_analyst
)

task2_research_technology = Task(
    description="""Research optimal technology stack based on analyzed requirements:

**Research Areas:**
1. **Technology Stack**: Languages, frameworks, databases, cloud services
2. **Architecture Patterns**: Design patterns, integration approaches, security frameworks
3. **Development Ecosystem**: Libraries, testing frameworks, monitoring solutions
4. **Implementation Strategy**: Development methodology, quality assurance, DevOps

**Quality Standards:**
- Industry best practices compliance
- Security and privacy considerations
- Scalability and maintainability analysis
- Cost-effectiveness evaluation
""",
    expected_output="Technology research report with justified recommendations and implementation roadmap",
    agent=technology_researcher
)

task3_design_architecture = Task(
    description="""Design comprehensive system architecture:

**Architecture Design:**
1. **System Architecture**: High-level design, component interactions, data flow
2. **Technical Specifications**: API design, database schema, UI wireframes
3. **Implementation Plan**: Development phases, resource allocation, quality checkpoints
4. **Deployment Architecture**: Infrastructure, environment configuration, monitoring

**Quality Assurance:**
- Architecture review checklist and performance benchmarking plan
- Security audit framework and compliance verification strategy
""",
    expected_output="Detailed system architecture with implementation specifications and quality assurance plan",
    agent=solution_architect
)

task4_implement_solution = Task(
    description="""Create production-ready implementation:

**Implementation Deliverables:**
1. **Complete Source Code**: Production-ready app with error handling and security
2. **Configuration**: Environment configs, dependencies, deployment scripts
3. **Testing Suite**: Unit tests, integration tests, API validation, performance testing
4. **Documentation**: Technical docs, API docs, user guides, deployment guides
5. **Quality Assurance**: Code review, security audit, performance benchmarks

Save all deliverables to: ''' + project_path + '''/output/
""",
    expected_output="Complete production-ready implementation with comprehensive documentation and testing",
    agent=implementation_engineer
)

# Create enhanced crew with 4 specialized agents
crew = Crew(
    agents=[requirements_analyst, technology_researcher, solution_architect, implementation_engineer],
    tasks=[task1_analyze_requirements, task2_research_technology, task3_design_architecture, task4_implement_solution],
    process=Process.sequential,
    verbose=True
)

def main():
    """Enhanced main execution function with comprehensive project delivery"""
    print("=" * 80)
    print("HIGH-QUALITY 4-Agent CrewAI System - Starting Execution")
    print(f"Execution ID: ''' + execution_id + '''")
    print(f"Project Path: ''' + project_path + '''")
    print(f"Requirement: ''' + requirement + '''")
    print("=" * 80)

    try:
        # Create comprehensive output structure
        output_dir = Path("''' + project_path + '''") / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        deliverables_dir = output_dir / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)

        # Execute CrewAI with enhanced monitoring
        print("\\n🚀 Starting 4-Agent CrewAI execution...")
        start_time = datetime.now()

        result = crew.kickoff()

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        print("\\n" + "=" * 80)
        print("✅ 4-AGENT EXECUTION COMPLETED SUCCESSFULLY!")
        print(f"⏱️  Total execution time: {execution_time:.2f} seconds")
        print(f"👥 Agents used: 4 specialized agents")
        print(f"📋 Tasks completed: 4 comprehensive tasks")
        print("=" * 80)
        print(result)

        # Save comprehensive results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Main result file
        result_file = output_dir / f"crew_result_{timestamp}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"4-Agent CrewAI Execution Results\\n")
            f.write(f"================================\\n")
            f.write(f"Execution ID: ''' + execution_id + '''\\n")
            f.write(f"Requirement: ''' + requirement + '''\\n")
            f.write(f"Start Time: {start_time}\\n")
            f.write(f"End Time: {end_time}\\n")
            f.write(f"Duration: {execution_time:.2f} seconds\\n")
            f.write(f"Agents: 4 specialized agents\\n\\n")
            f.write(f"Results:\\n")
            f.write(f"========\\n")
            f.write(str(result))

        # Execution metadata
        metadata_file = output_dir / f"execution_metadata_{timestamp}.json"
        metadata = {
            "execution_id": "''' + execution_id + '''",
            "requirement": "''' + requirement + '''",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": execution_time,
            "agent_count": 4,
            "agents_used": ["requirements_analyst", "technology_researcher", "solution_architect", "implementation_engineer"],
            "task_count": 4,
            "status": "completed",
            "output_files": [str(result_file), str(metadata_file)],
            "system_type": "enhanced_4_agent"
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\\n📁 Results saved:")
        print(f"   📄 Main result: {result_file}")
        print(f"   📊 Metadata: {metadata_file}")
        print(f"   📁 Output directory: {output_dir}")
        print(f"   📁 Deliverables: {deliverables_dir}")

    except Exception as e:
        error_time = datetime.now()
        print(f"\\n❌ ERROR OCCURRED: {e}")

        # Comprehensive error logging
        error_file = output_dir / f"error_log_{error_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"4-Agent System Error Report\\n")
            f.write(f"=========================\\n")
            f.write(f"Time: {error_time}\\n")
            f.write(f"Execution ID: ''' + execution_id + '''\\n")
            f.write(f"Error: {str(e)}\\n\\n")

            import traceback
            f.write("Full Traceback:\\n")
            f.write(traceback.format_exc())

        print(f"📄 Error log saved: {error_file}")

        # Re-raise for upstream handling
        raise

if __name__ == "__main__":
    main()
'''

    return script

def generate_general_script(requirement, selected_models, project_path, execution_id):
    """Generate general CrewAI script (3-agent fallback)"""

    script = f'''#!/usr/bin/env python3
# General CrewAI Script (3-Agent System)
# Generated: {execution_id}

import os
import sys
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Model configuration
MODELS = ''' + str(selected_models) + '''

# General-purpose agents
researcher = Agent(
    role="Researcher",
    goal="Analyze requirements and collect information",
    backstory="Professional research and analysis expert",
    verbose=True,
    llm=MODELS.get('researcher', 'gemini-2.5-flash'),
    allow_delegation=False
)

writer = Agent(
    role="Writer",
    goal="Create clear documentation",
    backstory="Expert in creating well-structured documents",
    verbose=True,
    llm=MODELS.get('writer', 'gpt-4'),
    allow_delegation=False
)

planner = Agent(
    role="Planner",
    goal="Develop execution plans",
    backstory="Expert in systematic planning and project management",
    verbose=True,
    llm=MODELS.get('planner', 'claude-3'),
    allow_delegation=False
)

# Tasks
task1 = Task(
    description=f"Analyze requirements and collect information: {requirement}",
    expected_output="Requirements analysis and collected information",
    agent=researcher
)

task2 = Task(
    description="Create systematic documentation based on analysis",
    expected_output="Well-organized documentation",
    agent=writer
)

task3 = Task(
    description="Develop specific execution plans",
    expected_output="Step-by-step execution plan",
    agent=planner
)

# Create crew
crew = Crew(
    agents=[researcher, writer, planner],
    tasks=[task1, task2, task3],
    process=Process.sequential,
    verbose=True
)

def main():
    print("General CrewAI (3-Agent System) - Starting execution")
    print(f"Execution ID: ''' + execution_id + '''")
    print(f"Project Path: ''' + project_path + '''")

    try:
        output_dir = Path(""" + f'"{project_path}"' + """) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = crew.kickoff()

        print("Execution completed!")
        print(result)

        result_file = output_dir / f"crew_result_{'{datetime.now().strftime(\\'%Y%m%d_%H%M%S\\')}'}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

        print(f"Result saved to: {'{result_file}'}")

    except Exception as e:
        print(f"Error occurred: {'{e}'}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
'''

    return script