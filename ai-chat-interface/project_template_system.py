# -*- coding: utf-8 -*-
"""
Project Template System
프로젝트 템플릿 시스템 - 다양한 프로젝트 유형별 템플릿 관리
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ProjectType(Enum):
    """프로젝트 유형 정의"""
    WEB_APP = "web_app"
    MOBILE_APP = "mobile_app"
    API_SERVER = "api_server"
    DESKTOP_APP = "desktop_app"
    DATA_ANALYSIS = "data_analysis"
    ML_PROJECT = "ml_project"
    BLOCKCHAIN = "blockchain"
    GAME_DEV = "game_dev"
    ECOMMERCE = "ecommerce"
    CRM_SYSTEM = "crm_system"

class Framework(Enum):
    """AI 프레임워크 정의"""
    CREW_AI = "crew_ai"
    META_GPT = "meta_gpt"

@dataclass
class LLMMapping:
    """역할별 LLM 매핑"""
    role: str
    llm_model: str
    description: str
    reason: str  # 해당 역할에 이 모델을 추천하는 이유

@dataclass
class ProjectTemplate:
    """프로젝트 템플릿 구조"""
    id: str
    name: str
    display_name: str
    description: str
    project_type: str
    framework: str
    icon: str
    tags: List[str]
    difficulty: str  # "beginner", "intermediate", "advanced"
    estimated_duration: str  # "1-2 hours", "1 day", "1 week" etc.

    # 프로젝트 설정
    default_settings: Dict[str, Any]
    llm_mappings: List[LLMMapping]
    required_skills: List[str]
    deliverables: List[str]

    # 템플릿 메타데이터
    created_at: str
    updated_at: str
    author: str
    version: str
    is_featured: bool = False
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)

class ProjectTemplateManager:
    """프로젝트 템플릿 관리자"""

    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(__file__), 'templates'
        )
        self.templates: Dict[str, ProjectTemplate] = {}
        self._ensure_templates_dir()
        self._load_default_templates()

    def _ensure_templates_dir(self):
        """템플릿 디렉토리 생성"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)

    def _load_default_templates(self):
        """기본 템플릿들 로드"""
        self._create_default_templates()

    def _create_default_templates(self):
        """기본 템플릿들 생성"""

        # 1. E-commerce 웹앱 (CrewAI)
        ecommerce_template = ProjectTemplate(
            id="ecommerce_web_crewai",
            name="ecommerce_web_app",
            display_name="E-commerce 웹 애플리케이션",
            description="온라인 쇼핑몰 웹사이트 개발 (React + Node.js + PostgreSQL)",
            project_type=ProjectType.WEB_APP.value,
            framework=Framework.CREW_AI.value,
            icon="🛒",
            tags=["ecommerce", "web", "react", "nodejs", "database"],
            difficulty="intermediate",
            estimated_duration="1-2 weeks",
            default_settings={
                "frontend": "React.js",
                "backend": "Node.js + Express",
                "database": "PostgreSQL",
                "payment": "Stripe",
                "features": ["product catalog", "shopping cart", "user authentication", "order management"]
            },
            llm_mappings=[
                LLMMapping("Researcher", "gemini-pro", "시장 조사 및 사용자 분석", "Gemini Pro는 대용량 데이터 분석과 시장 조사에 특화"),
                LLMMapping("Writer", "gpt-4", "기술 문서 및 사용자 가이드 작성", "GPT-4는 명확한 문서 작성에 뛰어남"),
                LLMMapping("Planner", "claude-3", "프로젝트 계획 및 아키텍처 설계", "Claude-3는 체계적인 계획 수립에 우수함")
            ],
            required_skills=["React", "Node.js", "Database Design", "API Development"],
            deliverables=["시장 조사 보고서", "기술 명세서", "프로젝트 계획서", "구현 가이드"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            author="AI Chat Interface",
            version="1.0",
            is_featured=True
        )

        # 2. 모바일 앱 (MetaGPT)
        mobile_app_template = ProjectTemplate(
            id="mobile_app_metagpt",
            name="mobile_health_app",
            display_name="헬스케어 모바일 앱",
            description="건강 관리 및 피트니스 추적 모바일 애플리케이션 (React Native)",
            project_type=ProjectType.MOBILE_APP.value,
            framework=Framework.META_GPT.value,
            icon="📱",
            tags=["mobile", "healthcare", "fitness", "react-native"],
            difficulty="intermediate",
            estimated_duration="2-3 weeks",
            default_settings={
                "platform": "React Native",
                "target_os": ["iOS", "Android"],
                "backend": "Firebase",
                "features": ["activity tracking", "health metrics", "goal setting", "social sharing"]
            },
            llm_mappings=[
                LLMMapping("Product Manager", "gpt-4", "제품 요구사항 분석", "GPT-4는 사용자 니즈 분석과 기능 정의에 탁월"),
                LLMMapping("Architect", "claude-3", "시스템 아키텍처 설계", "Claude-3는 모바일 앱 아키텍처 설계에 우수"),
                LLMMapping("Engineer", "deepseek-coder", "React Native 개발", "DeepSeek Coder는 모바일 개발 코드 생성에 특화"),
                LLMMapping("QA Engineer", "llama-3", "테스트 케이스 작성", "Llama-3는 포괄적인 테스트 시나리오 생성에 적합")
            ],
            required_skills=["React Native", "Mobile UI/UX", "Firebase", "API Integration"],
            deliverables=["PRD 문서", "시스템 설계서", "구현 코드", "테스트 계획서"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            author="AI Chat Interface",
            version="1.0",
            is_featured=True
        )

        # 3. API 서버 (MetaGPT)
        api_server_template = ProjectTemplate(
            id="api_server_metagpt",
            name="rest_api_server",
            display_name="RESTful API 서버",
            description="확장 가능한 RESTful API 서버 개발 (Python + FastAPI + PostgreSQL)",
            project_type=ProjectType.API_SERVER.value,
            framework=Framework.META_GPT.value,
            icon="🔗",
            tags=["api", "backend", "fastapi", "python", "rest"],
            difficulty="beginner",
            estimated_duration="1 week",
            default_settings={
                "framework": "FastAPI",
                "language": "Python",
                "database": "PostgreSQL",
                "authentication": "JWT",
                "features": ["CRUD operations", "authentication", "documentation", "rate limiting"]
            },
            llm_mappings=[
                LLMMapping("Product Manager", "gpt-4", "API 요구사항 정의", "GPT-4는 API 스펙 정의에 우수함"),
                LLMMapping("Architect", "claude-3", "API 설계 및 아키텍처", "Claude-3는 API 아키텍처 설계에 특화"),
                LLMMapping("Engineer", "deepseek-coder", "FastAPI 코드 구현", "DeepSeek Coder는 Python/FastAPI 개발에 최적화"),
                LLMMapping("QA Engineer", "gemini-pro", "API 테스트 자동화", "Gemini Pro는 테스트 자동화 구현에 효과적")
            ],
            required_skills=["Python", "FastAPI", "Database Design", "API Design"],
            deliverables=["API 명세서", "데이터베이스 스키마", "구현 코드", "테스트 슈트"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            author="AI Chat Interface",
            version="1.0"
        )

        # 4. 데이터 분석 프로젝트 (CrewAI)
        data_analysis_template = ProjectTemplate(
            id="data_analysis_crewai",
            name="sales_data_analysis",
            display_name="매출 데이터 분석 프로젝트",
            description="매출 데이터 분석 및 인사이트 도출 (Python + Pandas + Visualization)",
            project_type=ProjectType.DATA_ANALYSIS.value,
            framework=Framework.CREW_AI.value,
            icon="📊",
            tags=["data", "analysis", "python", "visualization", "business-intelligence"],
            difficulty="beginner",
            estimated_duration="3-5 days",
            default_settings={
                "language": "Python",
                "tools": ["Pandas", "NumPy", "Matplotlib", "Seaborn", "Jupyter"],
                "data_sources": ["CSV", "Database", "API"],
                "outputs": ["reports", "dashboards", "recommendations"]
            },
            llm_mappings=[
                LLMMapping("Researcher", "gemini-pro", "데이터 탐색 및 패턴 분석", "Gemini Pro는 대용량 데이터 패턴 분석에 뛰어남"),
                LLMMapping("Writer", "gpt-4", "분석 리포트 작성", "GPT-4는 데이터 인사이트를 명확한 리포트로 작성"),
                LLMMapping("Planner", "claude-3", "분석 전략 및 방법론 수립", "Claude-3는 체계적인 분석 접근법 설계에 우수")
            ],
            required_skills=["Python", "Data Analysis", "Statistics", "Visualization"],
            deliverables=["데이터 탐색 보고서", "분석 결과 리포트", "시각화 대시보드", "비즈니스 추천사항"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            author="AI Chat Interface",
            version="1.0"
        )

        # 5. 머신러닝 프로젝트 (MetaGPT)
        ml_template = ProjectTemplate(
            id="ml_project_metagpt",
            name="customer_churn_prediction",
            display_name="고객 이탈 예측 ML 모델",
            description="머신러닝을 활용한 고객 이탈 예측 시스템 (Python + Scikit-learn)",
            project_type=ProjectType.ML_PROJECT.value,
            framework=Framework.META_GPT.value,
            icon="🤖",
            tags=["machine-learning", "prediction", "python", "scikit-learn", "model"],
            difficulty="advanced",
            estimated_duration="2-3 weeks",
            default_settings={
                "language": "Python",
                "ml_libraries": ["Scikit-learn", "Pandas", "NumPy"],
                "model_types": ["Random Forest", "XGBoost", "Neural Network"],
                "evaluation_metrics": ["Accuracy", "Precision", "Recall", "F1-Score"]
            },
            llm_mappings=[
                LLMMapping("Product Manager", "gpt-4", "ML 프로젝트 요구사항 정의", "GPT-4는 비즈니스 요구사항을 ML 문제로 정의하는데 탁월"),
                LLMMapping("Architect", "claude-3", "ML 파이프라인 아키텍처", "Claude-3는 ML 시스템 아키텍처 설계에 우수"),
                LLMMapping("Engineer", "deepseek-coder", "ML 모델 구현", "DeepSeek Coder는 ML 코드 구현에 특화"),
                LLMMapping("QA Engineer", "gemini-pro", "모델 검증 및 테스트", "Gemini Pro는 ML 모델 평가와 검증에 효과적")
            ],
            required_skills=["Machine Learning", "Python", "Statistics", "Data Preprocessing"],
            deliverables=["데이터 분석 보고서", "ML 모델", "평가 리포트", "배포 가이드"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            author="AI Chat Interface",
            version="1.0"
        )

        # 템플릿들을 딕셔너리에 저장
        self.templates.update({
            ecommerce_template.id: ecommerce_template,
            mobile_app_template.id: mobile_app_template,
            api_server_template.id: api_server_template,
            data_analysis_template.id: data_analysis_template,
            ml_template.id: ml_template
        })

        # 파일로 저장
        self._save_templates_to_files()

    def _save_templates_to_files(self):
        """템플릿들을 개별 JSON 파일로 저장"""
        for template_id, template in self.templates.items():
            file_path = os.path.join(self.templates_dir, f"{template_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, indent=2, ensure_ascii=False)

    def get_all_templates(self) -> List[ProjectTemplate]:
        """모든 템플릿 조회"""
        return list(self.templates.values())

    def get_template_by_id(self, template_id: str) -> Optional[ProjectTemplate]:
        """ID로 템플릿 조회"""
        return self.templates.get(template_id)

    def get_templates_by_type(self, project_type: str) -> List[ProjectTemplate]:
        """프로젝트 유형별 템플릿 조회"""
        return [t for t in self.templates.values() if t.project_type == project_type]

    def get_templates_by_framework(self, framework: str) -> List[ProjectTemplate]:
        """프레임워크별 템플릿 조회"""
        return [t for t in self.templates.values() if t.framework == framework]

    def get_featured_templates(self) -> List[ProjectTemplate]:
        """추천 템플릿 조회"""
        return [t for t in self.templates.values() if t.is_featured]

    def search_templates(self, query: str) -> List[ProjectTemplate]:
        """템플릿 검색"""
        query = query.lower()
        results = []

        for template in self.templates.values():
            # 이름, 설명, 태그에서 검색
            if (query in template.name.lower() or
                query in template.display_name.lower() or
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)

        return results

    def create_project_from_template(self, template_id: str, project_name: str,
                                   custom_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """템플릿으로부터 프로젝트 생성"""
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")

        # 사용 횟수 증가
        template.usage_count += 1

        # 프로젝트 설정 병합
        project_settings = template.default_settings.copy()
        if custom_settings:
            project_settings.update(custom_settings)

        # 새 프로젝트 생성
        project_data = {
            "id": str(uuid.uuid4()),
            "name": project_name,
            "template_id": template_id,
            "template_name": template.display_name,
            "project_type": template.project_type,
            "framework": template.framework,
            "settings": project_settings,
            "llm_mappings": [asdict(mapping) for mapping in template.llm_mappings],
            "required_skills": template.required_skills,
            "deliverables": template.deliverables,
            "status": "initialized",
            "created_at": datetime.now().isoformat(),
            "estimated_duration": template.estimated_duration,
            "difficulty": template.difficulty
        }

        return project_data

    def get_template_statistics(self) -> Dict[str, Any]:
        """템플릿 사용 통계"""
        stats = {
            "total_templates": len(self.templates),
            "by_type": {},
            "by_framework": {},
            "by_difficulty": {},
            "most_used": [],
            "featured_count": len(self.get_featured_templates())
        }

        # 유형별 통계
        for template in self.templates.values():
            stats["by_type"][template.project_type] = stats["by_type"].get(template.project_type, 0) + 1
            stats["by_framework"][template.framework] = stats["by_framework"].get(template.framework, 0) + 1
            stats["by_difficulty"][template.difficulty] = stats["by_difficulty"].get(template.difficulty, 0) + 1

        # 가장 많이 사용된 템플릿
        sorted_templates = sorted(self.templates.values(), key=lambda t: t.usage_count, reverse=True)
        stats["most_used"] = [
            {"id": t.id, "name": t.display_name, "usage_count": t.usage_count}
            for t in sorted_templates[:5]
        ]

        return stats

# 전역 템플릿 매니저 인스턴스
template_manager = ProjectTemplateManager()