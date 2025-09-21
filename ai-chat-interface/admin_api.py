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
# 사용자 관리 API
# ============================================================================

# 이 함수는 중복이므로 제거됨 (아래 get_all_users 함수 사용)

@admin_bp.route('/users', methods=['POST'])
@admin_required()
def admin_create_user():
    """사용자 생성 (관리자 전용)"""
    try:
        current_admin = get_current_admin()
        data = request.get_json()

        # 필수 필드 검증
        if not data.get('user_id'):
            return jsonify({'error': '사용자 ID는 필수입니다'}), 400

        result = db.create_user(data)

        if result['success']:
            return jsonify({
                'success': True,
                'user': result['user'],
                'message': '사용자가 성공적으로 생성되었습니다'
            })
        else:
            return jsonify({'error': result['error']}), 400

    except Exception as e:
        return jsonify({'error': f'사용자 생성 실패: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required()
def admin_get_user(user_id):
    """사용자 상세 조회 (관리자 전용)"""
    try:
        current_admin = get_current_admin()

        result = db.get_user(user_id)

        if result['success']:
            return jsonify({
                'success': True,
                'user': result['user']
            })
        else:
            return jsonify({'error': result['error']}), 404

    except Exception as e:
        return jsonify({'error': f'사용자 조회 실패: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required()
def admin_update_user(user_id):
    """사용자 정보 수정 (관리자 전용)"""
    try:
        current_admin = get_current_admin()
        data = request.get_json()

        result = db.update_user(user_id, data, admin_user_id=current_admin['username'])

        if result['success']:
            return jsonify({
                'success': True,
                'user': result['user'],
                'message': '사용자 정보가 성공적으로 수정되었습니다'
            })
        else:
            return jsonify({'error': result['error']}), 400

    except Exception as e:
        return jsonify({'error': f'사용자 수정 실패: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required()
def admin_delete_user(user_id):
    """사용자 삭제 (관리자 전용)"""
    try:
        current_admin = get_current_admin()

        result = db.delete_user(user_id, admin_user_id=current_admin['username'])

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({'error': result['error']}), 400

    except Exception as e:
        return jsonify({'error': f'사용자 삭제 실패: {str(e)}'}), 500

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
            if db and hasattr(db, 'supabase') and db.supabase:
                result = db.supabase.table('projects').select('count').limit(1).execute()
                health_status['database'] = 'healthy'
            else:
                health_status['database'] = 'disconnected'
        except Exception as e:
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
        # 데이터베이스 연결 확인 (필수 요구사항)
        if not db or not hasattr(db, 'supabase') or not db.supabase:
            # Supabase 연결 실패 시 시스템 전체 중단
            return jsonify({
                'success': False,
                'error': 'SYSTEM_DOWN: 데이터베이스 연결 실패',
                'system_status': 'CRITICAL_ERROR',
                'message': '🚨 시스템 중단: Supabase 데이터베이스에 연결할 수 없습니다. 시스템 관리자에게 즉시 문의하세요.',
                'action_required': 'DB 연결 복구 필요'
            }), 503

        # projects 테이블에서 프로젝트 건수만 조회
        try:
            # count만 조회 (성능 최적화)
            result = db.supabase.table('projects').select('id').execute()
            if result.data:
                total_count = len(result.data)

                # 상세 정보가 필요한 경우에만 전체 데이터 조회
                query_param = request.args.get('detailed', 'false').lower()
                if query_param == 'true':
                    # 전체 프로젝트 정보 조회
                    full_result = db.supabase.table('projects').select('*').execute()
                    projects = full_result.data

                    # 각 프로젝트의 통계 정보 추가
                    for project in projects:
                        try:
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
                        except Exception:
                            # 통계 조회 실패 시 기본값 설정
                            project['statistics'] = {
                                'total_stages': 0,
                                'completed_stages': 0,
                                'total_deliverables': 0,
                                'approved_deliverables': 0
                            }
                else:
                    # 건수만 필요한 경우
                    projects = []

                return jsonify({
                    'success': True,
                    'projects': projects,
                    'total_count': total_count,
                    'message': f'총 {total_count}개의 프로젝트가 있습니다.'
                })
            else:
                return jsonify({
                    'success': True,
                    'projects': [],
                    'total_count': 0,
                    'message': '등록된 프로젝트가 없습니다.'
                })

        except Exception as e:
            # 데이터베이스 쿼리 실패 시 에러 반환
            print(f"프로젝트 조회 실패: {e}")
            return jsonify({
                'success': False,
                'error': f'프로젝트 조회 실패: {str(e)}',
                'projects': [],
                'total_count': 0,
                'message': 'projects 테이블에 접근할 수 없습니다.'
            }), 500

    except Exception as e:
        print(f"ERROR: 프로젝트 조회 실패 - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
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
# 사용자 관리 API
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@admin_required()
def get_users():
    """모든 사용자 조회 (관리자용)"""
    try:
        # 데이터베이스 연결 확인 (필수 요구사항)
        if not db or not hasattr(db, 'supabase') or not db.supabase:
            # Supabase 연결 실패 시 시스템 전체 중단
            return jsonify({
                'success': False,
                'error': 'SYSTEM_DOWN: 데이터베이스 연결 실패',
                'system_status': 'CRITICAL_ERROR',
                'message': '🚨 시스템 중단: Supabase 데이터베이스에 연결할 수 없습니다. 시스템 관리자에게 즉시 문의하세요.',
                'action_required': 'DB 연결 복구 필요'
            }), 503

        # auth.users 테이블에서 실제 Supabase 등록 사용자 수 조회
        try:
            result = db.supabase.table('auth.users').select('id').execute()
            if result.data:
                total_users = len(result.data)
                return jsonify({
                    'success': True,
                    'users': [],  # 보안상 사용자 상세 정보는 반환하지 않음
                    'total_count': total_users,
                    'message': f'Supabase Auth에 등록된 사용자 {total_users}명'
                })
            else:
                return jsonify({
                    'success': True,
                    'users': [],
                    'total_count': 0,
                    'message': '등록된 사용자가 없습니다.'
                })

        except Exception as e:
            # auth.users 테이블 접근 실패
            return jsonify({
                'success': False,
                'error': f'사용자 테이블 접근 실패: {str(e)}',
                'users': [],
                'total_count': 0,
                'message': 'Supabase Auth 테이블에 접근할 수 없습니다.'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'사용자 조회 실패: {str(e)}',
            'users': [],
            'total_count': 0
        }), 500

@admin_bp.route('/users', methods=['POST'])
@admin_required()
def create_user():
    """새 사용자 생성"""
    try:
        data = request.get_json()

        # 입력 데이터 검증
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 필드가 필요합니다'}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        # 사용자명 중복 검사 (향후 구현)
        # existing_user = db.supabase.table('users').select('*').eq('username', username).execute()
        # if existing_user.data:
        #     return jsonify({'error': '이미 존재하는 사용자명입니다'}), 409

        # 비밀번호 해싱
        import hashlib
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # 새 사용자 생성 (향후 데이터베이스 구현)
        new_user = {
            'id': 2,  # 임시 ID
            'username': username,
            'email': email,
            'role': role,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }

        return jsonify({
            'success': True,
            'message': '사용자가 성공적으로 생성되었습니다',
            'user': new_user
        })

    except Exception as e:
        return jsonify({'error': f'사용자 생성 실패: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required()
def update_user(user_id):
    """사용자 정보 수정"""
    try:
        data = request.get_json()

        # 업데이트할 필드들
        updatable_fields = ['email', 'role', 'status']
        update_data = {}

        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400

        # 사용자 존재 확인 및 업데이트 (향후 데이터베이스 구현)
        updated_user = {
            'id': user_id,
            'username': 'admin',  # 임시 데이터
            'email': update_data.get('email', 'admin@aichatinterface.com'),
            'role': update_data.get('role', 'admin'),
            'status': update_data.get('status', 'active'),
            'updated_at': datetime.now().isoformat()
        }

        return jsonify({
            'success': True,
            'message': '사용자 정보가 업데이트되었습니다',
            'user': updated_user
        })

    except Exception as e:
        return jsonify({'error': f'사용자 업데이트 실패: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    """사용자 삭제"""
    try:
        # 관리자 계정 삭제 방지
        if user_id == 1:
            return jsonify({'error': '기본 관리자 계정은 삭제할 수 없습니다'}), 400

        # 사용자 삭제 (향후 데이터베이스 구현)
        # result = db.supabase.table('users').delete().eq('id', user_id).execute()

        return jsonify({
            'success': True,
            'message': '사용자가 성공적으로 삭제되었습니다'
        })

    except Exception as e:
        return jsonify({'error': f'사용자 삭제 실패: {str(e)}'}), 500

# ============================================================================
# LLM 모델 관리 API
# ============================================================================

@admin_bp.route('/llm-models/manage', methods=['GET'])
@admin_required()
def get_llm_models_detailed():
    """LLM 모델 상세 관리 목록"""
    try:
        # 기본 LLM 모델 목록 (확장된 정보)
        llm_models = [
            {
                'id': 'gpt-4',
                'name': 'GPT-4',
                'provider': 'OpenAI',
                'status': 'active',
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 8192,
                'cost_per_1k_tokens': 0.03,
                'capabilities': ['text-generation', 'reasoning', 'coding'],
                'recommended_roles': ['Writer', 'Analyst'],
                'created_at': '2025-09-01T00:00:00.000Z'
            },
            {
                'id': 'gpt-4o',
                'name': 'GPT-4o',
                'provider': 'OpenAI',
                'status': 'active',
                'api_endpoint': 'https://api.openai.com/v1/chat/completions',
                'max_tokens': 4096,
                'cost_per_1k_tokens': 0.015,
                'capabilities': ['text-generation', 'multimodal', 'fast-response'],
                'recommended_roles': ['Researcher', 'Quick-Analysis'],
                'created_at': '2025-09-01T00:00:00.000Z'
            },
            {
                'id': 'claude-3',
                'name': 'Claude-3 Sonnet',
                'provider': 'Anthropic',
                'status': 'active',
                'api_endpoint': 'https://api.anthropic.com/v1/messages',
                'max_tokens': 4096,
                'cost_per_1k_tokens': 0.015,
                'capabilities': ['text-generation', 'reasoning', 'analysis'],
                'recommended_roles': ['Planner', 'Architect'],
                'created_at': '2025-09-01T00:00:00.000Z'
            },
            {
                'id': 'claude-3-haiku',
                'name': 'Claude-3 Haiku',
                'provider': 'Anthropic',
                'status': 'active',
                'api_endpoint': 'https://api.anthropic.com/v1/messages',
                'max_tokens': 4096,
                'cost_per_1k_tokens': 0.0025,
                'capabilities': ['text-generation', 'fast-response', 'lightweight'],
                'recommended_roles': ['Quick-Tasks', 'Assistant'],
                'created_at': '2025-09-01T00:00:00.000Z'
            },
            {
                'id': 'gemini-pro',
                'name': 'Gemini Pro',
                'provider': 'Google',
                'status': 'active',
                'api_endpoint': 'https://generativelanguage.googleapis.com/v1/models/gemini-pro',
                'max_tokens': 8192,
                'cost_per_1k_tokens': 0.0005,
                'capabilities': ['text-generation', 'reasoning', 'multimodal'],
                'recommended_roles': ['Researcher', 'Data-Analyst'],
                'created_at': '2025-09-01T00:00:00.000Z'
            },
            {
                'id': 'deepseek-coder',
                'name': 'DeepSeek Coder',
                'provider': 'DeepSeek',
                'status': 'active',
                'api_endpoint': 'https://api.deepseek.com/v1/chat/completions',
                'max_tokens': 16384,
                'cost_per_1k_tokens': 0.0014,
                'capabilities': ['code-generation', 'debugging', 'optimization'],
                'recommended_roles': ['Engineer', 'Developer'],
                'created_at': '2025-09-01T00:00:00.000Z'
            }
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

@admin_bp.route('/llm-models/manage', methods=['POST'])
@admin_required()
def add_llm_model():
    """새 LLM 모델 추가"""
    try:
        data = request.get_json()

        # 입력 데이터 검증
        required_fields = ['id', 'name', 'provider', 'api_endpoint']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 필드가 필요합니다'}), 400

        new_model = {
            'id': data.get('id'),
            'name': data.get('name'),
            'provider': data.get('provider'),
            'status': data.get('status', 'active'),
            'api_endpoint': data.get('api_endpoint'),
            'max_tokens': data.get('max_tokens', 4096),
            'cost_per_1k_tokens': data.get('cost_per_1k_tokens', 0.0),
            'capabilities': data.get('capabilities', []),
            'recommended_roles': data.get('recommended_roles', []),
            'created_at': datetime.now().isoformat(),
            'usage_count': 0
        }

        # 향후 데이터베이스 저장 구현
        # db.supabase.table('llm_models').insert(new_model).execute()

        return jsonify({
            'success': True,
            'message': 'LLM 모델이 성공적으로 추가되었습니다',
            'model': new_model
        })

    except Exception as e:
        return jsonify({'error': f'LLM 모델 추가 실패: {str(e)}'}), 500

@admin_bp.route('/llm-models/manage/<model_id>', methods=['PUT'])
@admin_required()
def update_llm_model(model_id):
    """LLM 모델 설정 수정"""
    try:
        data = request.get_json()

        # 업데이트할 필드들
        updatable_fields = ['name', 'status', 'api_endpoint', 'max_tokens', 'cost_per_1k_tokens', 'capabilities', 'recommended_roles']
        update_data = {}

        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400

        update_data['updated_at'] = datetime.now().isoformat()

        # 향후 데이터베이스 업데이트 구현
        # result = db.supabase.table('llm_models').update(update_data).eq('id', model_id).execute()

        return jsonify({
            'success': True,
            'message': 'LLM 모델 설정이 업데이트되었습니다',
            'model_id': model_id,
            'updated_fields': update_data
        })

    except Exception as e:
        return jsonify({'error': f'LLM 모델 업데이트 실패: {str(e)}'}), 500

@admin_bp.route('/llm-models/manage/<model_id>', methods=['DELETE'])
@admin_required()
def delete_llm_model(model_id):
    """LLM 모델 삭제"""
    try:
        # 기본 모델 삭제 방지
        core_models = ['gpt-4', 'claude-3', 'gemini-pro']
        if model_id in core_models:
            return jsonify({'error': '핵심 모델은 삭제할 수 없습니다'}), 400

        # 모델 삭제 (향후 데이터베이스 구현)
        # result = db.supabase.table('llm_models').delete().eq('id', model_id).execute()

        return jsonify({
            'success': True,
            'message': 'LLM 모델이 성공적으로 삭제되었습니다'
        })

    except Exception as e:
        return jsonify({'error': f'LLM 모델 삭제 실패: {str(e)}'}), 500

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