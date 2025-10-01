#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
설정 기반 스마트 모델 할당 시스템
JSON 설정 파일을 통해 LLM 모델 조합을 유연하게 관리
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from intelligent_requirement_analyzer import RequirementAnalysis, ComplexityLevel
from dynamic_agent_matcher import AgentSelection, AgentProfile

@dataclass
class ModelSpec:
    """모델 사양"""
    name: str                # 간단한 이름 (gpt-4, gemini-2.5-flash 등)
    litellm_name: str        # litellm 호환 이름 (openai/gpt-4, gemini/gemini-2.0-flash-exp 등)
    cost_level: str          # low, medium, high
    speed_level: str         # slow, medium, fast, very_fast
    strengths: List[str]     # 특장점
    api_provider: str        # openai, google, anthropic, etc.
    env_key: str             # 환경변수 키 (OPENAI_API_KEY, GOOGLE_API_KEY 등)
    enabled: bool = True
    backup_model: Optional[str] = None

@dataclass
class ModelAllocation:
    """모델 할당 결과"""
    agent_model_mapping: Dict[str, str]  # 에이전트 -> litellm 형식 모델명 매핑
    simple_model_mapping: Dict[str, str]  # 에이전트 -> 간단한 모델명 매핑 (호환성용)
    total_estimated_cost: float
    allocation_reasoning: str
    confidence_score: float
    backup_allocations: Dict[str, str]
    env_keys_required: List[str]  # 필요한 환경변수 목록
    missing_env_keys: List[str]   # 누락된 환경변수 목록

class SmartModelAllocator:
    """스마트 모델 할당 시스템"""

    def __init__(self, config_path: str = "model_config.json"):
        self.config_path = config_path
        self.config_dir = Path(config_path).parent
        self.config_dir.mkdir(exist_ok=True)

        self.model_config = self._load_or_create_config()
        self.model_specs = self._parse_model_specs()
        self.env_status = self._validate_environment_keys()

        # 환경변수 상태 출력
        if self.env_status['missing_keys']:
            print(f"WARNING: 누락된 환경변수: {', '.join(self.env_status['missing_keys'])}")
        if self.env_status['available_keys']:
            print(f"OK: 사용 가능한 환경변수: {', '.join(self.env_status['available_keys'])}")

    def _load_or_create_config(self) -> Dict:
        """설정 파일 로드 또는 생성"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}, 기본 설정 생성")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self) -> Dict:
        """기본 설정 생성"""
        default_config = {
            "version": "1.0",
            "last_updated": "2025-01-15",
            "description": "CrewAI LLM 모델 할당 설정 (수정 가능)",

            "model_pool": {
                "gpt-4": {
                    "cost_level": "high",
                    "speed_level": "medium",
                    "strengths": ["advanced_reasoning", "complex_analysis", "problem_solving"],
                    "api_provider": "openai",
                    "enabled": True,
                    "backup_model": "gpt-3.5-turbo"
                },
                "gpt-3.5-turbo": {
                    "cost_level": "medium",
                    "speed_level": "fast",
                    "strengths": ["general_purpose", "quick_response", "cost_effective"],
                    "api_provider": "openai",
                    "enabled": True,
                    "backup_model": "gemini-flash"
                },
                "gemini-flash": {
                    "cost_level": "low",
                    "speed_level": "fast",
                    "strengths": ["speed", "cost_efficiency", "general_tasks"],
                    "api_provider": "google",
                    "enabled": True,
                    "backup_model": "gpt-3.5-turbo"
                },
                "gemini-pro": {
                    "cost_level": "medium",
                    "speed_level": "medium",
                    "strengths": ["balanced_performance", "multimodal", "reasoning"],
                    "api_provider": "google",
                    "enabled": True,
                    "backup_model": "gpt-3.5-turbo"
                },
                "claude-3": {
                    "cost_level": "medium",
                    "speed_level": "medium",
                    "strengths": ["creative_writing", "document_analysis", "structured_output"],
                    "api_provider": "anthropic",
                    "enabled": True,
                    "backup_model": "gpt-3.5-turbo"
                },
                "deepseek-coder": {
                    "cost_level": "low",
                    "speed_level": "fast",
                    "strengths": ["coding", "technical_documentation", "debugging"],
                    "api_provider": "deepseek",
                    "enabled": True,
                    "backup_model": "gpt-3.5-turbo"
                }
            },

            "agent_preferences": {
                "requirements_analyst": {
                    "preferred_models": ["gpt-4", "claude-3", "gemini-pro"],
                    "reasoning": "복잡한 요구사항 분석에는 고급 추론 능력 필요"
                },
                "technology_researcher": {
                    "preferred_models": ["gpt-4", "gemini-pro", "gpt-3.5-turbo"],
                    "reasoning": "최신 기술 정보와 추론 능력 필요"
                },
                "solution_architect": {
                    "preferred_models": ["gpt-4", "claude-3"],
                    "reasoning": "시스템 설계에는 높은 수준의 분석력 필요"
                },
                "implementation_engineer": {
                    "preferred_models": ["deepseek-coder", "gpt-4", "gpt-3.5-turbo"],
                    "reasoning": "코딩 특화 모델 또는 고급 프로그래밍 능력 필요"
                },
                "frontend_developer": {
                    "preferred_models": ["deepseek-coder", "gpt-3.5-turbo", "gemini-flash"],
                    "reasoning": "프론트엔드 개발에는 빠른 응답과 코딩 능력 필요"
                },
                "backend_developer": {
                    "preferred_models": ["deepseek-coder", "gpt-4", "gpt-3.5-turbo"],
                    "reasoning": "백엔드 개발에는 복잡한 로직 처리 능력 필요"
                },
                "data_scientist": {
                    "preferred_models": ["gpt-4", "gemini-pro", "claude-3"],
                    "reasoning": "데이터 분석과 통계적 추론 능력 필요"
                },
                "data_engineer": {
                    "preferred_models": ["deepseek-coder", "gpt-4", "gemini-pro"],
                    "reasoning": "데이터 파이프라인 구축에는 코딩과 아키텍처 능력 필요"
                },
                "content_strategist": {
                    "preferred_models": ["claude-3", "gpt-4", "gemini-pro"],
                    "reasoning": "콘텐츠 전략에는 창의성과 분석력 필요"
                },
                "content_creator": {
                    "preferred_models": ["claude-3", "gpt-4", "gemini-pro"],
                    "reasoning": "창의적 글쓰기에는 언어 생성 능력 필요"
                },
                "seo_specialist": {
                    "preferred_models": ["gpt-3.5-turbo", "gemini-flash", "claude-3"],
                    "reasoning": "SEO 최적화에는 빠른 분석과 마케팅 지식 필요"
                },
                "automation_specialist": {
                    "preferred_models": ["deepseek-coder", "gpt-3.5-turbo", "gemini-flash"],
                    "reasoning": "자동화 스크립트에는 코딩과 효율성 필요"
                },
                "web_scraper": {
                    "preferred_models": ["deepseek-coder", "gpt-3.5-turbo", "gemini-flash"],
                    "reasoning": "웹 스크래핑에는 코딩과 빠른 처리 필요"
                },
                "document_parser": {
                    "preferred_models": ["claude-3", "gpt-4", "gemini-pro"],
                    "reasoning": "문서 처리에는 구조 분석과 텍스트 이해 능력 필요"
                },
                "information_extractor": {
                    "preferred_models": ["gpt-4", "claude-3", "gemini-pro"],
                    "reasoning": "정보 추출에는 고급 자연어 처리 능력 필요"
                },
                "quality_assurance": {
                    "preferred_models": ["gpt-4", "claude-3", "gpt-3.5-turbo"],
                    "reasoning": "품질 검증에는 꼼꼼한 분석 능력 필요"
                }
            },

            "budget_constraints": {
                "default_budget": "medium",
                "cost_limits": {
                    "low": 100,
                    "medium": 500,
                    "high": 1000,
                    "unlimited": 999999
                },
                "cost_weights": {
                    "low": 1.0,
                    "medium": 3.0,
                    "high": 8.0
                }
            },

            "allocation_strategies": {
                "default": "balanced",
                "available_strategies": {
                    "cost_optimized": "비용 최적화 우선",
                    "performance_optimized": "성능 최적화 우선",
                    "balanced": "비용과 성능 균형",
                    "single_model": "단일 모델 사용"
                }
            },

            "fallback_settings": {
                "enable_fallback": True,
                "fallback_model": "gemini-flash",
                "max_retries": 3
            }
        }

        # 설정 파일 저장
        self._save_config(default_config)
        return default_config

    def _save_config(self, config: Dict):
        """설정 파일 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")

    def _validate_environment_keys(self) -> Dict:
        """환경변수 키 검증"""
        env_settings = self.model_config.get("environment_settings", {})
        required_keys = env_settings.get("required_env_keys", [])
        optional_keys = env_settings.get("optional_env_keys", [])

        available_keys = []
        missing_keys = []

        # 필수 환경변수 확인
        for key in required_keys:
            if os.getenv(key):
                available_keys.append(key)
            else:
                missing_keys.append(key)

        # 선택적 환경변수 확인
        for key in optional_keys:
            if os.getenv(key):
                available_keys.append(key)

        return {
            'available_keys': available_keys,
            'missing_keys': missing_keys,
            'total_required': len(required_keys),
            'available_required': len([k for k in required_keys if k in available_keys])
        }

    def get_litellm_model_name(self, simple_name: str) -> str:
        """간단한 모델명을 litellm 형식으로 변환"""
        if simple_name in self.model_specs:
            return self.model_specs[simple_name].litellm_name

        # 호환성을 위한 자동 변환 시도
        litellm_compat = self.model_config.get("litellm_compatibility", {})
        if litellm_compat.get("auto_convert_model_names", False):
            return self._auto_convert_model_name(simple_name)

        return simple_name

    def _auto_convert_model_name(self, model_name: str) -> str:
        """모델명 자동 변환"""
        # 기본 변환 규칙
        conversions = {
            "gpt-4": "openai/gpt-4",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
            "gemini-flash": "gemini/gemini-1.5-flash",
            "gemini-pro": "gemini/gemini-1.5-pro",
            "gemini-2.5-flash": "gemini/gemini-2.0-flash-exp",
            "gemini-2.5-pro": "gemini/gemini-2.0-flash-thinking-exp",
            "claude-3": "anthropic/claude-3-sonnet-20240229",
            "deepseek-coder": "deepseek/deepseek-coder"
        }

        return conversions.get(model_name, model_name)

    def check_model_availability(self, model_name: str) -> bool:
        """모델 사용 가능성 확인"""
        if model_name not in self.model_specs:
            return False

        spec = self.model_specs[model_name]
        if not spec.enabled:
            return False

        # 환경변수 확인
        env_key = spec.env_key
        return env_key in self.env_status['available_keys']

    def _parse_model_specs(self) -> Dict[str, ModelSpec]:
        """모델 사양 파싱"""
        specs = {}
        for model_name, config in self.model_config["model_pool"].items():
            specs[model_name] = ModelSpec(
                name=model_name,
                litellm_name=config.get("litellm_name", model_name),  # 기본값은 모델명 그대로
                cost_level=config["cost_level"],
                speed_level=config["speed_level"],
                strengths=config["strengths"],
                api_provider=config["api_provider"],
                env_key=config.get("env_key", f"{config['api_provider'].upper()}_API_KEY"),  # 기본값 생성
                enabled=config.get("enabled", True),
                backup_model=config.get("backup_model")
            )
        return specs

    def reload_config(self):
        """설정 파일 재로드 (핫 리로드)"""
        self.model_config = self._load_or_create_config()
        self.model_specs = self._parse_model_specs()
        print("모델 설정이 재로드되었습니다.")

    def allocate_models(self, agent_selection: AgentSelection,
                       analysis: RequirementAnalysis,
                       budget: str = "medium",
                       strategy: str = "balanced") -> ModelAllocation:
        """에이전트별 최적 모델 할당"""

        # 1. 예산 및 전략 설정
        budget_limit = self.model_config["budget_constraints"]["cost_limits"][budget]
        cost_weights = self.model_config["budget_constraints"]["cost_weights"]

        # 2. 에이전트별 모델 후보 선별
        agent_candidates = self._get_agent_model_candidates(agent_selection.agents)

        # 3. 할당 전략 적용
        allocation = self._apply_allocation_strategy(
            agent_candidates, analysis, budget_limit, cost_weights, strategy
        )

        # 4. 백업 모델 설정
        backup_allocations = self._assign_backup_models(allocation)

        # 5. 비용 계산 및 검증
        total_cost = self._calculate_total_cost(allocation, cost_weights)

        # 6. 할당 근거 생성
        reasoning = self._generate_allocation_reasoning(
            allocation, agent_selection.agents, strategy, total_cost, budget_limit
        )

        # 7. litellm 형식과 간단한 형식 매핑 생성
        simple_model_mapping = {}
        litellm_model_mapping = {}
        env_keys_required = set()

        for agent_name, model in allocation.items():
            simple_model_mapping[agent_name] = model
            litellm_model_mapping[agent_name] = self.get_litellm_model_name(model)

            # 필요한 환경변수 수집
            if model in self.model_specs:
                env_keys_required.add(self.model_specs[model].env_key)

        missing_env_keys = [key for key in env_keys_required if key not in self.env_status['available_keys']]

        return ModelAllocation(
            agent_model_mapping=litellm_model_mapping,
            simple_model_mapping=simple_model_mapping,
            total_estimated_cost=total_cost,
            allocation_reasoning=reasoning,
            confidence_score=self._calculate_allocation_confidence(allocation, agent_selection),
            backup_allocations=backup_allocations,
            env_keys_required=list(env_keys_required),
            missing_env_keys=missing_env_keys
        )

    def _get_agent_model_candidates(self, agents: List[AgentProfile]) -> Dict[str, List[str]]:
        """에이전트별 모델 후보 리스트 생성"""
        candidates = {}

        for agent in agents:
            agent_name = agent.name

            # 설정에서 선호 모델 가져오기
            if agent_name in self.model_config["agent_preferences"]:
                preferred = self.model_config["agent_preferences"][agent_name]["preferred_models"]
                # 활성화된 모델만 필터링
                candidates[agent_name] = [
                    model for model in preferred
                    if model in self.model_specs and self.model_specs[model].enabled
                ]
            else:
                # 기본 후보 모델 (모든 활성화된 모델)
                candidates[agent_name] = [
                    model for model, spec in self.model_specs.items()
                    if spec.enabled
                ]

            # 후보가 없으면 폴백 모델 추가
            if not candidates[agent_name]:
                fallback = self.model_config["fallback_settings"]["fallback_model"]
                if fallback in self.model_specs:
                    candidates[agent_name] = [fallback]

        return candidates

    def _apply_allocation_strategy(self, agent_candidates: Dict[str, List[str]],
                                 analysis: RequirementAnalysis,
                                 budget_limit: float,
                                 cost_weights: Dict[str, float],
                                 strategy: str) -> Dict[str, str]:
        """할당 전략 적용"""

        if strategy == "single_model":
            return self._single_model_allocation(agent_candidates, analysis)
        elif strategy == "cost_optimized":
            return self._cost_optimized_allocation(agent_candidates, budget_limit, cost_weights)
        elif strategy == "performance_optimized":
            return self._performance_optimized_allocation(agent_candidates, analysis)
        else:  # balanced
            return self._balanced_allocation(agent_candidates, analysis, budget_limit, cost_weights)

    def _single_model_allocation(self, agent_candidates: Dict[str, List[str]],
                                analysis: RequirementAnalysis) -> Dict[str, str]:
        """단일 모델 할당"""
        # 복잡도와 도메인 기반으로 최적 모델 선택
        if analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]:
            if analysis.domain in ['data_analysis', 'document_processing']:
                best_model = "gpt-4"
            else:
                best_model = "gpt-3.5-turbo"
        else:
            best_model = "gemini-flash"

        # 모델이 활성화되어 있는지 확인
        if best_model not in self.model_specs or not self.model_specs[best_model].enabled:
            # 활성화된 첫 번째 모델 사용
            for model, spec in self.model_specs.items():
                if spec.enabled:
                    best_model = model
                    break

        allocation = {}
        for agent_name in agent_candidates.keys():
            allocation[agent_name] = best_model

        return allocation

    def _cost_optimized_allocation(self, agent_candidates: Dict[str, List[str]],
                                  budget_limit: float, cost_weights: Dict[str, float]) -> Dict[str, str]:
        """비용 최적화 할당"""
        allocation = {}

        for agent_name, candidates in agent_candidates.items():
            # 비용이 가장 낮은 모델 선택
            best_model = None
            lowest_cost = float('inf')

            for model in candidates:
                if model in self.model_specs:
                    spec = self.model_specs[model]
                    cost = cost_weights.get(spec.cost_level, 1.0)
                    if cost < lowest_cost:
                        lowest_cost = cost
                        best_model = model

            allocation[agent_name] = best_model or candidates[0]

        return allocation

    def _performance_optimized_allocation(self, agent_candidates: Dict[str, List[str]],
                                        analysis: RequirementAnalysis) -> Dict[str, str]:
        """성능 최적화 할당"""
        allocation = {}

        for agent_name, candidates in agent_candidates.items():
            # 에이전트 역할에 따른 최고 성능 모델 선택
            best_model = None
            highest_score = -1

            for model in candidates:
                if model in self.model_specs:
                    score = self._calculate_performance_score(model, agent_name, analysis)
                    if score > highest_score:
                        highest_score = score
                        best_model = model

            allocation[agent_name] = best_model or candidates[0]

        return allocation

    def _balanced_allocation(self, agent_candidates: Dict[str, List[str]],
                           analysis: RequirementAnalysis,
                           budget_limit: float,
                           cost_weights: Dict[str, float]) -> Dict[str, str]:
        """균형 할당 (비용과 성능 균형)"""
        allocation = {}
        estimated_total_cost = 0

        # 중요도 기반 정렬 (더 중요한 에이전트부터 할당)
        agent_importance = self._calculate_agent_importance(agent_candidates.keys(), analysis)
        sorted_agents = sorted(agent_candidates.keys(),
                             key=lambda x: agent_importance.get(x, 0), reverse=True)

        for agent_name in sorted_agents:
            candidates = agent_candidates[agent_name]
            best_model = None
            best_score = -1

            for model in candidates:
                if model in self.model_specs:
                    spec = self.model_specs[model]

                    # 성능 점수
                    performance_score = self._calculate_performance_score(model, agent_name, analysis)

                    # 비용 점수 (낮을수록 좋음)
                    cost = cost_weights.get(spec.cost_level, 1.0)
                    cost_score = 1.0 / (cost + 0.1)

                    # 균형 점수 (성능 60%, 비용 40%)
                    balanced_score = performance_score * 0.6 + cost_score * 0.4

                    # 예산 초과 확인
                    projected_cost = estimated_total_cost + cost
                    if projected_cost <= budget_limit and balanced_score > best_score:
                        best_score = balanced_score
                        best_model = model

            # 선택된 모델이 없으면 가장 저렴한 모델 선택
            if not best_model and candidates:
                best_model = min(candidates,
                               key=lambda m: cost_weights.get(self.model_specs[m].cost_level, 1.0))

            allocation[agent_name] = best_model or "gemini-flash"

            # 비용 업데이트
            if best_model and best_model in self.model_specs:
                estimated_total_cost += cost_weights.get(self.model_specs[best_model].cost_level, 1.0)

        return allocation

    def _calculate_performance_score(self, model: str, agent_name: str, analysis: RequirementAnalysis) -> float:
        """모델별 성능 점수 계산"""
        if model not in self.model_specs:
            return 0.0

        spec = self.model_specs[model]
        score = 0.0

        # 기본 점수 (모델별)
        base_scores = {
            "gpt-4": 0.9,
            "claude-3": 0.8,
            "gemini-pro": 0.75,
            "gpt-3.5-turbo": 0.7,
            "deepseek-coder": 0.8,  # 코딩에 특화
            "gemini-flash": 0.6
        }
        score += base_scores.get(model, 0.5)

        # 에이전트 역할별 보정
        role_bonuses = {
            ("deepseek-coder", "implementation_engineer"): 0.2,
            ("deepseek-coder", "frontend_developer"): 0.2,
            ("deepseek-coder", "backend_developer"): 0.2,
            ("claude-3", "content_creator"): 0.15,
            ("claude-3", "content_strategist"): 0.15,
            ("claude-3", "document_parser"): 0.15,
            ("gpt-4", "requirements_analyst"): 0.15,
            ("gpt-4", "solution_architect"): 0.15,
            ("gpt-4", "data_scientist"): 0.15
        }

        bonus = role_bonuses.get((model, agent_name), 0.0)
        score += bonus

        # 복잡도별 보정
        if analysis.complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED]:
            if model in ["gpt-4", "claude-3"]:
                score += 0.1
        else:
            if model in ["gemini-flash", "gpt-3.5-turbo"]:
                score += 0.05

        return min(score, 1.0)

    def _calculate_agent_importance(self, agent_names: List[str], analysis: RequirementAnalysis) -> Dict[str, float]:
        """에이전트 중요도 계산"""
        importance = {}

        # 기본 중요도
        base_importance = {
            "requirements_analyst": 0.9,
            "solution_architect": 0.85,
            "implementation_engineer": 0.8,
            "data_scientist": 0.8,
            "content_creator": 0.75,
            "frontend_developer": 0.7,
            "backend_developer": 0.7,
            "technology_researcher": 0.65,
            "quality_assurance": 0.6
        }

        for agent_name in agent_names:
            importance[agent_name] = base_importance.get(agent_name, 0.5)

        # 도메인별 중요도 조정
        domain_adjustments = {
            'data_analysis': {
                'data_scientist': 0.2,
                'data_engineer': 0.15,
                'visualization_specialist': 0.1
            },
            'content_creation': {
                'content_strategist': 0.2,
                'content_creator': 0.15,
                'seo_specialist': 0.1
            },
            'web_development': {
                'frontend_developer': 0.15,
                'backend_developer': 0.15,
                'ui_ux_designer': 0.1
            }
        }

        if analysis.domain in domain_adjustments:
            for agent_name, bonus in domain_adjustments[analysis.domain].items():
                if agent_name in importance:
                    importance[agent_name] += bonus

        return importance

    def _assign_backup_models(self, allocation: Dict[str, str]) -> Dict[str, str]:
        """백업 모델 할당"""
        backup_allocations = {}

        for agent_name, model in allocation.items():
            if model in self.model_specs:
                backup = self.model_specs[model].backup_model
                if backup and backup in self.model_specs and self.model_specs[backup].enabled:
                    backup_allocations[agent_name] = backup
                else:
                    # 기본 폴백 모델
                    fallback = self.model_config["fallback_settings"]["fallback_model"]
                    if fallback != model and fallback in self.model_specs:
                        backup_allocations[agent_name] = fallback

        return backup_allocations

    def _calculate_total_cost(self, allocation: Dict[str, str], cost_weights: Dict[str, float]) -> float:
        """총 비용 계산"""
        total_cost = 0.0

        for agent_name, model in allocation.items():
            if model in self.model_specs:
                spec = self.model_specs[model]
                cost = cost_weights.get(spec.cost_level, 1.0)
                total_cost += cost

        return total_cost

    def _generate_allocation_reasoning(self, allocation: Dict[str, str],
                                     agents: List[AgentProfile],
                                     strategy: str, total_cost: float,
                                     budget_limit: float) -> str:
        """할당 근거 생성"""
        reasons = []

        # 전략 설명
        strategy_descriptions = {
            "cost_optimized": "비용 최적화 전략",
            "performance_optimized": "성능 최적화 전략",
            "balanced": "균형 전략 (비용/성능)",
            "single_model": "단일 모델 전략"
        }
        reasons.append(strategy_descriptions.get(strategy, "기본 전략"))

        # 모델 분포
        model_counts = {}
        for model in allocation.values():
            model_counts[model] = model_counts.get(model, 0) + 1

        model_distribution = ", ".join([f"{model}({count}개)" for model, count in model_counts.items()])
        reasons.append(f"모델 분포: {model_distribution}")

        # 예산 사용률
        budget_usage = (total_cost / budget_limit) * 100 if budget_limit > 0 else 0
        reasons.append(f"예산 사용률: {budget_usage:.1f}%")

        # 특화 할당
        specialized_allocations = []
        coding_agents = ["implementation_engineer", "frontend_developer", "backend_developer"]
        creative_agents = ["content_creator", "content_strategist"]

        for agent_name, model in allocation.items():
            if agent_name in coding_agents and model == "deepseek-coder":
                specialized_allocations.append("코딩 특화")
            elif agent_name in creative_agents and model == "claude-3":
                specialized_allocations.append("창작 특화")

        if specialized_allocations:
            reasons.append(f"특화 할당: {', '.join(set(specialized_allocations))}")

        return " | ".join(reasons)

    def _calculate_allocation_confidence(self, allocation: Dict[str, str],
                                       agent_selection: AgentSelection) -> float:
        """할당 신뢰도 계산"""
        confidence = 0.0
        total_agents = len(allocation)

        if total_agents == 0:
            return 0.0

        # 선호 모델 매칭률
        preference_matches = 0
        for agent_name, assigned_model in allocation.items():
            if agent_name in self.model_config["agent_preferences"]:
                preferred = self.model_config["agent_preferences"][agent_name]["preferred_models"]
                if assigned_model in preferred:
                    preference_matches += 1

        preference_score = preference_matches / total_agents

        # 모델 가용성 점수
        availability_score = 1.0  # 모든 할당된 모델이 활성화되어 있다고 가정

        # 예산 적합성 (예산 내에서 할당되었는지)
        budget_score = 1.0  # 할당 과정에서 예산을 고려했으므로

        confidence = (preference_score * 0.5 + availability_score * 0.3 + budget_score * 0.2)

        return min(confidence, 1.0)

    def update_model_config(self, updates: Dict):
        """모델 설정 업데이트"""
        # 깊은 병합
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(self.model_config, updates)
        self._save_config(self.model_config)
        self.reload_config()

    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        return [name for name, spec in self.model_specs.items() if spec.enabled]

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """모델 정보 조회"""
        if model_name in self.model_config["model_pool"]:
            return self.model_config["model_pool"][model_name]
        return None

def main():
    """테스트 함수"""
    from intelligent_requirement_analyzer import IntelligentRequirementAnalyzer
    from dynamic_agent_matcher import DynamicAgentMatcher

    # 시스템 초기화
    analyzer = IntelligentRequirementAnalyzer()
    matcher = DynamicAgentMatcher()
    allocator = SmartModelAllocator("model_config.json")

    # 테스트 요구사항
    test_req = "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘"

    # 분석 및 매칭
    analysis = analyzer.analyze_requirement(test_req)
    agent_selection = matcher.select_optimal_agents(analysis)

    print(f"=== 모델 할당 테스트 ===")
    print(f"요구사항: {test_req}")
    print(f"선택된 에이전트: {[agent.name for agent in agent_selection.agents]}")

    # 다양한 전략으로 모델 할당 테스트
    strategies = ["balanced", "cost_optimized", "performance_optimized", "single_model"]

    for strategy in strategies:
        print(f"\n--- {strategy} 전략 ---")
        allocation = allocator.allocate_models(agent_selection, analysis, budget="medium", strategy=strategy)

        print(f"모델 할당:")
        for agent_name, model in allocation.agent_model_mapping.items():
            print(f"  {agent_name}: {model}")

        print(f"총 예상 비용: {allocation.total_estimated_cost:.1f}")
        print(f"할당 근거: {allocation.allocation_reasoning}")
        print(f"신뢰도: {allocation.confidence_score:.2f}")

    # 설정 파일 정보
    print(f"\n사용 가능한 모델: {allocator.get_available_models()}")
    print(f"설정 파일 위치: {allocator.config_path}")

if __name__ == "__main__":
    main()