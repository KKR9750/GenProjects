# -*- coding: utf-8 -*-
"""
Project Template Manager
프로젝트 템플릿 관리 및 생성 시스템
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class TemplateManager:
    """프로젝트 템플릿 관리 클래스"""

    def __init__(self, templates_file: str = "templates/project_templates.json"):
        self.templates_file = templates_file
        self.templates_data = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """템플릿 파일 로드"""
        try:
            templates_path = os.path.join(os.path.dirname(__file__), self.templates_file)
            with open(templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"템플릿 파일을 찾을 수 없습니다: {self.templates_file}")
            return {"templates": {}, "categories": []}
        except Exception as e:
            print(f"템플릿 파일 로드 실패: {e}")
            return {"templates": {}, "categories": []}

    def get_all_templates(self) -> Dict[str, Any]:
        """모든 템플릿 조회"""
        return {
            "success": True,
            "templates": self.templates_data.get("templates", {}),
            "categories": self.templates_data.get("categories", []),
            "count": len(self.templates_data.get("templates", {}))
        }

    def get_template_by_id(self, template_id: str) -> Dict[str, Any]:
        """특정 템플릿 조회"""
        templates = self.templates_data.get("templates", {})

        if template_id in templates:
            return {
                "success": True,
                "template": templates[template_id]
            }
        else:
            return {
                "success": False,
                "error": f"템플릿을 찾을 수 없습니다: {template_id}"
            }

    def get_templates_by_category(self, category: str) -> Dict[str, Any]:
        """카테고리별 템플릿 조회"""
        templates = self.templates_data.get("templates", {})
        filtered_templates = {}

        for template_id, template_data in templates.items():
            if template_data.get("category", "").lower() == category.lower():
                filtered_templates[template_id] = template_data

        return {
            "success": True,
            "templates": filtered_templates,
            "category": category,
            "count": len(filtered_templates)
        }

    def search_templates(self, query: str) -> Dict[str, Any]:
        """템플릿 검색"""
        templates = self.templates_data.get("templates", {})
        results = {}
        query_lower = query.lower()

        for template_id, template_data in templates.items():
            # 이름, 설명, 태그에서 검색
            searchable_text = (
                template_data.get("name", "") + " " +
                template_data.get("description", "") + " " +
                " ".join(template_data.get("tags", []))
            ).lower()

            if query_lower in searchable_text:
                results[template_id] = template_data

        return {
            "success": True,
            "templates": results,
            "query": query,
            "count": len(results)
        }

    def create_project_from_template(self, template_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 기반 프로젝트 생성"""
        template_result = self.get_template_by_id(template_id)

        if not template_result.get("success"):
            return template_result

        template = template_result["template"]

        # 기본 프로젝트 데이터 설정
        enhanced_project_data = {
            "name": project_data.get("name", f"새 {template['name']} 프로젝트"),
            "description": project_data.get("description", template["description"]),
            "template_id": template_id,
            "template_name": template["name"],
            "selected_ai": project_data.get("selected_ai", template["recommended_ai"]),
            "project_type": template_id,
            "category": template["category"],
            "estimated_duration": template["estimated_duration"],
            "complexity": template["complexity"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),

            # 템플릿 특화 데이터
            "technical_requirements": project_data.get("technical_requirements", template.get("tech_stack_suggestions", {})),
            "default_requirements": template.get("default_requirements", []),
            "project_structure": template.get("project_structure", {}),

            # 메타데이터
            "metadata": {
                "template_version": "1.0",
                "tags": template.get("tags", []),
                "icon": template.get("icon", "📁"),
                "auto_generated": True
            }
        }

        # AI 프레임워크별 LLM 매핑 설정
        selected_ai = enhanced_project_data["selected_ai"]
        default_mappings = template.get("default_llm_mapping", {})

        if selected_ai in default_mappings:
            enhanced_project_data["recommended_llm_mapping"] = default_mappings[selected_ai]

        return {
            "success": True,
            "project_data": enhanced_project_data,
            "template": template,
            "message": f"{template['name']} 템플릿 기반 프로젝트 데이터가 생성되었습니다"
        }

    def get_template_recommendations(self, user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 선호도 기반 템플릿 추천"""
        templates = self.templates_data.get("templates", {})
        recommendations = []

        # 선호 복잡도
        preferred_complexity = user_preferences.get("complexity", "medium")
        # 선호 카테고리
        preferred_categories = user_preferences.get("categories", [])
        # 경험 수준
        experience_level = user_preferences.get("experience", "intermediate")

        for template_id, template_data in templates.items():
            score = 0

            # 복잡도 매칭
            if template_data.get("complexity") == preferred_complexity:
                score += 3

            # 카테고리 매칭
            if template_data.get("category", "").lower() in [cat.lower() for cat in preferred_categories]:
                score += 2

            # 경험 수준별 가중치
            if experience_level == "beginner" and template_data.get("complexity") == "low":
                score += 2
            elif experience_level == "advanced" and template_data.get("complexity") == "high":
                score += 2

            if score > 0:
                recommendations.append({
                    "template_id": template_id,
                    "template": template_data,
                    "score": score,
                    "reason": self._get_recommendation_reason(template_data, user_preferences)
                })

        # 점수순 정렬
        recommendations.sort(key=lambda x: x["score"], reverse=True)

        return {
            "success": True,
            "recommendations": recommendations[:5],  # 상위 5개만 반환
            "count": len(recommendations)
        }

    def _get_recommendation_reason(self, template: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """추천 이유 생성"""
        reasons = []

        if template.get("complexity") == preferences.get("complexity"):
            reasons.append(f"{preferences.get('complexity')} 복잡도 선호에 적합")

        if template.get("category", "").lower() in [cat.lower() for cat in preferences.get("categories", [])]:
            reasons.append(f"{template.get('category')} 분야 선호에 적합")

        if not reasons:
            reasons.append("인기 있는 프로젝트 유형")

        return ", ".join(reasons)

    def get_template_statistics(self) -> Dict[str, Any]:
        """템플릿 통계 정보"""
        templates = self.templates_data.get("templates", {})
        categories = self.templates_data.get("categories", [])

        # 카테고리별 템플릿 수
        category_counts = {}
        complexity_counts = {"low": 0, "medium": 0, "high": 0}
        ai_framework_counts = {"crewai": 0, "metagpt": 0}

        for template_data in templates.values():
            # 카테고리별 계산
            category = template_data.get("category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

            # 복잡도별 계산
            complexity = template_data.get("complexity", "medium")
            if complexity in complexity_counts:
                complexity_counts[complexity] += 1

            # 추천 AI 프레임워크별 계산
            recommended_ai = template_data.get("recommended_ai", "")
            if "crew" in recommended_ai.lower():
                ai_framework_counts["crewai"] += 1
            elif "meta" in recommended_ai.lower():
                ai_framework_counts["metagpt"] += 1

        return {
            "success": True,
            "total_templates": len(templates),
            "total_categories": len(categories),
            "category_distribution": category_counts,
            "complexity_distribution": complexity_counts,
            "ai_framework_distribution": ai_framework_counts,
            "categories": [cat["name"] for cat in categories]
        }


# 전역 템플릿 매니저 인스턴스
template_manager = TemplateManager()