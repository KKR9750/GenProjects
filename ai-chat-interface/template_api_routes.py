# -*- coding: utf-8 -*-
"""
Template API Routes
템플릿 시스템 API 라우트
"""

from flask import Blueprint, request, jsonify
from project_template_system import template_manager, ProjectType, Framework
from project_initializer import project_initializer
from project_executor import project_executor
from error_handler import error_handler, handle_api_error
import uuid
from datetime import datetime

# Blueprint 생성
template_routes = Blueprint('template_routes', __name__, url_prefix='/api/templates')

@template_routes.route('/', methods=['GET'])
def get_all_templates():
    """모든 템플릿 조회"""
    try:
        templates = template_manager.get_all_templates()
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates],
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/featured', methods=['GET'])
def get_featured_templates():
    """추천 템플릿 조회"""
    try:
        templates = template_manager.get_featured_templates()
        return jsonify({
            'success': True,
            'templates': [t.to_dict() for t in templates],
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/types/<project_type>', methods=['GET'])
def get_templates_by_type(project_type):
    """프로젝트 유형별 템플릿 조회"""
    try:
        templates = template_manager.get_templates_by_type(project_type)
        return jsonify({
            'success': True,
            'project_type': project_type,
            'templates': [t.to_dict() for t in templates],
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/frameworks/<framework>', methods=['GET'])
def get_templates_by_framework(framework):
    """프레임워크별 템플릿 조회"""
    try:
        templates = template_manager.get_templates_by_framework(framework)
        return jsonify({
            'success': True,
            'framework': framework,
            'templates': [t.to_dict() for t in templates],
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/<template_id>', methods=['GET'])
def get_template_by_id(template_id):
    """특정 템플릿 조회"""
    try:
        template = template_manager.get_template_by_id(template_id)
        if template:
            return jsonify({
                'success': True,
                'template': template.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': '템플릿을 찾을 수 없습니다'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/search', methods=['GET'])
def search_templates():
    """템플릿 검색"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'success': False,
                'message': '검색어가 필요합니다'
            }), 400

        templates = template_manager.search_templates(query)
        return jsonify({
            'success': True,
            'query': query,
            'templates': [t.to_dict() for t in templates],
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/<template_id>/create-project', methods=['POST'])
@handle_api_error
def create_project_from_template(template_id):
    """템플릿으로부터 프로젝트 생성"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        custom_settings = data.get('custom_settings', {})

        if not project_name:
            return jsonify({
                'success': False,
                'message': '프로젝트 이름이 필요합니다'
            }), 400

        # 새로운 프로젝트 초기화 시스템 사용
        project_data = project_initializer.initialize_project(
            template_id, project_name, custom_settings
        )

        # 자동 실행 옵션 확인
        auto_execute = custom_settings.get('auto_execute', True)
        execution_result = None

        if auto_execute:
            execution_result = project_executor.execute_project(project_data['project_id'])

        return jsonify({
            'success': True,
            'project': project_data,
            'execution': execution_result,
            'message': f'프로젝트 "{project_name}"이 성공적으로 생성되었습니다',
            'ready_to_start': True,
            'auto_executed': auto_execute
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/statistics', methods=['GET'])
def get_template_statistics():
    """템플릿 사용 통계"""
    try:
        stats = template_manager.get_template_statistics()
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/project-types', methods=['GET'])
def get_project_types():
    """사용 가능한 프로젝트 유형 조회"""
    try:
        project_types = [
            {
                'value': ptype.value,
                'name': ptype.name,
                'display_name': _get_project_type_display_name(ptype.value)
            }
            for ptype in ProjectType
        ]
        return jsonify({
            'success': True,
            'project_types': project_types
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/frameworks', methods=['GET'])
def get_frameworks():
    """사용 가능한 프레임워크 조회"""
    try:
        frameworks = [
            {
                'value': framework.value,
                'name': framework.name,
                'display_name': _get_framework_display_name(framework.value)
            }
            for framework in Framework
        ]
        return jsonify({
            'success': True,
            'frameworks': frameworks
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _get_project_type_display_name(project_type: str) -> str:
    """프로젝트 유형 표시명 반환"""
    display_names = {
        'web_app': '웹 애플리케이션',
        'mobile_app': '모바일 앱',
        'api_server': 'API 서버',
        'desktop_app': '데스크톱 앱',
        'data_analysis': '데이터 분석',
        'ml_project': '머신러닝 프로젝트',
        'blockchain': '블록체인',
        'game_dev': '게임 개발',
        'ecommerce': 'E-commerce',
        'crm_system': 'CRM 시스템'
    }
    return display_names.get(project_type, project_type)

def _get_framework_display_name(framework: str) -> str:
    """프레임워크 표시명 반환"""
    display_names = {
        'crew_ai': 'CrewAI (협업 기반)',
        'meta_gpt': 'MetaGPT (단계별 워크플로우)'
    }
    return display_names.get(framework, framework)

@template_routes.route('/projects', methods=['GET'])
def get_created_projects():
    """생성된 프로젝트 목록 조회"""
    try:
        projects = project_initializer.list_projects()
        return jsonify({
            'success': True,
            'projects': projects,
            'count': len(projects)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/projects/<project_id>', methods=['GET'])
def get_project_status(project_id):
    """프로젝트 상태 조회"""
    try:
        project_status = project_initializer.get_project_status(project_id)
        if project_status:
            return jsonify({
                'success': True,
                'project': project_status
            })
        else:
            return jsonify({
                'success': False,
                'message': '프로젝트를 찾을 수 없습니다'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/projects/<project_id>/execute', methods=['POST'])
@handle_api_error
def execute_project(project_id):
    """프로젝트 실행 시작"""
    try:
        data = request.get_json() or {}
        auto_start = data.get('auto_start', True)

        result = project_executor.execute_project(project_id, auto_start)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/projects/<project_id>/execution/status', methods=['GET'])
def get_execution_status(project_id):
    """프로젝트 실행 상태 조회"""
    try:
        status = project_executor.get_execution_status(project_id)
        if status:
            return jsonify({
                'success': True,
                'execution': status
            })
        else:
            return jsonify({
                'success': False,
                'message': '실행 정보를 찾을 수 없습니다'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/projects/<project_id>/execution/cancel', methods=['POST'])
def cancel_execution(project_id):
    """프로젝트 실행 취소"""
    try:
        result = project_executor.cancel_execution(project_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_routes.route('/executions', methods=['GET'])
def list_executions():
    """모든 프로젝트 실행 상태 목록"""
    try:
        executions = project_executor.list_executions()
        return jsonify({
            'success': True,
            'executions': executions,
            'count': len(executions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500