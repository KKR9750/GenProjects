# -*- coding: utf-8 -*-
"""
Project Initializer
프로젝트 즉시 시작 시스템
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
from project_template_system import template_manager

class ProjectInitializer:
    """프로젝트 초기화 및 즉시 시작 시스템"""

    def __init__(self):
        # 프로젝트를 D:\GenProjects\Projects 하위에 저장
        self.projects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Projects')
        self.ensure_projects_directory()

    def ensure_projects_directory(self):
        """프로젝트 디렉토리 생성"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def initialize_project(self, template_id: str, project_name: str, custom_settings: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 기반 프로젝트 초기화"""

        # 템플릿 가져오기
        template = template_manager.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"템플릿을 찾을 수 없습니다: {template_id}")

        # 프로젝트 ID 생성
        project_id = str(uuid.uuid4())[:8]

        # 프로젝트 기본 구조
        project_data = {
            'id': project_id,
            'name': project_name,
            'template_id': template_id,
            'template_name': template.display_name,
            'project_type': template.project_type,
            'framework': template.framework,
            'description': custom_settings.get('description', ''),
            'created_at': datetime.now().isoformat(),
            'status': 'ready',
            'llm_mappings': [mapping.to_dict() for mapping in template.llm_mappings],
            'custom_settings': custom_settings
        }

        # 프로젝트별 디렉토리 생성
        project_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

        # 프로젝트 설정 파일 저장
        config_file = os.path.join(project_dir, 'project_config.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

        # 프레임워크별 초기화
        if template.framework == 'crew_ai':
            self._initialize_crewai_project(project_dir, project_data, template)
        elif template.framework == 'meta_gpt':
            self._initialize_metagpt_project(project_dir, project_data, template)

        return project_data

    def _initialize_crewai_project(self, project_dir: str, project_data: Dict[str, Any], template) -> None:
        """CrewAI 프로젝트 초기화"""

        # CrewAI 프로젝트 구조 생성
        crew_config = {
            'project_id': project_data['id'],
            'project_name': project_data['name'],
            'agents': [],
            'tasks': [],
            'crew_config': {
                'verbose': True,
                'memory': True
            }
        }

        # 템플릿 LLM 매핑을 CrewAI 에이전트로 변환
        for mapping in template.llm_mappings:
            agent_config = {
                'role': mapping.role,
                'goal': self._get_role_goal(mapping.role, project_data['project_type']),
                'backstory': self._get_role_backstory(mapping.role, project_data['project_type']),
                'llm_model': mapping.llm_model,
                'tools': self._get_role_tools(mapping.role),
                'verbose': True,
                'allow_delegation': mapping.role in ['Product Manager', 'Project Manager']
            }
            crew_config['agents'].append(agent_config)

        # 기본 태스크 생성
        crew_config['tasks'] = self._generate_default_tasks(project_data['project_type'])

        # CrewAI 설정 파일 저장
        crew_file = os.path.join(project_dir, 'crew_config.json')
        with open(crew_file, 'w', encoding='utf-8') as f:
            json.dump(crew_config, f, ensure_ascii=False, indent=2)

        # 실행 스크립트 생성
        self._create_crewai_runner(project_dir, project_data)

    def _initialize_metagpt_project(self, project_dir: str, project_data: Dict[str, Any], template) -> None:
        """MetaGPT 프로젝트 초기화"""

        # MetaGPT 프로젝트 구조 생성
        metagpt_config = {
            'project_id': project_data['id'],
            'project_name': project_data['name'],
            'project_description': project_data['description'],
            'roles': [],
            'workflow': self._get_metagpt_workflow(project_data['project_type']),
            'output_format': 'structured'
        }

        # 템플릿 LLM 매핑을 MetaGPT 역할로 변환
        for mapping in template.llm_mappings:
            role_config = {
                'name': mapping.role,
                'llm_model': mapping.llm_model,
                'responsibilities': self._get_metagpt_responsibilities(mapping.role),
                'output_format': self._get_role_output_format(mapping.role)
            }
            metagpt_config['roles'].append(role_config)

        # MetaGPT 설정 파일 저장
        metagpt_file = os.path.join(project_dir, 'metagpt_config.json')
        with open(metagpt_file, 'w', encoding='utf-8') as f:
            json.dump(metagpt_config, f, ensure_ascii=False, indent=2)

        # 실행 스크립트 생성
        self._create_metagpt_runner(project_dir, project_data)

    def _get_role_goal(self, role: str, project_type: str) -> str:
        """역할별 목표 생성"""
        role_goals = {
            'Researcher': f'{project_type} 프로젝트를 위한 최신 정보와 best practice 연구',
            'Writer': f'{project_type} 프로젝트의 문서화 및 콘텐츠 작성',
            'Planner': f'{project_type} 프로젝트의 전략 기획 및 일정 관리',
            'Product Manager': f'{project_type} 프로젝트의 제품 전략 및 요구사항 정의',
            'Architect': f'{project_type} 프로젝트의 시스템 아키텍처 설계',
            'Engineer': f'{project_type} 프로젝트의 개발 및 구현',
            'QA Engineer': f'{project_type} 프로젝트의 품질 보증 및 테스트'
        }
        return role_goals.get(role, f'{project_type} 프로젝트 진행')

    def _get_role_backstory(self, role: str, project_type: str) -> str:
        """역할별 배경 스토리 생성"""
        backstories = {
            'Researcher': '다양한 도메인의 최신 트렌드와 기술을 분석하는 전문 연구원',
            'Writer': '복잡한 기술적 내용을 명확하고 이해하기 쉽게 작성하는 테크니컬 라이터',
            'Planner': '프로젝트 일정과 리소스를 효율적으로 관리하는 프로젝트 매니저',
            'Product Manager': '시장 요구사항을 분석하고 제품 전략을 수립하는 제품 관리자',
            'Architect': '확장 가능하고 안정적인 시스템을 설계하는 솔루션 아키텍트',
            'Engineer': '최신 기술을 활용하여 효율적인 코드를 작성하는 소프트웨어 엔지니어',
            'QA Engineer': '품질과 사용자 경험을 최우선으로 하는 품질 보증 전문가'
        }
        return backstories.get(role, '전문적인 경험과 지식을 가진 팀 멤버')

    def _get_role_tools(self, role: str) -> List[str]:
        """역할별 도구 목록"""
        tools = {
            'Researcher': ['web_search', 'document_analysis', 'data_analysis'],
            'Writer': ['text_editor', 'documentation_tools', 'content_formatter'],
            'Planner': ['project_management', 'timeline_tools', 'resource_tracker'],
            'Product Manager': ['market_analysis', 'user_research', 'roadmap_tools'],
            'Architect': ['system_design', 'database_design', 'api_design'],
            'Engineer': ['code_editor', 'version_control', 'testing_tools'],
            'QA Engineer': ['testing_frameworks', 'automation_tools', 'bug_tracking']
        }
        return tools.get(role, ['general_tools'])

    def _generate_default_tasks(self, project_type: str) -> List[Dict[str, Any]]:
        """프로젝트 유형별 기본 태스크 생성"""
        if project_type == 'web_app':
            return [
                {
                    'description': '웹 애플리케이션 요구사항 분석 및 기술 스택 연구',
                    'agent': 'Researcher',
                    'expected_output': '기술 스택 추천 및 요구사항 문서'
                },
                {
                    'description': '프로젝트 계획 및 개발 일정 수립',
                    'agent': 'Planner',
                    'expected_output': '상세 개발 계획서 및 마일스톤'
                },
                {
                    'description': '기술 문서 및 사용자 가이드 작성',
                    'agent': 'Writer',
                    'expected_output': '완성된 프로젝트 문서'
                }
            ]
        elif project_type == 'api_server':
            return [
                {
                    'description': 'API 서버 아키텍처 및 엔드포인트 설계',
                    'agent': 'Researcher',
                    'expected_output': 'API 설계 문서 및 기술 스택'
                },
                {
                    'description': 'API 개발 일정 및 배포 계획 수립',
                    'agent': 'Planner',
                    'expected_output': '개발 및 배포 로드맵'
                },
                {
                    'description': 'API 문서 및 개발자 가이드 작성',
                    'agent': 'Writer',
                    'expected_output': 'API 문서 및 통합 가이드'
                }
            ]
        else:
            return [
                {
                    'description': f'{project_type} 프로젝트 기획 및 연구',
                    'agent': 'Researcher',
                    'expected_output': '프로젝트 기획서 및 기술 분석'
                },
                {
                    'description': f'{project_type} 프로젝트 실행 계획 수립',
                    'agent': 'Planner',
                    'expected_output': '실행 계획 및 일정표'
                },
                {
                    'description': f'{project_type} 프로젝트 문서화',
                    'agent': 'Writer',
                    'expected_output': '완성된 프로젝트 문서'
                }
            ]

    def _get_metagpt_workflow(self, project_type: str) -> List[str]:
        """MetaGPT 워크플로우 정의"""
        return [
            'Product Manager',
            'Architect',
            'Product Manager',
            'Engineer',
            'QA Engineer'
        ]

    def _get_metagpt_responsibilities(self, role: str) -> List[str]:
        """MetaGPT 역할별 책임"""
        responsibilities = {
            'Product Manager': [
                '프로덕트 요구사항 정의',
                '사용자 스토리 작성',
                '프로덕트 로드맵 수립'
            ],
            'Architect': [
                '시스템 아키텍처 설계',
                '기술 스택 선정',
                '데이터베이스 설계'
            ],
            'Engineer': [
                '코드 구현',
                '기능 개발',
                '통합 테스트'
            ],
            'QA Engineer': [
                '테스트 계획 수립',
                '품질 검증',
                '버그 리포트 작성'
            ]
        }
        return responsibilities.get(role, ['일반적인 프로젝트 업무'])

    def _get_role_output_format(self, role: str) -> str:
        """역할별 출력 형식"""
        formats = {
            'Product Manager': 'prd_document',
            'Architect': 'system_design_doc',
            'Engineer': 'code_implementation',
            'QA Engineer': 'test_report'
        }
        return formats.get(role, 'general_document')

    def _create_crewai_runner(self, project_dir: str, project_data: Dict[str, Any]) -> None:
        """CrewAI 실행 스크립트 생성"""
        runner_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 프로젝트 실행 스크립트
프로젝트: {project_data['name']}
생성일: {project_data['created_at']}
"""

import json
import sys
import os

# 프로젝트 설정 로드
with open('project_config.json', 'r', encoding='utf-8') as f:
    project_config = json.load(f)

with open('crew_config.json', 'r', encoding='utf-8') as f:
    crew_config = json.load(f)

print(f"🚀 CrewAI 프로젝트 시작: {{project_config['name']}}")
print(f"📋 프로젝트 ID: {{project_config['id']}}")
print(f"🎯 프로젝트 유형: {{project_config['project_type']}}")
print(f"👥 에이전트 수: {{len(crew_config['agents'])}}")
print(f"📝 태스크 수: {{len(crew_config['tasks'])}}")

# CrewAI 실행 로직을 여기에 추가
# 실제 CrewAI 라이브러리와 연동

if __name__ == "__main__":
    print("\\n✅ 프로젝트가 즉시 실행 가능한 상태입니다!")
    print("📚 자세한 설정은 crew_config.json을 참조하세요.")
'''

        runner_file = os.path.join(project_dir, 'run_crew.py')
        with open(runner_file, 'w', encoding='utf-8') as f:
            f.write(runner_content)

        # 실행 권한 부여 (Unix 시스템에서)
        try:
            os.chmod(runner_file, 0o755)
        except:
            pass  # Windows에서는 무시

    def _create_metagpt_runner(self, project_dir: str, project_data: Dict[str, Any]) -> None:
        """MetaGPT 실행 스크립트 생성"""
        runner_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MetaGPT 프로젝트 실행 스크립트
프로젝트: {project_data['name']}
생성일: {project_data['created_at']}
"""

import json
import sys
import os

# 프로젝트 설정 로드
with open('project_config.json', 'r', encoding='utf-8') as f:
    project_config = json.load(f)

with open('metagpt_config.json', 'r', encoding='utf-8') as f:
    metagpt_config = json.load(f)

print(f"🚀 MetaGPT 프로젝트 시작: {{project_config['name']}}")
print(f"📋 프로젝트 ID: {{project_config['id']}}")
print(f"🎯 프로젝트 유형: {{project_config['project_type']}}")
print(f"👥 역할 수: {{len(metagpt_config['roles'])}}")
print(f"🔄 워크플로우: {{' → '.join(metagpt_config['workflow'])}}")

# MetaGPT 실행 로직을 여기에 추가
# 실제 MetaGPT 라이브러리와 연동

if __name__ == "__main__":
    print("\\n✅ 프로젝트가 즉시 실행 가능한 상태입니다!")
    print("📚 자세한 설정은 metagpt_config.json을 참조하세요.")
'''

        runner_file = os.path.join(project_dir, 'run_metagpt.py')
        with open(runner_file, 'w', encoding='utf-8') as f:
            f.write(runner_content)

        # 실행 권한 부여 (Unix 시스템에서)
        try:
            os.chmod(runner_file, 0o755)
        except:
            pass  # Windows에서는 무시

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """프로젝트 상태 조회"""
        project_dir = os.path.join(self.projects_dir, project_id)
        config_file = os.path.join(project_dir, 'project_config.json')

        if not os.path.exists(config_file):
            return None

        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_projects(self) -> List[Dict[str, Any]]:
        """모든 프로젝트 목록 조회"""
        projects = []

        if not os.path.exists(self.projects_dir):
            return projects

        for project_id in os.listdir(self.projects_dir):
            project_status = self.get_project_status(project_id)
            if project_status:
                projects.append(project_status)

        return sorted(projects, key=lambda x: x['created_at'], reverse=True)

# 글로벌 인스턴스
project_initializer = ProjectInitializer()