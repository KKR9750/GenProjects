# -*- coding: utf-8 -*-
"""
사전 분석 서비스 (Pre-Analysis Service)
사용자 요청을 분석하여 구조화된 역할 분담 및 작업 계획을 생성
"""

import os
import json
import uuid
from datetime import datetime
import requests
from typing import Dict, List, Optional, Tuple
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreAnalysisService:
    """사전 분석 서비스 - LLM을 통한 구조화된 프로젝트 계획 생성"""

    def __init__(self):
        """초기화 - LLM API 설정"""
        self.supported_models = {
            'gemini-pro': {
                'api_key_env': 'GOOGLE_API_KEY',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent',
                'max_tokens': 8192
            },
            'gemini-flash': {
                'api_key_env': 'GOOGLE_API_KEY',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
                'max_tokens': 8192
            },
            'gemini-2.0-flash': {
                'api_key_env': 'GOOGLE_API_KEY',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent',
                'max_tokens': 8192
            },
            'gemini-2.5-flash': {
                'api_key_env': 'GOOGLE_API_KEY',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
                'max_tokens': 8192
            },
            'gemini-2.5-pro': {
                'api_key_env': 'GOOGLE_API_KEY',
                'endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent',
                'max_tokens': 8192
            },
            'gpt-4': {
                'api_key_env': 'OPENAI_API_KEY',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 4096
            },
            # Ollama Local Models (no API key required)
            'ollama-gemma2-2b': {
                'api_key_env': 'OLLAMA_BASE_URL',
                'endpoint': 'http://localhost:11434/api/generate',
                'max_tokens': 2048,
                'is_local': True
            },
            'ollama-deepseek-coder-6.7b': {
                'api_key_env': 'OLLAMA_BASE_URL',
                'endpoint': 'http://localhost:11434/api/generate',
                'max_tokens': 4096,
                'is_local': True
            },
            'ollama-llama3.1': {
                'api_key_env': 'OLLAMA_BASE_URL',
                'endpoint': 'http://localhost:11434/api/generate',
                'max_tokens': 4096,
                'is_local': True
            },
            'ollama-qwen3-coder-30b': {
                'api_key_env': 'OLLAMA_BASE_URL',
                'endpoint': 'http://localhost:11434/api/generate',
                'max_tokens': 8192,
                'is_local': True
            }
        }

        # 기본 모델 설정
        self.default_model = 'gemini-2.5-flash'

        # CrewAI 모델명 매핑 (실제 지원 모델로 변환)
        self.crewai_model_mapping = {
            'gemini-flash': 'gemini-flash',           # 기본 flash → 2.5-flash 엔드포인트 사용
            'gemini-pro': 'gemini-pro',              # 기본 pro → 2.5-pro 엔드포인트 사용
            'gemini-2.5-flash': 'gemini-2.5-flash',  # 2.5 flash
            'gemini-2.5-pro': 'gemini-2.5-pro',      # 2.5 pro
            'gemini-2.0-flash': 'gemini-2.0-flash',  # 2.0 flash
            'gpt-4': 'gpt-4',                        # OpenAI 모델
            'gpt-4o': 'gpt-4',                       # GPT-4o는 gpt-4로 매핑
            'claude-3-sonnet': 'gemini-2.5-flash',   # 지원하지 않는 모델은 최신 flash로
            'claude-3-haiku': 'gemini-2.5-flash',    # 지원하지 않는 모델은 최신 flash로
            # Ollama Local Models - use fallback for pre-analysis
            'ollama-gemma2-2b': 'gemini-2.5-flash',
            'ollama-deepseek-coder-6.7b': 'gemini-2.5-flash',
            'ollama-llama3.1': 'gemini-2.5-flash',
            'ollama-qwen3-coder-30b': 'gemini-2.5-flash'
        }

    def analyze_user_request(self,
                           user_request: str,
                           framework: str = 'crewai',
                           model: str = None) -> Dict:
        """
        사용자 요청을 분석하여 구조화된 프로젝트 계획 생성

        Args:
            user_request: 사용자의 원본 요청
            framework: 사용할 AI 프레임워크 ('crewai' 또는 'metagpt')
            model: 사용할 LLM 모델 (기본값: gemini-flash)

        Returns:
            Dict: 구조화된 프로젝트 계획
        """
        try:
            analysis_id = str(uuid.uuid4())
            model = model or self.default_model

            # CrewAI 모델명을 사전 분석용으로 변환
            actual_model = self.crewai_model_mapping.get(model, model)

            logger.info(f"사전 분석 시작: {analysis_id}, 프레임워크: {framework}, 요청 모델: {model}, 실제 모델: {actual_model}")

            # 프레임워크별 분석 프롬프트 생성
            system_prompt = self._create_analysis_prompt(framework)

            # API 키 확인
            has_api_key = bool(os.getenv('GOOGLE_API_KEY')) or bool(os.getenv('OPENAI_API_KEY'))

            if not has_api_key:
                error_msg = "LLM API 키가 설정되지 않았습니다. GOOGLE_API_KEY 또는 OPENAI_API_KEY 환경변수를 설정하세요."
                logger.error(error_msg)
                raise ValueError(error_msg)

            # LLM 호출
            analysis_result = self._call_llm(
                system_prompt=system_prompt,
                user_request=user_request,
                model=actual_model  # 변환된 모델명 사용
            )

            # 결과 구조화
            structured_analysis = self._structure_analysis_result(
                analysis_result,
                framework,
                user_request,
                analysis_id
            )

            logger.info(f"사전 분석 완료: {analysis_id}")
            return structured_analysis

        except Exception as e:
            logger.error(f"사전 분석 실패: {str(e)}")
            return self._create_error_response(str(e))

    def _create_analysis_prompt(self, framework: str) -> str:
        """프레임워크별 분석 프롬프트 생성"""

        base_prompt = """
        당신은 AI 프로젝트 분석 전문가입니다. 사용자의 요청을 분석하여 체계적이고 구조화된 프로젝트 계획을 생성해주세요.

        분석 결과는 다음 JSON 구조로 응답해주세요:
        {
            "project_summary": "프로젝트 한 줄 요약",
            "objectives": ["목표1", "목표2", "목표3"],
            "constraints": ["제약사항1", "제약사항2"],
            "success_criteria": ["성공기준1", "성공기준2"],
            "agents": [
                {
                    "role": "역할명",
                    "responsibilities": ["책임사항1", "책임사항2"],
                    "deliverables": ["산출물1", "산출물2"],
                    "expertise": "전문분야"
                }
            ],
            "workflow": [
                {
                    "step": 1,
                    "title": "단계명",
                    "description": "단계 설명",
                    "agent": "담당 역할",
                    "estimated_time": "예상 시간",
                    "dependencies": ["의존성1"]
                }
            ],
            "resources_needed": ["필요 리소스1", "필요 리소스2"],
            "potential_risks": ["위험요소1", "위험요소2"],
            "quality_gates": ["품질 체크포인트1", "품질 체크포인트2"]
        }
        """

        if framework == 'crewai':
            framework_specific = """
            CrewAI 프레임워크 특화 지침:
            - 3개의 핵심 역할 (Researcher, Writer, Planner)을 기반으로 역할 분담
            - 각 에이전트는 명확한 전문성과 책임을 가져야 함
            - 협업적 워크플로우 중심으로 단계 구성
            - Researcher: 정보 수집 및 분석
            - Writer: 콘텐츠 생성 및 문서화
            - Planner: 전략 수립 및 계획 관리
            """
        else:  # metagpt
            framework_specific = """
            MetaGPT 프레임워크 특화 지침:
            - 5단계 소프트웨어 개발 프로세스 적용
            - PM (Product Manager) → Architect → PM → Engineer → QA 순서
            - 각 단계별 명확한 산출물 정의
            - 기술적 구현에 중점을 둔 워크플로우
            - 코드 생성 및 품질 보증 과정 포함
            """

        return base_prompt + "\n" + framework_specific

    def _call_llm(self, system_prompt: str, user_request: str, model: str) -> str:
        """LLM API 호출"""

        if model not in self.supported_models:
            raise ValueError(f"지원하지 않는 모델: {model}")

        model_config = self.supported_models[model]
        api_key = os.getenv(model_config['api_key_env'])

        if not api_key:
            raise ValueError(f"API 키가 설정되지 않음: {model_config['api_key_env']}")

        try:
            if model.startswith('gemini'):
                response = self._call_gemini(
                    system_prompt, user_request, model_config, api_key
                )
            elif model.startswith('gpt'):
                response = self._call_openai(
                    system_prompt, user_request, model_config, api_key
                )
            else:
                raise ValueError(f"구현되지 않은 모델: {model}")

            return response

        except Exception as e:
            logger.error(f"LLM 호출 실패: {str(e)}")
            raise

    def _call_gemini(self, system_prompt: str, user_request: str,
                     model_config: Dict, api_key: str) -> str:
        """Google Gemini API 호출 (재시도 로직 포함)"""

        url = f"{model_config['endpoint']}?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\n사용자 요청:\n{user_request}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": model_config['max_tokens'],
                "temperature": 0.7
            }
        }

        headers = {
            "Content-Type": "application/json"
        }

        # 재시도 로직 (최대 3번)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                timeout = 60 if attempt == 0 else 90  # 첫 시도는 60초, 재시도는 90초
                logger.info(f"Gemini API 호출 시도 {attempt + 1}/{max_retries}, 타임아웃: {timeout}초")

                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
                response.raise_for_status()

                result = response.json()

                if 'candidates' in result and len(result['candidates']) > 0:
                    logger.info("Gemini API 호출 성공")
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    raise ValueError("Gemini API 응답에서 텍스트를 찾을 수 없습니다")

            except requests.exceptions.Timeout as e:
                logger.warning(f"Gemini API 타임아웃 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:  # 마지막 시도
                    raise Exception(f"Gemini API 타임아웃: {max_retries}번 시도 모두 실패")
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Gemini API 요청 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:  # 마지막 시도
                    raise
                continue

    def _call_openai(self, system_prompt: str, user_request: str,
                     model_config: Dict, api_key: str) -> str:
        """OpenAI GPT API 호출"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            "max_tokens": model_config['max_tokens'],
            "temperature": 0.7
        }

        response = requests.post(
            model_config['endpoint'],
            json=payload,
            headers=headers,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def _structure_analysis_result(self, analysis_result: str, framework: str,
                                  user_request: str, analysis_id: str) -> Dict:
        """분석 결과를 구조화"""

        try:
            # Gemini가 ```json으로 감싸서 응답하는 경우 처리
            cleaned_result = analysis_result.strip()

            # 빈 응답 처리
            if not cleaned_result:
                logger.error("LLM 응답이 비어있음")
                raise ValueError("LLM에서 빈 응답을 받았습니다")

            # ```json 마커 제거
            if cleaned_result.startswith('```json'):
                # ```json과 마지막 ``` 제거
                cleaned_result = cleaned_result[7:]  # ```json 제거
                if cleaned_result.endswith('```'):
                    cleaned_result = cleaned_result[:-3]  # ``` 제거
                cleaned_result = cleaned_result.strip()

            # 다시 빈 문자열인지 확인
            if not cleaned_result:
                logger.error("JSON 마커 제거 후 비어있음")
                raise ValueError("JSON 마커 제거 후 내용이 비어있습니다")

            # JSON 파싱 시도
            parsed_result = json.loads(cleaned_result)

            # 메타데이터 추가
            structured_result = {
                "analysis_id": analysis_id,
                "timestamp": datetime.now().isoformat(),
                "framework": framework,
                "original_request": user_request,
                "status": "completed",
                "analysis": parsed_result
            }

            return structured_result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 파싱 실패, 텍스트로 처리: {str(e)}")

            # JSON 파싱 실패 시 텍스트로 처리
            return {
                "analysis_id": analysis_id,
                "timestamp": datetime.now().isoformat(),
                "framework": framework,
                "original_request": user_request,
                "status": "completed",
                "analysis": {
                    "raw_text": analysis_result,
                    "project_summary": "분석 결과 파싱 필요",
                    "note": "LLM 응답을 수동으로 구조화해야 합니다."
                }
            }

    def _create_error_response(self, error_message: str) -> Dict:
        """에러 응답 생성"""

        return {
            "analysis_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "error": error_message,
            "analysis": None
        }


    def get_analysis_templates(self) -> Dict[str, Dict]:
        """분석 템플릿 반환"""

        return {
            "crewai": {
                "name": "CrewAI 3역할 협업",
                "description": "Researcher, Writer, Planner 3개 역할의 협업 프로젝트",
                "typical_roles": ["Researcher", "Writer", "Planner"],
                "workflow_pattern": "정보수집 → 콘텐츠생성 → 전략수립"
            },
            "metagpt": {
                "name": "MetaGPT 5단계 개발",
                "description": "PM → Architect → PM → Engineer → QA 순차 개발",
                "typical_roles": ["Product Manager", "Architect", "Engineer", "QA Engineer"],
                "workflow_pattern": "기획 → 설계 → 재기획 → 개발 → 테스트"
            }
        }

    def validate_analysis_result(self, analysis: Dict) -> Tuple[bool, List[str]]:
        """분석 결과 유효성 검증"""

        errors = []

        if not analysis.get('analysis'):
            errors.append("분석 결과가 없습니다")
            return False, errors

        analysis_data = analysis['analysis']

        # 필수 필드 검증
        required_fields = [
            'project_summary', 'objectives', 'agents', 'workflow'
        ]

        for field in required_fields:
            if field not in analysis_data:
                errors.append(f"필수 필드 누락: {field}")

        # 에이전트 구조 검증
        if 'agents' in analysis_data:
            agents = analysis_data['agents']
            if not isinstance(agents, list) or len(agents) == 0:
                errors.append("최소 1개의 에이전트가 필요합니다")

            for i, agent in enumerate(agents):
                if not isinstance(agent, dict):
                    errors.append(f"에이전트 {i}: 딕셔너리 형태여야 합니다")
                elif 'role' not in agent:
                    errors.append(f"에이전트 {i}: 역할(role)이 필요합니다")

        # 워크플로우 구조 검증
        if 'workflow' in analysis_data:
            workflow = analysis_data['workflow']
            if not isinstance(workflow, list) or len(workflow) == 0:
                errors.append("최소 1개의 워크플로우 단계가 필요합니다")

            for i, step in enumerate(workflow):
                if not isinstance(step, dict):
                    errors.append(f"워크플로우 단계 {i}: 딕셔너리 형태여야 합니다")
                elif 'title' not in step:
                    errors.append(f"워크플로우 단계 {i}: 제목(title)이 필요합니다")

        return len(errors) == 0, errors


# 사전 분석 서비스 인스턴스 생성
pre_analysis_service = PreAnalysisService()


# 유틸리티 함수들
def create_analysis_from_template(framework: str, project_type: str) -> Dict:
    """템플릿 기반 분석 생성"""

    templates = {
        'crewai': {
            'web_app': {
                'project_summary': '웹 애플리케이션 개발 프로젝트',
                'objectives': ['사용자 친화적 웹 인터페이스 개발', '안정적인 백엔드 구축', '반응형 디자인 구현'],
                'agents': [
                    {
                        'role': 'Researcher',
                        'responsibilities': ['시장 조사', '기술 스택 분석', '사용자 요구사항 조사'],
                        'deliverables': ['시장 분석 보고서', '기술 스택 추천서'],
                        'expertise': '시장 분석 및 기술 조사'
                    },
                    {
                        'role': 'Writer',
                        'responsibilities': ['UI/UX 콘텐츠 작성', '사용자 매뉴얼 작성', '기술 문서화'],
                        'deliverables': ['사용자 인터페이스 콘텐츠', '기술 문서'],
                        'expertise': '콘텐츠 작성 및 문서화'
                    },
                    {
                        'role': 'Planner',
                        'responsibilities': ['프로젝트 일정 관리', '리소스 할당', '품질 관리'],
                        'deliverables': ['프로젝트 계획서', '일정 관리표'],
                        'expertise': '프로젝트 관리 및 전략 기획'
                    }
                ]
            }
        }
    }

    template = templates.get(framework, {}).get(project_type)
    if not template:
        return None

    return {
        'analysis_id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'framework': framework,
        'status': 'template',
        'analysis': template
    }


if __name__ == "__main__":
    # 테스트 코드
    service = PreAnalysisService()

    test_request = "온라인 쇼핑몰을 만들고 싶어요. 상품 카탈로그, 장바구니, 결제 기능이 필요합니다."

    result = service.analyze_user_request(
        user_request=test_request,
        framework="crewai",
        model="gemini-flash"
    )

    print("분석 결과:")
    print(json.dumps(result, indent=2, ensure_ascii=False))