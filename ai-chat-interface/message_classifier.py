#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메시지 분류 시스템
- 요구사항과 시스템 메시지 구분
- 프로젝트 재개 명령 식별
- 승인/거부 신호 파싱
"""

import re
from typing import Dict, Any, Optional, Tuple
from enum import Enum

class MessageType(Enum):
    """메시지 타입 열거형"""
    REQUIREMENT = "requirement"  # 실제 요구사항
    SYSTEM_CONFIRMATION = "system_confirmation"  # 시스템 확인 메시지
    PROJECT_RESUME = "project_resume"  # 프로젝트 재개 요청
    APPROVAL_DECISION = "approval_decision"  # 승인/거부 결정
    UNKNOWN = "unknown"  # 분류 불가

class MessageClassifier:
    """메시지 분류기"""

    def __init__(self):
        # 시스템 확인 메시지 패턴
        self.confirmation_patterns = [
            r"계속\s*작업하시겠습니까\?",
            r"진행하시겠습니까\?",
            r"계속\s*진행할까요\?",
            r"이어서\s*계속하시겠습니까\?",
            r"작업을\s*계속하시겠습니까\?",
        ]

        # 단순 확인 답변 패턴
        self.simple_confirmations = [
            r"^\s*네\s*$",
            r"^\s*예\s*$",
            r"^\s*yes\s*$",
            r"^\s*y\s*$",
            r"^\s*확인\s*$",
            r"^\s*ok\s*$",
            r"^\s*좋아요?\s*$",
        ]

        # 거부 답변 패턴
        self.rejection_patterns = [
            r"^\s*아니[오]?\s*$",
            r"^\s*no\s*$",
            r"^\s*n\s*$",
            r"^\s*취소\s*$",
            r"^\s*중단\s*$",
            r"^\s*그만\s*$",
        ]

        # 프로젝트 재개 패턴
        self.resume_patterns = [
            r"이어서\s*계속",
            r"재개해?줘",
            r"계속\s*진행",
            r"중단된\s*작업\s*계속",
            r"resume",
            r"continue",
            r"이전\s*작업\s*계속",
        ]

        # 승인 관련 패턴
        self.approval_patterns = [
            r"승인",
            r"approve",
            r"거부",
            r"reject",
            r"수정\s*요청",
            r"modify",
            r"다시\s*해줘",
        ]

        # 실제 요구사항을 나타내는 패턴 (최소 길이 및 복잡성 기준)
        self.requirement_indicators = [
            r".+[을를]\s*.+해줘",
            r".+[을를]\s*.+만들어줘",
            r".+프로그램\s*생성",
            r".+시스템\s*구축",
            r".+개발해줘",
            r".+구현해줘",
            r".+만들어주세요",
            r".+해주세요",
            r".+생성해줘",
            r".+작성해줘",
        ]

    def classify_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        메시지를 분류하여 타입과 추가 정보 반환

        Args:
            message: 분류할 메시지
            context: 컨텍스트 정보 (프로젝트 상태 등)

        Returns:
            분류 결과 딕셔너리
        """
        if not message or not message.strip():
            return {
                'type': MessageType.UNKNOWN,
                'confidence': 0.0,
                'reason': '빈 메시지',
                'original_message': message
            }

        message_clean = message.strip()

        # 1. 단순 확인 답변 확인
        if self._matches_patterns(message_clean, self.simple_confirmations):
            return self._create_result(
                MessageType.SYSTEM_CONFIRMATION,
                0.9,
                '단순 확인 답변',
                message,
                {'confirmation_type': 'simple_yes'}
            )

        # 2. 거부 답변 확인
        if self._matches_patterns(message_clean, self.rejection_patterns):
            return self._create_result(
                MessageType.SYSTEM_CONFIRMATION,
                0.9,
                '거부 답변',
                message,
                {'confirmation_type': 'rejection'}
            )

        # 3. 승인 관련 메시지 확인
        if self._matches_patterns(message_clean, self.approval_patterns):
            return self._create_result(
                MessageType.APPROVAL_DECISION,
                0.8,
                '승인/거부 관련 메시지',
                message,
                {'decision_context': self._extract_approval_context(message_clean)}
            )

        # 4. 프로젝트 재개 요청 확인
        if self._matches_patterns(message_clean, self.resume_patterns):
            return self._create_result(
                MessageType.PROJECT_RESUME,
                0.8,
                '프로젝트 재개 요청',
                message,
                {'resume_context': self._extract_resume_context(message_clean)}
            )

        # 5. 실제 요구사항 확인
        if self._is_requirement_message(message_clean):
            return self._create_result(
                MessageType.REQUIREMENT,
                0.7,
                '실제 요구사항으로 판단',
                message,
                {'requirement_analysis': self._analyze_requirement(message_clean)}
            )

        # 6. 컨텍스트 기반 분류
        if context:
            context_result = self._classify_with_context(message_clean, context)
            if context_result:
                return context_result

        # 7. 분류 실패
        return self._create_result(
            MessageType.UNKNOWN,
            0.1,
            '분류할 수 없는 메시지',
            message,
            {'suggestion': '더 구체적인 요청이나 명확한 답변을 부탁드립니다.'}
        )

    def _matches_patterns(self, message: str, patterns: list) -> bool:
        """패턴 리스트 중 하나라도 매치되는지 확인"""
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False

    def _is_requirement_message(self, message: str) -> bool:
        """실제 요구사항인지 판단"""
        # 최소 길이 체크
        if len(message) < 10:
            return False

        # 요구사항 패턴 매치
        if self._matches_patterns(message, self.requirement_indicators):
            return True

        # 복잡성 기준 (단어 수, 구체성)
        words = message.split()
        if len(words) >= 5:
            # 기술적 용어나 구체적 요청사항 포함 여부
            technical_terms = ['프로그램', '시스템', '앱', '웹사이트', '데이터베이스',
                             '인터페이스', 'API', '서버', '클라이언트', '알고리즘',
                             '분석', '처리', '변환', '관리', '자동화', '통합']

            if any(term in message for term in technical_terms):
                return True

        return False

    def _extract_approval_context(self, message: str) -> Dict[str, Any]:
        """승인 관련 컨텍스트 추출"""
        context = {
            'decision': None,
            'feedback': None
        }

        if re.search(r'승인|approve', message, re.IGNORECASE):
            context['decision'] = 'approved'
        elif re.search(r'거부|reject', message, re.IGNORECASE):
            context['decision'] = 'rejected'
        elif re.search(r'수정|modify', message, re.IGNORECASE):
            context['decision'] = 'modify_requested'

        return context

    def _extract_resume_context(self, message: str) -> Dict[str, Any]:
        """재개 관련 컨텍스트 추출"""
        context = {
            'resume_type': 'general',
            'specific_project': None
        }

        # 특정 프로젝트 언급 확인
        project_match = re.search(r'프로젝트[_\s]*(\w+)', message)
        if project_match:
            context['specific_project'] = project_match.group(1)
            context['resume_type'] = 'specific_project'

        return context

    def _analyze_requirement(self, message: str) -> Dict[str, Any]:
        """요구사항 분석"""
        analysis = {
            'complexity': 'medium',
            'domain': 'general',
            'action_type': 'create',
            'keywords': []
        }

        # 복잡성 판단
        if len(message) > 100:
            analysis['complexity'] = 'high'
        elif len(message) < 30:
            analysis['complexity'] = 'low'

        # 액션 타입 판단
        if re.search(r'생성|만들|개발|구현', message):
            analysis['action_type'] = 'create'
        elif re.search(r'수정|변경|개선', message):
            analysis['action_type'] = 'modify'
        elif re.search(r'분석|조사|확인', message):
            analysis['action_type'] = 'analyze'

        # 도메인 판단
        domains = {
            'web': ['웹', '웹사이트', 'web', 'html', 'css', 'javascript'],
            'mobile': ['모바일', '앱', 'app', 'android', 'ios'],
            'data': ['데이터', '분석', '처리', '변환', '통계'],
            'ai': ['AI', '인공지능', '머신러닝', '딥러닝', 'ML', 'DL'],
            'system': ['시스템', '서버', 'API', '데이터베이스']
        }

        for domain, keywords in domains.items():
            if any(keyword in message for keyword in keywords):
                analysis['domain'] = domain
                analysis['keywords'].extend([kw for kw in keywords if kw in message])
                break

        return analysis

    def _classify_with_context(self, message: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """컨텍스트를 고려한 분류"""
        project_status = context.get('project_status')
        last_system_message = context.get('last_system_message', '')

        # 이전에 확인 메시지가 있었고, 단순한 답변인 경우
        if (last_system_message and
            re.search(r'계속.*하시겠습니까|진행.*하시겠습니까', last_system_message) and
            len(message) < 5):

            return self._create_result(
                MessageType.SYSTEM_CONFIRMATION,
                0.8,
                '시스템 확인 메시지에 대한 응답',
                message,
                {'context_based': True, 'last_system_message': last_system_message}
            )

        # 프로젝트가 승인 대기 상태인 경우
        if (project_status == 'planner_approval_pending' and
            len(message) < 20):

            return self._create_result(
                MessageType.APPROVAL_DECISION,
                0.7,
                '승인 대기 상태에서의 응답',
                message,
                {'project_status': project_status}
            )

        return None

    def _create_result(self, msg_type: MessageType, confidence: float,
                      reason: str, original: str, extra: Dict[str, Any] = None) -> Dict[str, Any]:
        """분류 결과 생성"""
        result = {
            'type': msg_type,
            'confidence': confidence,
            'reason': reason,
            'original_message': original,
            'timestamp': None  # 호출하는 곳에서 설정
        }

        if extra:
            result.update(extra)

        return result

    def extract_original_requirement(self, messages: list) -> Optional[str]:
        """메시지 리스트에서 원본 요구사항 추출"""
        for message in reversed(messages):  # 최신 메시지부터 역순으로 확인
            if isinstance(message, dict):
                msg_text = message.get('content', message.get('message', ''))
            else:
                msg_text = str(message)

            classification = self.classify_message(msg_text)

            if classification['type'] == MessageType.REQUIREMENT:
                return msg_text

        return None

    def is_continuation_request(self, message: str, context: Dict[str, Any] = None) -> bool:
        """연속 작업 요청인지 판단"""
        classification = self.classify_message(message, context)
        return classification['type'] in [
            MessageType.SYSTEM_CONFIRMATION,
            MessageType.PROJECT_RESUME,
            MessageType.APPROVAL_DECISION
        ]

# 사용 예시
def test_classifier():
    """분류기 테스트"""
    classifier = MessageClassifier()

    test_messages = [
        "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘.",
        "네",
        "계속 작업하시겠습니까?에 답변을 한거고",
        "승인합니다",
        "이어서 계속 진행해주세요",
        "거부합니다. 계획을 다시 수정해주세요.",
        "project_00023 재개해줘",
    ]

    print("🔍 메시지 분류 테스트:")
    print("=" * 60)

    for msg in test_messages:
        result = classifier.classify_message(msg)
        print(f"메시지: '{msg}'")
        print(f"분류: {result['type'].value}")
        print(f"신뢰도: {result['confidence']:.2f}")
        print(f"이유: {result['reason']}")
        print("-" * 40)

if __name__ == "__main__":
    test_classifier()