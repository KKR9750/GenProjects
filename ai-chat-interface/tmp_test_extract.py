from pre_analysis_chat_api import PreAnalysisService

message = "다음과 같이 요구사항을 정리했습니다:\n**프로젝트 목적**: - 매일 아침 8시에 구글 뉴스에서 주요 뉴스를 요약하여 사용자에게 보고\n**핵심 기능**: - 구글 뉴스에서 최신 뉴스 10개를 가져와 요약 - 경제, 정치, 사회, IT, 주식 관련 뉴스 필터링 - 매일 아침 8시에 사용자에게 요약된 뉴스 보고\n**대상 사용자**: - 사용자 본인 (1명)\n**기술 스택**: - (미정) - 사용자가 선호하는 기술 스택이 없는 것으로 파악됨.\n**제약 사항**: - 시간: 매일 아침 8시 정시에 보고해야 함 - 사용자가 1명이라는 점을 고려하여, 서버리스 환경 또는 개인용 PC에서 실행 가능한 솔루션 고려\n**확정 여부**: - 위 요구사항이 맞습니까? - 기술 스택에 대한 선호도가 있으신가요? (예: Python, Node.js 등)"
service = PreAnalysisService()
result = service._extract_requirement(message)
print(result.encode('utf-8'))
