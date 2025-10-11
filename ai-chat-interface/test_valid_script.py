#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""정상 스크립트 테스트"""

from crewai import Agent, Task, Crew

# 간단한 에이전트
agent = Agent(
    role="Tester",
    goal="Test the validation system",
    backstory="A test agent"
)

# 간단한 태스크
task = Task(
    description="Test task",
    expected_output="Test output",
    agent=agent
)

# 크루 생성
crew = Crew(
    agents=[agent],
    tasks=[task]
)

print("테스트 스크립트 로드 완료")