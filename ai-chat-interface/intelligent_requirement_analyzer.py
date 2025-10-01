#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지능형 요구사항 분석기
요구사항을 자동 분석하여 도메인, 복잡도, 기술스택, 에이전트 구성을 추천
"""

import re
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class ComplexityLevel(Enum):
    SIMPLE = "simple"          # 단순 (3개 에이전트)
    MEDIUM = "medium"          # 중간 (4개 에이전트)
    COMPLEX = "complex"        # 복합 (5개 에이전트)
    ADVANCED = "advanced"      # 고도화 (6-7개 에이전트)

@dataclass
class RequirementAnalysis:
    """요구사항 분석 결과"""
    domain: str
    sub_domains: List[str]
    complexity: ComplexityLevel
    tech_stack: List[str]
    required_libraries: List[str]
    agent_count: int
    confidence_score: float
    keywords: List[str]
    analysis_details: Dict

class IntelligentRequirementAnalyzer:
    """지능형 요구사항 분석기"""

    def __init__(self):
        self.domain_patterns = self._load_domain_patterns()
        self.tech_stack_patterns = self._load_tech_patterns()
        self.complexity_indicators = self._load_complexity_indicators()

    def _load_domain_patterns(self) -> Dict:
        """도메인 분류 패턴 정의"""
        return {
            'web_development': {
                'keywords': ['웹사이트', '웹앱', '웹개발', 'html', 'css', 'javascript', 'react', 'vue', 'angular',
                           '홈페이지', '포털', '온라인', 'api', 'backend', 'frontend', 'rest'],
                'indicators': ['사용자 인터페이스', 'UI', 'UX', '반응형', '브라우저'],
                'weight': 1.0
            },
            'data_analysis': {
                'keywords': ['데이터', '분석', '통계', '머신러닝', 'ML', 'AI', '예측', '모델링',
                           '시각화', '차트', '그래프', '리포트', '대시보드', 'BI'],
                'indicators': ['패턴', '트렌드', '인사이트', '예측 모델', '데이터 마이닝'],
                'weight': 1.0
            },
            'content_creation': {
                'keywords': ['블로그', '콘텐츠', '글', '작성', '포스팅', 'SEO', '소셜미디어',
                           '카피라이팅', '마케팅', '광고', '브랜딩'],
                'indicators': ['주제', '키워드', '검색엔진', '조회수', '트래픽'],
                'weight': 1.0
            },
            'automation': {
                'keywords': ['자동화', '스크립트', '배치', '스케줄', '크롤링', '스크래핑',
                           '봇', '매크로', 'RPA', '프로세스', '업무'],
                'indicators': ['반복', '일정', '자동 실행', '효율성', '생산성'],
                'weight': 1.0
            },
            'mobile_app': {
                'keywords': ['모바일', '앱', 'iOS', 'Android', '스마트폰', '태블릿',
                           'Flutter', 'React Native', '앱스토어', '플레이스토어'],
                'indicators': ['모바일 기기', '터치', '푸시 알림', '오프라인'],
                'weight': 1.0
            },
            'document_processing': {
                'keywords': ['문서', '파일', 'PDF', 'Excel', 'Word', '이력서', '파싱',
                           '추출', '변환', 'OCR', '스캔'],
                'indicators': ['형식 변환', '정보 추출', '구조화', '표준화'],
                'weight': 1.0
            },
            'ecommerce': {
                'keywords': ['쇼핑몰', '이커머스', '온라인쇼핑', '결제', '주문', '배송',
                           '상품', '카트', '결제시스템', '재고'],
                'indicators': ['판매', '구매', '거래', '상거래', '수익'],
                'weight': 1.0
            },
            'game_development': {
                'keywords': ['게임', '플레이어', '스코어', '레벨', '캐릭터', '아이템',
                           'Unity', 'Unreal', '3D', '2D', '그래픽'],
                'indicators': ['게임플레이', '인터랙션', '엔터테인먼트', '재미'],
                'weight': 1.0
            }
        }

    def _load_tech_patterns(self) -> Dict:
        """기술스택 패턴 정의"""
        return {
            'web_frameworks': {
                'patterns': ['flask', 'django', 'fastapi', 'express', 'node', 'react', 'vue', 'angular'],
                'libraries': ['requests', 'beautifulsoup4', 'selenium', 'flask', 'django', 'fastapi']
            },
            'data_science': {
                'patterns': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly', 'scikit-learn', 'tensorflow'],
                'libraries': ['pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn', 'jupyter']
            },
            'nlp_text': {
                'patterns': ['텍스트', '자연어', 'NLP', '언어모델', '챗봇', '번역', '요약'],
                'libraries': ['transformers', 'openai', 'langchain', 'nltk', 'spacy', 'konlpy']
            },
            'web_scraping': {
                'patterns': ['크롤링', '스크래핑', '수집', '파싱', '웹사이트'],
                'libraries': ['requests', 'beautifulsoup4', 'selenium', 'scrapy', 'lxml']
            },
            'database': {
                'patterns': ['데이터베이스', 'DB', 'SQL', '저장', '조회', '관리'],
                'libraries': ['sqlalchemy', 'psycopg2', 'sqlite3', 'pymongo', 'redis']
            },
            'api_integration': {
                'patterns': ['API', '연동', '통합', '외부서비스', 'REST', 'GraphQL'],
                'libraries': ['requests', 'httpx', 'aiohttp', 'fastapi', 'flask-restful']
            }
        }

    def _load_complexity_indicators(self) -> Dict:
        """복잡도 지표 정의"""
        return {
            'simple': {
                'indicators': ['간단한', '기본적인', '단순한', '빠른', '최소한의'],
                'anti_indicators': ['복잡한', '고도화', '대용량', '다중', '통합'],
                'max_features': 3,
                'max_systems': 1
            },
            'medium': {
                'indicators': ['일반적인', '표준적인', '기본 기능', '일부 기능'],
                'anti_indicators': ['매우 복잡한', '엔터프라이즈급', '대규모'],
                'max_features': 7,
                'max_systems': 2
            },
            'complex': {
                'indicators': ['다양한', '여러', '통합', '고급', '다중', '포괄적인'],
                'anti_indicators': ['매우 단순한', '기본만'],
                'max_features': 12,
                'max_systems': 4
            },
            'advanced': {
                'indicators': ['엔터프라이즈', '대규모', '고도화', '전문적인', '완전한', '포괄적인'],
                'anti_indicators': [],
                'max_features': 20,
                'max_systems': 8
            }
        }

    def analyze_requirement(self, requirement: str) -> RequirementAnalysis:
        """요구사항 종합 분석"""

        # 전처리
        requirement_lower = requirement.lower()

        # 1. 도메인 분석
        domain, domain_confidence = self._analyze_domain(requirement_lower)

        # 2. 서브 도메인 분석
        sub_domains = self._analyze_sub_domains(requirement_lower, domain)

        # 3. 복잡도 분석
        complexity = self._analyze_complexity(requirement_lower)

        # 4. 기술스택 추론
        tech_stack = self._infer_tech_stack(requirement_lower, domain)

        # 5. 필요 라이브러리 추론
        required_libraries = self._infer_libraries(requirement_lower, tech_stack)

        # 6. 에이전트 수 결정
        agent_count = self._determine_agent_count(complexity, len(sub_domains))

        # 7. 키워드 추출
        keywords = self._extract_keywords(requirement_lower)

        # 8. 종합 신뢰도 점수
        confidence_score = self._calculate_confidence(domain_confidence, complexity, len(keywords))

        return RequirementAnalysis(
            domain=domain,
            sub_domains=sub_domains,
            complexity=complexity,
            tech_stack=tech_stack,
            required_libraries=required_libraries,
            agent_count=agent_count,
            confidence_score=confidence_score,
            keywords=keywords,
            analysis_details={
                'domain_confidence': domain_confidence,
                'complexity_factors': self._get_complexity_factors(requirement_lower),
                'tech_reasoning': self._get_tech_reasoning(requirement_lower, domain)
            }
        )

    def _analyze_domain(self, requirement: str) -> Tuple[str, float]:
        """도메인 분석"""
        domain_scores = {}

        for domain, patterns in self.domain_patterns.items():
            score = 0.0

            # 키워드 매칭
            for keyword in patterns['keywords']:
                if keyword in requirement:
                    score += patterns['weight']

            # 지표 매칭
            for indicator in patterns['indicators']:
                if indicator in requirement:
                    score += patterns['weight'] * 0.5

            domain_scores[domain] = score

        if not domain_scores or max(domain_scores.values()) == 0:
            return 'general', 0.5

        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = min(domain_scores[best_domain] / 3.0, 1.0)  # 정규화

        return best_domain, confidence

    def _analyze_sub_domains(self, requirement: str, main_domain: str) -> List[str]:
        """서브 도메인 분석"""
        sub_domains = []

        # 주 도메인 외 다른 도메인 요소들 찾기
        for domain, patterns in self.domain_patterns.items():
            if domain == main_domain:
                continue

            score = 0
            for keyword in patterns['keywords']:
                if keyword in requirement:
                    score += 1

            if score >= 2:  # 임계값
                sub_domains.append(domain)

        return sub_domains[:3]  # 최대 3개까지

    def _analyze_complexity(self, requirement: str) -> ComplexityLevel:
        """복잡도 분석"""
        complexity_scores = {level: 0 for level in ComplexityLevel}

        # 문장 길이 기반 기본 점수
        word_count = len(requirement.split())
        if word_count < 10:
            complexity_scores[ComplexityLevel.SIMPLE] += 2
        elif word_count < 25:
            complexity_scores[ComplexityLevel.MEDIUM] += 2
        elif word_count < 50:
            complexity_scores[ComplexityLevel.COMPLEX] += 2
        else:
            complexity_scores[ComplexityLevel.ADVANCED] += 2

        # 복잡도 지표 매칭
        for level_name, indicators in self.complexity_indicators.items():
            level = ComplexityLevel(level_name)

            # 긍정 지표
            for indicator in indicators['indicators']:
                if indicator in requirement:
                    complexity_scores[level] += 1

            # 부정 지표
            for anti_indicator in indicators['anti_indicators']:
                if anti_indicator in requirement:
                    complexity_scores[level] -= 1

        # 기능 수 추정
        feature_keywords = ['기능', '모듈', '시스템', '서비스', '처리', '관리', '분석', '생성']
        feature_count = sum(1 for keyword in feature_keywords if keyword in requirement)

        if feature_count <= 2:
            complexity_scores[ComplexityLevel.SIMPLE] += 1
        elif feature_count <= 5:
            complexity_scores[ComplexityLevel.MEDIUM] += 1
        elif feature_count <= 10:
            complexity_scores[ComplexityLevel.COMPLEX] += 1
        else:
            complexity_scores[ComplexityLevel.ADVANCED] += 1

        return max(complexity_scores, key=complexity_scores.get)

    def _infer_tech_stack(self, requirement: str, domain: str) -> List[str]:
        """기술스택 추론"""
        tech_stack = []

        # 도메인 기반 기본 스택
        domain_tech_map = {
            'web_development': ['Python', 'Flask/FastAPI', 'HTML/CSS', 'JavaScript'],
            'data_analysis': ['Python', 'Pandas', 'NumPy', 'Matplotlib'],
            'content_creation': ['Python', 'NLP Libraries', 'Web APIs'],
            'automation': ['Python', 'Selenium', 'Requests', 'Schedule'],
            'mobile_app': ['Flutter', 'React Native', 'Native Development'],
            'document_processing': ['Python', 'PyPDF2', 'openpyxl', 'docx'],
            'ecommerce': ['Python', 'Flask/Django', 'Payment APIs', 'Database'],
            'game_development': ['Unity', 'C#', 'Python', 'Game Engines']
        }

        if domain in domain_tech_map:
            tech_stack.extend(domain_tech_map[domain])

        # 패턴 기반 추가 기술
        for tech_category, patterns in self.tech_stack_patterns.items():
            for pattern in patterns['patterns']:
                if pattern in requirement:
                    tech_stack.append(tech_category.replace('_', ' ').title())
                    break

        return list(set(tech_stack))  # 중복 제거

    def _infer_libraries(self, requirement: str, tech_stack: List[str]) -> List[str]:
        """필요 라이브러리 추론"""
        libraries = set(['crewai', 'python-dotenv', 'langchain-litellm'])  # 기본 라이브러리

        # 기술스택 기반 라이브러리 추가
        for tech_category, patterns in self.tech_stack_patterns.items():
            for pattern in patterns['patterns']:
                if pattern in requirement:
                    libraries.update(patterns['libraries'])

        # 도메인별 추가 라이브러리
        domain_libraries = {
            'web_development': ['flask', 'requests', 'jinja2'],
            'data_analysis': ['pandas', 'numpy', 'matplotlib'],
            'content_creation': ['openai', 'requests', 'beautifulsoup4'],
            'automation': ['selenium', 'schedule', 'requests'],
            'document_processing': ['PyPDF2', 'openpyxl', 'python-docx'],
        }

        # 요구사항에서 직접 언급된 라이브러리
        mentioned_libs = re.findall(r'\b(pandas|numpy|flask|django|selenium|requests|beautifulsoup4|openai)\b', requirement)
        libraries.update(mentioned_libs)

        return sorted(list(libraries))

    def _determine_agent_count(self, complexity: ComplexityLevel, sub_domain_count: int) -> int:
        """에이전트 수 결정"""
        base_count = {
            ComplexityLevel.SIMPLE: 3,
            ComplexityLevel.MEDIUM: 4,
            ComplexityLevel.COMPLEX: 5,
            ComplexityLevel.ADVANCED: 6
        }

        count = base_count[complexity]

        # 서브 도메인이 있으면 에이전트 추가
        count += min(sub_domain_count, 2)

        return min(count, 7)  # 최대 7개

    def _extract_keywords(self, requirement: str) -> List[str]:
        """핵심 키워드 추출"""
        # 불용어 제거
        stop_words = {'을', '를', '이', '가', '은', '는', '에', '에서', '로', '으로', '와', '과', '의', '도', '만', '까지', '부터', '하고', '하는', '한', '할', '해'}

        # 단어 추출 (한글, 영문, 숫자)
        words = re.findall(r'[가-힣a-zA-Z0-9]+', requirement)

        # 불용어 제거 및 길이 필터링
        keywords = [word for word in words if word not in stop_words and len(word) >= 2]

        # 빈도 기반 상위 키워드 (최대 10개)
        from collections import Counter
        word_freq = Counter(keywords)

        return [word for word, _ in word_freq.most_common(10)]

    def _calculate_confidence(self, domain_confidence: float, complexity: ComplexityLevel, keyword_count: int) -> float:
        """종합 신뢰도 점수 계산"""
        base_score = domain_confidence * 0.4  # 도메인 신뢰도 40%

        # 복잡도 점수 20%
        complexity_score = {
            ComplexityLevel.SIMPLE: 0.9,
            ComplexityLevel.MEDIUM: 0.8,
            ComplexityLevel.COMPLEX: 0.7,
            ComplexityLevel.ADVANCED: 0.6
        }[complexity] * 0.2

        # 키워드 충실도 40%
        keyword_score = min(keyword_count / 10.0, 1.0) * 0.4

        return min(base_score + complexity_score + keyword_score, 1.0)

    def _get_complexity_factors(self, requirement: str) -> List[str]:
        """복잡도 결정 요인"""
        factors = []

        if '다양한' in requirement or '여러' in requirement:
            factors.append('다중 기능 요구')
        if '통합' in requirement or '연동' in requirement:
            factors.append('시스템 통합 필요')
        if '자동화' in requirement:
            factors.append('자동화 프로세스')
        if '분석' in requirement:
            factors.append('데이터 분석 포함')
        if len(requirement.split()) > 30:
            factors.append('상세한 요구사항')

        return factors

    def _get_tech_reasoning(self, requirement: str, domain: str) -> str:
        """기술 선택 근거"""
        reasons = []

        if 'python' in requirement:
            reasons.append('Python 명시적 요구')
        elif domain in ['data_analysis', 'automation', 'document_processing']:
            reasons.append('도메인 특성상 Python 최적')

        if '웹' in requirement or 'api' in requirement:
            reasons.append('웹 개발 프레임워크 필요')

        if '데이터' in requirement or '분석' in requirement:
            reasons.append('데이터 처리 라이브러리 필요')

        return ', '.join(reasons) if reasons else '일반적인 기술스택 적용'

def main():
    """테스트 함수"""
    analyzer = IntelligentRequirementAnalyzer()

    # 테스트 요구사항들
    test_requirements = [
        "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘",
        "사용자 이력서 PDF 파일을 분석해서 개인정보, 경력, 학력을 추출하고 구조화된 JSON으로 변환하는 시스템",
        "온라인 쇼핑몰 주문 관리 시스템을 만들어서 상품 등록, 주문 처리, 결제 연동, 재고 관리 기능 포함",
        "간단한 할일 목록 웹앱 만들어줘"
    ]

    for req in test_requirements:
        print(f"\n{'='*60}")
        print(f"요구사항: {req}")
        print('='*60)

        analysis = analyzer.analyze_requirement(req)

        print(f"도메인: {analysis.domain}")
        print(f"서브도메인: {analysis.sub_domains}")
        print(f"복잡도: {analysis.complexity.value}")
        print(f"에이전트 수: {analysis.agent_count}")
        print(f"기술스택: {analysis.tech_stack}")
        print(f"필요 라이브러리: {analysis.required_libraries}")
        print(f"신뢰도: {analysis.confidence_score:.2f}")
        print(f"키워드: {analysis.keywords}")

if __name__ == "__main__":
    main()