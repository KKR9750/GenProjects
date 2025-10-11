from project_initialization_api import _apply_role_specific_definition

final_req = "📌 프로젝트 요약\n- 매일 아침 8시에 구글 뉴스 주요 뉴스를 요약해 보고합니다.\n\n✅ 주요 요구사항\n- 핵심 기능: 구글 뉴스에서 최신 뉴스 10개 수집 및 요약\n- 제약 사항: 매일 8시 정각 보고, 개인 PC 또는 서버리스 환경 고려\n- 대상 사용자: 사용자 본인 (1명)\n- 기술 스택: 선호 스택 없음\n\n❓ 확인 요청\n- 위 요구사항이 맞습니까?\n- 선호 기술 스택이 있으신가요?"

for role in ['Planner', 'Researcher', 'Writer']:
    goal, backstory = _apply_role_specific_definition(role, final_req, '', '')
    print(role)
    print(goal)
    print(backstory)
    print('---')
