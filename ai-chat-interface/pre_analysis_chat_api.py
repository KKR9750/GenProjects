"""
Pre-analysis Chat API
사용자와 LLM 간의 대화를 통해 요구사항을 명확히 하는 API
"""
from flask import Blueprint, request, jsonify
import os
from typing import List, Dict
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    ChatAnthropic = None
from langchain.schema import HumanMessage, AIMessage, SystemMessage

pre_analysis_bp = Blueprint('pre_analysis', __name__)

class PreAnalysisService:
    """사전분석 서비스"""

    def __init__(self):
        self.system_prompt = """당신은 소프트웨어 프로젝트 요구사항을 분석하는 전문가입니다.

사용자의 요구사항을 듣고, 다음 항목들을 명확히 하기 위해 질문하세요:

1. **프로젝트 목적**: 무엇을 만들고 싶은가?
2. **핵심 기능**: 반드시 필요한 기능은 무엇인가?
3. **대상 사용자**: 누가 사용할 것인가?
4. **기술 스택**: 선호하는 기술이 있는가?
5. **제약사항**: 시간, 예산, 기술적 제약은?

사용자의 답변을 듣고, 모호한 부분이 있으면 추가 질문을 하세요.
요구사항이 충분히 명확해지면, 최종 요구사항을 정리하여 제시하고 확정 여부를 물어보세요.

**응답 형식**:
- 질문이 필요한 경우: 명확하고 구체적인 질문
- 요구사항 정리가 가능한 경우: "다음과 같이 요구사항을 정리했습니다:" 로 시작하는 요약
"""

    def get_llm(self, model_name: str):
        """모델명에 따라 LLM 반환"""
        if model_name.startswith('gpt'):
            return ChatOpenAI(
                model=model_name,
                temperature=0.7,
                api_key=os.getenv('OPENAI_API_KEY')
            )
        elif model_name.startswith('gemini'):
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.7,
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )
        elif model_name.startswith('claude'):
            if ANTHROPIC_AVAILABLE:
                return ChatAnthropic(
                    model=model_name,
                    temperature=0.7,
                    anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')
                )
            else:
                # Claude 사용 불가능한 경우 Gemini로 폴백
                print(f"Warning: Claude model requested but langchain_anthropic not available. Falling back to Gemini.")
                return ChatGoogleGenerativeAI(
                    model='gemini-2.0-flash-exp',
                    temperature=0.7,
                    google_api_key=os.getenv('GOOGLE_API_KEY')
                )
        else:
            # 기본값
            return ChatGoogleGenerativeAI(
                model='gemini-2.0-flash-exp',
                temperature=0.7,
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )

    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict],
        model: str = 'gemini-2.0-flash-exp'
    ) -> Dict:
        """
        사전분석 대화 처리

        Args:
            user_message: 사용자 메시지
            conversation_history: 이전 대화 이력
            model: 사용할 LLM 모델

        Returns:
            {
                'analysis': AI 응답,
                'canFinalize': 요구사항 확정 가능 여부,
                'suggestedRequirement': 제안된 최종 요구사항 (canFinalize=True인 경우)
            }
        """
        llm = self.get_llm(model)

        # 메시지 구성
        messages = [SystemMessage(content=self.system_prompt)]

        # 대화 이력 추가
        for msg in conversation_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))

        # 현재 사용자 메시지 추가
        messages.append(HumanMessage(content=user_message))

        # LLM 호출
        response = llm.invoke(messages)
        ai_message = response.content

        # 요구사항 확정 가능 여부 판단
        can_finalize = self._can_finalize(ai_message)
        suggested_requirement = None

        if can_finalize:
            suggested_requirement = self._extract_requirement(ai_message)

        return {
            'analysis': ai_message,
            'canFinalize': can_finalize,
            'suggestedRequirement': suggested_requirement
        }


    @staticmethod
    def _ensure_statement(text: str) -> str:
        if not text:
            return ''
        normalized = re.sub(r'\*+', '', text).strip()
        if not normalized:
            return ''
        normalized = re.sub(r'\s+', ' ', normalized)
        if normalized[-1] in '.?!…':
            return normalized
        return normalized + '.'

    @classmethod
    def _normalize_requirement_sentences(cls, lines: List[str]) -> List[str]:
        cleaned = []
        for raw in lines:
            if not raw:
                continue
            stripped = re.sub(r'^[-•·\d\.\)\s]+', '', raw)
            stripped = re.sub(r'\*+', '', stripped).strip()
            stripped = stripped.lstrip('📌✅❓').strip()
            if not stripped:
                continue
            statement = cls._ensure_statement(stripped)
            if statement:
                cleaned.append(statement)
        return cleaned

    @staticmethod
    def _split_items(text: str) -> List[str]:
        if not text:
            return []
        normalized = (text.replace(' - ', '|')
                        .replace('- ', '|')
                        .replace('•', '|')
                        .replace('·', '|'))
        parts = []
        for part in normalized.split('|'):
            cleaned = part.strip(' -•·')
            if cleaned:
                parts.append(cleaned)
        return parts

    @classmethod
    def _structure_requirement_sections(cls, lines: List[str]) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {}
        current_header = None
        for raw in lines:
            plain = re.sub(r'\*+', '', raw).strip()
            header_match = re.match(r'([^:]+):(.*)', plain)
            if header_match:
                header = header_match.group(1).strip()
                body = header_match.group(2).strip()
                current_header = header
                if body:
                    sections.setdefault(header, []).extend(cls._split_items(body))
            else:
                if current_header:
                    sections.setdefault(current_header, []).extend(cls._split_items(plain))
                else:
                    sections.setdefault('기타', []).append(plain)
        return sections


    def _can_finalize(self, ai_message: str) -> bool:
        """AI 응답에서 요구사항 확정 가능 여부 판단"""
        finalize_keywords = [
            '최종 요구사항을 정리했습니다',
            '다음과 같이 요구사항을 정리했습니다',
            '요구사항 정리',
            '최종 요구사항',
            '이상으로 정리',
            '확인해 주실 수 있을까요',
            '검토해 주실 수 있을까요'
        ]
        return any(keyword in ai_message for keyword in finalize_keywords)


    def _extract_requirement(self, ai_message: str) -> str:
        """AI 응답에서 최종 요구사항 추출"""
        lines = ai_message.splitlines()
        requirement_lines = []
        capture = False

        trigger_phrases = [
            '최종 요구사항을 정리했습니다',
            '최종 요구사항을 정리했어요',
            '최종 요구사항을 정리하겠습니다',
            '다음과 같이 요구사항을 정리했습니다'
        ]

        for line in lines:
            if any(phrase in line for phrase in trigger_phrases):
                capture = True
                continue
            if capture:
                stripped = line.strip()
                if stripped and not stripped.startswith('확인'):
                    requirement_lines.append(stripped)

        cleaned_lines = self._normalize_requirement_sentences(requirement_lines)
        sections = self._structure_requirement_sections(cleaned_lines) if cleaned_lines else {}

        summary_candidates = sections.get('프로젝트 목적') or sections.get('요약') or []
        summary = summary_candidates[0] if summary_candidates else (cleaned_lines[0] if cleaned_lines else '')

        detail_headers = ['핵심 기능', '대상 사용자', '기술 스택', '기술', '제약 사항', '비고', '추가 정보']
        detail_items = []
        for header in detail_headers:
            for item in sections.get(header, []):
                detail_items.append(f"{header}: {item}")

        miscellaneous = [
            item
            for key, values in sections.items()
            if key not in detail_headers + ['프로젝트 목적', '요약', '확정 여부']
            for item in (f"{key}: {value}" for value in values)
        ]
        detail_items.extend(miscellaneous)

        questions = sections.get('확정 여부', [])

        result_lines: List[str] = []
        if summary:
            result_lines.append('📌 프로젝트 요약')
            result_lines.append(f"- {summary}")

        if detail_items:
            result_lines.append('')
            result_lines.append('✅ 주요 요구사항')
            result_lines.extend(f"- {item}" for item in detail_items)

        if questions:
            result_lines.append('')
            result_lines.append('❓ 확인 요청')
            result_lines.extend(f"- {question}" for question in questions)

        if result_lines:
            return '\n'.join(result_lines)

        fallback_lines = self._normalize_requirement_sentences([ai_message])
        if fallback_lines:
            return '\n'.join(fallback_lines)
        return ai_message





# Flask 라우트
@pre_analysis_bp.route('/api/pre-analysis/chat', methods=['POST'])
def pre_analysis_chat():
    """
    사전분석 대화 API

    Request Body:
    {
        "userMessage": "전자상거래 웹사이트를 만들고 싶어요",
        "conversationHistory": [
            {"role": "assistant", "content": "어떤 프로젝트를 만들고 싶으신가요?"},
            {"role": "user", "content": "쇼핑몰을 만들고 싶어요"}
        ],
        "model": "gemini-2.0-flash-exp"
    }

    Response:
    {
        "analysis": "AI의 응답",
        "canFinalize": true/false,
        "suggestedRequirement": "정리된 최종 요구사항" (canFinalize=true인 경우)
    }
    """
    try:
        data = request.get_json()

        user_message = data.get('userMessage')
        conversation_history = data.get('conversationHistory', [])
        model = data.get('model', 'gemini-2.0-flash-exp')

        if not user_message:
            return jsonify({'error': 'User message is required'}), 400

        # 사전분석 서비스 실행
        service = PreAnalysisService()
        result = service.chat(
            user_message=user_message,
            conversation_history=conversation_history,
            model=model
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@pre_analysis_bp.route('/api/pre-analysis/initial', methods=['POST'])
def get_initial_question():
    """
    사전분석 초기 질문 생성

    Request Body:
    {
        "framework": "crewai" | "metagpt",
        "model": "gemini-2.0-flash-exp"
    }

    Response:
    {
        "initialQuestion": "초기 질문"
    }
    """
    try:
        data = request.get_json()
        framework = data.get('framework', 'crewai')
        model = data.get('model', 'gemini-2.0-flash-exp')

        # 프레임워크별 초기 질문
        if framework == 'crewai':
            initial_question = """안녕하세요! CrewAI 프로젝트 생성을 시작합니다.

CrewAI는 여러 AI 에이전트가 협업하여 복잡한 작업을 수행하는 프레임워크입니다.

어떤 프로젝트를 만들고 싶으신가요?
예를 들어:
- 데이터 분석 및 리포트 생성
- 콘텐츠 제작 및 편집
- 연구 및 정보 수집
- 기타 창의적인 작업

구체적으로 설명해주세요."""

        elif framework == 'metagpt':
            initial_question = """안녕하세요! MetaGPT 프로젝트 생성을 시작합니다.

MetaGPT는 소프트웨어 개발 전 과정(기획, 설계, 구현, 테스트)을 자동화하는 프레임워크입니다.

어떤 소프트웨어를 개발하고 싶으신가요?
예를 들어:
- 웹 애플리케이션
- 모바일 앱
- API 서버
- 데이터 처리 시스템
- 머신러닝 프로젝트

구체적으로 설명해주세요."""

        else:
            initial_question = "어떤 프로젝트를 만들고 싶으신가요?"

        return jsonify({'initialQuestion': initial_question}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
