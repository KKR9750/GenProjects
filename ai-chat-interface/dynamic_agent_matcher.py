#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
동적 에이전트 매칭 시스템
요구사항 분석 결과를 바탕으로 최적의 에이전트 조합을 선택
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from intelligent_requirement_analyzer import RequirementAnalysis, ComplexityLevel

@dataclass
class AgentProfile:
    """에이전트 프로필"""
    name: str
    role: str
    goal: str
    backstory: str
    domains: List[str]          # 전문 도메인
    capabilities: List[str]     # 핵심 역량
    complexity_fit: List[str]   # 적합한 복잡도 레벨
    priority: int              # 우선순위 (1=최고)
    synergy_agents: List[str]  # 시너지 에이전트들

@dataclass
class AgentSelection:
    """선택된 에이전트 정보"""
    agents: List[AgentProfile]
    selection_reasoning: str
    confidence_score: float
    estimated_performance: float

class DynamicAgentMatcher:
    """동적 에이전트 매칭 시스템"""

    def __init__(self):
        self.agent_pool = self._initialize_agent_pool()
        self.synergy_matrix = self._build_synergy_matrix()

    def _initialize_agent_pool(self) -> Dict[str, AgentProfile]:
        """에이전트 풀 초기화"""
        agents = {
            # === 범용 분석 에이전트 ===
            'requirements_analyst': AgentProfile(
                name="requirements_analyst",
                role="Senior Requirements Analyst",
                goal="Analyze and structure project requirements with precision",
                backstory="You are a senior business analyst with 15+ years of experience. You excel at understanding complex requirements, identifying hidden needs, and translating business goals into clear technical specifications.",
                domains=['general', 'web_development', 'data_analysis', 'automation'],
                capabilities=['requirement_analysis', 'business_logic', 'specification'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=1,
                synergy_agents=['technology_researcher', 'solution_architect']
            ),

            'technology_researcher': AgentProfile(
                name="technology_researcher",
                role="Technology Research Specialist",
                goal="Research and recommend optimal technology stack and implementation approaches",
                backstory="You are a technology research expert with deep knowledge of modern frameworks, tools, and best practices. You stay current with industry trends and can recommend the most suitable technologies for any project type.",
                domains=['general', 'web_development', 'mobile_app', 'data_analysis'],
                capabilities=['tech_research', 'framework_selection', 'best_practices'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=2,
                synergy_agents=['requirements_analyst', 'solution_architect', 'implementation_engineer']
            ),

            'solution_architect': AgentProfile(
                name="solution_architect",
                role="Senior Solution Architect",
                goal="Design comprehensive system architecture and implementation strategy",
                backstory="You are a senior solution architect with expertise in designing scalable, maintainable systems. You excel at creating detailed technical designs that balance performance, security, and development efficiency.",
                domains=['general', 'web_development', 'data_analysis', 'ecommerce'],
                capabilities=['system_design', 'architecture', 'scalability', 'integration'],
                complexity_fit=['complex', 'advanced'],
                priority=2,
                synergy_agents=['technology_researcher', 'implementation_engineer']
            ),

            'implementation_engineer': AgentProfile(
                name="implementation_engineer",
                role="Senior Implementation Engineer",
                goal="Create production-ready code and comprehensive project deliverables",
                backstory="You are a senior software engineer with expertise in multiple programming languages and frameworks. You write clean, well-documented, production-ready code with comprehensive testing and deployment strategies.",
                domains=['general', 'web_development', 'automation', 'document_processing'],
                capabilities=['coding', 'testing', 'deployment', 'documentation'],
                complexity_fit=['simple', 'medium', 'complex', 'advanced'],
                priority=1,
                synergy_agents=['solution_architect', 'quality_assurance']
            ),

            # === 웹 개발 전문 에이전트 ===
            'frontend_developer': AgentProfile(
                name="frontend_developer",
                role="Senior Frontend Developer",
                goal="Create modern, responsive, and user-friendly web interfaces",
                backstory="You are a frontend expert with deep knowledge of modern JavaScript frameworks, CSS, and UX/UI principles. You create beautiful, accessible, and performant web applications.",
                domains=['web_development'],
                capabilities=['frontend', 'ui_ux', 'responsive_design', 'javascript'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=1,
                synergy_agents=['backend_developer', 'ui_ux_designer']
            ),

            'backend_developer': AgentProfile(
                name="backend_developer",
                role="Senior Backend Developer",
                goal="Build robust, scalable, and secure backend systems and APIs",
                backstory="You are a backend expert specializing in server-side development, database design, API development, and system integration. You ensure high performance and security.",
                domains=['web_development', 'ecommerce'],
                capabilities=['backend', 'api_design', 'database', 'security'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=1,
                synergy_agents=['frontend_developer', 'database_specialist']
            ),

            'ui_ux_designer': AgentProfile(
                name="ui_ux_designer",
                role="UI/UX Design Specialist",
                goal="Design intuitive and engaging user experiences",
                backstory="You are a design expert with deep understanding of user psychology, design principles, and modern design trends. You create user-centered designs that are both beautiful and functional.",
                domains=['web_development', 'mobile_app'],
                capabilities=['design', 'user_experience', 'prototyping', 'usability'],
                complexity_fit=['medium', 'complex'],
                priority=2,
                synergy_agents=['frontend_developer']
            ),

            # === 데이터 분석 전문 에이전트 ===
            'data_scientist': AgentProfile(
                name="data_scientist",
                role="Senior Data Scientist",
                goal="Extract insights from data using advanced analytics and machine learning",
                backstory="You are a data science expert with deep knowledge of statistics, machine learning, and data visualization. You transform raw data into actionable business insights.",
                domains=['data_analysis'],
                capabilities=['machine_learning', 'statistics', 'data_mining', 'predictive_modeling'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=1,
                synergy_agents=['data_engineer', 'visualization_specialist']
            ),

            'data_engineer': AgentProfile(
                name="data_engineer",
                role="Senior Data Engineer",
                goal="Build robust data pipelines and infrastructure for data processing",
                backstory="You are a data engineering expert specializing in ETL processes, data warehousing, and big data technologies. You ensure data quality and accessibility.",
                domains=['data_analysis'],
                capabilities=['data_pipeline', 'etl', 'big_data', 'data_quality'],
                complexity_fit=['complex', 'advanced'],
                priority=2,
                synergy_agents=['data_scientist', 'database_specialist']
            ),

            'visualization_specialist': AgentProfile(
                name="visualization_specialist",
                role="Data Visualization Specialist",
                goal="Create compelling and insightful data visualizations",
                backstory="You are a visualization expert who transforms complex data into clear, engaging charts and dashboards. You understand how to communicate data stories effectively.",
                domains=['data_analysis'],
                capabilities=['data_visualization', 'dashboard_design', 'storytelling'],
                complexity_fit=['simple', 'medium', 'complex'],
                priority=2,
                synergy_agents=['data_scientist']
            ),

            # === 콘텐츠 생성 전문 에이전트 ===
            'content_strategist': AgentProfile(
                name="content_strategist",
                role="Content Strategy Expert",
                goal="Develop comprehensive content strategies and editorial guidelines",
                backstory="You are a content strategy expert with deep understanding of audience needs, content marketing, and editorial best practices. You create content that engages and converts.",
                domains=['content_creation'],
                capabilities=['content_strategy', 'editorial', 'audience_analysis'],
                complexity_fit=['medium', 'complex'],
                priority=1,
                synergy_agents=['content_creator', 'seo_specialist']
            ),

            'content_creator': AgentProfile(
                name="content_creator",
                role="Professional Content Creator",
                goal="Create high-quality, engaging content across various formats",
                backstory="You are a professional writer and content creator with expertise in various content formats. You create compelling, well-researched content that resonates with target audiences.",
                domains=['content_creation'],
                capabilities=['writing', 'content_creation', 'research', 'editing'],
                complexity_fit=['simple', 'medium', 'complex'],
                priority=1,
                synergy_agents=['content_strategist', 'seo_specialist']
            ),

            'seo_specialist': AgentProfile(
                name="seo_specialist",
                role="SEO and Digital Marketing Expert",
                goal="Optimize content for search engines and digital marketing performance",
                backstory="You are an SEO expert with deep knowledge of search engine algorithms, keyword research, and digital marketing strategies. You ensure content performs well in search results.",
                domains=['content_creation', 'web_development'],
                capabilities=['seo', 'keyword_research', 'digital_marketing'],
                complexity_fit=['medium', 'complex'],
                priority=2,
                synergy_agents=['content_creator', 'content_strategist']
            ),

            # === 자동화 전문 에이전트 ===
            'automation_specialist': AgentProfile(
                name="automation_specialist",
                role="Process Automation Expert",
                goal="Design and implement efficient automation solutions",
                backstory="You are an automation expert with deep knowledge of workflow optimization, scripting, and process automation tools. You streamline repetitive tasks and improve efficiency.",
                domains=['automation'],
                capabilities=['process_automation', 'workflow_design', 'scripting'],
                complexity_fit=['simple', 'medium', 'complex'],
                priority=1,
                synergy_agents=['implementation_engineer', 'integration_specialist']
            ),

            'web_scraper': AgentProfile(
                name="web_scraper",
                role="Web Scraping Specialist",
                goal="Extract and process data from websites efficiently and ethically",
                backstory="You are a web scraping expert with deep knowledge of web technologies, data extraction techniques, and ethical scraping practices. You handle complex scraping challenges.",
                domains=['automation', 'data_analysis'],
                capabilities=['web_scraping', 'data_extraction', 'parsing'],
                complexity_fit=['medium', 'complex'],
                priority=2,
                synergy_agents=['automation_specialist', 'data_engineer']
            ),

            'integration_specialist': AgentProfile(
                name="integration_specialist",
                role="System Integration Expert",
                goal="Integrate multiple systems and APIs seamlessly",
                backstory="You are an integration expert specializing in connecting different systems, APIs, and services. You ensure smooth data flow and system interoperability.",
                domains=['automation', 'web_development', 'ecommerce'],
                capabilities=['api_integration', 'system_integration', 'middleware'],
                complexity_fit=['complex', 'advanced'],
                priority=2,
                synergy_agents=['backend_developer', 'automation_specialist']
            ),

            # === 문서 처리 전문 에이전트 ===
            'document_parser': AgentProfile(
                name="document_parser",
                role="Document Processing Expert",
                goal="Parse and extract information from various document formats",
                backstory="You are a document processing expert with deep knowledge of file formats, text extraction, and OCR technologies. You handle complex document parsing challenges.",
                domains=['document_processing'],
                capabilities=['document_parsing', 'text_extraction', 'ocr', 'format_conversion'],
                complexity_fit=['simple', 'medium', 'complex'],
                priority=1,
                synergy_agents=['information_extractor', 'data_validator']
            ),

            'information_extractor': AgentProfile(
                name="information_extractor",
                role="Information Extraction Specialist",
                goal="Extract structured information from unstructured text using NLP",
                backstory="You are an NLP expert specializing in information extraction, named entity recognition, and text analysis. You transform unstructured text into structured data.",
                domains=['document_processing', 'data_analysis'],
                capabilities=['nlp', 'information_extraction', 'entity_recognition'],
                complexity_fit=['medium', 'complex'],
                priority=1,
                synergy_agents=['document_parser', 'data_validator']
            ),

            'data_validator': AgentProfile(
                name="data_validator",
                role="Data Quality Assurance Expert",
                goal="Ensure data accuracy, completeness, and consistency",
                backstory="You are a data quality expert specializing in validation frameworks, data cleansing, and quality metrics. You ensure high-quality data outputs.",
                domains=['document_processing', 'data_analysis'],
                capabilities=['data_validation', 'quality_assurance', 'data_cleansing'],
                complexity_fit=['simple', 'medium', 'complex'],
                priority=2,
                synergy_agents=['information_extractor', 'data_engineer']
            ),

            # === 품질 보증 에이전트 ===
            'quality_assurance': AgentProfile(
                name="quality_assurance",
                role="Quality Assurance Specialist",
                goal="Ensure high-quality deliverables through systematic testing and validation",
                backstory="You are a QA expert with deep knowledge of testing methodologies, quality standards, and validation processes. You ensure deliverables meet the highest quality standards.",
                domains=['general'],
                capabilities=['testing', 'quality_control', 'validation', 'debugging'],
                complexity_fit=['medium', 'complex', 'advanced'],
                priority=2,
                synergy_agents=['implementation_engineer']
            ),

            # === 데이터베이스 전문 에이전트 ===
            'database_specialist': AgentProfile(
                name="database_specialist",
                role="Database Architecture Expert",
                goal="Design and optimize database systems for performance and scalability",
                backstory="You are a database expert with deep knowledge of relational and NoSQL databases, optimization techniques, and data modeling. You ensure efficient data storage and retrieval.",
                domains=['web_development', 'data_analysis', 'ecommerce'],
                capabilities=['database_design', 'query_optimization', 'data_modeling'],
                complexity_fit=['complex', 'advanced'],
                priority=2,
                synergy_agents=['backend_developer', 'data_engineer']
            )
        }

        return agents

    def _build_synergy_matrix(self) -> Dict:
        """에이전트 간 시너지 매트릭스 구축"""
        return {
            'data_pipeline': ['data_scientist', 'data_engineer', 'database_specialist'],
            'web_fullstack': ['frontend_developer', 'backend_developer', 'database_specialist'],
            'content_optimization': ['content_strategist', 'content_creator', 'seo_specialist'],
            'document_processing': ['document_parser', 'information_extractor', 'data_validator'],
            'automation_pipeline': ['automation_specialist', 'web_scraper', 'integration_specialist'],
            'enterprise_web': ['requirements_analyst', 'solution_architect', 'backend_developer', 'frontend_developer', 'database_specialist'],
            'research_content': ['technology_researcher', 'content_strategist', 'content_creator']
        }

    def select_optimal_agents(self, analysis: RequirementAnalysis) -> AgentSelection:
        """최적 에이전트 조합 선택"""

        # 1. 도메인 기반 1차 필터링
        candidate_agents = self._filter_by_domain(analysis.domain, analysis.sub_domains)

        # 2. 복잡도 기반 필터링
        candidate_agents = self._filter_by_complexity(candidate_agents, analysis.complexity)

        # 3. 키워드 매칭 점수 계산
        scored_agents = self._score_agents_by_keywords(candidate_agents, analysis.keywords)

        # 4. 시너지 효과 고려한 조합 생성
        optimal_combinations = self._generate_optimal_combinations(
            scored_agents, analysis.agent_count, analysis.domain
        )

        # 5. 최고 조합 선택
        best_combination = self._select_best_combination(optimal_combinations, analysis)

        # 6. 선택 근거 생성
        reasoning = self._generate_selection_reasoning(best_combination, analysis)

        return AgentSelection(
            agents=best_combination,
            selection_reasoning=reasoning,
            confidence_score=self._calculate_selection_confidence(best_combination, analysis),
            estimated_performance=self._estimate_performance(best_combination, analysis)
        )

    def _filter_by_domain(self, primary_domain: str, sub_domains: List[str]) -> List[AgentProfile]:
        """도메인 기반 에이전트 필터링"""
        candidates = []
        all_domains = [primary_domain] + sub_domains

        for agent in self.agent_pool.values():
            # 일반 에이전트는 항상 포함
            if 'general' in agent.domains:
                candidates.append(agent)
                continue

            # 도메인 매칭 점수 계산
            domain_match_score = 0
            for domain in all_domains:
                if domain in agent.domains:
                    domain_match_score += 1

            # 매칭 점수가 있으면 후보에 포함
            if domain_match_score > 0:
                candidates.append(agent)

        return candidates

    def _filter_by_complexity(self, candidates: List[AgentProfile], complexity: ComplexityLevel) -> List[AgentProfile]:
        """복잡도 기반 필터링"""
        filtered = []

        for agent in candidates:
            if complexity.value in agent.complexity_fit:
                filtered.append(agent)

        return filtered if filtered else candidates  # 빈 경우 원본 반환

    def _score_agents_by_keywords(self, candidates: List[AgentProfile], keywords: List[str]) -> List[Tuple[AgentProfile, float]]:
        """키워드 매칭 점수 계산"""
        scored_agents = []

        for agent in candidates:
            score = 0.0

            # 역할/목표/배경에서 키워드 매칭
            agent_text = (agent.role + " " + agent.goal + " " + agent.backstory).lower()

            for keyword in keywords:
                if keyword.lower() in agent_text:
                    score += 1.0

            # 역량 매칭
            for capability in agent.capabilities:
                for keyword in keywords:
                    if keyword.lower() in capability.lower():
                        score += 0.5

            # 우선순위 보정 (우선순위 높을수록 점수 추가)
            score += (5 - agent.priority) * 0.2

            scored_agents.append((agent, score))

        # 점수 순 정렬
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents

    def _generate_optimal_combinations(self, scored_agents: List[Tuple[AgentProfile, float]],
                                     target_count: int, domain: str) -> List[List[AgentProfile]]:
        """최적 조합 생성"""
        combinations = []

        # 1. 도메인별 기본 조합 확인
        domain_templates = self._get_domain_templates(domain)
        for template in domain_templates:
            if len(template) == target_count:
                template_agents = [self.agent_pool[name] for name in template if name in self.agent_pool]
                if len(template_agents) == target_count:
                    combinations.append(template_agents)

        # 2. 점수 기반 조합 생성
        high_score_agents = [agent for agent, score in scored_agents[:target_count*2]]  # 상위 후보들

        # 다양한 조합 시도
        if len(high_score_agents) >= target_count:
            # 최고 점수 조합
            combinations.append(high_score_agents[:target_count])

            # 균형 잡힌 조합 (다양한 역할 포함)
            balanced_combination = self._create_balanced_combination(high_score_agents, target_count)
            if balanced_combination:
                combinations.append(balanced_combination)

        # 3. 시너지 기반 조합
        synergy_combinations = self._create_synergy_combinations(target_count, domain)
        combinations.extend(synergy_combinations)

        return combinations[:5]  # 최대 5개 조합

    def _get_domain_templates(self, domain: str) -> List[List[str]]:
        """도메인별 추천 템플릿"""
        templates = {
            'web_development': [
                ['requirements_analyst', 'frontend_developer', 'backend_developer', 'database_specialist'],
                ['technology_researcher', 'frontend_developer', 'backend_developer', 'quality_assurance'],
                ['solution_architect', 'frontend_developer', 'backend_developer', 'ui_ux_designer', 'database_specialist']
            ],
            'data_analysis': [
                ['requirements_analyst', 'data_scientist', 'visualization_specialist'],
                ['data_scientist', 'data_engineer', 'visualization_specialist', 'quality_assurance'],
                ['requirements_analyst', 'data_scientist', 'data_engineer', 'visualization_specialist', 'database_specialist']
            ],
            'content_creation': [
                ['content_strategist', 'content_creator', 'seo_specialist'],
                ['technology_researcher', 'content_strategist', 'content_creator', 'seo_specialist'],
                ['requirements_analyst', 'content_strategist', 'content_creator', 'seo_specialist', 'automation_specialist']
            ],
            'automation': [
                ['automation_specialist', 'web_scraper', 'implementation_engineer'],
                ['requirements_analyst', 'automation_specialist', 'web_scraper', 'integration_specialist'],
                ['automation_specialist', 'web_scraper', 'integration_specialist', 'quality_assurance', 'implementation_engineer']
            ],
            'document_processing': [
                ['document_parser', 'information_extractor', 'data_validator'],
                ['requirements_analyst', 'document_parser', 'information_extractor', 'data_validator'],
                ['document_parser', 'information_extractor', 'data_validator', 'implementation_engineer', 'quality_assurance']
            ],
            'ecommerce': [
                ['requirements_analyst', 'backend_developer', 'frontend_developer', 'database_specialist'],
                ['solution_architect', 'backend_developer', 'frontend_developer', 'integration_specialist', 'database_specialist']
            ]
        }

        return templates.get(domain, [
            ['requirements_analyst', 'technology_researcher', 'implementation_engineer'],
            ['requirements_analyst', 'solution_architect', 'implementation_engineer', 'quality_assurance']
        ])

    def _create_balanced_combination(self, candidates: List[AgentProfile], target_count: int) -> Optional[List[AgentProfile]]:
        """균형 잡힌 조합 생성"""
        if len(candidates) < target_count:
            return None

        combination = []
        used_roles = set()

        # 다양한 역할 우선 선택
        for agent in candidates:
            if len(combination) >= target_count:
                break

            role_category = self._get_role_category(agent.name)
            if role_category not in used_roles:
                combination.append(agent)
                used_roles.add(role_category)

        # 부족한 에이전트는 점수 순으로 추가
        remaining_needed = target_count - len(combination)
        remaining_candidates = [agent for agent in candidates if agent not in combination]

        combination.extend(remaining_candidates[:remaining_needed])

        return combination if len(combination) == target_count else None

    def _get_role_category(self, agent_name: str) -> str:
        """에이전트 역할 카테고리 분류"""
        categories = {
            'analysis': ['requirements_analyst', 'technology_researcher'],
            'architecture': ['solution_architect'],
            'development': ['implementation_engineer', 'frontend_developer', 'backend_developer'],
            'data': ['data_scientist', 'data_engineer', 'database_specialist'],
            'content': ['content_strategist', 'content_creator', 'seo_specialist'],
            'automation': ['automation_specialist', 'web_scraper', 'integration_specialist'],
            'document': ['document_parser', 'information_extractor', 'data_validator'],
            'quality': ['quality_assurance'],
            'design': ['ui_ux_designer', 'visualization_specialist']
        }

        for category, agents in categories.items():
            if agent_name in agents:
                return category

        return 'general'

    def _create_synergy_combinations(self, target_count: int, domain: str) -> List[List[AgentProfile]]:
        """시너지 기반 조합 생성"""
        combinations = []

        for synergy_name, agent_names in self.synergy_matrix.items():
            if len(agent_names) == target_count:
                agents = [self.agent_pool[name] for name in agent_names if name in self.agent_pool]
                if len(agents) == target_count:
                    combinations.append(agents)

        return combinations

    def _select_best_combination(self, combinations: List[List[AgentProfile]], analysis: RequirementAnalysis) -> List[AgentProfile]:
        """최고 조합 선택"""
        if not combinations:
            # 폴백: 기본 조합
            return self._get_fallback_combination(analysis.agent_count)

        best_combination = None
        best_score = -1

        for combination in combinations:
            score = self._evaluate_combination(combination, analysis)
            if score > best_score:
                best_score = score
                best_combination = combination

        return best_combination or combinations[0]

    def _evaluate_combination(self, combination: List[AgentProfile], analysis: RequirementAnalysis) -> float:
        """조합 평가"""
        score = 0.0

        # 1. 도메인 커버리지 (40%)
        domain_coverage = self._calculate_domain_coverage(combination, analysis.domain, analysis.sub_domains)
        score += domain_coverage * 0.4

        # 2. 역량 다양성 (30%)
        capability_diversity = self._calculate_capability_diversity(combination)
        score += capability_diversity * 0.3

        # 3. 시너지 효과 (20%)
        synergy_effect = self._calculate_synergy_effect(combination)
        score += synergy_effect * 0.2

        # 4. 복잡도 적합성 (10%)
        complexity_fit = self._calculate_complexity_fit(combination, analysis.complexity)
        score += complexity_fit * 0.1

        return score

    def _calculate_domain_coverage(self, combination: List[AgentProfile], primary_domain: str, sub_domains: List[str]) -> float:
        """도메인 커버리지 계산"""
        all_domains = set([primary_domain] + sub_domains)
        covered_domains = set()

        for agent in combination:
            for domain in agent.domains:
                if domain in all_domains or domain == 'general':
                    covered_domains.add(domain)

        if 'general' in covered_domains:
            covered_domains.update(all_domains)  # 범용 에이전트가 있으면 모든 도메인 커버

        return len(covered_domains) / max(len(all_domains), 1)

    def _calculate_capability_diversity(self, combination: List[AgentProfile]) -> float:
        """역량 다양성 계산"""
        all_capabilities = set()
        for agent in combination:
            all_capabilities.update(agent.capabilities)

        # 다양한 역량을 보유할수록 높은 점수
        return min(len(all_capabilities) / 10.0, 1.0)

    def _calculate_synergy_effect(self, combination: List[AgentProfile]) -> float:
        """시너지 효과 계산"""
        agent_names = [agent.name for agent in combination]
        synergy_score = 0.0

        for agent in combination:
            for synergy_agent in agent.synergy_agents:
                if synergy_agent in agent_names:
                    synergy_score += 1.0

        # 정규화
        max_possible_synergy = len(combination) * 3  # 평균적으로 에이전트당 3개 시너지
        return min(synergy_score / max_possible_synergy, 1.0)

    def _calculate_complexity_fit(self, combination: List[AgentProfile], complexity: ComplexityLevel) -> float:
        """복잡도 적합성 계산"""
        fit_count = 0
        for agent in combination:
            if complexity.value in agent.complexity_fit:
                fit_count += 1

        return fit_count / len(combination)

    def _get_fallback_combination(self, target_count: int) -> List[AgentProfile]:
        """폴백 조합 (기본)"""
        fallback_agents = [
            'requirements_analyst',
            'technology_researcher',
            'implementation_engineer',
            'solution_architect',
            'quality_assurance'
        ]

        agents = []
        for agent_name in fallback_agents[:target_count]:
            if agent_name in self.agent_pool:
                agents.append(self.agent_pool[agent_name])

        # 부족하면 추가
        while len(agents) < target_count and len(agents) < len(self.agent_pool):
            for agent in self.agent_pool.values():
                if agent not in agents:
                    agents.append(agent)
                    break

        return agents[:target_count]

    def _generate_selection_reasoning(self, selected_agents: List[AgentProfile], analysis: RequirementAnalysis) -> str:
        """선택 근거 생성"""
        reasons = []

        # 도메인 매칭
        domain_specialists = [agent for agent in selected_agents if analysis.domain in agent.domains]
        if domain_specialists:
            reasons.append(f"{analysis.domain} 도메인 전문 에이전트 {len(domain_specialists)}개 포함")

        # 복잡도 적합성
        complexity_fit_agents = [agent for agent in selected_agents if analysis.complexity.value in agent.complexity_fit]
        if complexity_fit_agents:
            reasons.append(f"{analysis.complexity.value} 복잡도에 적합한 에이전트 {len(complexity_fit_agents)}개 선택")

        # 시너지 효과
        synergy_count = 0
        agent_names = [agent.name for agent in selected_agents]
        for agent in selected_agents:
            for synergy_agent in agent.synergy_agents:
                if synergy_agent in agent_names:
                    synergy_count += 1

        if synergy_count > 0:
            reasons.append(f"에이전트 간 {synergy_count}개 시너지 효과 확인")

        # 역량 커버리지
        all_capabilities = set()
        for agent in selected_agents:
            all_capabilities.update(agent.capabilities)
        reasons.append(f"{len(all_capabilities)}개 핵심 역량 커버")

        return " | ".join(reasons) if reasons else "기본 에이전트 조합 적용"

    def _calculate_selection_confidence(self, selected_agents: List[AgentProfile], analysis: RequirementAnalysis) -> float:
        """선택 신뢰도 계산"""
        return self._evaluate_combination(selected_agents, analysis)

    def _estimate_performance(self, selected_agents: List[AgentProfile], analysis: RequirementAnalysis) -> float:
        """성능 예측"""
        base_performance = 0.7  # 기본 성능

        # 도메인 전문성
        domain_specialists = [agent for agent in selected_agents if analysis.domain in agent.domains]
        domain_boost = min(len(domain_specialists) * 0.1, 0.2)

        # 시너지 효과
        agent_names = [agent.name for agent in selected_agents]
        synergy_count = 0
        for agent in selected_agents:
            for synergy_agent in agent.synergy_agents:
                if synergy_agent in agent_names:
                    synergy_count += 1

        synergy_boost = min(synergy_count * 0.05, 0.1)

        return min(base_performance + domain_boost + synergy_boost, 0.95)

def main():
    """테스트 함수"""
    from intelligent_requirement_analyzer import IntelligentRequirementAnalyzer

    analyzer = IntelligentRequirementAnalyzer()
    matcher = DynamicAgentMatcher()

    # 테스트 요구사항
    test_req = "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘"

    # 요구사항 분석
    analysis = analyzer.analyze_requirement(test_req)
    print(f"분석 결과: {analysis.domain}, 복잡도: {analysis.complexity.value}, 에이전트 수: {analysis.agent_count}")

    # 에이전트 매칭
    selection = matcher.select_optimal_agents(analysis)

    print(f"\n선택된 에이전트 ({len(selection.agents)}개):")
    for agent in selection.agents:
        print(f"- {agent.name}: {agent.role}")

    print(f"\n선택 근거: {selection.selection_reasoning}")
    print(f"신뢰도: {selection.confidence_score:.2f}")
    print(f"예상 성능: {selection.estimated_performance:.2f}")

if __name__ == "__main__":
    main()