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
# 데이터베이스 연결 관리 API
# ============================================================================

@admin_bp.route('/database/connection', methods=['GET'])
@admin_required()
def check_database_connection():
    """데이터베이스 연결 상태 확인"""
    try:
        result = db.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e),
            'message': f'연결 상태 확인 실패: {str(e)}'
        }), 500

@admin_bp.route('/database/reconnect', methods=['POST'])
@admin_required()
def reconnect_database():
    """데이터베이스 연결 재시도"""
    try:
        result = db.reconnect()
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 503
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'연결 재시도 실패: {str(e)}'
        }), 500

# ============================================================================
# 사용자 관리 API
# ============================================================================

# 중복 함수 제거됨 - 통합된 create_user 함수 사용

@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required()
def admin_get_user(user_id):
    """사용자 상세 조회 (관리자 전용)"""
    try:
        current_admin = get_current_admin()

        result = db.get_user(user_id)

        if result['success']:
            # 일관성을 위해 user_id를 id로 변환
            user = result['user'].copy()
            user['id'] = user.get('user_id')
            user['username'] = user.get('user_id')
            if 'is_active' in user:
                user['status'] = 'active' if user['is_active'] else 'inactive'

            return jsonify({
                'success': True,
                'user': user
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
            'websocket': 'healthy'
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

        # 전체 시스템 상태 결정 (실제 서비스만 체크)
        overall_health = 'healthy' if all(
            status == 'healthy' for status in health_status.values()
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
            return jsonify({
                'success': False,
                'error': 'DATABASE_CONNECTION_FAILED',
                'message': '데이터베이스 연결에 실패했습니다. 시스템 관리자에게 문의하세요.',
                'projects': [],
                'total_count': 0
            }), 503

        # projects 테이블에서 프로젝트 건수만 조회
        try:
            # count만 조회 (성능 최적화)
            result = db.supabase.table('projects').select('project_id').execute()
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
                            stages_result = db.supabase.table('project_stages').select('*').eq('project_id', project['project_id']).execute()
                            stages = stages_result.data

                            # 산출물 정보
                            deliverables_result = db.supabase.table('project_deliverables').select('*').eq('project_id', project['project_id']).execute()
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
        }).eq('project_id', project_id).execute()

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
            return jsonify({
                'success': False,
                'error': 'DATABASE_CONNECTION_FAILED',
                'message': '데이터베이스 연결에 실패했습니다. 시스템 관리자에게 문의하세요.',
                'users': [],
                'total_count': 0
            }), 503

        # users 테이블에서 사용자 목록 조회
        try:
            result = db.supabase.table('users').select('user_id, email, display_name, role, is_active, last_login_at, created_at, updated_at').execute()

            users = []
            for user in result.data:
                users.append({
                    'id': user['user_id'],
                    'username': user['user_id'],
                    'email': user['email'],
                    'display_name': user['display_name'],
                    'role': user['role'],
                    'status': 'active' if user['is_active'] else 'inactive',
                    'last_login': user['last_login_at'],
                    'created_at': user['created_at'],
                    'updated_at': user['updated_at']
                })

            return jsonify({
                'success': True,
                'users': users,
                'total_count': len(users),
                'message': f'등록된 사용자 {len(users)}명 조회 완료'
            })

        except Exception as e:
            # users 테이블 접근 실패
            return jsonify({
                'success': False,
                'error': f'사용자 테이블 접근 실패: {str(e)}',
                'users': [],
                'total_count': 0,
                'message': '사용자 데이터베이스에 접근할 수 없습니다.'
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

        # 입력 데이터 검증 (user_id와 username 모두 지원)
        user_id = data.get('user_id') or data.get('username')
        if not user_id:
            return jsonify({'error': '사용자 ID(user_id 또는 username)는 필수입니다'}), 400

        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        # 필수 필드 검증
        required_fields = ['email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 필드가 필요합니다'}), 400

        # 데이터베이스 연결 확인
        if not db.supabase:
            return jsonify({'error': '데이터베이스 연결이 필요합니다'}), 503

        # 사용자 ID 중복 검사
        existing_user = db.supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if existing_user.data:
            return jsonify({'error': '이미 존재하는 사용자 ID입니다'}), 409

        # 이메일 중복 검사
        existing_email = db.supabase.table('users').select('user_id').eq('email', email).execute()
        if existing_email.data:
            return jsonify({'error': '이미 존재하는 이메일입니다'}), 409

        # 사용자 생성 데이터 준비
        user_create_data = {
            'user_id': user_id,
            'email': email,
            'password': password,
            'display_name': data.get('display_name', user_id),
            'role': role,
            'is_active': True
        }

        # database.py의 create_user 함수 사용
        try:
            result = db.create_user(user_create_data)

            if not result['success']:
                return jsonify({'error': result.get('error', '사용자 생성에 실패했습니다')}), 500

            # 응답용 사용자 정보 (비밀번호 제외)
            created_user = result['user']
            new_user = {
                'id': created_user['user_id'],
                'username': created_user['user_id'],
                'email': created_user['email'],
                'display_name': created_user['display_name'],
                'role': created_user['role'],
                'status': 'active' if created_user['is_active'] else 'inactive',
                'created_at': created_user['created_at'],
                'last_login': None
            }

        except Exception as db_error:
            return jsonify({'error': f'데이터베이스 오류: {str(db_error)}'}), 500

        return jsonify({
            'success': True,
            'message': '사용자가 성공적으로 생성되었습니다',
            'user': new_user
        })

    except Exception as e:
        return jsonify({'error': f'사용자 생성 실패: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['PUT'])
@admin_required()
def update_user(user_id):
    """사용자 정보 수정"""
    try:
        # 데이터베이스 연결 확인
        if not db.supabase:
            return jsonify({'error': '데이터베이스 연결이 필요합니다'}), 503

        data = request.get_json()

        # 업데이트할 필드들
        updatable_fields = ['email', 'display_name', 'role', 'is_active']
        update_data = {}

        for field in updatable_fields:
            if field in data:
                if field == 'status':  # status를 is_active로 변환
                    update_data['is_active'] = data[field] == 'active'
                else:
                    update_data[field] = data[field]

        if not update_data:
            return jsonify({'error': '업데이트할 데이터가 없습니다'}), 400

        # 사용자 존재 확인
        existing_user = db.supabase.table('users').select('user_id').eq('user_id', user_id).execute()
        if not existing_user.data:
            return jsonify({'error': '존재하지 않는 사용자입니다'}), 404

        # 업데이트 시간 추가
        update_data['updated_at'] = datetime.now().isoformat()

        # 사용자 정보 업데이트
        try:
            result = db.supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            if not result.data:
                return jsonify({'error': '사용자 업데이트에 실패했습니다'}), 500

            # 업데이트된 사용자 정보 조회
            updated_result = db.supabase.table('users').select('user_id, email, display_name, role, is_active, updated_at').eq('user_id', user_id).execute()

            if updated_result.data:
                user_data = updated_result.data[0]
                updated_user = {
                    'id': user_data['user_id'],
                    'username': user_data['user_id'],
                    'email': user_data['email'],
                    'display_name': user_data['display_name'],
                    'role': user_data['role'],
                    'status': 'active' if user_data['is_active'] else 'inactive',
                    'updated_at': user_data['updated_at']
                }
            else:
                return jsonify({'error': '업데이트된 사용자 정보를 조회할 수 없습니다'}), 500

        except Exception as db_error:
            return jsonify({'error': f'데이터베이스 오류: {str(db_error)}'}), 500

        return jsonify({
            'success': True,
            'message': '사용자 정보가 업데이트되었습니다',
            'user': updated_user
        })

    except Exception as e:
        return jsonify({'error': f'사용자 업데이트 실패: {str(e)}'}), 500

@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required()
def delete_user(user_id):
    """사용자 삭제"""
    try:
        # 데이터베이스 연결 확인
        if not db.supabase:
            return jsonify({'error': '데이터베이스 연결이 필요합니다'}), 503

        # 관리자 계정 삭제 방지
        if user_id == 'admin':
            return jsonify({'error': '기본 관리자 계정은 삭제할 수 없습니다'}), 400

        # 사용자 존재 확인
        existing_user = db.supabase.table('users').select('user_id, role').eq('user_id', user_id).execute()
        if not existing_user.data:
            return jsonify({'error': '존재하지 않는 사용자입니다'}), 404

        # 마지막 관리자 삭제 방지
        user_data = existing_user.data[0]
        if user_data['role'] == 'admin':
            admin_count = db.supabase.table('users').select('user_id').eq('role', 'admin').execute()
            if len(admin_count.data) <= 1:
                return jsonify({'error': '마지막 관리자 계정은 삭제할 수 없습니다'}), 400

        # 사용자 삭제
        try:
            result = db.supabase.table('users').delete().eq('user_id', user_id).execute()
            if not result.data:
                return jsonify({'error': '사용자 삭제에 실패했습니다'}), 500

        except Exception as db_error:
            return jsonify({'error': f'데이터베이스 오류: {str(db_error)}'}), 500

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

        # 시스템 설정 저장 로직 구현
        import json
        import os

        # 설정 파일 경로
        settings_file_path = os.path.join(os.path.dirname(__file__), 'system_settings.json')

        # 기본 설정 구조
        default_settings = {
            'server': {
                'port': 3000,
                'debug': False,
                'host': '0.0.0.0'
            },
            'database': {
                'backup_enabled': True,
                'backup_interval': 24
            },
            'security': {
                'session_timeout': 30,
                'max_login_attempts': 5,
                'password_min_length': 8
            },
            'logging': {
                'level': 'INFO',
                'max_file_size': '10MB',
                'retention_days': 30
            },
            'features': {
                'user_registration': True,
                'email_notifications': False,
                'auto_backup': True
            }
        }

        # 현재 설정 로드
        current_settings = default_settings.copy()
        if os.path.exists(settings_file_path):
            try:
                with open(settings_file_path, 'r', encoding='utf-8') as f:
                    stored_settings = json.load(f)
                    # 기존 설정과 병합
                    for category, settings in stored_settings.items():
                        if category in current_settings:
                            current_settings[category].update(settings)
                        else:
                            current_settings[category] = settings
            except Exception as file_error:
                print(f"설정 파일 로드 실패: {file_error}")

        # 새 설정 업데이트
        for category, settings in updated_settings.items():
            if category in current_settings:
                current_settings[category].update(settings)
            else:
                current_settings[category] = settings

        # 설정 파일에 저장
        try:
            with open(settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2, ensure_ascii=False)
        except Exception as file_error:
            return jsonify({'error': f'설정 파일 저장 실패: {str(file_error)}'}), 500

        # 데이터베이스에도 백업 저장 (Supabase 연결 시)
        if db.supabase:
            try:
                settings_record = {
                    'settings_data': current_settings,
                    'updated_at': datetime.now().isoformat(),
                    'updated_by': 'admin'  # 현재 관리자 정보
                }

                # 기존 설정이 있는지 확인
                existing_settings = db.supabase.table('system_settings').select('id').limit(1).execute()

                if existing_settings.data:
                    # 업데이트
                    db.supabase.table('system_settings').update(settings_record).eq('id', existing_settings.data[0]['id']).execute()
                else:
                    # 새로 삽입
                    db.supabase.table('system_settings').insert(settings_record).execute()

            except Exception as db_error:
                print(f"데이터베이스 설정 저장 실패: {db_error}")

        updated_settings = current_settings

        return jsonify({
            'success': True,
            'message': '설정이 업데이트되었습니다',
            'settings': updated_settings
        })

    except Exception as e:
        return jsonify({'error': f'설정 업데이트 실패: {str(e)}'}), 500

@admin_bp.route('/system/settings', methods=['GET'])
@admin_required()
def get_detailed_system_settings():
    """시스템 설정 상세 조회"""
    try:
        import json
        import os

        # 설정 파일 경로
        settings_file_path = os.path.join(os.path.dirname(__file__), 'system_settings.json')

        # 기본 설정
        default_settings = {
            'server': {
                'port': 3000,
                'debug': False,
                'host': '0.0.0.0'
            },
            'database': {
                'backup_enabled': True,
                'backup_interval': 24
            },
            'security': {
                'session_timeout': 30,
                'max_login_attempts': 5,
                'password_min_length': 8
            },
            'logging': {
                'level': 'INFO',
                'max_file_size': '10MB',
                'retention_days': 30
            },
            'features': {
                'user_registration': True,
                'email_notifications': False,
                'auto_backup': True
            }
        }

        # 저장된 설정 로드
        current_settings = default_settings.copy()
        if os.path.exists(settings_file_path):
            try:
                with open(settings_file_path, 'r', encoding='utf-8') as f:
                    stored_settings = json.load(f)
                    # 기존 설정과 병합
                    for category, settings in stored_settings.items():
                        if category in current_settings:
                            current_settings[category].update(settings)
                        else:
                            current_settings[category] = settings
            except Exception as file_error:
                print(f"설정 파일 로드 실패: {file_error}")

        return jsonify({
            'success': True,
            'settings': current_settings,
            'file_path': settings_file_path,
            'last_updated': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': f'설정 조회 실패: {str(e)}'}), 500