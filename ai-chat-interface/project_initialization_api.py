"""
프로젝트 초기화 API
사전분석 완료 후 확정된 요구사항으로 Agent/Task를 DB에 생성
"""
from flask import Blueprint, request, jsonify
from database import get_supabase_client
from typing import Dict, List, Tuple
import json
from datetime import datetime, timedelta
import os
import re
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from project_name_generator import generate_project_name_from_requirement

project_init_bp = Blueprint('project_init', __name__)

def get_llm(model_name="gemini-2.0-flash-exp"):
    """LLM 인스턴스를 생성하는 헬퍼 함수"""
    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        timeout=90,  # 90초 타임아웃
        max_retries=2  # 최대 2번 재시도
    )

def refine_agent_definition(agent_template: dict, requirement: str) -> dict:
    """LLM을 사용하여 Agent의 Goal과 Backstory를 정제합니다."""
    try:
        llm = get_llm()
        prompt = f"""당신은 AI 프로젝트의 역할을 명확하게 정의하는 시스템 설계 전문가입니다.
주어진 기본 Agent 역할과 프로젝트 전체 요구사항을 바탕으로, 해당 Agent만을 위한 간결하고 명확한 'Goal'과 'Backstory'를 한국어로 재작성해주세요.

**프로젝트 전체 요구사항:**
{requirement}

**기본 Agent 정보:**
- 역할(Role): {agent_template['role']}
- 기본 목표(Goal) 템플릿: {agent_template['goal_template']}
- 기본 배경(Backstory) 템플릿: {agent_template['backstory_template']}

**출력 형식 (JSON):**
{{
    "refined_goal": "해당 Agent에게 특화된, 간결하게 정제된 목표",
    "refined_backstory": "해당 Agent의 전문성을 강조하는, 간결하게 정제된 배경 설명"
}}"""
        response = llm.invoke(prompt)
        refined_data = json.loads(response.content)
        return {
            "goal": refined_data.get("refined_goal"),
            "backstory": refined_data.get("refined_backstory")
        }
    except Exception as e:
        print(f"Agent 정의 정제 실패 (폴백 실행): {e}")
        return {
            "goal": agent_template['goal_template'].format(requirement=requirement),
            "backstory": agent_template['backstory_template'].format(requirement=requirement)
        }

def refine_task_definition(task_template: dict, requirement: str, all_agents: List[Dict]) -> dict:
    """LLM을 사용하여 Task의 Description과 Expected Output을 정제합니다."""
    try:
        llm = get_llm()

        # 담당 Agent 정보 찾기
        assigned_agent_order = task_template.get('assigned_agent_order')
        assigned_agent_role = "담당자 미지정"
        if assigned_agent_order is not None:
            for agent in all_agents:
                if agent['agent_order'] == assigned_agent_order:
                    assigned_agent_role = agent['role']
                    break

        prompt = f"""당신은 AI 프로젝트의 Task를 명확하게 정의하는 시스템 설계 전문가입니다.
주어진 기본 Task 설명과 프로젝트 전체 요구사항, 그리고 이 Task를 수행할 Agent의 역할을 바탕으로, 간결하고 명확한 'Description'과 'Expected Output'을 한국어로 재작성해주세요.

**프로젝트 전체 요구사항:**
{requirement}

**이 Task를 수행할 Agent의 역할:**
{assigned_agent_role}

**기본 Task 정보:**
- Task 유형(Type): {task_template['task_type']}
- 기본 설명(Description) 템플릿: {task_template['description_template']}
- 기본 기대 결과물(Expected Output) 템플릿: {task_template['expected_output_template']}

**출력 형식 (JSON):**
{{
    "refined_description": "해당 Task에 특화된, 간결하게 정제된 작업 설명",
    "refined_expected_output": "해당 Task가 완료되었을 때 나와야 하는, 구체적이고 명확한 기대 결과물"
}}"""
        response = llm.invoke(prompt)
        refined_data = json.loads(response.content)
        return {
            "description": refined_data.get("refined_description"),
            "expected_output": refined_data.get("refined_expected_output")
        }
    except Exception as e:
        print(f"Task 정의 정제 실패 (폴백 실행): {e}")
        return {
            "description": task_template['description_template'].format(requirement=requirement),
            "expected_output": task_template['expected_output_template'].format(requirement=requirement)
        }



def _ensure_sentence(value: str) -> str:
    if not value:
        return ''
    trimmed = value.strip()
    if not trimmed:
        return ''
    if trimmed[-1] in '.?!…':
        return trimmed
    return trimmed + '.'



def _sanitize_agent_text(value: str) -> str:
    if not value:
        return ''
    cleaned = value.replace('다음과 같이 요구사항을 정리했습니다.', '')
    cleaned = cleaned.replace('다음과 같이 요구사항을 정리했습니다', '')
    cleaned = re.sub(r'프로젝트 목적\s*:\s*', '', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip()

def _truncate_text(value: str, limit: int = 140) -> str:
    if not value:
        return ''
    trimmed = value.strip()
    if len(trimmed) <= limit:
        return trimmed
    return trimmed[:limit - 3].rstrip() + '...'


def _extract_requirement_summary_points(requirement: str) -> Tuple[str, List[str]]:
    if not requirement:
        return '', []

    normalized_lines: List[str] = []
    for raw_line in requirement.splitlines():
        cleaned = re.sub(r'^[\-\*\d\.\)\s]+', '', raw_line)
        cleaned = re.sub(r'\*+', '', cleaned).strip()
        if not cleaned:
            continue
        normalized_lines.append(cleaned)

    summary = ''
    details: List[str] = []
    section = None

    for line in normalized_lines:
        if line.startswith('📌'):
            section = 'summary'
            continue
        if line.startswith('✅'):
            section = 'details'
            continue
        if line.startswith('❓'):
            section = 'questions'
            continue

        content = line.lstrip('- ').strip()
        if not content:
            continue

        if section == 'summary' and not summary:
            summary = content
            continue

        if section == 'details':
            details.append(content)
            continue

        if section is None:
            if not summary:
                summary = content
            else:
                details.append(content)

    if not summary:
        summary = details[0] if details else requirement.strip()

    summary = _truncate_text(summary)
    cleaned_details: List[str] = []
    for item in details:
        cleaned_item = _truncate_text(item)
        if cleaned_item:
            cleaned_details.append(cleaned_item)
        if len(cleaned_details) >= 4:
            break

    return summary, cleaned_details



def _fill_template_text(template_value: str, requirement: str) -> str:
    if not template_value:
        return ''
    try:
        return template_value.format(requirement=requirement)
    except Exception:
        return template_value.replace('{requirement}', requirement)


def _coalesce_text(*values: str) -> str:
    for value in values:
        if value:
            trimmed = value.strip()
            if trimmed:
                return trimmed
    return ''


def _generate_fallback_definitions(final_requirement: str, templates: List[Dict]) -> Dict[str, Dict[str, str]]:
    """폴백: 템플릿을 그대로 사용하여 Agent 정의 생성"""
    print("[agent-role-definition] Using fallback definitions")
    definitions: Dict[str, Dict[str, str]] = {}

    for template in templates:
        role = (template.get('role') or '').strip()
        if not role:
            continue

        # 템플릿에서 goal과 backstory 가져오기
        goal_template = template.get('goal_template') or template.get('default_goal') or ''
        backstory_template = template.get('backstory_template') or template.get('default_backstory') or ''

        # {requirement} 플레이스홀더 치환
        goal = goal_template.format(requirement=final_requirement) if goal_template else f"{role}의 목표를 달성합니다."
        backstory = backstory_template.format(requirement=final_requirement) if backstory_template else f"{role}는 전문가입니다."

        definitions[role.lower()] = {
            'goal': _sanitize_agent_text(_ensure_sentence(goal)),
            'backstory': _sanitize_agent_text(_ensure_sentence(backstory))
        }

    return definitions


def _apply_role_specific_definition(role: str, final_requirement: str, goal: str, backstory: str) -> Tuple[str, str]:
    normalized_role = (role or '').strip().lower()
    summary, points = _extract_requirement_summary_points(final_requirement or '')
    reference = _truncate_text(summary or final_requirement or '', 140).rstrip('.!?… ')
    base_goal = _coalesce_text(goal)
    base_backstory = _coalesce_text(backstory)

    if not normalized_role:
        return base_goal, base_backstory

    def detail_fragment(prefix: str) -> str:
        if not points:
            return ''
        filtered = [p for p in points if not p.lower().startswith('프로젝트 목적')][:2]
        fragment = '; '.join(filtered)
        if not fragment:
            return ''
        return _ensure_sentence(f"{prefix}: {fragment}")

    if '요구' in normalized_role or 'requirement' in normalized_role:
        detail = '; '.join(points[:3]) if points else ''
        narrative_parts = ["고객과 합의한 최종 요구사항을 공유하는 기준 문서입니다."]
        if reference:
            narrative_parts.append(f"핵심 목표는 {reference}입니다.")
        if detail:
            narrative_parts.append(_ensure_sentence(f"세부 항목: {detail}"))
        new_goal = _coalesce_text(base_goal, "확정된 요구사항을 팀 전체에 전달하고 기준선을 유지합니다.")
        return _sanitize_agent_text(new_goal), _sanitize_agent_text(_coalesce_text(' '.join(narrative_parts), base_backstory))

    if 'planner' in normalized_role:
        goal_candidate = f"{reference} 프로젝트의 전체 설계 및 품질 관리" if reference else ''
        new_goal = _coalesce_text(goal_candidate, base_goal)
        narrative_parts = [
            "당신은 프로젝트 일정과 품질을 총괄하는 시니어 플래너입니다."
        ]
        if reference:
            narrative_parts.append(f"{reference} 목표를 기준으로 단계별 전략을 세우고 팀 간 협업을 조율합니다.")
        else:
            narrative_parts.append("최종 요구사항을 기준으로 단계별 전략을 세우고 팀 간 협업을 조율합니다.")
        requirement_detail = detail_fragment("주요 요구사항")
        if requirement_detail:
            narrative_parts.append(requirement_detail)
        return _sanitize_agent_text(new_goal), _sanitize_agent_text(_coalesce_text(' '.join(narrative_parts), base_backstory))

    if 'researcher' in normalized_role:
        goal_candidate = f"{reference} 달성을 위한 근거 자료 수집" if reference else ''
        new_goal = _coalesce_text(goal_candidate, base_goal)
        narrative_parts = [
            "당신은 최신 트렌드와 신뢰도 높은 데이터를 발굴하는 리서치 전문가입니다."
        ]
        if reference:
            narrative_parts.append(f"{reference} 구현에 필요한 통계와 사례를 재빨리 모읍니다.")
        else:
            narrative_parts.append("요구사항 구현에 필요한 통계와 사례를 재빨리 모읍니다.")
        narrative_parts.append("Planner와 Writer가 활용할 수 있도록 핵심 근거와 출처를 정리합니다.")
        focus_detail = detail_fragment("조사 초점")
        if focus_detail:
            narrative_parts.append(focus_detail)
        return _sanitize_agent_text(new_goal), _sanitize_agent_text(_coalesce_text(' '.join(narrative_parts), base_backstory))

    if 'writer' in normalized_role:
        goal_candidate = f"{reference}에 맞는 산출물 작성 및 구조화" if reference else ''
        new_goal = _coalesce_text(goal_candidate, base_goal)
        narrative_parts = [
            "당신은 명확하고 재사용 가능한 문서와 결과물을 작성하는 시니어 라이터입니다."
        ]
        if reference:
            narrative_parts.append(f"{reference} 목표를 이해하기 쉬운 산출물로 다듬고,")
        else:
            narrative_parts.append("요구사항을 이해하기 쉬운 산출물로 다듬고,")
        narrative_parts.append("Planner의 품질 기준과 Researcher가 전달한 근거를 반영해 구조화된 결과물을 제공합니다.")
        emphasis_detail = detail_fragment("작성 시 강조할 세부 요구사항")
        if emphasis_detail:
            narrative_parts.append(emphasis_detail)
        return _sanitize_agent_text(new_goal), _sanitize_agent_text(_coalesce_text(' '.join(narrative_parts), base_backstory))

    if 'notifier' in normalized_role or 'communicator' in normalized_role or '알림' in normalized_role:
        info_fragment = '; '.join(points[:2]) if points else reference
        new_goal = _coalesce_text("산출물을 이해관계자에게 전달하고 피드백을 수집합니다.", base_goal)
        narrative_parts = ["당신은 프로젝트 결과를 이해관계자에게 전달하고 피드백을 수집하는 커뮤니케이션 담당자입니다."]
        if info_fragment:
            narrative_parts.append(_ensure_sentence(f"전달 핵심 메시지: {info_fragment}"))
        return _sanitize_agent_text(new_goal), _sanitize_agent_text(_coalesce_text(' '.join(narrative_parts), base_backstory))

    return base_goal, base_backstory




def generate_agent_role_definitions(final_requirement: str, templates: List[Dict]) -> Dict[str, Dict[str, str]]:
    """Use LLM to craft goal/backstory per role based on final requirement."""
    if not final_requirement or not templates:
        print("[agent-role-definition] ERROR: Missing requirement or templates")
        return _generate_fallback_definitions(final_requirement, templates)

    try:
        llm = get_llm()
    except Exception as exc:
        print(f"[agent-role-definition] LLM unavailable: {exc}")
        return _generate_fallback_definitions(final_requirement, templates)

    template_brief = []
    for template in templates:
        role = (template.get('role') or '').strip()
        if not role:
            continue
        template_brief.append({
            'role': role,
            'default_goal': template.get('goal_template') or template.get('goal'),
            'default_backstory': template.get('backstory_template') or template.get('backstory'),
            'notes': template.get('description') or template.get('template_name')
        })

    if not template_brief:
        return {}


    prompt = ''
    content = None
    try:
        prompt = """당신은 CrewAI 프로젝트에서 에이전트 역할을 설계하는 시니어 아키텍트입니다.
아래 확정 요구사항을 토대로 각 에이전트의 Goal과 Backstory를 한국어로 명확하게 정의하세요.
항상 역할별로 서로 겹치지 않는 책임과 어조를 유지하고, 불릿이나 질문형 문장을 사용하지 마세요.

[확정 요구사항]
{requirement}

[기본 에이전트 템플릿]
{templates}

출력 형식(JSON):
{{
  "agents": [
    {{"role": "Planner", "goal": "...", "backstory": "..."}},
    ...
  ]
}}

제약 조건:
- Goal은 1~3문장, Backstory는 2~5문장으로 작성하세요.
- 마크다운, 불릿, 인용부호 등을 넣지 마세요.
- 각 문장은 완결형 진술문으로 끝내세요.
- 역할명은 입력된 role 값과 동일하게 유지하세요.
- 반드시 순수 JSON만 출력하세요. ```json 같은 마크다운 코드 블록을 사용하지 마세요.""".format(
            requirement=final_requirement.strip(),
            templates=json.dumps(template_brief, ensure_ascii=False, indent=2)
        )
        print("[agent-role-definition] prompt:", prompt)
        response = llm.invoke(prompt)

        # 응답 내용 추출
        if hasattr(response, 'content'):
            content = response.content
        elif isinstance(response, dict) and 'content' in response:
            content = response['content']
        else:
            content = str(response)

        print("[agent-role-definition] raw response:", content)

        # 빈 응답 체크
        if not content or not content.strip():
            print("[agent-role-definition] ERROR: Empty response from LLM")
            return {}

        # JSON 마커 제거 (```json...``` 형태)
        cleaned_content = content.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
        elif cleaned_content.startswith('```'):
            cleaned_content = cleaned_content[3:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()

        # JSON 파싱
        data = json.loads(cleaned_content)
        agents = data.get('agents', []) if isinstance(data, dict) else []

        if not agents:
            print("[agent-role-definition] ERROR: No agents in response")
            print("[agent-role-definition] Falling back to template-based definitions")
            return _generate_fallback_definitions(final_requirement, templates)

    except json.JSONDecodeError as exc:
        print(f"[agent-role-definition] JSON decode failed: {exc}")
        print(f"[agent-role-definition] unparsable content: {content}")
        print("[agent-role-definition] Falling back to template-based definitions")
        return _generate_fallback_definitions(final_requirement, templates)
    except Exception as exc:
        print(f"[agent-role-definition] LLM call failed: {exc}")
        print(f"[agent-role-definition] failure response: {content}")
        print("[agent-role-definition] Falling back to template-based definitions")
        return _generate_fallback_definitions(final_requirement, templates)

    definitions: Dict[str, Dict[str, str]] = {}
    for agent in agents:
        role = (agent.get('role') or '').strip()
        if not role:
            continue
        definitions[role.lower()] = {
            'goal': agent.get('goal', '').strip(),
            'backstory': agent.get('backstory', '').strip()
        }
    return definitions



class ProjectInitializer:
    """프로젝트 초기화 로직"""

    def __init__(self):
        pass

    def initialize_project(
        self,
        project_id: str,
        framework: str,
        final_requirement: str,
        pre_analysis_history: List[Dict] = None
    ) -> Dict:
        """
        프로젝트 초기화: Agent/Task를 템플릿에서 복사하여 생성

        Args:
            project_id: 프로젝트 ID
            framework: 'crewai' 또는 'metagpt'
            final_requirement: 확정된 최종 요구사항
            pre_analysis_history: 사전분석 대화 이력 (선택)

        Returns:
            생성된 Agent/Task 정보
        """
        try:
            supabase = get_supabase_client()

            # 1. projects 테이블 UPDATE (이미 create_project에서 생성된 프로젝트 업데이트)
            # final_requirement와 pre_analysis_history만 추가
            # 요구사항 기반 프로젝트명 생성
            project_name = generate_project_name_from_requirement(final_requirement)
            print(f"[initialize_project] Generated project name: {project_name}")

            update_data = {
                'name': project_name,
                'final_requirement': final_requirement,
                'pre_analysis_history': pre_analysis_history or [],
                'updated_at': datetime.now().isoformat()
            }

            # UPDATE 실행 (프로젝트는 이미 생성되어 있음)
            supabase.table('projects')\
                .update(update_data)\
                .eq('project_id', project_id)\
                .execute()

            # 2. Agent 템플릿 복사
            agents_created = self._copy_agents_from_template_supabase(
                supabase, project_id, framework, final_requirement
            )

            # 3. Task 템플릿 복사
            tasks_created = self._copy_tasks_from_template_supabase(
                supabase, project_id, framework, final_requirement
            )

            return {
                'status': 'success',
                'project_id': project_id,
                'framework': framework,
                'agents_created': agents_created,
                'tasks_created': tasks_created
            }

        except Exception as e:
            print(f"프로젝트 초기화 실패: {e}")
            raise e




    def _copy_agents_from_template(
        self,
        cursor,
        project_id: str,
        framework: str,
        final_requirement: str
    ) -> int:
        """Agent 템플릿을 프로젝트에 복사 (DB 커서)"""

        cursor.execute("""
            SELECT
                template_name,
                role,
                goal_template,
                backstory_template,
                default_llm_model,
                is_verbose,
                allow_delegation,
                agent_order
            FROM agent_templates
            WHERE framework = %s
            ORDER BY agent_order
        """, (framework,))

        templates = cursor.fetchall()
        if not templates:
            return 0

        templates_for_llm = []
        for template_name, role, goal_template, backstory_template, default_llm_model, is_verbose, allow_delegation, agent_order in templates:
            templates_for_llm.append({
                'role': role,
                'goal_template': goal_template,
                'backstory_template': backstory_template,
                'template_name': template_name
            })

        try:
            role_definitions = generate_agent_role_definitions(final_requirement, templates_for_llm)
        except Exception as exc:
            raise ValueError(f"Agent role definition failed: {exc}") from exc

        if not role_definitions:
            raise ValueError("Agent role definition failed: empty response")

        agents_created = 0
        for template_name, role, goal_template, backstory_template, default_llm_model, is_verbose, allow_delegation, agent_order in templates:
            normalized_role = (role or '').strip().lower()
            definition = role_definitions.get(normalized_role)
            if not definition:
                raise ValueError(f"Agent role definition missing for role '{role}'")

            goal_text = _sanitize_agent_text(_ensure_sentence(definition.get('goal')))
            backstory_text = _sanitize_agent_text(_ensure_sentence(definition.get('backstory')))
            if not goal_text or not backstory_text:
                raise ValueError(f"Agent role definition incomplete for role '{role}'")

            cursor.execute("""
                INSERT INTO project_agents (
                    project_id,
                    framework,
                    agent_order,
                    role,
                    goal,
                    backstory,
                    llm_model,
                    is_verbose,
                    allow_delegation
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, framework, agent_order) DO NOTHING
            """, (
                project_id,
                framework,
                agent_order,
                role,
                goal_text,
                backstory_text,
                default_llm_model,
                is_verbose,
                allow_delegation
            ))

            agents_created += cursor.rowcount

        return agents_created

    def _copy_tasks_from_template(
        self,
        cursor,
        project_id: str,
        framework: str,
        final_requirement: str
    ) -> int:
        """Task 템플릿을 프로젝트에 복사"""

        # 템플릿 조회
        cursor.execute("""
            SELECT
                task_type,
                description_template,
                expected_output_template,
                assigned_agent_order,
                depends_on_task_order,
                task_order
            FROM task_templates
            WHERE framework = %s
            ORDER BY task_order
        """, (framework,))

        templates = cursor.fetchall()
        tasks_created = 0

        for template in templates:
            (task_type, description_template, expected_output_template,
             assigned_agent_order, depends_on_task_order, task_order) = template

            # {requirement} 플레이스홀더 치환
            description = description_template.replace('{requirement}', final_requirement)
            expected_output = expected_output_template.replace('{requirement}', final_requirement)

            # Task 생성
            cursor.execute("""
                INSERT INTO project_tasks (
                    project_id,
                    framework,
                    task_order,
                    task_type,
                    description,
                    expected_output,
                    agent_project_id,
                    agent_framework,
                    agent_order,
                    depends_on_project_id,
                    depends_on_framework,
                    depends_on_task_order
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, framework, task_order) DO NOTHING
            """, (
                project_id,
                framework,
                task_order,
                task_type,
                description,
                expected_output,
                project_id,  # agent_project_id
                framework,   # agent_framework
                assigned_agent_order,
                project_id if depends_on_task_order else None,  # depends_on_project_id
                framework if depends_on_task_order else None,   # depends_on_framework
                depends_on_task_order
            ))

            tasks_created += cursor.rowcount

        return tasks_created




    def _copy_agents_from_template_supabase(
        self,
        supabase,
        project_id: str,
        framework: str,
        final_requirement: str
    ) -> int:
        """Agent 템플릿을 프로젝트에 복사 (Supabase)"""

        result = supabase.table('agent_templates')\
            .select('*')\
            .eq('framework', framework)\
            .order('agent_order')\
            .execute()

        templates = result.data or []
        if not templates:
            return 0

        try:
            role_definitions = generate_agent_role_definitions(final_requirement, templates)
        except Exception as exc:
            raise ValueError(f"Agent role definition failed: {exc}") from exc

        if not role_definitions:
            raise ValueError("Agent role definition failed: empty response")

        agents_created = 0
        for template in templates:
            role = template.get('role')
            normalized_role = (role or '').strip().lower()
            definition = role_definitions.get(normalized_role)
            if not definition:
                raise ValueError(f"Agent role definition missing for role '{role}'")

            goal_text = _sanitize_agent_text(_ensure_sentence(definition.get('goal')))
            backstory_text = _sanitize_agent_text(_ensure_sentence(definition.get('backstory')))
            if not goal_text or not backstory_text:
                raise ValueError(f"Agent role definition incomplete for role '{role}'")

            agent_data = {
                'project_id': project_id,
                'framework': framework,
                'agent_order': template.get('agent_order'),
                'role': role,
                'goal': goal_text,
                'backstory': backstory_text,
                'llm_model': template.get('default_llm_model'),
                'is_verbose': template.get('is_verbose', False),
                'allow_delegation': template.get('allow_delegation', False)
            }

            supabase.table('project_agents').upsert(agent_data).execute()
            agents_created += 1

        return agents_created

    def _copy_tasks_from_template_supabase(
        self,
        supabase,
        project_id: str,
        framework: str,
        final_requirement: str
    ) -> int:
        """Task 템플릿을 프로젝트에 복사 (Supabase 버전)"""

        # 템플릿 조회
        result = supabase.table('task_templates')\
            .select('*')\
            .eq('framework', framework)\
            .order('task_order')\
            .execute()

        templates = result.data
        tasks_created = 0

        for template in templates:
            # Task는 요구사항을 그대로 유지하는 것이 명확할 수 있으므로, 여기서는 단순 치환을 유지합니다.
            # 만약 Task 설명도 정제가 필요하다면 refine_task_definition 함수를 만들어 적용할 수 있습니다.
            description = template['description_template'].format(requirement=final_requirement)
            expected_output = template['expected_output_template'].format(requirement=final_requirement)

            # Task 생성 (UPSERT)
            task_data = {
                'project_id': project_id,
                'framework': framework,
                'task_order': template['task_order'],
                'task_type': template['task_type'],
                'description': description,
                'expected_output': expected_output,
                'agent_project_id': project_id,
                'agent_framework': framework,
                'agent_order': template['assigned_agent_order'],
                'depends_on_project_id': project_id if template.get('depends_on_task_order') else None,
                'depends_on_framework': framework if template.get('depends_on_task_order') else None,
                'depends_on_task_order': template.get('depends_on_task_order')
            }

            try:
                # Supabase upsert - 복합 PK는 upsert만으로 처리 (on_conflict 불필요)
                supabase.table('project_tasks').upsert(task_data).execute()
                tasks_created += 1
            except Exception as e:
                print(f"Task 생성 실패 ({template.get('task_type', 'Unknown')}): {e}")

        return tasks_created


def generate_next_project_id(supabase) -> str:
    """프로젝트 ID를 순차적으로 생성 (proj_0000001 형태)"""
    max_sequence = 0
    try:
        response = supabase.table('projects').select('project_id').execute()
        rows = []
        if hasattr(response, 'data') and response.data:
            rows = response.data
        elif isinstance(response, dict) and response.get('data'):
            rows = response['data']
        for row in rows:
            project_id = row.get('project_id') if isinstance(row, dict) else None
            if not project_id or not isinstance(project_id, str):
                continue
            match = re.search(r'(\d+)$', project_id)
            if match:
                try:
                    value = int(match.group(1))
                    max_sequence = max(max_sequence, value)
                except ValueError:
                    continue
    except Exception as exc:
        print(f"Project ID scan failed: {exc}")
    next_value = max_sequence + 1
    return f"proj_{next_value:07d}"



# Flask 라우트
@project_init_bp.route('/api/v2/projects', methods=['POST'])
def create_project():
    """
    프로젝트 레코드 생성 API

    Request Body:
    {
        "project_id": "project_12345",
        "name": "프로젝트명",
        "framework": "crewai" | "metagpt",
        "creation_type": "dynamic" | "template"
    }
    """
    try:
        data = request.get_json()

        project_id = (data.get('project_id') or '').strip() or None
        name = data.get('name', '새로운 자동화 프로젝트')
        framework = data.get('framework')
        creation_type = data.get('creation_type', 'dynamic')

        print(f"[create_project] 요청 시작 - name: {name}, framework: {framework}, timestamp: {datetime.now()}")

        if not framework or framework not in ['crewai', 'metagpt']:
            return jsonify({'error': 'Invalid framework'}), 400

        supabase = get_supabase_client()

        # 중복 요청 방지: 최근 10초 이내 동일한 name + framework 조합 확인
        if not project_id:  # 새 프로젝트 생성 시에만 체크
            ten_seconds_ago = (datetime.now() - timedelta(seconds=10)).isoformat()
            try:
                recent_check = supabase.table('projects')\
                    .select('project_id, created_at')\
                    .eq('name', name)\
                    .gte('created_at', ten_seconds_ago)\
                    .execute()

                if recent_check.data and len(recent_check.data) > 0:
                    existing_project = recent_check.data[0]
                    print(f"[create_project] 중복 요청 감지 - 기존 project_id 반환: {existing_project['project_id']}")
                    return jsonify({
                        'status': 'success',
                        'project_id': existing_project['project_id'],
                        'message': '이미 생성된 프로젝트입니다.'
                    }), 200
            except Exception as e:
                print(f"[create_project] 중복 체크 실패 (무시하고 계속): {e}")
                pass

        base_project_data = {
            'name': name,
            'selected_ai': 'crew-ai' if framework == 'crewai' else 'meta-gpt',
            'status': 'planning',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        try:
            base_project_data['creation_type'] = creation_type
        except Exception:
            pass

        created_rows = []
        project_insert_error = None

        if project_id:
            current_project_data = base_project_data.copy()
            current_project_data['project_id'] = project_id
            current_project_data['updated_at'] = datetime.now().isoformat()

            try:
                result = supabase.table('projects').upsert(current_project_data).execute()
            except Exception as exc:
                raise ValueError(str(exc))

            error = None
            if hasattr(result, 'error') and result.error:
                error = result.error
            elif isinstance(result, dict) and result.get('error'):
                error = result['error']

            if error:
                raise ValueError(str(error))

            if hasattr(result, 'data') and result.data:
                created_rows = result.data
            elif isinstance(result, dict) and result.get('data'):
                created_rows = result['data']
            else:
                created_rows = [current_project_data]
        else:
            attempts = 0

            while attempts < 5 and not created_rows:
                attempts += 1
                current_project_data = base_project_data.copy()
                generated_id = generate_next_project_id(supabase)
                current_project_data['project_id'] = generated_id

                try:
                    result = supabase.table('projects').insert(current_project_data).execute()
                except Exception as exc:
                    error_text = str(exc)
                    if ('duplicate key value' in error_text.lower() or '23505' in error_text) and attempts < 5:
                        project_insert_error = error_text
                        continue
                    raise

                error = None
                if hasattr(result, 'error') and result.error:
                    error = result.error
                elif isinstance(result, dict) and result.get('error'):
                    error = result['error']

                if error:
                    project_insert_error = str(error)
                    if ('duplicate key value' in project_insert_error.lower() or '23505' in project_insert_error) and attempts < 5:
                        continue
                    raise ValueError(project_insert_error)

                if hasattr(result, 'data') and result.data:
                    created_rows = result.data
                    project_id = generated_id
                elif isinstance(result, dict) and result.get('data'):
                    created_rows = result['data']
                    project_id = generated_id
                else:
                    project_insert_error = project_insert_error or 'Failed to create project record'

            if not created_rows:
                fallback_project_id = f"proj_{uuid.uuid4().hex[:10]}"
                current_project_data = base_project_data.copy()
                current_project_data['project_id'] = fallback_project_id
                try:
                    fallback_result = supabase.table('projects').insert(current_project_data).execute()
                except Exception as exc:
                    raise ValueError(project_insert_error or str(exc))

                if hasattr(fallback_result, 'data') and fallback_result.data:
                    created_rows = fallback_result.data
                elif isinstance(fallback_result, dict) and fallback_result.get('data'):
                    created_rows = fallback_result['data']
                else:
                    raise ValueError(project_insert_error or 'Failed to create project record (fallback)')

                project_id = fallback_project_id

        created_project = created_rows[0]
        project_id = created_project.get('project_id') or project_id
        if not project_id:
            raise ValueError('Project ID generation failed')

        print(f"[create_project] 생성 완료 - project_id: {project_id}")

        return jsonify({
            'status': 'success',
            'project_id': project_id,
            'message': '프로젝트 레코드가 생성되었습니다.'
        }), 201

    except Exception as e:
        print(f"[create_project] 오류 발생: {e}")
        return jsonify({'error': str(e)}), 500


@project_init_bp.route('/api/v2/projects/<project_id>/initialize', methods=['POST'])
def initialize_project(project_id: str):
    """
    프로젝트 초기화 API

    Request Body:
    {
        "framework": "crewai" | "metagpt",
        "finalRequirement": "확정된 최종 요구사항",
        "preAnalysisHistory": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    try:
        print(f"[initialize_project] 시작 - project_id: {project_id}")

        data = request.get_json()

        framework = data.get('framework')
        final_requirement = data.get('finalRequirement')
        pre_analysis_history = data.get('preAnalysisHistory', [])

        # 검증
        if not framework or framework not in ['crewai', 'metagpt']:
            return jsonify({'error': 'Invalid framework'}), 400

        if not final_requirement:
            return jsonify({'error': 'Final requirement is required'}), 400

        # 초기화 실행
        initializer = ProjectInitializer()
        result = initializer.initialize_project(
            project_id=project_id,
            framework=framework,
            final_requirement=final_requirement,
            pre_analysis_history=pre_analysis_history
        )

        print(f"[initialize_project] 완료 - agents: {result.get('agents_created')}, tasks: {result.get('tasks_created')}")

        return jsonify(result), 200

    except Exception as e:
        print(f"[initialize_project] 오류: {e}")
        return jsonify({'error': str(e)}), 500


@project_init_bp.route('/api/v2/projects/<project_id>/agents', methods=['GET'])
def get_project_agents(project_id: str):
    """프로젝트의 Agent 목록 조회"""
    try:
        framework = request.args.get('framework', 'crewai')

        # Supabase client 사용
        supabase = get_supabase_client()

        # Agent 조회
        result = supabase.table('project_agents')\
            .select('*')\
            .eq('project_id', project_id)\
            .eq('framework', framework)\
            .order('agent_order')\
            .execute()

        agents = result.data

        # datetime 필드를 문자열로 변환 (이미 ISO 형식)
        for agent in agents:
            if agent.get('created_at') and isinstance(agent['created_at'], str):
                pass  # 이미 문자열
            if agent.get('updated_at') and isinstance(agent['updated_at'], str):
                pass  # 이미 문자열

        return jsonify({'agents': agents}), 200

    except Exception as e:
        print(f"Agent 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500


@project_init_bp.route('/api/v2/projects/<project_id>/tasks', methods=['GET'])
def get_project_tasks(project_id: str):
    """프로젝트의 Task 목록 조회"""
    try:
        framework = request.args.get('framework', 'crewai')

        # Supabase client 사용
        supabase = get_supabase_client()

        # Task 조회 (agent_role 포함을 위해 JOIN)
        result = supabase.table('project_tasks')\
            .select('*, project_agents!project_tasks_agent_project_id_agent_framework_agent_order_fkey(role)')\
            .eq('project_id', project_id)\
            .eq('framework', framework)\
            .order('task_order')\
            .execute()

        tasks = []
        for task in result.data:
            # Agent role 추출
            agent_role = None
            if task.get('project_agents'):
                agent_role = task['project_agents'].get('role')

            # task 데이터 정리
            task_data = {
                'project_id': task.get('project_id'),
                'framework': task.get('framework'),
                'task_order': task.get('task_order'),
                'task_type': task.get('task_type'),
                'description': task.get('description'),
                'expected_output': task.get('expected_output'),
                'agent_order': task.get('agent_order'),
                'depends_on_task_order': task.get('depends_on_task_order'),
                'is_active': task.get('is_active'),
                'created_at': task.get('created_at'),
                'updated_at': task.get('updated_at'),
                'agent_role': agent_role
            }
            tasks.append(task_data)

        return jsonify({'tasks': tasks}), 200

    except Exception as e:
        print(f"Task 조회 실패: {e}")
        return jsonify({'error': str(e)}), 500
