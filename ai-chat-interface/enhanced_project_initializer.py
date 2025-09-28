#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 프로젝트 초기화 시스템
- 메시지 분류 통합
- 요구사항 추출 및 보존
- 스마트 프로젝트 생성
"""

import os
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# 프로젝트 모듈 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from message_classifier import MessageClassifier, MessageType
from project_state_manager import ProjectStateManager, ProjectStatus
from project_template_system import ProjectTemplate, ProjectType, Framework

class EnhancedProjectInitializer:
    """강화된 프로젝트 초기화기"""

    def __init__(self, base_projects_dir: str):
        self.base_projects_dir = base_projects_dir
        self.message_classifier = MessageClassifier()

        # 디렉토리 생성
        os.makedirs(base_projects_dir, exist_ok=True)

    def process_user_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        사용자 메시지를 처리하여 적절한 액션 결정

        Returns:
            액션 타입과 처리 결과
        """
        # 메시지 분류
        classification = self.message_classifier.classify_message(message, context)

        if classification['type'] == MessageType.REQUIREMENT:
            # 새로운 프로젝트 요구사항
            return self._handle_new_requirement(message, classification)

        elif classification['type'] == MessageType.SYSTEM_CONFIRMATION:
            # 시스템 확인에 대한 응답
            return self._handle_system_confirmation(message, classification, context)

        elif classification['type'] == MessageType.PROJECT_RESUME:
            # 프로젝트 재개 요청
            return self._handle_project_resume(message, classification, context)

        elif classification['type'] == MessageType.APPROVAL_DECISION:
            # 승인/거부 결정
            return self._handle_approval_decision(message, classification, context)

        else:
            # 분류되지 않은 메시지
            return {
                'action': 'clarification_needed',
                'message': '요청사항을 명확히 해주시겠어요? 구체적인 프로젝트 요구사항이나 명령을 입력해주세요.',
                'classification': classification
            }

    def _handle_new_requirement(self, message: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """새로운 요구사항 처리"""
        # 프로젝트 생성
        project_result = self.create_project_from_requirement(message)

        if project_result['success']:
            return {
                'action': 'project_created',
                'message': f"새로운 프로젝트가 생성되었습니다: {project_result['project_name']}",
                'project': project_result,
                'classification': classification
            }
        else:
            return {
                'action': 'project_creation_failed',
                'message': f"프로젝트 생성에 실패했습니다: {project_result.get('error', '알 수 없는 오류')}",
                'classification': classification
            }

    def _handle_system_confirmation(self, message: str, classification: Dict[str, Any],
                                  context: Dict[str, Any] = None) -> Dict[str, Any]:
        """시스템 확인 메시지 처리"""
        confirmation_type = classification.get('confirmation_type', 'simple_yes')

        if confirmation_type == 'simple_yes':
            # 계속 진행 요청
            if context and context.get('pending_project'):
                project_id = context['pending_project']
                return {
                    'action': 'continue_project',
                    'message': f"프로젝트 {project_id} 작업을 계속 진행합니다.",
                    'project_id': project_id,
                    'classification': classification
                }
            else:
                return {
                    'action': 'no_pending_project',
                    'message': '계속 진행할 프로젝트가 없습니다. 새로운 요구사항을 입력해주세요.',
                    'classification': classification
                }

        elif confirmation_type == 'rejection':
            return {
                'action': 'project_cancelled',
                'message': '프로젝트가 취소되었습니다.',
                'classification': classification
            }

        return {
            'action': 'confirmation_processed',
            'message': '확인되었습니다.',
            'classification': classification
        }

    def _handle_project_resume(self, message: str, classification: Dict[str, Any],
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """프로젝트 재개 요청 처리"""
        resume_context = classification.get('resume_context', {})
        specific_project = resume_context.get('specific_project')

        if specific_project:
            # 특정 프로젝트 재개
            project_path = os.path.join(self.base_projects_dir, specific_project)
            if os.path.exists(project_path):
                manager = ProjectStateManager(project_path)
                if manager.can_resume():
                    resume_point = manager.get_resume_point()
                    return {
                        'action': 'resume_specific_project',
                        'message': f"프로젝트 {specific_project}를 {resume_point} 단계부터 재개합니다.",
                        'project_id': specific_project,
                        'resume_point': resume_point,
                        'classification': classification
                    }
                else:
                    return {
                        'action': 'cannot_resume_project',
                        'message': f"프로젝트 {specific_project}는 현재 재개할 수 없습니다.",
                        'project_id': specific_project,
                        'classification': classification
                    }
            else:
                return {
                    'action': 'project_not_found',
                    'message': f"프로젝트 {specific_project}를 찾을 수 없습니다.",
                    'classification': classification
                }
        else:
            # 재개 가능한 프로젝트 찾기
            resumable_projects = self._find_resumable_projects()
            if resumable_projects:
                if len(resumable_projects) == 1:
                    project = resumable_projects[0]
                    return {
                        'action': 'resume_found_project',
                        'message': f"프로젝트 {project['id']}를 {project['resume_point']} 단계부터 재개합니다.",
                        'project_id': project['id'],
                        'resume_point': project['resume_point'],
                        'classification': classification
                    }
                else:
                    return {
                        'action': 'multiple_resumable_projects',
                        'message': f"재개 가능한 프로젝트가 {len(resumable_projects)}개 있습니다. 구체적인 프로젝트명을 지정해주세요.",
                        'projects': resumable_projects,
                        'classification': classification
                    }
            else:
                return {
                    'action': 'no_resumable_projects',
                    'message': '현재 재개할 수 있는 프로젝트가 없습니다.',
                    'classification': classification
                }

    def _handle_approval_decision(self, message: str, classification: Dict[str, Any],
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """승인/거부 결정 처리"""
        decision_context = classification.get('decision_context', {})
        decision = decision_context.get('decision')

        if context and context.get('pending_approval_project'):
            project_id = context['pending_approval_project']
            return {
                'action': 'approval_decision',
                'message': f"프로젝트 {project_id}에 대한 {decision} 결정이 처리됩니다.",
                'project_id': project_id,
                'decision': decision,
                'feedback': message,
                'classification': classification
            }
        else:
            return {
                'action': 'no_pending_approval',
                'message': '현재 승인 대기 중인 프로젝트가 없습니다.',
                'classification': classification
            }

    def create_project_from_requirement(self, requirement: str) -> Dict[str, Any]:
        """요구사항으로부터 프로젝트 생성"""
        try:
            # 프로젝트 기본 정보 생성
            project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            project_path = os.path.join(self.base_projects_dir, project_id)

            # 요구사항 분석
            analysis = self._analyze_requirement(requirement)
            project_name = analysis.get('suggested_name', project_id)
            description = analysis.get('description', requirement[:100] + '...')

            # 프로젝트 디렉토리 생성
            os.makedirs(project_path, exist_ok=True)

            # 상태 관리자 생성 및 초기화
            manager = ProjectStateManager(project_path)

            # 요구사항 저장
            manager.save_original_requirements(requirement, {
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'message_classification': self.message_classifier.classify_message(requirement)
            })

            # 프로젝트 상태 초기화
            manager.initialize_project_status(project_name, description)

            # CrewAI 실행 스크립트 생성 (강화된 버전 사용)
            script_path = self._create_enhanced_execution_script(
                project_path, requirement, project_name, description
            )

            return {
                'success': True,
                'project_id': project_id,
                'project_name': project_name,
                'project_path': project_path,
                'description': description,
                'analysis': analysis,
                'execution_script': script_path,
                'message': f"프로젝트 '{project_name}'이 생성되었습니다."
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"프로젝트 생성 중 오류 발생: {str(e)}"
            }

    def _analyze_requirement(self, requirement: str) -> Dict[str, Any]:
        """요구사항 분석"""
        analysis = {
            'length': len(requirement),
            'word_count': len(requirement.split()),
            'complexity': 'medium',
            'domain': 'general',
            'suggested_name': '',
            'description': '',
            'keywords': [],
            'framework_recommendation': Framework.CREW_AI.value
        }

        # 복잡성 분석
        if analysis['word_count'] > 50:
            analysis['complexity'] = 'high'
        elif analysis['word_count'] < 10:
            analysis['complexity'] = 'low'

        # 키워드 추출
        keywords = []
        technical_terms = {
            'web': ['웹', '웹사이트', 'web', 'html', 'css', 'javascript', '브라우저'],
            'mobile': ['모바일', '앱', 'app', 'android', 'ios', '스마트폰'],
            'data': ['데이터', '분석', '처리', '변환', '통계', '시각화', '차트'],
            'ai': ['AI', '인공지능', '머신러닝', '딥러닝', 'ML', 'DL', '예측'],
            'system': ['시스템', '서버', 'API', '데이터베이스', '관리', '자동화'],
            'document': ['문서', '파일', '포맷', '변환', '통합', '이력서', '보고서']
        }

        for domain, terms in technical_terms.items():
            matching_terms = [term for term in terms if term.lower() in requirement.lower()]
            if matching_terms:
                analysis['domain'] = domain
                keywords.extend(matching_terms)

        analysis['keywords'] = keywords

        # 프로젝트명 제안
        if '이력서' in requirement:
            analysis['suggested_name'] = '이력서통합시스템'
            analysis['description'] = '여러 포맷의 이력서를 통합 관리하는 시스템'
        elif '웹' in requirement or '웹사이트' in requirement:
            analysis['suggested_name'] = '웹애플리케이션'
            analysis['description'] = '웹 기반 애플리케이션'
        elif '분석' in requirement or '데이터' in requirement:
            analysis['suggested_name'] = '데이터분석도구'
            analysis['description'] = '데이터 분석 및 처리 도구'
        else:
            # 일반적인 이름 생성
            key_words = [word for word in requirement.split()[:3]
                        if len(word) > 1 and not word in ['을', '를', '에', '의', '로', '으로']]
            if key_words:
                analysis['suggested_name'] = ''.join(key_words) + '시스템'
            else:
                analysis['suggested_name'] = f"커스텀프로젝트_{datetime.now().strftime('%m%d')}"

        analysis['description'] = requirement[:100] + ('...' if len(requirement) > 100 else '')

        return analysis

    def _create_enhanced_execution_script(self, project_path: str, requirement: str,
                                        project_name: str, description: str) -> str:
        """강화된 실행 스크립트 생성"""
        script_content = f"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

# 프로젝트 경로를 sys.path에 추가
project_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(project_dir)
sys.path.append(parent_dir)

# 강화된 실행기 import 및 실행
try:
    from enhanced_crewai_executor import EnhancedCrewAIExecutor

    executor = EnhancedCrewAIExecutor(
        project_path="{project_path}",
        original_requirements="""{requirement}""",
        project_name="{project_name}",
        description="{description}"
    )

    # 실행
    executor.execute()

except ImportError as e:
    print("강화된 실행기를 찾을 수 없습니다:", e)
    print("기본 CrewAI 실행기를 사용합니다.")

    # 기본 실행기 폴백
    from crewai import Agent, Task, Crew, Process
    from langchain_openai import ChatOpenAI

    print("기본 CrewAI 실행 시작...")
    print("요구사항:", "{requirement}")
    print("프로젝트 경로:", "{project_path}")

except Exception as e:
    print("실행 중 오류:", e)
    sys.exit(1)
"""

        script_path = os.path.join(project_path, 'execute_project.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

    def _find_resumable_projects(self) -> List[Dict[str, Any]]:
        """재개 가능한 프로젝트 찾기"""
        resumable_projects = []

        if not os.path.exists(self.base_projects_dir):
            return resumable_projects

        for project_name in os.listdir(self.base_projects_dir):
            project_path = os.path.join(self.base_projects_dir, project_name)
            if os.path.isdir(project_path):
                try:
                    manager = ProjectStateManager(project_path)
                    if manager.can_resume():
                        status_data = manager.load_project_status()
                        resumable_projects.append({
                            'id': project_name,
                            'name': status_data.get('project_name', project_name),
                            'resume_point': manager.get_resume_point(),
                            'status': status_data.get('status'),
                            'updated_at': status_data.get('updated_at')
                        })
                except Exception as e:
                    print(f"프로젝트 {project_name} 상태 확인 오류: {e}")
                    continue

        return resumable_projects

    def get_project_context(self, project_id: str) -> Optional[Dict[str, Any]]:
        """프로젝트 컨텍스트 조회"""
        project_path = os.path.join(self.base_projects_dir, project_id)
        if not os.path.exists(project_path):
            return None

        try:
            manager = ProjectStateManager(project_path)
            status_data = manager.load_project_status()
            requirements_data = manager.load_original_requirements()

            return {
                'project_id': project_id,
                'project_path': project_path,
                'status': status_data,
                'requirements': requirements_data,
                'can_resume': manager.can_resume(),
                'resume_point': manager.get_resume_point()
            }
        except Exception as e:
            print(f"프로젝트 컨텍스트 조회 오류: {e}")
            return None

# 사용 예시 및 테스트
def test_enhanced_initializer():
    """강화된 프로젝트 초기화기 테스트"""
    initializer = EnhancedProjectInitializer("D:\\GenProjects\\Projects")

    test_messages = [
        "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘.",
        "네",
        "project_00023 이어서 진행해줘",
        "승인합니다",
        "거부합니다. 다시 계획해주세요.",
    ]

    for msg in test_messages:
        print(f"\n입력: '{msg}'")
        result = initializer.process_user_message(msg)
        print(f"액션: {result['action']}")
        print(f"응답: {result['message']}")
        print("-" * 50)

if __name__ == "__main__":
    test_enhanced_initializer()