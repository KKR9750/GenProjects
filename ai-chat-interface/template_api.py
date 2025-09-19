# -*- coding: utf-8 -*-
"""
Template API Endpoints
프로젝트 템플릿 관련 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
from template_manager import template_manager
from security_utils import validate_request_data, check_request_security
from database import db

template_bp = Blueprint('template', __name__, url_prefix='/api/templates')

# Rate limiting decorator (if available)
def rate_limit(max_requests, window_seconds):
    """Rate limiting decorator - simple implementation"""
    def decorator(func):
        return func
    return decorator

@template_bp.route('/', methods=['GET'])
@rate_limit(30, 60)
def get_all_templates():
    """모든 템플릿 조회"""
    try:
        result = template_manager.get_all_templates()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 조회 실패: {str(e)}'
        }), 500


@template_bp.route('/<template_id>', methods=['GET'])
@rate_limit(60, 60)
def get_template(template_id):
    """특정 템플릿 조회"""
    try:
        result = template_manager.get_template_by_id(template_id)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 조회 실패: {str(e)}'
        }), 500


@template_bp.route('/category/<category>', methods=['GET'])
@rate_limit(30, 60)
def get_templates_by_category(category):
    """카테고리별 템플릿 조회"""
    try:
        result = template_manager.get_templates_by_category(category)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'카테고리별 템플릿 조회 실패: {str(e)}'
        }), 500


@template_bp.route('/search', methods=['GET'])
@rate_limit(20, 60)
def search_templates():
    """템플릿 검색"""
    try:
        query = request.args.get('q', '')

        if not query:
            return jsonify({
                'success': False,
                'error': '검색어가 필요합니다'
            }), 400

        result = template_manager.search_templates(query)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 검색 실패: {str(e)}'
        }), 500


@template_bp.route('/recommendations', methods=['POST'])
@rate_limit(10, 60)
def get_template_recommendations():
    """사용자 선호도 기반 템플릿 추천"""
    try:
        data = request.get_json() or {}

        # 기본 선호도 설정
        user_preferences = {
            'complexity': data.get('complexity', 'medium'),
            'categories': data.get('categories', []),
            'experience': data.get('experience', 'intermediate')
        }

        result = template_manager.get_template_recommendations(user_preferences)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 추천 실패: {str(e)}'
        }), 500


@template_bp.route('/statistics', methods=['GET'])
@rate_limit(20, 60)
def get_template_statistics():
    """템플릿 통계 정보"""
    try:
        result = template_manager.get_template_statistics()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 통계 조회 실패: {str(e)}'
        }), 500


@template_bp.route('/<template_id>/create-project', methods=['POST'])
@rate_limit(10, 60)
def create_project_from_template(template_id):
    """템플릿 기반 프로젝트 생성"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': '프로젝트 데이터가 필요합니다'
            }), 400

        # 보안 검사
        security_issues = check_request_security(data)
        if security_issues:
            return jsonify({
                'success': False,
                'error': 'Security validation failed',
                'details': security_issues
            }), 400

        # 템플릿 기반 프로젝트 데이터 생성
        template_result = template_manager.create_project_from_template(template_id, data)

        if not template_result['success']:
            return jsonify(template_result), 400

        # 생성된 프로젝트 데이터를 데이터베이스에 저장
        project_data = template_result['project_data']

        # 입력 데이터 검증
        validation_result = validate_request_data(project_data, 'project')
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Template project data validation failed',
                'details': validation_result['errors']
            }), 400

        # 데이터베이스에 프로젝트 생성
        db_result = db.create_project(validation_result['data'])

        if db_result['success']:
            # 추천 LLM 매핑이 있는 경우 설정
            if 'recommended_llm_mapping' in project_data:
                project_id = db_result['project']['id']
                llm_mappings = []

                for role_name, llm_model in project_data['recommended_llm_mapping'].items():
                    llm_mappings.append({
                        'role_name': role_name,
                        'llm_model': llm_model
                    })

                # LLM 매핑 설정
                if llm_mappings:
                    db.set_project_role_llm_mapping(project_id, llm_mappings)

            return jsonify({
                'success': True,
                'project': db_result['project'],
                'template': template_result['template'],
                'message': f"'{template_result['template']['name']}' 템플릿으로 프로젝트가 생성되었습니다",
                'simulation': db_result.get('simulation', False)
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Database project creation failed',
                'details': db_result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿 기반 프로젝트 생성 실패: {str(e)}'
        }), 500


@template_bp.route('/categories', methods=['GET'])
@rate_limit(30, 60)
def get_template_categories():
    """템플릿 카테고리 목록 조회"""
    try:
        result = template_manager.get_all_templates()

        if result['success']:
            return jsonify({
                'success': True,
                'categories': result['categories']
            })
        else:
            return jsonify(result), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'카테고리 조회 실패: {str(e)}'
        }), 500


# 템플릿 기반 프로젝트 목록 조회 (특정 템플릿으로 생성된 프로젝트들)
@template_bp.route('/<template_id>/projects', methods=['GET'])
@rate_limit(20, 60)
def get_projects_by_template(template_id):
    """특정 템플릿으로 생성된 프로젝트 목록"""
    try:
        # 데이터베이스에서 해당 템플릿으로 생성된 프로젝트 조회
        all_projects = db.get_projects()

        if all_projects['success']:
            template_projects = [
                project for project in all_projects['projects']
                if project.get('template_id') == template_id or
                   project.get('project_type') == template_id
            ]

            return jsonify({
                'success': True,
                'template_id': template_id,
                'projects': template_projects,
                'count': len(template_projects)
            })
        else:
            return jsonify({
                'success': False,
                'error': '프로젝트 조회 실패'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'템플릿별 프로젝트 조회 실패: {str(e)}'
        }), 500