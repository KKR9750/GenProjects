# -*- coding: utf-8 -*-
"""
Admin API Routes
관리자 시스템 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
import psutil
import os
from datetime import datetime, timedelta
import json

from admin_auth import admin_auth, admin_required, get_current_admin
from database import db
from security_utils import validate_request_data

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================================
# 인증 관련 API
# ============================================================================

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """관리자 로그인"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': '사용자명과 패스워드를 입력하세요'}), 400

        # 패스워드 검증
        if admin_auth.verify_password(username, password):
            token = admin_auth.generate_token(username)
            return jsonify({
                'success': True,
                'token': token,
                'username': username,
                'role': 'admin'
            })
        else:
            return jsonify({'error': '잘못된 사용자명 또는 패스워드입니다'}), 401

    except Exception as e:
        return jsonify({'error': f'로그인 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@admin_bp.route('/verify', methods=['GET'])
@admin_required()
def verify_admin():
    """관리자 토큰 검증"""
    admin_info = get_current_admin()
    return jsonify({
        'success': True,
        'admin': admin_info
    })

@admin_bp.route('/logout', methods=['POST'])
@admin_required()
def admin_logout():
    """관리자 로그아웃"""
    # JWT는 stateless이므로 클라이언트에서 토큰 삭제
    return jsonify({'success': True, 'message': '로그아웃되었습니다'})

# ============================================================================
# 시스템 모니터링 API
# ============================================================================

@admin_bp.route('/system/status', methods=['GET'])
@admin_required()
def get_system_status():
    """시스템 상태 조회"""
    try:
        # CPU 및 메모리 사용률
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # 프로세스 정보
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info['name'] in ['python.exe', 'python', 'node.exe', 'node']:
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return jsonify({
            'success': True,
            'system': {
                'cpu_usage': cpu_usage,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'used': disk.used,
                    'percent': (disk.used / disk.total) * 100
                },
                'processes': processes[:10],  # 상위 10개 프로세스
                'timestamp': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({'error': f'시스템 상태 조회 실패: {str(e)}'}), 500

@admin_bp.route('/system/health', methods=['GET'])
@admin_required()
def get_system_health():
    """시스템 헬스체크"""
    try:
        health_status = {
            'database': 'healthy',
            'flask_server': 'healthy',
            'websocket': 'healthy',
            'crewai_service': 'unknown',
            'metagpt_service': 'unknown'
        }

        # 데이터베이스 연결 테스트
        try:
            if db.supabase:
                result = db.supabase.table('projects').select('count').limit(1).execute()
                health_status['database'] = 'healthy'
            else:
                health_status['database'] = 'disconnected'
        except Exception:
            health_status['database'] = 'error'

        # CrewAI 서비스 체크
        try:
            import requests
            response = requests.get('http://localhost:3001/health', timeout=5)
            health_status['crewai_service'] = 'healthy' if response.status_code == 200 else 'error'
        except:
            health_status['crewai_service'] = 'disconnected'

        # MetaGPT 서비스 체크
        try:
            import requests
            response = requests.get('http://localhost:3002/health', timeout=5)
            health_status['metagpt_service'] = 'healthy' if response.status_code == 200 else 'error'
        except:
            health_status['metagpt_service'] = 'disconnected'

        overall_health = 'healthy' if all(
            status in ['healthy', 'unknown'] for status in health_status.values()
        ) else 'degraded'

        return jsonify({
            'success': True,
            'overall_health': overall_health,
            'services': health_status,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': f'헬스체크 실패: {str(e)}'}), 500

# ============================================================================
# 프로젝트 관리 API
# ============================================================================

@admin_bp.route('/projects', methods=['GET'])
@admin_required()
def get_all_projects():
    """모든 프로젝트 조회 (관리자용)"""
    try:
        if not db.supabase:
            return jsonify({'error': '데이터베이스 연결이 필요합니다'}), 503

        # 프로젝트 목록 조회
        result = db.supabase.table('projects').select('*').execute()
        projects = result.data

        # 각 프로젝트의 통계 정보 추가
        for project in projects:
            # 프로젝트 단계 정보
            stages_result = db.supabase.table('project_stages').select('*').eq('project_id', project['id']).execute()
            stages = stages_result.data

            # 산출물 정보
            deliverables_result = db.supabase.table('project_deliverables').select('*').eq('project_id', project['id']).execute()
            deliverables = deliverables_result.data

            project['statistics'] = {
                'total_stages': len(stages),
                'completed_stages': len([s for s in stages if s.get('stage_status') == 'completed']),
                'total_deliverables': len(deliverables),
                'approved_deliverables': len([d for d in deliverables if d.get('status') == 'approved'])
            }

        return jsonify({
            'success': True,
            'projects': projects,
            'total_count': len(projects)
        })

    except Exception as e:
        return jsonify({'error': f'프로젝트 조회 실패: {str(e)}'}), 500

@admin_bp.route('/projects/<project_id>/force-complete', methods=['PUT'])
@admin_required()
def force_complete_project(project_id):
    """프로젝트 강제 완료 처리"""
    try:
        if not db.supabase:
            return jsonify({'error': '데이터베이스 연결이 필요합니다'}), 503

        # 프로젝트 상태 업데이트
        result = db.supabase.table('projects').update({
            'status': 'completed',
            'progress_percentage': 100,
            'updated_at': datetime.now().isoformat()
        }).eq('id', project_id).execute()

        if result.data:
            return jsonify({
                'success': True,
                'message': '프로젝트가 완료 처리되었습니다',
                'project': result.data[0]
            })
        else:
            return jsonify({'error': '프로젝트를 찾을 수 없습니다'}), 404

    except Exception as e:
        return jsonify({'error': f'프로젝트 완료 처리 실패: {str(e)}'}), 500

# ============================================================================
# 사용자 활동 로그 API
# ============================================================================

@admin_bp.route('/activity-logs', methods=['GET'])
@admin_required()
def get_activity_logs():
    """사용자 활동 로그 조회"""
    try:
        # 로그 파일 읽기 (향후 데이터베이스로 이전 예정)
        logs = []
        log_file_path = os.path.join(os.path.dirname(__file__), 'logs', 'activity.log')

        if os.path.exists(log_file_path):
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f.readlines()[-100:]:  # 최근 100개 로그
                    try:
                        log_data = json.loads(line.strip())
                        logs.append(log_data)
                    except json.JSONDecodeError:
                        continue

        return jsonify({
            'success': True,
            'logs': logs[-50:],  # 최근 50개만 반환
            'total_count': len(logs)
        })

    except Exception as e:
        return jsonify({'error': f'활동 로그 조회 실패: {str(e)}'}), 500

# ============================================================================
# LLM 모델 관리 API
# ============================================================================

@admin_bp.route('/llm-models', methods=['GET'])
@admin_required()
def get_llm_models():
    """LLM 모델 목록 및 사용 통계"""
    try:
        # 기본 LLM 모델 목록
        llm_models = [
            {'id': 'gpt-4', 'name': 'GPT-4', 'provider': 'OpenAI', 'status': 'active'},
            {'id': 'gpt-4o', 'name': 'GPT-4o', 'provider': 'OpenAI', 'status': 'active'},
            {'id': 'claude-3', 'name': 'Claude-3 Sonnet', 'provider': 'Anthropic', 'status': 'active'},
            {'id': 'claude-3-haiku', 'name': 'Claude-3 Haiku', 'provider': 'Anthropic', 'status': 'active'},
            {'id': 'gemini-pro', 'name': 'Gemini Pro', 'provider': 'Google', 'status': 'active'},
            {'id': 'gemini-ultra', 'name': 'Gemini Ultra', 'provider': 'Google', 'status': 'active'},
            {'id': 'llama-3', 'name': 'Llama-3 70B', 'provider': 'Meta', 'status': 'active'},
            {'id': 'llama-3-8b', 'name': 'Llama-3 8B', 'provider': 'Meta', 'status': 'active'},
            {'id': 'mistral-large', 'name': 'Mistral Large', 'provider': 'Mistral AI', 'status': 'active'},
            {'id': 'mistral-7b', 'name': 'Mistral 7B', 'provider': 'Mistral AI', 'status': 'active'},
            {'id': 'deepseek-coder', 'name': 'DeepSeek Coder', 'provider': 'DeepSeek', 'status': 'active'},
            {'id': 'codellama', 'name': 'Code Llama', 'provider': 'Meta', 'status': 'active'}
        ]

        # 데이터베이스에서 사용 통계 조회
        if db.supabase:
            try:
                result = db.supabase.table('project_role_llm_mapping').select('llm_model').execute()
                usage_stats = {}
                for record in result.data:
                    model = record.get('llm_model')
                    usage_stats[model] = usage_stats.get(model, 0) + 1

                # 모델별 사용 통계 추가
                for model in llm_models:
                    model['usage_count'] = usage_stats.get(model['id'], 0)
            except:
                # 통계 조회 실패 시 기본값 설정
                for model in llm_models:
                    model['usage_count'] = 0

        return jsonify({
            'success': True,
            'models': llm_models,
            'total_count': len(llm_models)
        })

    except Exception as e:
        return jsonify({'error': f'LLM 모델 조회 실패: {str(e)}'}), 500

# ============================================================================
# 시스템 설정 API
# ============================================================================

@admin_bp.route('/settings', methods=['GET'])
@admin_required()
def get_system_settings():
    """시스템 설정 조회"""
    try:
        settings = {
            'server': {
                'port': 3000,
                'debug_mode': True,
                'environment': 'development'
            },
            'database': {
                'provider': 'Supabase',
                'connected': db.supabase is not None
            },
            'features': {
                'websocket_enabled': True,
                'realtime_progress': True,
                'template_system': True,
                'project_auto_execution': True
            },
            'security': {
                'jwt_expiry_hours': 24,
                'password_policy': 'basic',
                'rate_limiting': False
            }
        }

        return jsonify({
            'success': True,
            'settings': settings
        })

    except Exception as e:
        return jsonify({'error': f'설정 조회 실패: {str(e)}'}), 500

@admin_bp.route('/settings', methods=['PUT'])
@admin_required()
def update_system_settings():
    """시스템 설정 업데이트"""
    try:
        data = request.get_json()

        # 검증된 설정만 업데이트 (실제 구현에서는 파일 또는 DB에 저장)
        updated_settings = data.get('settings', {})

        # TODO: 실제 설정 파일 업데이트 로직 구현

        return jsonify({
            'success': True,
            'message': '설정이 업데이트되었습니다',
            'settings': updated_settings
        })

    except Exception as e:
        return jsonify({'error': f'설정 업데이트 실패: {str(e)}'}), 500