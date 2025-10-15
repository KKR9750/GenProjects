# -*- coding: utf-8 -*-
"""
Message Classifier - Centralized Logic for User Input Analysis
사용자 입력 분석을 위한 중앙 집중식 로직
"""

import random

def is_project_request(text: str) -> bool:
    """프로젝트 요청인지 판단하는 중앙 함수"""
    text_lower = text.lower()
    project_keywords = [
        '만들어', '개발해', '작성해', '구현해', '생성해', '코딩해',
        '프로그램', '앱', '웹사이트', '게임', '시스템', 'api',
        '계산기', '웹앱', '서버', '데이터베이스', '블로그',
        'python', 'javascript', 'react', 'node', 'flask', 'django'
    ]
    casual_keywords = [
        '안녕', '하이', '헬로', '고마워', '감사', '괜찮', '좋아',
        '어떻게', '뭐야', '그래', '맞아', '네', '응', '아니'
    ]
    for keyword in casual_keywords:
        if keyword in text_lower and len(text) < 20:
            return False
    for keyword in project_keywords:
        if keyword in text_lower:
            return True
    if len(text) > 15 and ('해줘' in text or '만들' in text or '작성' in text):
        return True
    return False

def handle_casual_chat(message: str) -> str:
    """일반 대화를 처리하는 중앙 함수"""
    message_lower = message.lower()
    if any(word in message_lower for word in ['누구', '이름', '뭐', '무엇']):
        return random.choice([
            "안녕하세요! 저는 AI 프로젝트 생성 플랫폼입니다. 🤖\n\n어떤 프로그램을 만들어드릴까요?",
            "AI 프로젝트 생성 플랫폼입니다! 📱\n\nCrewAI나 MetaGPT를 사용해서 원하는 프로그램을 만들어보세요."
        ])
    if any(word in message_lower for word in ['안녕', '하이', '헬로']):
        return random.choice([
            "안녕하세요! 반갑습니다 😊\n\n어떤걸 만들어볼까요?",
            "안녕하세요! 좋은 하루네요 ✨\n\n무엇을 개발해드릴까요?"
        ])
    return random.choice([
        "네, 말씀하세요! 어떤 프로그램을 만들어보고 싶으신가요? 🤔",
        "흥미롭네요! 더 구체적으로 말씀해주시면 도와드릴게요 ✨",
        "좋은 생각이에요! 어떤 기술을 사용해서 만들어볼까요? 💡"
    ])