#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트명 자동 생성기
요구사항에서 핵심 키워드를 추출하여 의미있는 프로젝트명 생성
"""

import re
import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import json


def generate_project_name_from_requirement(requirement: str, max_length: int = 50) -> str:
    """
    요구사항에서 LLM을 사용하여 의미있는 프로젝트명 생성

    Args:
        requirement: 최종 요구사항 텍스트
        max_length: 프로젝트명 최대 길이

    Returns:
        생성된 프로젝트명
    """
    try:
        # LLM 사용하여 프로젝트명 생성
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[WARN] No API key found, using fallback method")
            return _generate_name_by_keywords(requirement, max_length)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            timeout=30,
            max_retries=2
        )

        prompt = f"""당신은 프로젝트명을 생성하는 전문가입니다.
주어진 요구사항에서 핵심 내용을 파악하여 간결하고 명확한 프로젝트명을 한국어로 생성해주세요.

**요구사항:**
{requirement[:500]}

**프로젝트명 생성 규칙:**
1. 핵심 기능이나 목적을 명확히 표현
2. 15자 이내의 간결한 이름
3. 특수문자 사용 금지 (한글, 영문, 숫자, 공백, 하이픈만 가능)
4. "프로젝트", "시스템" 같은 일반적인 단어 지양
5. 구체적이고 의미있는 이름 사용

**출력 형식 (JSON):**
{{
    "project_name": "생성된 프로젝트명"
}}

**예시:**
- 요구사항: "매일 아침 뉴스 요약" → 프로젝트명: "아침 뉴스 요약 봇"
- 요구사항: "주식 가격 추적" → 프로젝트명: "주식 모니터링"
- 요구사항: "할일 관리 앱" → 프로젝트명: "스마트 할일 매니저"
"""

        response = llm.invoke(prompt)
        result = json.loads(response.content)
        project_name = result.get("project_name", "").strip()

        if not project_name:
            print("[WARN] LLM returned empty name, using fallback")
            return _generate_name_by_keywords(requirement, max_length)

        # 길이 제한
        if len(project_name) > max_length:
            project_name = project_name[:max_length].strip()

        # 유효성 검사
        if not _is_valid_project_name(project_name):
            print(f"[WARN] Invalid project name: {project_name}, using fallback")
            return _generate_name_by_keywords(requirement, max_length)

        print(f"[OK] Generated project name: {project_name}")
        return project_name

    except Exception as e:
        print(f"[ERROR] Failed to generate project name with LLM: {e}")
        return _generate_name_by_keywords(requirement, max_length)


def _generate_name_by_keywords(requirement: str, max_length: int = 50) -> str:
    """
    키워드 기반 프로젝트명 생성 (폴백 방법)

    Args:
        requirement: 요구사항 텍스트
        max_length: 최대 길이

    Returns:
        생성된 프로젝트명
    """
    # 키워드 추출
    keywords = _extract_keywords(requirement)

    if not keywords:
        return "자동화 프로젝트"

    # 상위 2-3개 키워드로 이름 생성
    selected_keywords = keywords[:3]
    project_name = " ".join(selected_keywords)

    # 길이 제한
    if len(project_name) > max_length:
        project_name = " ".join(selected_keywords[:2])

    if len(project_name) > max_length:
        project_name = selected_keywords[0]

    return project_name


def _extract_keywords(text: str) -> list:
    """
    텍스트에서 핵심 키워드 추출

    Args:
        text: 입력 텍스트

    Returns:
        추출된 키워드 리스트
    """
    # 불용어 (제거할 일반적인 단어들)
    stop_words = {
        '프로젝트', '시스템', '서비스', '플랫폼', '애플리케이션', '앱',
        '목적', '기능', '사항', '요약', '정리', '다음', '같이', '위해',
        '사용자', '경우', '예', '등', '및', '또는', '그리고', '하는',
        '있는', '없는', '되는', '되어', '입니다', '습니다', '합니다'
    }

    # 숫자와 특수문자 제거, 공백으로 분리
    words = re.findall(r'[가-힣a-zA-Z]+', text)

    # 빈도수 계산 (불용어 제외, 2글자 이상)
    word_freq = {}
    for word in words:
        if len(word) >= 2 and word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 빈도수 기준 정렬
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    # 상위 키워드 반환
    keywords = [word for word, freq in sorted_words[:5]]

    return keywords


def _is_valid_project_name(name: str) -> bool:
    """
    프로젝트명 유효성 검사

    Args:
        name: 검사할 프로젝트명

    Returns:
        유효하면 True
    """
    if not name or len(name) < 2:
        return False

    # 허용: 한글, 영문, 숫자, 공백, 하이픈, 언더스코어
    if not re.match(r'^[가-힣a-zA-Z0-9\s\-_]+$', name):
        return False

    return True


# 테스트
if __name__ == "__main__":
    test_requirements = [
        "매일 아침 8시에 구글 뉴스에서 주요 뉴스를 요약하여 사용자에게 보고",
        "주식 가격을 실시간으로 추적하고 특정 조건 만족 시 알림",
        "할일 관리 및 일정 추적 웹 애플리케이션",
        "고객 문의 자동 응답 챗봇 시스템"
    ]

    print("=== 프로젝트명 생성 테스트 ===\n")

    for req in test_requirements:
        name = generate_project_name_from_requirement(req)
        print(f"요구사항: {req[:50]}...")
        print(f"생성된 이름: {name}\n")
