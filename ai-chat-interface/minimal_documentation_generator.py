#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간소한 자동 문서화 시스템
프로젝트별로 README.md 1개 파일만 생성하는 최소화된 문서화 시스템
"""

import os
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path
from intelligent_requirement_analyzer import RequirementAnalysis
from dynamic_agent_matcher import AgentSelection
from smart_model_allocator import ModelAllocation

@dataclass
class DocumentationContent:
    """문서화 내용"""
    title: str
    overview: str
    agent_description: str
    execution_guide: str
    expected_results: str
    technical_notes: str

class MinimalDocumentationGenerator:
    """간소한 문서화 생성기"""

    def __init__(self):
        self.template = self._load_readme_template()

    def _load_readme_template(self) -> str:
        """README.md 템플릿 로드"""
        return """# {title}

## 📋 프로젝트 개요
{overview}

## 🤖 에이전트 구성
{agent_description}

## 🚀 실행 방법
{execution_guide}

## 📈 예상 결과
{expected_results}

{technical_notes}
"""

    def generate_documentation(self,
                             requirement: str,
                             analysis: RequirementAnalysis,
                             agent_selection: AgentSelection,
                             model_allocation: ModelAllocation,
                             project_path: str) -> str:
        """문서 생성"""

        # 1. 문서 내용 구성
        content = self._build_documentation_content(
            requirement, analysis, agent_selection, model_allocation
        )

        # 2. 템플릿 적용
        readme_content = self.template.format(
            title=content.title,
            overview=content.overview,
            agent_description=content.agent_description,
            execution_guide=content.execution_guide,
            expected_results=content.expected_results,
            technical_notes=content.technical_notes
        )

        # 3. README.md 파일 저장
        readme_path = os.path.join(project_path, "README.md")
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print(f"✅ README.md 생성 완료: {readme_path}")
        except Exception as e:
            print(f"❌ README.md 생성 실패: {e}")

        return readme_content

    def _build_documentation_content(self,
                                   requirement: str,
                                   analysis: RequirementAnalysis,
                                   agent_selection: AgentSelection,
                                   model_allocation: ModelAllocation) -> DocumentationContent:
        """문서 내용 구성"""

        # 1. 제목 생성
        title = self._generate_title(requirement, analysis.domain)

        # 2. 개요 생성
        overview = self._generate_overview(requirement, analysis)

        # 3. 에이전트 설명
        agent_description = self._generate_agent_description(agent_selection, model_allocation)

        # 4. 실행 가이드
        execution_guide = self._generate_execution_guide(analysis)

        # 5. 예상 결과
        expected_results = self._generate_expected_results(requirement, analysis)

        # 6. 기술 노트
        technical_notes = self._generate_technical_notes(analysis, model_allocation)

        return DocumentationContent(
            title=title,
            overview=overview,
            agent_description=agent_description,
            execution_guide=execution_guide,
            expected_results=expected_results,
            technical_notes=technical_notes
        )

    def _generate_title(self, requirement: str, domain: str) -> str:
        """제목 생성"""
        domain_titles = {
            'web_development': '웹 개발 시스템',
            'data_analysis': '데이터 분석 시스템',
            'content_creation': '콘텐츠 생성 시스템',
            'automation': '자동화 시스템',
            'mobile_app': '모바일 앱 개발 시스템',
            'document_processing': '문서 처리 시스템',
            'ecommerce': '이커머스 시스템',
            'game_development': '게임 개발 시스템'
        }

        base_title = domain_titles.get(domain, 'AI 프로그램 시스템')

        # 요구사항에서 구체적인 키워드 추출
        specific_keywords = []
        if '블로그' in requirement:
            specific_keywords.append('블로그')
        if '분석' in requirement:
            specific_keywords.append('분석')
        if '자동' in requirement or '자동화' in requirement:
            specific_keywords.append('자동')
        if '이력서' in requirement:
            specific_keywords.append('이력서')
        if '쇼핑몰' in requirement:
            specific_keywords.append('쇼핑몰')

        if specific_keywords:
            return f"{' '.join(specific_keywords)} {base_title}"
        else:
            return base_title

    def _generate_overview(self, requirement: str, analysis: RequirementAnalysis) -> str:
        """개요 생성"""
        overview_parts = []

        # 원본 요구사항
        overview_parts.append(f"**요구사항**: {requirement}")

        # 도메인 정보
        domain_descriptions = {
            'web_development': '웹 애플리케이션 개발',
            'data_analysis': '데이터 수집, 분석 및 시각화',
            'content_creation': '콘텐츠 기획, 생성 및 최적화',
            'automation': '업무 프로세스 자동화',
            'mobile_app': '모바일 애플리케이션 개발',
            'document_processing': '문서 파싱 및 정보 추출',
            'ecommerce': '전자상거래 플랫폼 구축',
            'game_development': '게임 개발 및 디자인'
        }

        domain_desc = domain_descriptions.get(analysis.domain, '범용 AI 시스템')
        overview_parts.append(f"**분야**: {domain_desc}")

        # 복잡도 및 규모
        complexity_descriptions = {
            'simple': '간단한 기능 중심의 경량화된 시스템',
            'medium': '표준적인 기능을 포함한 중간 규모 시스템',
            'complex': '다양한 기능과 통합을 포함한 복합 시스템',
            'advanced': '고도화된 기능과 확장성을 갖춘 엔터프라이즈급 시스템'
        }

        complexity_desc = complexity_descriptions.get(analysis.complexity.value, '표준 시스템')
        overview_parts.append(f"**규모**: {complexity_desc}")

        # 핵심 기술
        if analysis.tech_stack:
            tech_summary = ', '.join(analysis.tech_stack[:3])  # 상위 3개만
            overview_parts.append(f"**핵심 기술**: {tech_summary}")

        return '\n\n'.join(overview_parts)

    def _generate_agent_description(self, agent_selection: AgentSelection,
                                  model_allocation: ModelAllocation) -> str:
        """에이전트 설명 생성"""
        descriptions = []

        # 에이전트별 설명
        for agent in agent_selection.agents:
            agent_name = agent.name
            assigned_model = model_allocation.agent_model_mapping.get(agent_name, "N/A")

            # 역할 번역
            role_translations = {
                'Senior Requirements Analyst': '요구사항 분석 전문가',
                'Technology Research Specialist': '기술 연구 전문가',
                'Senior Solution Architect': '솔루션 아키텍트',
                'Senior Implementation Engineer': '구현 개발 전문가',
                'Senior Frontend Developer': '프론트엔드 개발 전문가',
                'Senior Backend Developer': '백엔드 개발 전문가',
                'Senior Data Scientist': '데이터 사이언티스트',
                'Content Strategy Expert': '콘텐츠 전략 전문가',
                'Professional Content Creator': '콘텐츠 제작 전문가',
                'Process Automation Expert': '프로세스 자동화 전문가',
                'Document Processing Expert': '문서 처리 전문가',
                'Information Extraction Specialist': '정보 추출 전문가',
                'Quality Assurance Specialist': '품질 보증 전문가'
            }

            role_kr = role_translations.get(agent.role, agent.role)

            # 목표 간단 요약
            goal_summary = self._summarize_goal(agent.goal)

            descriptions.append(f"- **{role_kr}** ({assigned_model}): {goal_summary}")

        # 에이전트 협업 구조
        if len(agent_selection.agents) > 3:
            descriptions.append(f"\n**협업 구조**: {len(agent_selection.agents)}개 전문 에이전트가 순차적으로 협업하여 고품질 결과물 생성")

        return '\n'.join(descriptions)

    def _summarize_goal(self, goal: str) -> str:
        """목표 요약"""
        # 영어 목표를 간단한 한국어로 요약
        goal_summaries = {
            'analyze and structure project requirements': '프로젝트 요구사항 분석 및 구조화',
            'research and recommend optimal technology': '최적 기술 스택 연구 및 추천',
            'design comprehensive system architecture': '시스템 아키텍처 설계',
            'create production-ready code': '실용적인 코드 구현',
            'create modern, responsive web interfaces': '현대적인 웹 인터페이스 개발',
            'build robust backend systems': '견고한 백엔드 시스템 구축',
            'extract insights from data': '데이터에서 인사이트 추출',
            'develop comprehensive content strategies': '포괄적인 콘텐츠 전략 수립',
            'create high-quality content': '고품질 콘텐츠 제작',
            'design and implement automation': '자동화 솔루션 설계 및 구현',
            'parse and extract information': '문서 파싱 및 정보 추출',
            'extract structured information': '구조화된 정보 추출',
            'ensure high-quality deliverables': '고품질 결과물 보장'
        }

        goal_lower = goal.lower()
        for key, summary in goal_summaries.items():
            if key in goal_lower:
                return summary

        # 기본 요약 (첫 번째 문장만)
        first_sentence = goal.split('.')[0]
        if len(first_sentence) > 50:
            return first_sentence[:50] + "..."
        return first_sentence

    def _generate_execution_guide(self, analysis: RequirementAnalysis) -> str:
        """실행 가이드 생성"""
        steps = []

        # 1. 기본 설정
        steps.append("### 1. 환경 설정")
        steps.append("```bash")
        steps.append("pip install -r requirements.txt")
        steps.append("```")

        # 2. API 키 설정 (필요한 경우)
        if self._requires_api_keys(analysis):
            steps.append("\n### 2. API 키 설정")
            steps.append("`.env` 파일에 필요한 API 키를 설정하세요:")
            steps.append("```")

            if 'content_creation' in [analysis.domain] + analysis.sub_domains:
                steps.append("OPENAI_API_KEY=your_openai_key_here")

            if analysis.domain in ['web_development', 'automation']:
                steps.append("# 외부 서비스 API 키 (필요시)")

            steps.append("```")

        # 3. 실행
        steps.append("\n### 3. 프로그램 실행")
        steps.append("```bash")
        steps.append("python crewai_script.py")
        steps.append("```")

        # 4. 결과 확인
        steps.append("\n### 4. 결과 확인")
        steps.append("실행 결과는 `output/` 폴더에 저장됩니다:")
        steps.append("- `crew_result_[timestamp].txt`: 상세 실행 결과")
        steps.append("- `execution_metadata_[timestamp].json`: 실행 메타데이터")

        return '\n'.join(steps)

    def _requires_api_keys(self, analysis: RequirementAnalysis) -> bool:
        """API 키가 필요한지 확인"""
        api_requiring_domains = ['content_creation', 'data_analysis']
        api_requiring_keywords = ['api', '외부', '서비스', '연동']

        # 도메인 기반 체크
        if analysis.domain in api_requiring_domains:
            return True

        # 키워드 기반 체크
        for keyword in api_requiring_keywords:
            if keyword in analysis.keywords:
                return True

        return False

    def _generate_expected_results(self, requirement: str, analysis: RequirementAnalysis) -> str:
        """예상 결과 생성"""
        results = []

        # 도메인별 예상 결과
        domain_results = {
            'web_development': [
                "완전한 웹 애플리케이션 코드",
                "프론트엔드 및 백엔드 구현",
                "데이터베이스 스키마 및 API 설계"
            ],
            'data_analysis': [
                "데이터 분석 스크립트 및 결과",
                "시각화 차트 및 대시보드",
                "인사이트 리포트 및 권장사항"
            ],
            'content_creation': [
                "고품질 콘텐츠 (글, 블로그 포스트)",
                "SEO 최적화된 콘텐츠",
                "콘텐츠 전략 및 키워드 분석"
            ],
            'automation': [
                "자동화 스크립트 및 도구",
                "프로세스 최적화 방안",
                "스케줄링 및 모니터링 시스템"
            ],
            'document_processing': [
                "문서 파싱 및 데이터 추출 결과",
                "구조화된 JSON/Excel 출력",
                "데이터 품질 검증 리포트"
            ]
        }

        if analysis.domain in domain_results:
            results.extend(domain_results[analysis.domain])

        # 복잡도별 추가 결과
        if analysis.complexity.value in ['complex', 'advanced']:
            results.extend([
                "포괄적인 기술 문서",
                "테스트 코드 및 검증 시나리오",
                "배포 가이드 및 운영 매뉴얼"
            ])

        # 요구사항 특화 결과
        if '블로그' in requirement:
            results.append("매일 자동 생성되는 블로그 포스트")
        if '분석' in requirement:
            results.append("데이터 기반 인사이트 및 트렌드 분석")
        if '자동' in requirement:
            results.append("완전 자동화된 워크플로우")

        if not results:
            results = ["요구사항에 맞는 맞춤형 솔루션", "실행 가능한 프로그램 코드", "상세한 구현 문서"]

        return '\n'.join(f"- {result}" for result in results)

    def _generate_technical_notes(self, analysis: RequirementAnalysis,
                                model_allocation: ModelAllocation) -> str:
        """기술 노트 생성"""
        notes = []

        # 기술 스택 정보
        if analysis.tech_stack:
            notes.append("## 🔧 기술 스택")
            tech_list = '\n'.join(f"- {tech}" for tech in analysis.tech_stack)
            notes.append(tech_list)

        # 모델 할당 정보
        notes.append("\n## 🤖 AI 모델 구성")
        model_info = []

        # 사용된 모델들
        used_models = set(model_allocation.agent_model_mapping.values())
        for model in used_models:
            agents_using_model = [agent for agent, m in model_allocation.agent_model_mapping.items() if m == model]
            model_info.append(f"- **{model}**: {len(agents_using_model)}개 에이전트 ({', '.join(agents_using_model)})")

        notes.append('\n'.join(model_info))

        # 할당 근거
        notes.append(f"\n**할당 전략**: {model_allocation.allocation_reasoning}")

        # 의존성 정보
        if analysis.required_libraries:
            notes.append("\n## 📦 주요 의존성")
            lib_list = '\n'.join(f"- {lib}" for lib in analysis.required_libraries[:8])  # 상위 8개만
            notes.append(lib_list)

        # 성능 및 신뢰도
        notes.append(f"\n## 📊 품질 지표")
        notes.append(f"- **요구사항 분석 신뢰도**: {analysis.confidence_score:.1%}")
        notes.append(f"- **에이전트 매칭 신뢰도**: {model_allocation.confidence_score:.1%}")
        notes.append(f"- **예상 성능**: 고품질 결과물 생성 보장")

        return '\n'.join(notes)

def main():
    """테스트 함수"""
    from intelligent_requirement_analyzer import IntelligentRequirementAnalyzer
    from dynamic_agent_matcher import DynamicAgentMatcher
    from smart_model_allocator import SmartModelAllocator

    # 시스템 초기화
    analyzer = IntelligentRequirementAnalyzer()
    matcher = DynamicAgentMatcher()
    allocator = SmartModelAllocator("model_config.json")
    doc_generator = MinimalDocumentationGenerator()

    # 테스트 요구사항
    test_req = "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘"

    # 분석 및 매칭
    analysis = analyzer.analyze_requirement(test_req)
    agent_selection = matcher.select_optimal_agents(analysis)
    model_allocation = allocator.allocate_models(agent_selection, analysis)

    print(f"=== 문서화 시스템 테스트 ===")
    print(f"요구사항: {test_req}")

    # 임시 디렉토리에 문서 생성
    test_project_path = "test_project"
    os.makedirs(test_project_path, exist_ok=True)

    # 문서 생성
    readme_content = doc_generator.generate_documentation(
        test_req, analysis, agent_selection, model_allocation, test_project_path
    )

    print(f"\n생성된 README.md 내용:")
    print("=" * 60)
    print(readme_content)

if __name__ == "__main__":
    main()