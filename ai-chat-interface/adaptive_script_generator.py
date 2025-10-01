#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
적응형 스크립트 생성 엔진
요구사항 분석 결과를 바탕으로 최적화된 CrewAI 스크립트를 동적으로 생성
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from intelligent_requirement_analyzer import IntelligentRequirementAnalyzer, RequirementAnalysis
from dynamic_agent_matcher import DynamicAgentMatcher, AgentSelection
from smart_model_allocator import SmartModelAllocator, ModelAllocation
from quality_assurance_framework import QualityAssuranceFramework
from minimal_documentation_generator import MinimalDocumentationGenerator

@dataclass
class ScriptGenerationResult:
    """스크립트 생성 결과"""
    script_content: str
    requirements_path: str
    readme_path: str
    quality_score: float
    generation_metadata: Dict
    is_production_ready: bool

class AdaptiveScriptGenerator:
    """적응형 스크립트 생성 엔진"""

    def __init__(self, model_config_path: str = "model_config.json"):
        self.analyzer = IntelligentRequirementAnalyzer()
        self.matcher = DynamicAgentMatcher()
        self.allocator = SmartModelAllocator(model_config_path)
        self.qa_framework = QualityAssuranceFramework()
        self.doc_generator = MinimalDocumentationGenerator()

    def generate_optimal_script(self,
                              requirement: str,
                              project_path: str,
                              execution_id: str,
                              budget: str = "medium",
                              strategy: str = "balanced",
                              max_quality_iterations: int = 2) -> ScriptGenerationResult:
        """최적화된 스크립트 생성"""

        print(f"🚀 적응형 스크립트 생성 시작 - {execution_id}")

        # 1. 요구사항 분석
        print("📋 요구사항 분석 중...")
        analysis = self.analyzer.analyze_requirement(requirement)
        print(f"   도메인: {analysis.domain}, 복잡도: {analysis.complexity.value}, 에이전트 수: {analysis.agent_count}")

        # 2. 에이전트 매칭
        print("🎭 최적 에이전트 조합 선택 중...")
        agent_selection = self.matcher.select_optimal_agents(analysis)
        print(f"   선택된 에이전트: {[agent.name for agent in agent_selection.agents]}")

        # 3. 모델 할당
        print("🧠 LLM 모델 할당 중...")
        model_allocation = self.allocator.allocate_models(agent_selection, analysis, budget, strategy)
        print(f"   할당 전략: {strategy}, 예상 비용: {model_allocation.total_estimated_cost:.1f}")

        # 4. 스크립트 생성
        print("⚙️  CrewAI 스크립트 생성 중...")
        script_content = self._generate_script_content(
            requirement, analysis, agent_selection, model_allocation, project_path, execution_id
        )

        # 5. 품질 검증 및 개선
        print("🔍 품질 검증 및 개선 중...")
        script_content, quality_report = self._improve_script_quality(
            script_content, requirement, project_path, max_quality_iterations
        )

        # 6. 프로젝트 구조 생성
        print("📁 프로젝트 구조 생성 중...")
        project_structure = self._create_project_structure(
            project_path, script_content, analysis.required_libraries
        )

        # 7. 문서화
        print("📝 문서 생성 중...")
        readme_path = self._generate_documentation(
            requirement, analysis, agent_selection, model_allocation, project_path
        )

        # 8. 메타데이터 생성
        generation_metadata = self._create_generation_metadata(
            requirement, analysis, agent_selection, model_allocation, quality_report, execution_id
        )

        print(f"✅ 스크립트 생성 완료! 품질 점수: {quality_report.overall_score:.1f}/100")

        return ScriptGenerationResult(
            script_content=script_content,
            requirements_path=project_structure['requirements'],
            readme_path=readme_path,
            quality_score=quality_report.overall_score,
            generation_metadata=generation_metadata,
            is_production_ready=quality_report.is_production_ready
        )

    def _generate_script_content(self,
                               requirement: str,
                               analysis: RequirementAnalysis,
                               agent_selection: AgentSelection,
                               model_allocation: ModelAllocation,
                               project_path: str,
                               execution_id: str) -> str:
        """적응형 스크립트 내용 생성"""

        # 기본 템플릿 로드
        template = self._get_base_template()

        # 동적 구성 요소 생성
        imports_section = self._generate_imports_section(analysis)
        models_section = self._generate_models_section(model_allocation)
        agents_section = self._generate_agents_section(agent_selection, model_allocation)
        tasks_section = self._generate_tasks_section(agent_selection, requirement, analysis, project_path)
        crew_section = self._generate_crew_section(agent_selection)
        main_section = self._generate_main_section(requirement, project_path, execution_id, analysis)

        # 템플릿 조립
        script_content = template.format(
            execution_id=execution_id,
            requirement=requirement,
            imports=imports_section,
            models=models_section,
            agents=agents_section,
            tasks=tasks_section,
            crew=crew_section,
            main=main_section
        )

        return script_content

    def _get_base_template(self) -> str:
        """기본 스크립트 템플릿"""
        return '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고품질 CrewAI 스크립트 (적응형 생성)
실행 ID: {execution_id}
요구사항: {requirement}
"""

{imports}

{models}

{agents}

{tasks}

{crew}

{main}

if __name__ == "__main__":
    main()
'''

    def _generate_imports_section(self, analysis: RequirementAnalysis) -> str:
        """import 섹션 생성"""
        imports = [
            "import os",
            "import sys",
            "import json",
            "from datetime import datetime",
            "from pathlib import Path",
            "from dotenv import load_dotenv",
            "from crewai import Agent, Task, Crew, Process",
            "from langchain_litellm import ChatLiteLLM",
            "",
            "# 현재 스크립트 파일의 디렉토리를 기준으로 .env 파일의 경로를 지정",
            "# 이렇게 하면 어떤 위치에서 스크립트를 실행하더라도 .env 파일을 올바르게 찾을 수 있음",
            "dotenv_path = os.path.join(os.path.dirname(__file__), '.env')",
            "load_dotenv(dotenv_path=dotenv_path)",
            "",
            "# API 키 확인",
            "missing_keys = []",
            "if not os.getenv('GOOGLE_API_KEY'):",
            "    missing_keys.append('GOOGLE_API_KEY')",
            "if not os.getenv('OPENAI_API_KEY'):",
            "    missing_keys.append('OPENAI_API_KEY')",
            "",
            "if missing_keys:",
            "    print(f'⚠️  경고: 다음 환경변수가 설정되지 않았습니다: {\", \".join(missing_keys)}', file=sys.stderr)",
            "    print('   .env 파일에 해당 키를 추가하거나 시스템 환경변수를 설정해주세요.', file=sys.stderr)",
            "    print('   일부 에이전트가 작동하지 않을 수 있습니다.', file=sys.stderr)"
        ]

        # 도메인별 추가 import
        domain_imports = {
            'data_analysis': ['import pandas as pd', 'import numpy as np'],
            'web_development': ['import requests'],
            'document_processing': ['import re'],
            'automation': ['import schedule', 'import time'],
            'content_creation': ['import re']
        }

        if analysis.domain in domain_imports:
            imports.extend(domain_imports[analysis.domain])

        # 서브 도메인 import
        for sub_domain in analysis.sub_domains:
            if sub_domain in domain_imports:
                imports.extend(domain_imports[sub_domain])

        return '\n'.join(imports)

    def _generate_models_section(self, model_allocation: ModelAllocation) -> str:
        """모델 설정 섹션 생성 (ChatLiteLLM 객체 방식)"""
        model_mapping = model_allocation.agent_model_mapping

        # 모델별 API 키 매핑
        api_key_mapping = {
            'gemini': 'GOOGLE_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'deepseek': 'DEEPSEEK_API_KEY'
        }

        models_code = ["# LLM 모델 설정 (ChatLiteLLM 객체 생성)", ""]
        models_code.append("# 각 모델에 대한 LLM 객체 생성")
        models_code.append("MODELS = {}")
        models_code.append("")

        for agent_name, model_name in model_mapping.items():
            # 모델명에서 제공자 추출 (예: gemini/gemini-2.5-flash -> gemini)
            provider = model_name.split('/')[0] if '/' in model_name else 'gemini'
            api_key_env = api_key_mapping.get(provider, 'GOOGLE_API_KEY')

            model_code = f'''# {agent_name} 모델
MODELS['{agent_name}'] = ChatLiteLLM(
    model="{model_name}",
    api_key=os.getenv("{api_key_env}")
)'''
            models_code.append(model_code)

        return '\n'.join(models_code)

    def _generate_agents_section(self, agent_selection: AgentSelection,
                                model_allocation: ModelAllocation) -> str:
        """에이전트 섹션 생성"""
        agents_code = []
        agents_code.append("# 전문 에이전트 정의")

        for agent in agent_selection.agents:
            agent_name = agent.name

            agent_code = f'''
{agent_name} = Agent(
    role="{agent.role}",
    goal="{agent.goal}",
    backstory="""{agent.backstory}""",
    verbose=True,
    llm=MODELS['{agent_name}'],  # ChatLiteLLM 객체 직접 전달
    allow_delegation=False
)'''
            agents_code.append(agent_code)

        return '\n'.join(agents_code)

    def _generate_tasks_section(self, agent_selection: AgentSelection,
                              requirement: str, analysis: RequirementAnalysis,
                              project_path: str) -> str:
        """태스크 섹션 생성"""
        tasks_code = []
        tasks_code.append("# 전문 태스크 정의")

        for i, agent in enumerate(agent_selection.agents, 1):
            task_description = self._generate_task_description(agent, requirement, analysis, project_path)
            expected_output = self._generate_expected_output(agent, analysis)

            task_code = f'''
task{i}_{agent.name} = Task(
    description="""{task_description}""",
    expected_output="{expected_output}",
    agent={agent.name}
)'''
            tasks_code.append(task_code)

        return '\n'.join(tasks_code)

    def _generate_task_description(self, agent, requirement: str,
                                 analysis: RequirementAnalysis, project_path: str) -> str:
        """에이전트별 태스크 설명 생성"""

        base_descriptions = {
            'requirements_analyst': f"""다음 요구사항을 체계적으로 분석하세요: {requirement}

**분석 항목:**
1. **핵심 기능**: 주요 요구사항과 기능 분석
2. **기술적 제약**: 성능, 보안, 호환성 요구사항
3. **성공 기준**: 측정 가능한 결과물과 품질 기준
4. **위험 요소**: 잠재적 문제점과 대응 방안

**결과물**: 구조화된 요구사항 분석 보고서""",

            'technology_researcher': f"""요구사항에 최적화된 기술 스택을 연구하고 추천하세요:

**연구 영역:**
1. **프로그래밍 언어**: Python, JavaScript 등 최적 언어 선택
2. **프레임워크**: {', '.join(analysis.tech_stack[:3])} 등 적합한 프레임워크
3. **라이브러리**: {', '.join(analysis.required_libraries[:5])} 등 필수 라이브러리
4. **아키텍처**: 확장 가능하고 유지보수 가능한 설계 패턴

**결과물**: 기술 스택 추천서와 구현 가이드라인""",

            'solution_architect': f"""포괄적인 시스템 아키텍처를 설계하세요:

**설계 요소:**
1. **시스템 구조**: 컴포넌트 간 상호작용과 데이터 플로우
2. **API 설계**: 인터페이스 명세와 데이터 스키마
3. **데이터베이스**: 효율적인 데이터 저장 및 조회 구조
4. **보안 설계**: 데이터 보호와 접근 제어 방안

**결과물**: 상세한 시스템 아키텍처 설계서""",

            'implementation_engineer': f"""생산 준비된 완전한 구현을 개발하세요:

**구현 요소:**
1. **핵심 코드**: 요구사항을 완전히 구현하는 프로덕션 코드
2. **설정 관리**: 환경 설정과 의존성 관리
3. **테스트 코드**: 단위 테스트와 통합 테스트 구현
4. **문서화**: 코드 문서와 사용자 가이드

저장 위치: {project_path}/output/
**결과물**: 즉시 실행 가능한 완전한 애플리케이션""",

            'content_creator': f"""고품질 콘텐츠를 기획하고 제작하세요:

**제작 요소:**
1. **콘텐츠 기획**: 타겟 독자와 목적에 맞는 콘텐츠 전략
2. **글 작성**: SEO 최적화된 고품질 텍스트 콘텐츠
3. **구조화**: 읽기 쉬운 형식과 논리적 구성
4. **최적화**: 검색 엔진과 사용자 경험 최적화

**결과물**: 완성된 고품질 콘텐츠와 게시 가이드""",

            'data_scientist': f"""데이터 분석과 인사이트 도출을 수행하세요:

**분석 항목:**
1. **데이터 수집**: 관련 데이터 소스 식별 및 수집
2. **데이터 처리**: 정제, 변환, 통합 과정
3. **분석 수행**: 통계 분석과 패턴 탐지
4. **시각화**: 인사이트를 명확히 전달하는 차트와 그래프

**결과물**: 데이터 분석 리포트와 시각화 자료""",

            'automation_specialist': f"""효율적인 자동화 솔루션을 구현하세요:

**자동화 요소:**
1. **프로세스 분석**: 자동화 가능한 작업 흐름 식별
2. **스크립트 개발**: 반복 작업을 자동화하는 스크립트
3. **스케줄링**: 정기적 실행을 위한 스케줄 설정
4. **모니터링**: 자동화 프로세스 상태 추적

**결과물**: 완전 자동화된 워크플로우 시스템"""
        }

        return base_descriptions.get(agent.name, f"전문 분야에서 최고 품질의 결과물을 생성하세요: {requirement}")

    def _generate_expected_output(self, agent, analysis: RequirementAnalysis) -> str:
        """예상 출력 생성"""
        outputs = {
            'requirements_analyst': '체계적인 요구사항 분석 보고서와 성공 기준',
            'technology_researcher': '최적화된 기술 스택 추천서와 구현 로드맵',
            'solution_architect': '상세한 시스템 아키텍처와 설계 명세서',
            'implementation_engineer': '완전히 구현된 프로덕션 코드와 테스트',
            'content_creator': '고품질 콘텐츠와 SEO 최적화 가이드',
            'data_scientist': '데이터 분석 결과와 인사이트 리포트',
            'automation_specialist': '자동화 스크립트와 실행 가이드'
        }

        return outputs.get(agent.name, '전문 분야의 고품질 결과물')

    def _generate_crew_section(self, agent_selection: AgentSelection) -> str:
        """크루 섹션 생성"""
        agent_names = [agent.name for agent in agent_selection.agents]
        task_names = [f"task{i+1}_{agent.name}" for i, agent in enumerate(agent_selection.agents)]

        return f'''# 전문 크루 구성
crew = Crew(
    agents=[{', '.join(agent_names)}],
    tasks=[{', '.join(task_names)}],
    process=Process.sequential,
    verbose=True
)'''

    def _generate_main_section(self, requirement: str, project_path: str,
                             execution_id: str, analysis: RequirementAnalysis) -> str:
        """메인 함수 섹션 생성"""
        return f'''def main():
    """고품질 CrewAI 실행 함수"""
    print("=" * 80)
    print("🚀 고품질 CrewAI 시스템 실행 시작")
    print(f"실행 ID: {execution_id}")
    print(f"프로젝트 경로: {project_path}")
    print(f"요구사항: {requirement}")
    print(f"복잡도: {analysis.complexity.value}")
    print(f"에이전트 수: {analysis.agent_count}")
    print("=" * 80)

    try:
        # 출력 디렉토리 생성
        output_dir = Path("{project_path}") / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = output_dir / "logs"
        logs_dir.mkdir(exist_ok=True)

        deliverables_dir = output_dir / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)

        # 실행 시간 측정
        start_time = datetime.now()
        print(f"\\n🚀 CrewAI 실행 시작: {{start_time.strftime('%Y-%m-%d %H:%M:%S')}}")

        # CrewAI 실행
        result = crew.kickoff()

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        print("\\n" + "=" * 80)
        print("✅ 실행 완료!")
        print(f"⏱️  실행 시간: {{execution_time:.2f}}초")
        print(f"👥 에이전트: {analysis.agent_count}개 전문 에이전트")
        print(f"📋 태스크: {analysis.agent_count}개 전문 태스크")
        print("=" * 80)
        print("\\n📄 실행 결과:")
        print(result)

        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 메인 결과 파일
        result_file = output_dir / f"crew_result_{{timestamp}}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"CrewAI 실행 결과\\n")
            f.write(f"================\\n")
            f.write(f"실행 ID: {execution_id}\\n")
            f.write(f"요구사항: {requirement}\\n")
            f.write(f"시작 시간: {{start_time}}\\n")
            f.write(f"종료 시간: {{end_time}}\\n")
            f.write(f"실행 시간: {{execution_time:.2f}}초\\n")
            f.write(f"에이전트 수: {analysis.agent_count}\\n\\n")
            f.write(f"결과:\\n")
            f.write(f"======\\n")
            f.write(str(result))

        # 실행 메타데이터
        metadata_file = output_dir / f"execution_metadata_{{timestamp}}.json"
        metadata = {{
            "execution_id": "{execution_id}",
            "requirement": "{requirement}",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": execution_time,
            "agent_count": {analysis.agent_count},
            "complexity": "{analysis.complexity.value}",
            "domain": "{analysis.domain}",
            "status": "completed",
            "output_files": [str(result_file), str(metadata_file)]
        }}

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"\\n📁 결과 파일:")
        print(f"   📄 메인 결과: {{result_file}}")
        print(f"   📊 메타데이터: {{metadata_file}}")
        print(f"   📁 출력 디렉토리: {{output_dir}}")

        return result

    except Exception as e:
        error_time = datetime.now()
        print(f"\\n❌ 오류 발생: {{e}}")

        # 오류 로깅
        error_file = Path("{project_path}") / "output" / f"error_log_{{error_time.strftime('%Y%m%d_%H%M%S')}}.txt"
        error_file.parent.mkdir(parents=True, exist_ok=True)

        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"CrewAI 실행 오류 보고서\\n")
            f.write(f"=====================\\n")
            f.write(f"시간: {{error_time}}\\n")
            f.write(f"실행 ID: {execution_id}\\n")
            f.write(f"오류: {{str(e)}}\\n\\n")

            import traceback
            f.write("상세 오류 정보:\\n")
            f.write(traceback.format_exc())

        print(f"📄 오류 로그: {{error_file}}")
        raise'''

    def _improve_script_quality(self, script_content: str, requirement: str,
                               project_path: str, max_iterations: int):
        """스크립트 품질 개선"""

        current_script = script_content
        best_score = 0.0

        for iteration in range(max_iterations):
            print(f"   품질 검증 {iteration + 1}/{max_iterations}...")

            # 품질 평가
            quality_report = self.qa_framework.assess_quality(current_script, requirement, project_path)

            print(f"   품질 점수: {quality_report.overall_score:.1f}/100")

            # 점수가 개선되었으면 업데이트
            if quality_report.overall_score > best_score:
                best_score = quality_report.overall_score
                best_script = current_script
                best_report = quality_report

            # 만족할만한 품질이면 중단
            if quality_report.overall_score >= 85.0:
                print("   ✅ 고품질 달성!")
                break

            # 개선이 필요한 경우 자동 수정
            if iteration < max_iterations - 1:
                current_script = self._apply_automatic_fixes(current_script, quality_report)

        return best_script if 'best_script' in locals() else current_script, \
               best_report if 'best_report' in locals() else quality_report

    def _apply_automatic_fixes(self, script_content: str, quality_report) -> str:
        """자동 수정 적용"""
        improved_script = script_content

        # 치명적 이슈 자동 수정
        for issue in quality_report.issues:
            if issue.severity == "critical":
                if "import" in issue.description.lower():
                    # import 문 수정
                    if "crewai" in issue.description.lower():
                        improved_script = "from crewai import Agent, Task, Crew, Process\n" + improved_script

                if "utf-8" in issue.description.lower():
                    # UTF-8 인코딩 추가
                    if "# -*- coding: utf-8 -*-" not in improved_script:
                        lines = improved_script.split('\n')
                        lines.insert(1, "# -*- coding: utf-8 -*-")
                        improved_script = '\n'.join(lines)

        return improved_script

    def _create_project_structure(self, project_path: str, script_content: str,
                                required_libraries: List[str]) -> Dict[str, str]:
        """프로젝트 구조 생성"""

        # 디렉토리 생성
        Path(project_path).mkdir(parents=True, exist_ok=True)
        Path(project_path, "output").mkdir(exist_ok=True)
        Path(project_path, "output", "logs").mkdir(exist_ok=True)
        Path(project_path, "output", "deliverables").mkdir(exist_ok=True)

        # 메인 스크립트 저장
        script_path = os.path.join(project_path, "crewai_script.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # requirements.txt 생성
        requirements_path = os.path.join(project_path, "requirements.txt")
        with open(requirements_path, 'w', encoding='utf-8') as f:
            for lib in required_libraries:
                f.write(f"{lib}\n")

        # .env.example 생성
        env_example_path = os.path.join(project_path, ".env.example")
        with open(env_example_path, 'w', encoding='utf-8') as f:
            f.write("# LLM API 키 설정\n")
            f.write("OPENAI_API_KEY=your_openai_key_here\n")
            f.write("GOOGLE_API_KEY=your_google_key_here\n")
            f.write("ANTHROPIC_API_KEY=your_anthropic_key_here\n")
            f.write("\n# 기타 설정\n")
            f.write("# LOG_LEVEL=INFO\n")

        # 실제 .env 파일 생성 (시스템 환경변수에서 복사)
        env_path = os.path.join(project_path, ".env")
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# LLM API 키 설정 (자동 생성)\n")

            # 시스템 환경변수에서 API 키 가져오기
            api_keys = {
                'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
                'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY', ''),
                'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
                'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY', '')
            }

            for key, value in api_keys.items():
                if value:
                    f.write(f"{key}={value}\n")
                    print(f"✅ {key} 환경변수 복사됨")
                else:
                    f.write(f"# {key}=your_key_here\n")
                    print(f"⚠️  {key} 환경변수 없음 (.env 파일에 수동 설정 필요)")

            f.write("\n# 기타 설정\n")
            f.write("LOG_LEVEL=INFO\n")

        return {
            'script': script_path,
            'requirements': requirements_path,
            'env_example': env_example_path,
            'env': env_path
        }

    def _generate_documentation(self, requirement: str, analysis: RequirementAnalysis,
                              agent_selection: AgentSelection, model_allocation: ModelAllocation,
                              project_path: str) -> str:
        """문서 생성"""

        readme_content = self.doc_generator.generate_documentation(
            requirement, analysis, agent_selection, model_allocation, project_path
        )

        return os.path.join(project_path, "README.md")

    def _create_generation_metadata(self, requirement: str, analysis: RequirementAnalysis,
                                   agent_selection: AgentSelection, model_allocation: ModelAllocation,
                                   quality_report, execution_id: str) -> Dict:
        """생성 메타데이터 생성"""

        return {
            "generation_info": {
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
                "generator_version": "1.0.0"
            },
            "requirement_analysis": {
                "original_requirement": requirement,
                "domain": analysis.domain,
                "complexity": analysis.complexity.value,
                "confidence_score": analysis.confidence_score,
                "keywords": analysis.keywords
            },
            "agent_selection": {
                "agent_count": len(agent_selection.agents),
                "selected_agents": [agent.name for agent in agent_selection.agents],
                "selection_reasoning": agent_selection.selection_reasoning,
                "confidence_score": agent_selection.confidence_score
            },
            "model_allocation": {
                "allocation_strategy": model_allocation.allocation_reasoning,
                "total_cost": model_allocation.total_estimated_cost,
                "model_mapping": model_allocation.agent_model_mapping,
                "confidence_score": model_allocation.confidence_score
            },
            "quality_assessment": {
                "overall_score": quality_report.overall_score,
                "quality_level": quality_report.quality_level.value,
                "is_production_ready": quality_report.is_production_ready,
                "stage_scores": quality_report.stage_scores
            }
        }

    def generate_optimal_script_with_manual_models(self,
                                                   requirement: str,
                                                   selected_models: dict,
                                                   project_path: str,
                                                   execution_id: str,
                                                   budget: str = "medium",
                                                   strategy: str = "balanced",
                                                   max_quality_iterations: int = 2) -> ScriptGenerationResult:
        """수동 모델 선택을 사용한 최적화된 스크립트 생성"""

        print(f"🚀 수동 모델 선택 적응형 스크립트 생성 시작 - {execution_id}")
        print(f"   선택된 모델: {selected_models}")

        # 1. 요구사항 분석
        print("📋 요구사항 분석 중...")
        analysis = self.analyzer.analyze_requirement(requirement)
        print(f"   도메인: {analysis.domain}, 복잡도: {analysis.complexity.value}, 에이전트 수: {analysis.agent_count}")

        # 2. 에이전트 매칭 (고품질 에이전트 강제 사용)
        print("🎭 고품질 에이전트 조합 선택 중...")
        agent_selection = self.matcher.select_optimal_agents(analysis)
        print(f"   선택된 에이전트: {[agent.name for agent in agent_selection.agents]}")

        # 3. 수동 모델 할당 생성
        print("🧠 수동 선택 모델 할당 중...")
        model_allocation = self._create_manual_model_allocation(selected_models, agent_selection)
        print(f"   수동 할당 완료, 에이전트-모델 매핑: {model_allocation.agent_model_mapping}")

        # 4. 스크립트 생성
        print("⚙️  CrewAI 스크립트 생성 중...")
        script_content = self._generate_script_content(
            requirement, analysis, agent_selection, model_allocation, project_path, execution_id
        )

        # 5. 프로젝트 구조 생성
        print("📁 프로젝트 구조 생성 중...")
        project_structure = self.doc_generator.create_project_structure(project_path)

        # 6. README 생성
        print("📄 README.md 생성 중...")
        readme_path = self.doc_generator.generate_readme(
            project_path, requirement, agent_selection, model_allocation, analysis
        )

        # 7. 품질 평가
        print("🔍 품질 평가 중...")
        quality_report = self.quality_framework.evaluate_script(script_content, analysis)

        # 8. 메타데이터 생성
        generation_metadata = {
            "generation_mode": "manual_models",
            "selected_models": selected_models,
            "agent_count": len(agent_selection.agents),
            "domain": analysis.domain,
            "complexity": analysis.complexity.value,
            "budget": budget,
            "strategy": strategy,
            "quality_score": quality_report.overall_score,
            "generation_timestamp": datetime.now().isoformat(),
            "execution_id": execution_id
        }

        print(f"✅ 수동 모델 스크립트 생성 완료! 품질 점수: {quality_report.overall_score:.1f}/100")

        return ScriptGenerationResult(
            script_content=script_content,
            requirements_path=project_structure['requirements'],
            readme_path=readme_path,
            quality_score=quality_report.overall_score,
            generation_metadata=generation_metadata,
            is_production_ready=quality_report.is_production_ready
        )

    def _create_manual_model_allocation(self, selected_models: dict, agent_selection: AgentSelection):
        """수동 선택된 모델을 ModelAllocation 객체로 변환"""
        from smart_model_allocator import ModelAllocation

        # 수동 모델을 에이전트에 매핑
        agent_model_mapping = {}
        model_role_mapping = {
            'planner': ['Planner', 'Project Manager', 'Product Manager'],
            'researcher': ['Researcher', 'Data Scientist', 'Research Specialist'],
            'writer': ['Writer', 'Documentation Specialist', 'Content Creator']
        }

        for agent in agent_selection.agents:
            assigned_model = None
            # 에이전트 이름을 기반으로 적절한 수동 선택 모델 할당
            for role_key, role_names in model_role_mapping.items():
                if any(role_name.lower() in agent.name.lower() for role_name in role_names):
                    assigned_model = selected_models.get(role_key, 'gemini-flash')
                    break

            if not assigned_model:
                # 기본값 할당
                assigned_model = list(selected_models.values())[0] if selected_models.values() else 'gemini-flash'

            agent_model_mapping[agent.name] = assigned_model

        return ModelAllocation(
            agent_model_mapping=agent_model_mapping,
            total_estimated_cost=1.0,  # 수동 선택이므로 비용 계산 생략
            strategy="manual",
            budget_utilization=0.5
        )

def main():
    """테스트 함수"""
    generator = AdaptiveScriptGenerator()

    # 테스트 요구사항
    test_requirement = "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘"
    test_project_path = "test_generated_project"
    test_execution_id = "test_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=== 적응형 스크립트 생성 엔진 테스트 ===")

    # 스크립트 생성
    result = generator.generate_optimal_script(
        requirement=test_requirement,
        project_path=test_project_path,
        execution_id=test_execution_id,
        budget="medium",
        strategy="balanced"
    )

    print(f"\n📊 생성 결과:")
    print(f"품질 점수: {result.quality_score:.1f}/100")
    print(f"프로덕션 준비: {'✅' if result.is_production_ready else '❌'}")
    print(f"README 경로: {result.readme_path}")
    print(f"Requirements 경로: {result.requirements_path}")

    print(f"\n📁 생성된 파일들:")
    if os.path.exists(test_project_path):
        for file_path in Path(test_project_path).rglob("*"):
            if file_path.is_file():
                print(f"  {file_path}")

if __name__ == "__main__":
    main()