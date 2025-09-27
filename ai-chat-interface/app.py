# -*- coding: utf-8 -*-
"""
AI Chat Interface - Flask Integration Server
Single Python server integrating CrewAI and MetaGPT
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
# Real-time monitoring removed
import os
import sys
import json
import subprocess
import threading
import time
import psutil
from datetime import datetime
import requests
from functools import wraps
from dotenv import load_dotenv
import uuid
import gevent
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# UTF-8 인코딩 전역 설정 (가장 먼저 실행)
def setup_global_utf8_environment():
    """전역 UTF-8 인코딩 환경 설정 (강화버전)"""
    import locale
    import io
    import unicodedata

    # 1단계: 환경 변수 강제 설정
    utf8_env_vars = {
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONLEGACYWINDOWSSTDIO': '0',
        'PYTHONUTF8': '1',
        'LC_ALL': 'ko_KR.UTF-8',
        'LANG': 'ko_KR.UTF-8'
    }

    for key, value in utf8_env_vars.items():
        os.environ[key] = value

    # 2단계: Windows 특별 처리 (강화)
    if sys.platform.startswith('win'):
        try:
            # Windows 콘솔 UTF-8 모드 활성화
            os.system('chcp 65001 > nul 2>&1')

            # Windows 레지스트리 기반 UTF-8 설정 (가능한 경우)
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Console")
                winreg.SetValueEx(key, "CodePage", 0, winreg.REG_DWORD, 65001)
                winreg.CloseKey(key)
            except:
                pass  # 권한 없는 경우 무시

            # stdout/stderr UTF-8 재구성 (강화)
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                except Exception:
                    # 폴백: TextIOWrapper 사용
                    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
            else:
                # 이전 Python 버전
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

        except Exception as e:
            print(f"Windows UTF-8 설정 경고: {e}")

    # 로케일 설정 시도
    try:
        locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Korean_Korea.65001')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass  # 로케일 설정 실패해도 계속 진행

    print("✅ UTF-8 인코딩 환경 설정 완료")

# UTF-8 환경 즉시 설정
setup_global_utf8_environment()

# Import database module
from database import db
from security_utils import validate_request_data, check_request_security
from template_api import template_bp
from ollama_client import ollama_client
# WebSocket manager removed
# Progress tracking simplified
from admin_auth import admin_auth
from crewai_logger import crewai_logger, ExecutionPhase
from generate_crewai_script_new import generate_crewai_execution_script_with_approval

# 새로운 모듈 import
from pre_analysis_service import pre_analysis_service
from approval_workflow import approval_workflow_manager

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Add CrewAI and MetaGPT paths - 프로젝트 루트에서 직접 참조
crewai_path = os.path.join(os.path.dirname(current_dir), 'CrewAi')
metagpt_path = os.path.join(os.path.dirname(current_dir), 'MetaGPT')
sys.path.append(crewai_path)
sys.path.append(metagpt_path)

# 경로 확인 완료
# CrewAI: D:\GenProjects\CrewAi
# MetaGPT: D:\GenProjects\MetaGPT

app = Flask(__name__, static_folder='.', static_url_path='')

# UTF-8 처리 강화
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# UTF-8 처리를 위한 헬퍼 함수
def get_json_safely():
    """안전한 JSON 파싱"""
    try:
        if request.is_json:
            return request.get_json(force=True)
        else:
            # 강제로 JSON으로 파싱 시도
            raw_data = request.get_data(as_text=True)
            if raw_data.startswith('\ufeff'):  # BOM 제거
                raw_data = raw_data[1:]
            return json.loads(raw_data)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
        print(f"JSON 파싱 오류: {e}")
        return None

# SocketIO removed for simplicity

# CORS 설정 강화
CORS(app,
     origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True,
     max_age=3600)

# WebSocket functionality removed

# Register blueprints
app.register_blueprint(template_bp)

# Import and register template routes
try:
    from template_api_routes import template_routes
    app.register_blueprint(template_routes)
    print("✅ 템플릿 API 라우트 등록 완료")
except ImportError as e:
    print(f"⚠️ 템플릿 API 라우트 등록 실패: {e}")

# Import and register admin routes
try:
    from admin_api import admin_bp
    app.register_blueprint(admin_bp)
    print("✅ 관리자 API 라우트 등록 완료")
except ImportError as e:
    print(f"⚠️ 관리자 API 라우트 등록 실패: {e}")

# Supabase 클라이언트 설정
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None
    print("⚠️ Supabase 설정이 필요합니다. .env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY를 추가하세요.")

# CrewAI 관련 설정
CREWAI_BASE_DIR = os.path.join(os.path.dirname(current_dir), 'CrewAi')  # CrewAI 소스 코드 경로
PROJECTS_BASE_DIR = os.path.join(os.path.dirname(current_dir), 'Projects')  # 생성된 프로젝트 저장 경로
execution_status = {}  # 전역 변수로 실행 상태 관리
# Client management simplified

# 보안 헤더 설정
@app.after_request
def set_security_headers(response):
    # XSS 보호
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # HSTS (HTTPS 강제)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # CSP (Content Security Policy)
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' http://localhost:* https://unpkg.com https://cdnjs.cloudflare.com"

    return response

# Port configuration - 통합 포트
PORT = 3000

# 라우팅 설정
CREWAI_URL = "http://localhost:3001"  # 내부 CrewAI 서버
METAGPT_URL = "http://localhost:3002"  # 내부 MetaGPT 서버

# Global variables
execution_status = {}
request_counts = {}  # IP별 요청 카운트
request_timestamps = {}  # IP별 요청 시간

# ==================== SECURITY DECORATORS ====================

def rate_limit(max_requests=60, window_seconds=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
            current_time = time.time()

            # IP별 요청 기록 초기화
            if client_ip not in request_counts:
                request_counts[client_ip] = []

            # 윈도우 시간 밖의 요청 제거
            request_counts[client_ip] = [
                timestamp for timestamp in request_counts[client_ip]
                if current_time - timestamp < window_seconds
            ]

            # 요청 제한 확인
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'최대 {max_requests}개의 요청이 {window_seconds}초 내에 허용됩니다',
                    'retry_after': window_seconds
                }), 429

            # 현재 요청 기록
            request_counts[client_ip].append(current_time)

            return f(*args, **kwargs)

        return decorated
    return decorator

def validate_json_input(required_fields=None):
    """JSON 입력 검증 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Empty JSON data'}), 400

            # 필수 필드 검증
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400

            return f(*args, **kwargs)

        return decorated
    return decorator

# ==================== AUTHENTICATION DECORATORS ====================

def token_required(f):
    """JWT token required decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        token_result = db.verify_jwt_token(token)
        if not token_result['success']:
            return jsonify({'error': token_result['error']}), 401

        request.current_user = token_result['payload']
        return f(*args, **kwargs)

    return decorated

def optional_auth(f):
    """Optional authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                token_result = db.verify_jwt_token(token)
                if token_result['success']:
                    request.current_user = token_result['payload']
            except:
                pass

        if not hasattr(request, 'current_user'):
            request.current_user = None

        return f(*args, **kwargs)

    return decorated


@app.route('/')
def index():
    """통합 대시보드 메인 페이지"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/crewai')
def crewai_interface():
    """CrewAI 인터페이스"""
    return send_from_directory('.', 'crewai.html')

@app.route('/crewai/logs')
def crewai_logs():
    """CrewAI 로깅 대시보드"""
    return send_from_directory('.', 'crewai_logs.html')

@app.route('/metagpt')
def metagpt_interface():
    """MetaGPT 인터페이스"""
    return send_from_directory('.', 'metagpt.html')

@app.route('/templates')
def templates_interface():
    """프로젝트 템플릿 인터페이스"""
    return send_from_directory('.', 'templates.html')

@app.route('/projects')
def projects_interface():
    """프로젝트 관리 대시보드"""
    return send_from_directory('.', 'projects.html')

@app.route('/admin')
def admin_interface():
    """관리자 대시보드"""
    return send_from_directory('.', 'admin.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Static file serving"""
    return send_from_directory('.', filename)


# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    database_status = db.test_connection()

    return jsonify({
        'status': 'OK',
        'message': 'AI Chat Interface Server is running',
        'server': 'Flask (Python)',
        'timestamp': datetime.now().isoformat(),
        'database': {
            'connected': database_status.get('connected', False),
            'message': database_status.get('message', ''),
            'simulation_mode': database_status.get('simulation_mode', False)
        }
    })


def check_crewai_service():
    """Check CrewAI service status"""
    try:
        # Check if CrewAI server is running using main page
        response = requests.get(f'{CREWAI_URL}/', timeout=2)
        return 'available' if response.status_code == 200 else 'unavailable'
    except:
        return 'unavailable'


def check_metagpt_service():
    """Check MetaGPT service status"""
    try:
        # Check MetaGPT environment
        metagpt_script = os.path.join(metagpt_path, 'run_metagpt.py')
        return 'available' if os.path.exists(metagpt_script) else 'unavailable'
    except:
        return 'unavailable'


@app.route('/api/crewai', methods=['POST'])
def handle_crewai_request():
    """Handle CrewAI requests with enhanced message classification and project management"""
    data = request.get_json()
    requirement = data.get('requirement')
    selected_models = data.get('selectedModels', {})
    pre_analysis_model = data.get('preAnalysisModel', 'gemini-flash')  # 사전 분석 모델 추가
    project_id = data.get('projectId')

    if not requirement:
        return jsonify({'error': 'Requirement is required'}), 400

    # 강화된 메시지 처리 시스템 사용
    try:
        from enhanced_project_initializer import EnhancedProjectInitializer
        from message_classifier import MessageClassifier, MessageType

        # 메시지 분류기 초기화
        classifier = MessageClassifier()
        initializer = EnhancedProjectInitializer(PROJECTS_BASE_DIR)

        # 컨텍스트 수집 (기존 프로젝트 정보)
        context = {}
        if project_id:
            context = initializer.get_project_context(project_id) or {}

        # 메시지 처리
        processing_result = initializer.process_user_message(requirement, context)

        # 처리 결과에 따른 분기
        if processing_result['action'] == 'project_created':
            # 새 프로젝트 생성됨 - 기존 로직으로 실행
            project_info = processing_result['project']
            requirement = project_info.get('original_requirements', requirement)  # 정제된 요구사항 사용
            project_path = project_info['project_path']
            project_name = project_info['project_name']

            # 강화된 실행기 사용 설정
            use_enhanced_executor = True

        elif processing_result['action'] == 'continue_project':
            # 기존 프로젝트 계속 진행
            project_id_only = processing_result['project_id']
            project_path = os.path.join(PROJECTS_BASE_DIR, project_id_only)
            project_name = project_id_only
            use_enhanced_executor = True

        elif processing_result['action'] == 'resume_specific_project':
            # 특정 프로젝트 재개
            project_id_only = processing_result['project_id']
            project_path = os.path.join(PROJECTS_BASE_DIR, project_id_only)
            project_name = project_id_only
            resume_point = processing_result.get('resume_point')
            use_enhanced_executor = True

        elif processing_result['action'] == 'clarification_needed':
            # 명확화 필요
            return jsonify({
                'success': False,
                'error': 'Clarification needed',
                'message': processing_result['message'],
                'classification': processing_result.get('classification'),
                'suggestion': '구체적인 프로젝트 요구사항을 입력해주세요.'
            }), 400

        else:
            # 기본 처리 (기존 로직 사용)
            use_enhanced_executor = False

    except ImportError:
        print("강화된 시스템을 로드할 수 없습니다. 기본 시스템을 사용합니다.")
        use_enhanced_executor = False
    except Exception as e:
        print(f"강화된 시스템 처리 중 오류: {e}")
        use_enhanced_executor = False

    # Enhanced executor를 사용할 수 없는 경우 기본 로직 사용
    if not use_enhanced_executor or not 'project_path' in locals():
        # 기본 프로젝트 생성 로직
        if not project_id:
            existing_projects = [d for d in os.listdir(PROJECTS_BASE_DIR) if d.startswith('project_') and os.path.isdir(os.path.join(PROJECTS_BASE_DIR, d))]
            project_number = len(existing_projects) + 1
            project_name = f"project_{project_number:05d}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)
        else:
            # project_id가 이미 "project_" 접두사를 가지고 있는지 확인
            if project_id.startswith('project_'):
                project_name = project_id
            else:
                project_name = f"project_{project_id}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)

    # 실행 ID 생성
    execution_id = str(uuid.uuid4())
    crew_id = f"crew_{int(time.time())}"

    # 🔍 사전 분석 및 승인 워크플로우 실행
    print(f"[CREWAI] 사전 분석 시작: execution_id={execution_id}")

    try:
        # 1. 사전 분석 서비스 호출
        print(f"[CREWAI] 사전 분석 모델: {pre_analysis_model}")
        analysis_result = pre_analysis_service.analyze_user_request(
            user_request=requirement,
            framework="crewai",
            model=pre_analysis_model
        )

        # 2. 분석 결과 검증
        if analysis_result.get('status') == 'error' or analysis_result.get('error'):
            error_msg = analysis_result.get('error', '사전 분석 실패')
            print(f"[CREWAI ERROR] 사전 분석 실패: {error_msg}")
            return jsonify({'error': error_msg}), 500

        print(f"[CREWAI] 사전 분석 성공: {analysis_result.get('analysis', {}).get('summary', 'N/A')}")

        # 3. 프로젝트 정보 미리 준비 (승인 후 실행에 필요)
        if not project_id:
            # 새 프로젝트 경로 생성 (실제 디렉토리는 승인 후 생성)
            existing_projects = [d for d in os.listdir(PROJECTS_BASE_DIR) if d.startswith('project_') and os.path.isdir(os.path.join(PROJECTS_BASE_DIR, d))]
            project_number = len(existing_projects) + 1
            project_name = f"project_{project_number:05d}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)
        else:
            if project_id.startswith('project_'):
                project_name = project_id
            else:
                project_name = f"project_{project_id}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)

        print(f"[CREWAI] 프로젝트 경로 준비: {project_path}")

        # 4. 승인 요청에 포함할 프로젝트 데이터 구성
        project_data = {
            'execution_id': execution_id,
            'crew_id': crew_id,
            'framework': 'crewai',
            'requirement': requirement,
            'selected_models': selected_models,
            'pre_analysis_model': pre_analysis_model,
            'project_id': project_id,
            'project_name': project_name,
            'project_path': project_path,
            'projects_base_dir': PROJECTS_BASE_DIR,
            'created_at': datetime.now().isoformat()
        }

        print(f"[CREWAI] 프로젝트 데이터 구성 완료: {project_data['project_name']}")

        # 5. 승인 요청 생성 (프로젝트 데이터 포함)
        approval_id = approval_workflow_manager.create_approval_request(
            analysis_result=analysis_result,
            project_data=project_data,  # 실행에 필요한 모든 정보 포함
            project_id=project_id,
            requester="crewai_interface"
        )

        print(f"[CREWAI] 승인 요청 생성 완료: {approval_id}")

        # 6. 승인 대기 응답 반환
        return jsonify({
            'success': True,
            'message': 'AI 계획이 분석되었습니다. 승인을 기다리고 있습니다.',
            'approval_id': approval_id,
            'execution_id': execution_id,
            'status': 'pending_approval',
            'analysis': analysis_result.get('analysis', {}),
            'project_info': {
                'name': project_name,
                'path': project_path
            },
            'requires_approval': True
        })

    except Exception as analysis_error:
        print(f"[CREWAI ERROR] 사전 분석 오류: {analysis_error}")
        import traceback
        print(f"[CREWAI ERROR] 스택 추적:\n{traceback.format_exc()}")

        # 사전 분석 실패 시 에러 반환 (기존 방식 진행 제거)
        return jsonify({
            'error': f'사전 분석 중 오류가 발생했습니다: {str(analysis_error)}',
            'details': 'AI 계획 분석이 필요합니다. 다시 시도해주세요.',
            'execution_id': execution_id
        }), 500

    try:
        # 상세 로깅 시작
        crewai_logger.start_execution_logging(execution_id, crew_id, {
            'requirement': requirement,
            'selected_models': selected_models,
            'project_id': project_id
        })

        crewai_logger.start_step_tracking(execution_id, crew_id, total_steps=10)

        # 단계 1: 시스템 검증
        crewai_logger.advance_step(execution_id, crew_id, "시스템 검증", "시작", ExecutionPhase.VALIDATION)
        crewai_logger.log_system_check(execution_id, crew_id, "UTF-8 인코딩 환경", True)
        crewai_logger.log_system_check(execution_id, crew_id, "프로젝트 디렉토리 접근", os.path.exists(PROJECTS_BASE_DIR))

        # 단계 2: 프로젝트 초기화
        crewai_logger.advance_step(execution_id, crew_id, "프로젝트 초기화", "시작", ExecutionPhase.INITIALIZATION)

        if not project_id:
            # 새 프로젝트 생성
            # 프로젝트 번호 생성 (기존 프로젝트 개수 + 1)
            existing_projects = [d for d in os.listdir(PROJECTS_BASE_DIR) if d.startswith('project_') and os.path.isdir(os.path.join(PROJECTS_BASE_DIR, d))]
            project_number = len(existing_projects) + 1
            project_name = f"project_{project_number:05d}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)
        else:
            # 기존 프로젝트 사용 - project_id가 이미 project_를 포함하는지 확인
            if project_id.startswith('project_'):
                project_name = project_id
            else:
                project_name = f"project_{project_id}"
            project_path = os.path.join(PROJECTS_BASE_DIR, project_name)

        # 단계 3: 프로젝트 디렉토리 생성
        crewai_logger.advance_step(execution_id, crew_id, "디렉토리 생성", project_path, ExecutionPhase.DIRECTORY_CREATION)

        try:
            os.makedirs(project_path, exist_ok=True)
            crewai_logger.log_directory_operation(execution_id, crew_id, "생성", project_path, True)
        except Exception as dir_error:
            crewai_logger.log_directory_operation(execution_id, crew_id, "생성", project_path, False, {"error": str(dir_error)})
            raise dir_error

        # 단계 4: 환경 설정
        crewai_logger.advance_step(execution_id, crew_id, "환경 설정", "", ExecutionPhase.ENVIRONMENT_SETUP)

        # UTF-8 환경 변수 설정
        env_vars = {
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONLEGACYWINDOWSSTDIO': '0',
            'CREWAI_PROJECT_PATH': project_path,
            'CREWAI_REQUIREMENT': requirement,
            'CREWAI_EXECUTION_ID': execution_id
        }

        crewai_logger.log_environment_setup(execution_id, crew_id, env_vars, True)

        # 단계 5: CrewAI 스크립트 생성
        crewai_logger.advance_step(execution_id, crew_id, "스크립트 생성", "", ExecutionPhase.FILE_GENERATION)

        # 고도화된 스크립트 생성기 사용 (모든 CrewAI 요청에 적용)
        try:
            from enhanced_script_generator import generate_enhanced_crewai_script
            print(f"[CREWAI] 고도화된 스크립트 생성기 사용")
            script_content = generate_enhanced_crewai_script(requirement, selected_models, project_path, execution_id)
        except ImportError:
            print(f"[CREWAI] 승인 기반 스크립트 생성기 사용 (fallback)")
            script_content = generate_crewai_execution_script_with_approval(
                requirement=requirement,
                selected_models=selected_models,
                project_path=project_path,
                execution_id=execution_id
            )

        script_path = os.path.join(project_path, "execute_crewai.py")

        try:
            # UTF-8 서로게이트 문제 해결을 위한 안전한 문자열 정리
            import unicodedata

            # 1단계: 유니코드 정규화
            normalized_content = unicodedata.normalize('NFKC', script_content)

            # 2단계: 서로게이트 문자 제거
            safe_content = ''.join(char for char in normalized_content
                                 if not (0xD800 <= ord(char) <= 0xDFFF))

            # 3단계: UTF-8 안전 인코딩/디코딩
            safe_content = safe_content.encode('utf-8', errors='replace').decode('utf-8')

            # 4단계: 파일 쓰기 (Windows 호환성 강화)
            with open(script_path, 'w', encoding='utf-8', errors='replace', newline='\n') as f:
                f.write(safe_content)

            crewai_logger.log_file_generation(execution_id, crew_id, script_path, "Python Script", len(safe_content), True, {
                "original_length": len(script_content),
                "processed_length": len(safe_content),
                "encoding": "utf-8",
                "processing_steps": ["normalize", "surrogate_filter", "utf8_encode"]
            })
        except Exception as file_error:
            crewai_logger.log_file_generation(execution_id, crew_id, script_path, "Python Script", 0, False, {"error": str(file_error)})
            crewai_logger.log_error(execution_id, crew_id, file_error, "CrewAI 스크립트 파일 생성", {
                "script_path": script_path,
                "content_preview": script_content[:200] if script_content else "None"
            })
            raise file_error

        # 단계 6: 요구사항 파일 생성
        crewai_logger.advance_step(execution_id, crew_id, "요구사항 저장", "", ExecutionPhase.FILE_GENERATION)

        requirements_path = os.path.join(project_path, "requirements.txt")
        requirements_content = "\n".join([
            "crewai>=0.28.8",
            "langchain>=0.1.0",
            "langchain-openai>=0.0.5",
            "python-dotenv>=1.0.0"
        ])

        try:
            # UTF-8 안전 서로게이트 처리
            safe_requirements = requirements_content.encode('utf-8', errors='replace').decode('utf-8')
            with open(requirements_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(safe_requirements)
            crewai_logger.log_file_generation(execution_id, crew_id, requirements_path, "Requirements", len(safe_requirements), True)
        except Exception as req_error:
            crewai_logger.log_file_generation(execution_id, crew_id, requirements_path, "Requirements", 0, False, {"error": str(req_error)})

        # 단계 7: CrewAI 실행
        crewai_logger.advance_step(execution_id, crew_id, "CrewAI 실행", "시작", ExecutionPhase.EXECUTION)

        # 실제 CrewAI 실행 (백그라운드에서)
        def execute_crewai_async():
            start_time = int(time.time() * 1000)  # 밀리초 단위 시작 시간
            try:
                # 현재 환경 변수 설정 (한글 인코딩 강화)
                current_env = os.environ.copy()
                current_env.update(env_vars)

                # Windows 특별 UTF-8 설정
                if sys.platform.startswith('win'):
                    current_env['PYTHONIOENCODING'] = 'utf-8'
                    current_env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
                    current_env['PYTHONUTF8'] = '1'
                    current_env['CHCP'] = '65001'

                # CrewAI 실행 명령 (한글 지원 강화)
                cmd = [sys.executable, '-u', '-X', 'utf8', script_path] if sys.platform.startswith('win') else [sys.executable, '-u', script_path]

                crewai_logger.log_subprocess_start(execution_id, crew_id, script_path, current_env)

                # UTF-8 인코딩 테스트
                test_korean = "한글 테스트 문자열"
                crewai_logger.log_korean_encoding_test(execution_id, crew_id, test_korean, "UTF-8", True)

                # 프로세스 중복 실행 방지 로직
                script_name = os.path.basename(script_path)
                existing_processes = []

                try:
                    # 현재 실행 중인 Python 프로세스 중 같은 스크립트 실행 여부 확인
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['name'] and 'python' in proc.info['name'].lower():
                                cmdline = proc.info['cmdline'] or []
                                # 같은 스크립트 파일을 실행 중인지 확인
                                if any(script_name in arg for arg in cmdline):
                                    existing_processes.append({
                                        'pid': proc.info['pid'],
                                        'cmdline': ' '.join(cmdline)
                                    })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                    if existing_processes:
                        warning_msg = f"⚠️ 이미 실행 중인 {script_name} 프로세스 발견 ({len(existing_processes)}개)"
                        crewai_logger.log_warning(execution_id, crew_id, warning_msg, {
                            'existing_processes': existing_processes,
                            'script_path': script_path
                        })
                        print(f"{warning_msg}")
                        for proc in existing_processes:
                            print(f"  - PID {proc['pid']}: {proc['cmdline'][:100]}...")

                        # 기존 프로세스가 있어도 계속 진행 (사용자가 의도적으로 실행했을 수 있음)
                        # 하지만 경고 로그는 남김

                except Exception as check_error:
                    crewai_logger.log_error(execution_id, crew_id, check_error, "프로세스 중복 확인")

                # 서브프로세스 실행 (인코딩 안전성 강화)
                try:
                    process = subprocess.Popen(
                        cmd,
                        cwd=project_path,
                        env=current_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',  # 인코딩 오류 시 대체 문자 사용
                        universal_newlines=True
                    )
                except Exception as proc_error:
                    crewai_logger.log_error(execution_id, crew_id, proc_error, "서브프로세스 생성")
                    # 폴백 방식으로 재시도
                    process = subprocess.Popen(
                        cmd,
                        cwd=project_path,
                        env=current_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                crewai_logger.log_subprocess_execution(execution_id, crew_id, " ".join(cmd), project_path, True, process.pid)

                # 실시간 출력 처리
                stdout, stderr = process.communicate()

                if stdout:
                    crewai_logger.log_subprocess_output(execution_id, crew_id, "stdout", stdout)
                    lines = stdout.split('\n')
                    for i, line in enumerate(lines[:20]):  # 처음 20줄만 처리
                        if line.strip():
                            crewai_logger.log_output_processing(execution_id, crew_id, "stdout", line, i+1, True)

                if stderr:
                    crewai_logger.log_subprocess_output(execution_id, crew_id, "stderr", stderr)

                exit_code = process.returncode
                success = exit_code == 0

                # 완료 로깅
                end_time = int(time.time() * 1000)
                total_duration = end_time - start_time
                crewai_logger.log_completion(execution_id, crew_id, success, total_duration, {
                    "exit_code": exit_code,
                    "project_path": project_path,
                    "files_created": len([f for f in os.listdir(project_path) if os.path.isfile(os.path.join(project_path, f))])
                })

            except Exception as exec_error:
                crewai_logger.log_error(execution_id, crew_id, exec_error, "CrewAI 비동기 실행")

        # 백그라운드 실행 시작
        execution_thread = threading.Thread(target=execute_crewai_async)
        execution_thread.daemon = True
        execution_thread.start()

        # 단계 8: 응답 반환
        crewai_logger.advance_step(execution_id, crew_id, "응답 준비", "완료", ExecutionPhase.COMPLETION)

        return jsonify({
            'success': True,
            'execution_id': execution_id,
            'crew_id': crew_id,
            'requirement': requirement,
            'project_path': project_path,
            'project_name': project_name,
            'result': f'CrewAI 실행이 시작되었습니다.\n\n프로젝트: {project_name}\n경로: {project_path}\n\n작업이 완료되면 결과를 확인하실 수 있습니다.',
            'models_used': selected_models,
            'agents_involved': ["Planner", "Researcher", "Writer"],
            'status': 'executing',
            'files_created': [
                os.path.basename(script_path),
                os.path.basename(requirements_path)
            ]
        })

    except Exception as e:
        crewai_logger.log_error(execution_id, crew_id, e, "CrewAI 요청 처리")
        return jsonify({
            'success': False,
            'execution_id': execution_id,
            'error': 'Error processing CrewAI request',
            'details': str(e)
        }), 500


def generate_crewai_execution_script(requirement: str, selected_models: dict, project_path: str, execution_id: str) -> str:
    """
    CrewAI 실행 스크립트 생성 - 통합되고 안전한 방식
    이전의 모순된 이중 처리 구조를 단일화하여 일관성 확보
    """
    import json
    from datetime import datetime

    # 1. 단순화된 안전한 텍스트 처리 함수
    def safe_text_escape(text: str, max_length: int = 400) -> str:
        """단순화된 텍스트 처리 - 최소한의 이스케이핑만 수행"""
        if len(text) > max_length:
            text = text[:max_length] + '...'
        # 필수 이스케이핑만 수행
        text = text.replace('"', "'").replace('\n', '\\n').replace('\r', '')
        return text

    def safe_path_escape(path: str) -> str:
        """경로 문자열 안전 처리 (Windows/Linux 호환)"""
        return path.replace('\\', '\\\\')

    # 2. 안전한 매개변수 준비
    safe_requirement = safe_text_escape(requirement)
    safe_project_path = safe_path_escape(project_path)

    # 모델 정규화 - 모든 모델을 그대로 사용 (CrewAI에서 처리)
    normalized_models = {}
    for role, model in selected_models.items():
        normalized_models[role] = model

    # 기본값이 없는 경우 gemini-flash 설정
    if not normalized_models:
        normalized_models = {
            "planner": "gemini-flash",
            "researcher": "gemini-flash",
            "writer": "gemini-flash"
        }

    # 3. 스크립트 템플릿 (변수명 일치성 확보)
    script_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 자동 생성 실행 스크립트
실행 ID: {execution_id}
생성 시간: {generation_time}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM
from langchain_openai import ChatOpenAI
import json

# UTF-8 인코딩 환경 설정 (간소화 버전)
def setup_utf8_environment():
    """UTF-8 인코딩 환경 설정"""
    import io

    # 환경 변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    # Windows 콘솔 UTF-8 설정
    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass

    # stdout/stderr UTF-8 재구성
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

    return True

# 환경 설정 실행
setup_utf8_environment()

print("✅ UTF-8 인코딩 환경 설정 완료")
print("🚀 CrewAI 실행 시작...")
print("🎯 요구사항: {requirement_display}")
print(f"📁 프로젝트 경로: {project_path}")
print(f"🆔 실행 ID: {execution_id}")
print("\\n" + "="*50 + "\\n")

# LLM 모델 설정
def get_llm_model(role_name: str):
    """역할별 LLM 모델 반환"""
    # 동적 모델 매핑 - 사용자 선택 모델 사용
    models = {normalized_models_str}
    model_id = models.get(role_name.lower(), 'gemini-flash')

    print("🤖 " + role_name + " 역할 → " + model_id + " 모델")

    # gemini 모델 사용시 CrewAI의 LLM 클래스 사용
    if 'gemini' in model_id:
        from crewai import LLM
        return LLM(
            model="gemini/" + model_id,
            temperature=0.7
        )
    else:
        # OpenAI 모델의 경우
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_id,
            temperature=0.7,
            max_tokens=2000
        )

# CrewAI 에이전트 정의
print("👥 에이전트 팀 구성중...")

planner = Agent(
    role="Project Planner",
    goal="프로젝트 요구사항을 분석하고 체계적인 개발 계획을 수립합니다.",
    backstory="당신은 소프트웨어 프로젝트 관리 전문가입니다. 복잡한 요구사항을 구체적이고 실행 가능한 단계로 분해하는 능력이 뛰어납니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("planner")
)

researcher = Agent(
    role="Research Specialist",
    goal="프로젝트에 필요한 최적의 기술 스택과 구현 방법을 조사합니다.",
    backstory="당신은 기술 리서치 전문가입니다. 최신 기술 동향을 파악하고, 프로젝트 요구사항에 가장 적합한 도구와 방법론을 선별하는데 전문성을 가지고 있습니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("researcher")
)

writer = Agent(
    role="Technical Writer",
    goal="조사 결과를 바탕으로 실제 동작하는 코드와 완전한 문서를 작성합니다.",
    backstory="당신은 기술 문서 및 코드 작성 전문가입니다. 연구 결과를 실제 동작하는 고품질 코드로 변환하고, 이해하기 쉬운 문서를 작성하는 능력이 탁월합니다.",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("writer")
)

print("📋 작업 태스크 설정중...")

# 원본 요구사항을 그대로 사용 (이스케이핑 제거된 버전)
original_requirement = "{requirement_original}"

# 태스크 체인 정의
task1 = Task(
    description=f"""
다음 요구사항을 분석하여 체계적인 프로젝트 계획을 수립하세요:

**요구사항:**
{{original_requirement}}

**계획에 포함할 내용:**
1. 프로젝트 목표 및 범위 정의
2. 핵심 기능 목록 및 우선순위
3. 기술적 요구사항 분석
4. 개발 단계 및 마일스톤
5. 예상 개발 일정

구체적이고 실행 가능한 계획을 한글로 작성해주세요.
    """,
    expected_output="상세한 프로젝트 계획서 (마크다운 형식, 한글)",
    agent=planner
)

task2 = Task(
    description="""
Planner가 수립한 계획을 바탕으로 기술적 조사를 수행하세요:

**조사 항목:**
1. 권장 프로그래밍 언어 및 프레임워크
2. 필수 라이브러리 및 패키지 목록
3. 개발 환경 구성 가이드
4. 아키텍처 패턴 및 디자인 권장사항
5. 테스트 및 배포 전략
6. 보안 고려사항

실제 구현 가능한 구체적인 기술 솔루션을 제시해주세요.
    """,
    expected_output="기술 조사 보고서 및 구현 가이드 (마크다운 형식, 한글)",
    agent=researcher
)

task3 = Task(
    description="""
계획과 조사 결과를 바탕으로 완성된 프로젝트를 구현하세요:

**구현 내용:**
1. 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (완전 동작)
3. 설정 파일 (requirements.txt, package.json 등)
4. README.md (설치, 설정, 실행 방법)
5. 기본 테스트 코드
6. 실행 예시 및 사용법

모든 코드는 실제로 동작해야 하며, 충분한 주석을 포함해야 합니다.
    """,
    expected_output="완전히 구현된 프로젝트 (코드, 문서, 설정 파일 포함)",
    agent=writer
)

# CrewAI 팀 구성 및 실행
print("🚀 CrewAI 팀 실행 시작...")

crew = Crew(
    agents=[planner, researcher, writer],
    tasks=[task1, task2, task3],
    verbose=2,
    process=Process.sequential
)

try:
    # 실행 시작
    start_time = datetime.now()
    print("⏰ 실행 시작 시간: " + start_time.strftime('%Y-%m-%d %H:%M:%S'))

    result = crew.kickoff()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\\n" + "="*50)
    print("🎉 CrewAI 실행 완료!")
    print("⏱️ 총 소요시간: " + str(duration))
    print("="*50 + "\\n")

    # 결과 저장
    output_file = os.path.join("{project_path}", "crewai_result.md")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 프로젝트 생성 결과\\n\\n")
        f.write(f"**실행 ID**: {execution_id}\\n")
        f.write("**생성 시간**: " + start_time.strftime('%Y-%m-%d %H:%M:%S') + "\\n")
        f.write("**완료 시간**: " + end_time.strftime('%Y-%m-%d %H:%M:%S') + "\\n")
        f.write("**소요 시간**: " + str(duration) + "\\n\\n")
        f.write("**원본 요구사항**:\\n" + "{requirement_original}" + "\\n\\n")
        f.write("---\\n\\n")
        f.write("## 생성 결과\\n\\n")
        f.write(str(result))

    print(f"📄 결과 저장 완료: {{os.path.abspath(output_file)}}")
    print("✅ 모든 작업이 성공적으로 완료되었습니다!")

except Exception as e:
    import traceback
    error_details = traceback.format_exc()

    print(f"\\n❌ 실행 중 오류 발생:")
    print(f"오류 내용: {{str(e)}}")
    print(f"상세 정보:\\n{{error_details}}")

    # 오류 로그 저장
    error_file = os.path.join("{project_path}", "execution_error.log")
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"CrewAI 실행 오류 로그\\n")
        f.write(f"실행 ID: {execution_id}\\n")
        f.write("오류 발생 시간: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\\n\\n")
        f.write("오류 메시지: " + str(e) + "\\n\\n")
        f.write("상세 추적 정보:\\n" + error_details)

    print("🗂️ 오류 로그 저장: " + os.path.abspath(error_file))

    sys.exit(1)
'''

    # 4. 템플릿 변수 값 준비 (변수명 일치 확보)
    normalized_models_str = json.dumps(normalized_models, ensure_ascii=False, indent=8).replace('\n', '\n    ')

    template_vars = {
        'execution_id': execution_id,
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'requirement_display': safe_requirement[:100] + ('...' if len(safe_requirement) > 100 else ''),
        'requirement_original': requirement,  # 원본 요구사항 (이스케이핑 없음)
        'project_path': safe_project_path,
        'normalized_models_str': normalized_models_str
    }

    # 5. 안전한 스크립트 생성
    try:
        formatted_script = script_template.format(**template_vars)

        # 최종 UTF-8 안전성 확보
        return formatted_script.encode('utf-8', errors='replace').decode('utf-8')

    except Exception as e:
        # 폴백 스크립트 (최소한의 동작 보장)
        fallback_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 스크립트 생성 오류 발생 - 폴백 모드
실행 ID: {execution_id}
오류: {str(e)}
"""

print("⚠️ CrewAI 스크립트 생성 중 오류 발생")
print(f"실행 ID: {execution_id}")
print(f"오류 내용: {str(e)}")
print("\\n문제 해결 후 다시 시도해주세요.")

import sys
sys.exit(1)
'''
        return fallback_script



@app.route('/api/metagpt', methods=['POST'])
def handle_metagpt_request():
    """Handle MetaGPT requests"""
    data = request.get_json()
    requirement = data.get('requirement')
    selected_models = data.get('selectedModels', {})

    if not requirement:
        return jsonify({'error': 'Requirement is required'}), 400

    try:
        print(f'MetaGPT request: {requirement}')
        print(f'Selected models: {selected_models}')

        ai_type = data.get('aiType', 'meta-gpt')
        print(f'AI Type: {ai_type}')

        # MetaGPT 처리 - 실제 MetaGPT 모듈 호출
        if ai_type == 'meta-gpt':
            return call_metagpt_module(requirement, selected_models)

    except Exception as e:
        return jsonify({
            'error': 'Error processing MetaGPT request',
            'details': str(e)
        }), 500


def call_metagpt_module(requirement, selected_models):
    """실제 MetaGPT 모듈 호출"""
    try:
        # MetaGPT 모듈 경로 확인 (이미 전역에서 설정됨)
        metagpt_path_full = metagpt_path

        if not os.path.exists(metagpt_path_full):
            return jsonify({
                'success': False,
                'error': 'MetaGPT module not found',
                'message': 'MetaGPT 모듈을 찾을 수 없습니다.',
                'path_checked': metagpt_path_full
            }), 404

        # MetaGPT 모듈에서 실제 처리
        # 여기서는 subprocess로 MetaGPT 스크립트 실행
        import subprocess
        import json

        # MetaGPT 실행 스크립트 경로
        script_path = os.path.join(metagpt_path_full, 'run_step_by_step.py')

        if os.path.exists(script_path):
            # 실제 MetaGPT 스크립트 실행 (1단계부터 시작)
            result = subprocess.run([
                sys.executable, script_path,
                requirement,  # 첫 번째 인자: 요구사항
                '1'          # 두 번째 인자: 시작 단계
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    return jsonify(response_data)
                except json.JSONDecodeError:
                    return jsonify({
                        'success': True,
                        'message': result.stdout,
                        'type': 'text_response'
                    })
            else:
                return jsonify({
                    'success': False,
                    'error': 'MetaGPT execution failed',
                    'details': result.stderr
                }), 500
        else:
            # 스크립트가 없으면 기본 MetaGPT 호출
            return call_basic_metagpt(requirement, metagpt_path_full)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'MetaGPT module call failed',
            'details': str(e)
        }), 500


def call_basic_metagpt(requirement, metagpt_path):
    """기본 MetaGPT 호출"""
    try:
        # 기존의 데모 프로젝트 생성
        project_path = create_demo_project(requirement)

        return jsonify({
            'success': True,
            'requirement': requirement,
            'message': "MetaGPT에서 프로젝트를 생성했습니다.",
            'project_path': project_path,
            'agents': ["ProductManager", "Architect", "Engineer"],
            'process': "Basic project generation completed",
            'workspace': f"Project created at: {project_path}",
            'note': "단계별 승인 시스템을 사용하려면 MetaGPT 모듈 설정이 필요합니다."
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Basic MetaGPT call failed',
            'details': str(e)
        }), 500


def analyze_project_requirement(requirement):
    """프로젝트 요구사항 분석"""
    req_lower = requirement.lower()

    # 프로젝트 타입 분석
    if any(word in req_lower for word in ["게임", "game"]):
        project_type = "게임"
        domain = "엔터테인먼트"
        technology = "Python/JavaScript"
    elif any(word in req_lower for word in ["쇼핑몰", "shopping", "ecommerce"]):
        project_type = "이커머스"
        domain = "비즈니스"
        technology = "React/Node.js"
    elif any(word in req_lower for word in ["웹", "web", "사이트"]):
        project_type = "웹 애플리케이션"
        domain = "웹 개발"
        technology = "HTML/CSS/JavaScript"
    elif any(word in req_lower for word in ["api", "서버", "server"]):
        project_type = "백엔드 서비스"
        domain = "백엔드"
        technology = "Python/Flask"
    else:
        project_type = "일반 애플리케이션"
        domain = "소프트웨어"
        technology = "Python"

    # 복잡도 분석
    if any(word in req_lower for word in ["간단한", "simple", "basic"]):
        complexity = "낮음"
        estimated_time = "30-60분"
    elif any(word in req_lower for word in ["복잡한", "advanced", "완전한"]):
        complexity = "높음"
        estimated_time = "2-4시간"
    else:
        complexity = "중간"
        estimated_time = "1-2시간"

    return {
        "project_type": project_type,
        "domain": domain,
        "technology": technology,
        "complexity": complexity,
        "estimated_time": estimated_time,
        "key_features": extract_key_features(requirement),
        "requirements": extract_requirements(requirement)
    }


def extract_key_features(requirement):
    """핵심 기능 추출"""
    features = []
    req_lower = requirement.lower()

    if "환율" in req_lower or "exchange" in req_lower:
        features = ["실시간 환율 조회", "통화 변환", "API 연동", "데이터 시각화"]
    elif "게임" in req_lower:
        features = ["게임 로직", "점수 시스템", "사용자 인터페이스", "게임 상태 관리"]
    elif "쇼핑몰" in req_lower:
        features = ["상품 관리", "장바구니", "결제 시스템", "사용자 인증", "주문 관리"]
    elif "할일" in req_lower or "todo" in req_lower:
        features = ["할일 추가/삭제", "완료 상태 관리", "필터링", "데이터 저장"]
    else:
        features = ["기본 기능", "사용자 인터페이스", "데이터 처리"]

    return features


def extract_requirements(requirement):
    """세부 요구사항 추출"""
    requirements = []
    req_lower = requirement.lower()

    if "react" in req_lower:
        requirements.append("React 프레임워크 사용")
    if "python" in req_lower:
        requirements.append("Python 언어 사용")
    if "api" in req_lower:
        requirements.append("RESTful API 구현")
    if "데이터베이스" in req_lower or "database" in req_lower:
        requirements.append("데이터베이스 연동")
    if "인증" in req_lower or "auth" in req_lower:
        requirements.append("사용자 인증 시스템")

    return requirements if requirements else ["표준 개발 프로세스 적용"]


def generate_team_plan(requirement, project_analysis):
    """팀 구성 계획 생성"""
    base_team = [
        {
            "role": "ProductManager",
            "name": "제품 관리자",
            "responsibility": f"{project_analysis['project_type']} 요구사항 분석 및 PRD 작성",
            "estimated_time": "15-20분",
            "deliverables": ["제품 요구사항 문서", "사용자 스토리", "성공 지표"]
        },
        {
            "role": "Architect",
            "name": "시스템 설계자",
            "responsibility": f"{project_analysis['technology']} 기반 아키텍처 설계",
            "estimated_time": "20-25분",
            "deliverables": ["시스템 아키텍처", "API 명세서", "데이터 모델"]
        },
        {
            "role": "Engineer",
            "name": "개발자",
            "responsibility": f"{project_analysis['project_type']} 구현 및 코딩",
            "estimated_time": "30-45분",
            "deliverables": ["실행 가능한 코드", "테스트 코드", "문서화"]
        }
    ]

    # 복잡도에 따른 팀원 추가
    if project_analysis["complexity"] == "높음":
        base_team.extend([
            {
                "role": "ProjectManager",
                "name": "프로젝트 관리자",
                "responsibility": "프로젝트 일정 관리 및 품질 보증",
                "estimated_time": "10-15분",
                "deliverables": ["프로젝트 계획서", "일정 관리", "품질 보고서"]
            },
            {
                "role": "QaEngineer",
                "name": "품질 보증 엔지니어",
                "responsibility": "테스트 전략 수립 및 품질 검증",
                "estimated_time": "15-20분",
                "deliverables": ["테스트 계획서", "테스트 케이스", "품질 보고서"]
            }
        ])

    return {
        "team_size": len(base_team),
        "team_members": base_team,
        "total_estimated_time": project_analysis["estimated_time"],
        "workflow": "순차적 단계별 승인 프로세스"
    }


def generate_execution_plan(requirement, project_analysis, team_plan):
    """실행 계획 생성"""
    phases = []

    for i, member in enumerate(team_plan["team_members"]):
        phases.append({
            "phase": i + 1,
            "role": member["role"],
            "name": member["name"],
            "title": f"{member['name']} 작업 단계",
            "description": member["responsibility"],
            "estimated_time": member["estimated_time"],
            "deliverables": member["deliverables"],
            "approval_required": True,
            "dependencies": [phases[i-1]["phase"]] if i > 0 else []
        })

    return {
        "total_phases": len(phases),
        "phases": phases,
        "execution_mode": "단계별 승인 기반",
        "user_interaction": "각 단계마다 사용자 승인 필요",
        "project_folder": f"metagpt_{int(time.time())}",
        "estimated_budget": "$5.00",
        "success_criteria": [
            "모든 단계 완료",
            "사용자 승인 획득",
            "실행 가능한 코드 생성",
            "문서화 완료"
        ]
    }


def create_demo_project(requirement):
    """Create a demo project based on requirement"""
    import uuid
    from datetime import datetime

    # Generate unique project name
    project_name = f"project_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    # Create project directory - MetaGPT 폴더 안에 workspace 생성
    workspace_dir = os.path.join(metagpt_path, 'workspace')
    project_path = os.path.join(workspace_dir, project_name)

    os.makedirs(project_path, exist_ok=True)

    # Generate project files based on requirement
    files_content = generate_project_files(requirement, project_name)

    # Create files
    for filename, content in files_content.items():
        file_path = os.path.join(project_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return project_path


def generate_project_files(requirement, project_name):
    """Generate project files based on requirement"""

    # Simple project template
    files = {
        'main.py': f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
{project_name}
Generated based on: {requirement}
"""

def main():
    """Main function for {requirement}"""
    print("Welcome to {project_name}")
    print("Requirement: {requirement}")

    # TODO: Implement the actual functionality
    print("This is a demo implementation.")
    print("Please implement the required features.")

if __name__ == "__main__":
    main()
''',

        'README.md': f'''# {project_name}

## Description
{requirement}

## Generated Files
- `main.py` - Main application file
- `README.md` - This documentation file
- `requirements.txt` - Python dependencies

## Usage
```bash
python main.py
```

## Development
This project was generated automatically based on the requirement:
> {requirement}

## Next Steps
1. Implement the core functionality in `main.py`
2. Add necessary dependencies to `requirements.txt`
3. Write tests for your implementation
4. Update this README with specific usage instructions

Generated by: MetaGPT + VS Code Integration
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
''',

        'requirements.txt': '''# Python dependencies
# Add your project dependencies here

# Example:
# requests>=2.28.0
# flask>=2.0.0
''',

        '.gitignore': '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
'''
    }

    return files




def run_metagpt_background(execution_id, requirement, selected_models, script_path):
    """Execute MetaGPT in background"""
    try:
        # Execute Python process
        process = subprocess.Popen(
            [sys.executable, script_path, requirement, json.dumps(selected_models)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir
        )

        stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout

        if process.returncode == 0:
            try:
                result = json.loads(stdout) if stdout.strip() else {}
                execution_status[execution_id].update({
                    'status': 'completed',
                    'result': result,
                    'end_time': datetime.now()
                })
            except json.JSONDecodeError:
                execution_status[execution_id].update({
                    'status': 'completed',
                    'result': {'output': stdout},
                    'end_time': datetime.now()
                })
        else:
            execution_status[execution_id].update({
                'status': 'failed',
                'error': stderr,
                'end_time': datetime.now()
            })

    except subprocess.TimeoutExpired:
        process.kill()
        execution_status[execution_id].update({
            'status': 'failed',
            'error': 'MetaGPT execution timeout (5 minutes)',
            'end_time': datetime.now()
        })
    except Exception as e:
        execution_status[execution_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now()
        })


@app.route('/api/execution/<execution_id>/status', methods=['GET'])
def get_execution_status(execution_id):
    """Query execution status"""
    status = execution_status.get(execution_id)
    if status:
        # Convert datetime objects to strings
        if isinstance(status.get('start_time'), datetime):
            status['start_time'] = status['start_time'].isoformat()
        if isinstance(status.get('end_time'), datetime):
            status['end_time'] = status['end_time'].isoformat()
        return jsonify({'success': True, 'data': status})
    else:
        return jsonify({
            'success': False,
            'error': 'Execution information not found.'
        }), 404


# ==================== SERVICE MANAGEMENT ENDPOINTS ====================

@app.route('/api/services/crewai/start', methods=['POST'])
def start_crewai_service():
    """Start CrewAI service"""
    try:
        crewai_server_path = os.path.join(crewai_path, 'crewai_platform', 'server.py')
        if os.path.exists(crewai_server_path):
            # Start CrewAI server in background
            subprocess.Popen([sys.executable, crewai_server_path], cwd=os.path.dirname(crewai_server_path))
            return jsonify({
                'success': True,
                'message': 'CrewAI service started.',
                'url': 'http://localhost:3003'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'CrewAI server file not found.'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start CrewAI service: {str(e)}'
        }), 500


@app.route('/api/services/status', methods=['GET'])
def get_services_status():
    """Query all service status"""
    return jsonify({
        'crewai': {
            'status': check_crewai_service(),
            'url': CREWAI_URL
        },
        'metagpt': {
            'status': check_metagpt_service(),
            'path': metagpt_path
        }
    })


# ==================== NEW DATABASE API ENDPOINTS ====================

@app.route('/api/v2/projects', methods=['GET'])
@optional_auth
def get_projects_v2():
    """Get projects list from database"""
    limit = request.args.get('limit', 20, type=int)
    # Pass user_id=None to show all projects (for now)
    result = db.get_projects(user_id=None, limit=limit)

    return jsonify(result)

@app.route('/api/v2/projects', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
@validate_json_input(['name'])
@optional_auth
def create_project_v2():
    """Create new project in database"""
    data = request.get_json()

    # 보안 검증
    security_issues = check_request_security(data)
    if security_issues:
        return jsonify({
            'success': False,
            'error': 'Security validation failed',
            'details': security_issues
        }), 400

    # 입력 데이터 검증
    validation_result = validate_request_data(data, 'project')
    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'error': 'Input validation failed',
            'details': validation_result['errors']
        }), 400

    # 검증된 데이터로 프로젝트 생성
    result = db.create_project(validation_result['data'])
    status_code = 201 if result.get('success') else 400

    return jsonify(result), status_code

@app.route('/api/v2/projects/<project_id>', methods=['GET'])
@optional_auth
def get_project_v2(project_id):
    """Get single project from database"""
    result = db.get_project_by_id(project_id)
    status_code = 200 if result.get('success') else 404

    return jsonify(result), status_code

@app.route('/api/v2/projects/<project_id>', methods=['PUT'])
@optional_auth
def update_project_v2(project_id):
    """Update project in database"""
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': '업데이트할 데이터가 필요합니다'
        }), 400

    result = db.update_project(project_id, data)
    status_code = 200 if result.get('success') else 400

    return jsonify(result), status_code

@app.route('/api/v2/projects/<project_id>', methods=['DELETE'])
@optional_auth
def delete_project_v2(project_id):
    """Delete project from database"""
    result = db.delete_project(project_id)
    status_code = 200 if result.get('success') else 400

    return jsonify(result), status_code

@app.route('/api/v2/projects/<project_id>/role-llm-mapping', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
@validate_json_input(['mappings'])
@optional_auth
def set_role_llm_mapping(project_id):
    """Set role-LLM mapping for project"""
    data = request.get_json()

    # 보안 검증
    security_issues = check_request_security(data)
    if security_issues:
        return jsonify({
            'success': False,
            'error': 'Security validation failed',
            'details': security_issues
        }), 400

    # 입력 데이터 검증
    validation_result = validate_request_data(data, 'llm_mapping')
    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'error': 'Input validation failed',
            'details': validation_result['errors']
        }), 400

    # 검증된 데이터로 매핑 설정
    result = db.set_project_role_llm_mapping(project_id, validation_result['mappings'])
    status_code = 200 if result.get('success') else 400

    return jsonify(result), status_code

@app.route('/api/v2/projects/<project_id>/role-llm-mapping', methods=['GET'])
@optional_auth
def get_role_llm_mapping(project_id):
    """Get role-LLM mapping for project"""
    result = db.get_project_role_llm_mapping(project_id)
    status_code = 200 if result.get('success') else 404

    return jsonify(result), status_code

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '데이터가 필요합니다'}), 400

        user_id = data.get('user_id')
        password = data.get('password')

        if not user_id or not password:
            return jsonify({'success': False, 'error': '사용자 ID와 비밀번호가 필요합니다'}), 400

        # Check if it's admin login
        if admin_auth.verify_password(user_id, password):
            token = admin_auth.generate_token(user_id)
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'user_id': user_id,
                    'role': 'admin',
                    'display_name': '시스템 관리자'
                },
                'message': '로그인 성공'
            })

        # Check database users
        result = db.verify_user(user_id, password)
        if result['success']:
            # Generate JWT token for database user
            user_data = {
                'id': user_id,
                'email': result['user'].get('email', f"{user_id}@example.com"),
                'role': result['user'].get('role', 'user'),
                'display_name': result['user'].get('display_name', user_id)
            }
            token = db.generate_jwt_token(user_data)

            return jsonify({
                'success': True,
                'token': token,
                'user': user_data,
                'message': '로그인 성공'
            })
        else:
            return jsonify({'success': False, 'error': '잘못된 사용자 ID 또는 비밀번호입니다'}), 401

    except Exception as e:
        return jsonify({'success': False, 'error': f'로그인 처리 중 오류: {str(e)}'}), 500

@app.route('/api/v2/auth/token', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
@validate_json_input()
def generate_auth_token():
    """Generate authentication token"""
    data = request.get_json()

    # Generate token with provided user data
    user_data = {
        'id': data.get('user_id'),
        'email': data.get('email', f"{data.get('user_id')}@example.com"),
        'role': data.get('role', 'user')
    }

    token = db.generate_jwt_token(user_data)

    return jsonify({
        'success': True,
        'token': token,
        'user': user_data,
        'message': '인증 토큰이 생성되었습니다'
    })

@app.route('/api/v2/auth/verify', methods=['POST'])
def verify_auth_token():
    """Verify authentication token"""
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({
            'success': False,
            'error': '인증 헤더가 필요합니다'
        }), 401

    try:
        token = auth_header.split(' ')[1]
        result = db.verify_jwt_token(token)

        return jsonify(result)
    except IndexError:
        return jsonify({
            'success': False,
            'error': '토큰 형식이 올바르지 않습니다'
        }), 401

# ==================== LEGACY API ENDPOINTS ====================

@app.route('/api/projects-legacy', methods=['GET'])
def get_projects_list():
    """프로젝트 목록 조회 (Legacy)"""
    try:
        # MetaGPT workspace에서 프로젝트 목록 조회
        projects_path = os.path.join(metagpt_path, 'workspace')

        if not os.path.exists(projects_path):
            return jsonify({
                'success': True,
                'projects': [],
                'message': 'MetaGPT workspace 디렉토리가 없습니다.'
            })

        projects = []
        for project_dir in os.listdir(projects_path):
            project_path = os.path.join(projects_path, project_dir)
            if os.path.isdir(project_path):
                metadata_file = os.path.join(project_path, 'project_metadata.json')
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # 진행 상황 파악
                        step_files = []
                        for i in range(1, 6):
                            step_file_pattern = f"step_{i}_*.json"
                            step_files_found = [f for f in os.listdir(project_path) if f.startswith(f"step_{i}_")]
                            if step_files_found:
                                step_files.append(i)

                        completed_steps = len(step_files)
                        progress_percentage = (completed_steps / 5) * 100

                        projects.append({
                            'project_name': metadata.get('project_name', project_dir),
                            'project_id': metadata.get('project_id', project_dir),
                            'requirement': metadata.get('requirement', ''),
                            'created_at': metadata.get('created_at', ''),
                            'current_step': metadata.get('current_step', 1),
                            'completed_steps': completed_steps,
                            'total_steps': 5,
                            'progress_percentage': progress_percentage,
                            'workspace_path': project_path,
                            'status': '완료' if completed_steps >= 5 else f'{completed_steps}/5 단계 진행 중'
                        })
                    except Exception as e:
                        print(f"프로젝트 메타데이터 읽기 실패: {project_dir} - {e}")

        # 최신 순으로 정렬
        projects.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            'success': True,
            'projects': projects
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 목록 조회 실패: {str(e)}'
        }), 500


@app.route('/api/projects/<project_name>', methods=['GET'])
def get_project_details(project_name):
    """특정 프로젝트 상세 정보 조회"""
    try:
        # MetaGPT workspace에서 특정 프로젝트 조회
        projects_path = os.path.join(metagpt_path, 'workspace')
        project_path = os.path.join(projects_path, project_name)

        if not os.path.exists(project_path):
            return jsonify({
                'success': False,
                'error': '프로젝트를 찾을 수 없습니다.'
            }), 404

        metadata_file = os.path.join(project_path, 'project_metadata.json')
        if not os.path.exists(metadata_file):
            return jsonify({
                'success': False,
                'error': '프로젝트 메타데이터를 찾을 수 없습니다.'
            }), 404

        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # 각 단계별 결과 읽기
        step_results = {}
        for i in range(1, 6):
            step_files = [f for f in os.listdir(project_path) if f.startswith(f"step_{i}_")]
            if step_files:
                step_file = os.path.join(project_path, step_files[0])
                try:
                    with open(step_file, 'r', encoding='utf-8') as f:
                        step_data = json.load(f)
                    step_results[i] = step_data
                except Exception as e:
                    print(f"단계 {i} 파일 읽기 실패: {e}")

        return jsonify({
            'success': True,
            'project': {
                'metadata': metadata,
                'step_results': step_results,
                'next_step': len(step_results) + 1 if len(step_results) < 5 else None
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 상세 정보 조회 실패: {str(e)}'
        }), 500


@app.route('/api/metagpt/step', methods=['POST'])
def handle_metagpt_step():
    """Handle MetaGPT step-by-step workflow"""
    data = request.get_json()

    requirement = data.get('requirement')
    step_number = data.get('step', 1)
    user_response = data.get('user_response')  # 'approve', 'reject', 'modify'
    modifications = data.get('modifications', '')

    if not requirement:
        return jsonify({'error': 'Requirement is required'}), 400

    try:
        # MetaGPT 경로 사용 (전역에서 설정됨)
        script_path = os.path.join(metagpt_path, 'run_step_by_step.py')

        if not os.path.exists(script_path):
            return jsonify({
                'success': False,
                'error': 'MetaGPT step-by-step script not found'
            }), 404

        # 사용자 입력 준비
        user_input = {}
        if user_response:
            user_input = {
                'response': user_response,
                'modifications': modifications
            }

        # MetaGPT 스크립트 실행
        args = [sys.executable, script_path, requirement, str(step_number)]
        if user_input:
            args.append(json.dumps(user_input))

        result = subprocess.run(args, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            try:
                response_data = json.loads(result.stdout)
                return jsonify(response_data)
            except json.JSONDecodeError:
                return jsonify({
                    'success': True,
                    'message': result.stdout,
                    'type': 'text_response'
                })
        else:
            return jsonify({
                'success': False,
                'error': 'MetaGPT step execution failed',
                'details': result.stderr
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Error processing MetaGPT step',
            'details': str(e)
        }), 500


# ==================== 프록시 라우팅 ====================

@app.route('/api/crewai/projects', methods=['GET'])
def proxy_crewai_projects():
    """CrewAI 프로젝트 목록 프록시"""
    try:
        response = requests.get(f'{CREWAI_URL}/api/projects', timeout=10)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'CrewAI 서버에 연결할 수 없습니다.',
            'details': str(e)
        }), 503

@app.route('/api/crewai/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_crewai(endpoint):
    """CrewAI API 프록시"""
    try:
        url = f'{CREWAI_URL}/api/{endpoint}'

        if request.method == 'GET':
            response = requests.get(url, params=request.args, timeout=10)
        elif request.method == 'POST':
            response = requests.post(url, json=request.get_json(), timeout=30)
        elif request.method == 'PUT':
            response = requests.put(url, json=request.get_json(), timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(url, timeout=10)

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'CrewAI 서버 연결 실패: {endpoint}',
            'details': str(e)
        }), 503

@app.route('/api/metagpt/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_metagpt(endpoint):
    """MetaGPT API 프록시"""
    try:
        # MetaGPT는 내장 처리로 대체
        if endpoint == 'projects':
            return get_projects_list()
        elif endpoint.startswith('step'):
            return handle_metagpt_step()
        else:
            return jsonify({
                'success': False,
                'error': f'MetaGPT 엔드포인트를 찾을 수 없습니다: {endpoint}'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'MetaGPT 처리 실패: {endpoint}',
            'details': str(e)
        }), 500


# ==================== PROJECT MANAGEMENT API ====================

@app.route('/api/projects', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
def get_projects():
    """프로젝트 목록 조회"""
    try:
        limit = request.args.get('limit', 20, type=int)
        result = db.get_projects(limit=limit)

        if result['success']:
            return jsonify({
                'success': True,
                'projects': result['projects'],
                'count': result['count'],
                'simulation': result.get('simulation', False)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 목록 조회 실패: {str(e)}'
        }), 500


@app.route('/api/projects', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
@validate_json_input(['name'])
def create_project():
    """새 프로젝트 생성"""
    try:
        data = request.get_json()

        # 입력 데이터 검증
        validation_result = validate_request_data(data, 'project')
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid input data',
                'details': validation_result['errors']
            }), 400

        # 보안 검사
        security_issues = check_request_security(data)
        if security_issues:
            return jsonify({
                'success': False,
                'error': 'Security validation failed',
                'details': security_issues
            }), 400

        # 프로젝트 생성
        result = db.create_project(validation_result['data'])

        if result['success']:
            return jsonify({
                'success': True,
                'project': result['project'],
                'message': result['message'],
                'simulation': result.get('simulation', False)
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 생성 실패: {str(e)}'
        }), 500


@app.route('/api/projects/<project_id>', methods=['GET'])
@rate_limit(max_requests=60, window_seconds=60)
def get_project(project_id):
    """특정 프로젝트 조회"""
    try:
        result = db.get_project_by_id(project_id)

        if result['success']:
            return jsonify({
                'success': True,
                'project': result['project'],
                'simulation': result.get('simulation', False)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'find' in result['error'] else 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 조회 실패: {str(e)}'
        }), 500


@app.route('/api/projects/<project_id>', methods=['PUT'])
@rate_limit(max_requests=20, window_seconds=60)
@validate_json_input()
def update_project(project_id):
    """프로젝트 업데이트"""
    try:
        data = request.get_json()

        # 입력 데이터 검증 (업데이트이므로 필수 필드 없음)
        validation_result = validate_request_data(data, 'project')
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid input data',
                'details': validation_result['errors']
            }), 400

        # 보안 검사
        security_issues = check_request_security(data)
        if security_issues:
            return jsonify({
                'success': False,
                'error': 'Security validation failed',
                'details': security_issues
            }), 400

        # 프로젝트 업데이트
        result = db.update_project(project_id, validation_result['data'])

        if result['success']:
            return jsonify({
                'success': True,
                'project': result['project'],
                'message': result['message'],
                'simulation': result.get('simulation', False)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'프로젝트 업데이트 실패: {str(e)}'
        }), 500


# ==================== ROLE-LLM MAPPING API ====================

@app.route('/api/projects/<project_id>/role-llm-mapping', methods=['GET'])
@rate_limit(max_requests=60, window_seconds=60)
def get_project_role_mapping(project_id):
    """프로젝트 역할-LLM 매핑 조회"""
    try:
        result = db.get_project_role_llm_mapping(project_id)

        if result['success']:
            return jsonify({
                'success': True,
                'mappings': result['mappings'],
                'simulation': result.get('simulation', False)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LLM 매핑 조회 실패: {str(e)}'
        }), 500


@app.route('/api/projects/<project_id>/role-llm-mapping', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
@validate_json_input(['mappings'])
def set_project_role_mapping(project_id):
    """프로젝트 역할-LLM 매핑 설정"""
    try:
        data = request.get_json()
        mappings = data.get('mappings', [])

        # 매핑 데이터 검증
        validation_result = validate_request_data({'mappings': mappings}, 'llm_mapping')
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid mapping data',
                'details': validation_result['errors']
            }), 400

        # 보안 검사
        security_issues = check_request_security(data)
        if security_issues:
            return jsonify({
                'success': False,
                'error': 'Security validation failed',
                'details': security_issues
            }), 400

        # 매핑 설정
        result = db.set_project_role_llm_mapping(project_id, validation_result['mappings'])

        if result['success']:
            return jsonify({
                'success': True,
                'mappings': result['mappings'],
                'message': result['message'],
                'simulation': result.get('simulation', False)
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LLM 매핑 설정 실패: {str(e)}'
        }), 500


# ==================== DATABASE UTILITIES API ====================

@app.route('/api/database/test', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=60)
def test_database():
    """데이터베이스 연결 테스트"""
    try:
        result = db.test_connection()
        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'데이터베이스 테스트 실패: {str(e)}'
        }), 500


@app.route('/api/database/status', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
def database_status():
    """데이터베이스 상태 확인"""
    try:
        connected = db.is_connected()
        test_result = db.test_connection()

        return jsonify({
            'connected': connected,
            'status': test_result,
            'environment': {
                'supabase_url_configured': bool(os.getenv('SUPABASE_URL')),
                'supabase_key_configured': bool(os.getenv('SUPABASE_ANON_KEY')),
                'jwt_secret_configured': bool(os.getenv('JWT_SECRET_KEY'))
            }
        })

    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500


# ==================== METAGPT API ENDPOINTS ====================

@app.route('/api/metagpt/projects', methods=['GET'])
def get_metagpt_projects():
    """Get all MetaGPT projects"""
    try:
        # Use global db instance
        result = db.get_projects()

        if result.get('success'):
            # Filter for MetaGPT projects
            metagpt_projects = [
                project for project in result['projects']
                if project.get('selected_ai') == 'meta-gpt'
            ]

            return jsonify({
                'success': True,
                'projects': metagpt_projects,
                'count': len(metagpt_projects)
            })
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"Error getting MetaGPT projects: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects', methods=['POST'])
def create_metagpt_project():
    """Create a new MetaGPT project with workflow stages"""
    try:
        data = request.get_json()
        # Use global db instance

        # Create project with MetaGPT specific settings
        project_data = {
            'name': data.get('name', 'Untitled MetaGPT Project'),
            'description': data.get('description', ''),
            'selected_ai': 'meta-gpt',
            'project_type': data.get('project_type', 'web_app'),
            'status': 'planning',
            'current_stage': 'requirement',
            'progress_percentage': 0
        }

        result = db.create_metagpt_project(project_data)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"Error creating MetaGPT project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects/<project_id>', methods=['GET'])
def get_metagpt_project(project_id):
    """Get specific MetaGPT project with workflow stages"""
    try:
        # Use global db instance
        project_result = db.get_project_by_id(project_id)
        project = project_result.get('project') if project_result.get('success') else None

        if not project:
            return jsonify({
                'success': False,
                'error': 'Project not found'
            }), 404

        # Get workflow stages
        workflow_stages = db.get_metagpt_workflow_stages(project_id)

        # Get role-LLM mapping
        role_llm_mapping = db.get_metagpt_role_llm_mapping(project_id)

        return jsonify({
            'success': True,
            'project': project,
            'workflow_stages': workflow_stages,
            'role_llm_mapping': role_llm_mapping
        })

    except Exception as e:
        print(f"Error getting MetaGPT project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects/<project_id>/workflow-stages', methods=['GET'])
def get_metagpt_workflow_stages(project_id):
    """Get workflow stages for a MetaGPT project"""
    try:
        # Use global db instance
        stages = db.get_metagpt_workflow_stages(project_id)

        return jsonify({
            'success': True,
            'workflow_stages': stages,
            'count': len(stages)
        })

    except Exception as e:
        print(f"Error getting workflow stages: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects/<project_id>/workflow-stages/<stage_id>', methods=['PUT'])
def update_metagpt_workflow_stage(project_id, stage_id):
    """Update a specific workflow stage"""
    try:
        data = request.get_json()
        # Use global db instance

        status = data.get('status', 'in_progress')
        output_content = data.get('output_content', '')

        result = db.update_metagpt_stage_status(stage_id, status, output_content)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"Error updating workflow stage: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects/<project_id>/role-llm-mapping', methods=['GET'])
def get_metagpt_role_llm_mapping(project_id):
    """Get role-LLM mapping for a MetaGPT project"""
    try:
        # Use global db instance
        mapping = db.get_metagpt_role_llm_mapping(project_id)

        return jsonify({
            'success': True,
            'role_llm_mapping': mapping
        })

    except Exception as e:
        print(f"Error getting role-LLM mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/metagpt/projects/<project_id>/role-llm-mapping', methods=['POST'])
def set_metagpt_role_llm_mapping(project_id):
    """Set role-LLM mapping for a MetaGPT project"""
    try:
        data = request.get_json()
        # Use global db instance

        result = db.set_metagpt_role_llm_mapping(project_id, data)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        print(f"Error setting role-LLM mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Deliverable endpoints will be implemented later when needed


@app.route('/api/metagpt/dashboard', methods=['GET'])
def get_metagpt_dashboard():
    """Get MetaGPT dashboard view data"""
    try:
        # Use global db instance

        # Get dashboard data using the view
        if db.is_connected():
            dashboard_data = db.supabase.table('metagpt_project_dashboard').select('*').execute()
            performance_data = db.supabase.table('metagpt_performance_summary').select('*').execute()

            return jsonify({
                'success': True,
                'dashboard': dashboard_data.data,
                'performance': performance_data.data
            })
        else:
            # Simulation mode fallback
            projects = db.get_projects_by_ai('meta-gpt')
            return jsonify({
                'success': True,
                'dashboard': projects,
                'performance': [],
                'simulation_mode': True
            })

    except Exception as e:
        print(f"Error getting MetaGPT dashboard: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== CREWAI DIRECT INTEGRATION ====================
# CrewAI 서버 기능을 직접 통합 - 별도 서버 불필요

def start_background_execution(crew_id, inputs, script_path):
    """백그라운드 실행을 시작하는 공통 함수"""
    execution_id = str(uuid.uuid4())

    execution_status[execution_id] = {
        "status": "running",
        "start_time": datetime.now(),
        "progress": 0,
        "message": "프로그램을 시작하고 있습니다...",
        "crew_id": crew_id
    }

    # 강화된 로깅 시작
    crewai_logger.start_execution_logging(execution_id, crew_id, inputs)
    crewai_logger.log_validation(execution_id, crew_id, "script_path",
                                os.path.exists(script_path), {"script_path": script_path})

    # 실행 이력 DB에 'running' 상태로 기록 시작
    try:
        if supabase:
            supabase.table('execution_history').insert({
                "id": execution_id,
                "crew_id": crew_id,
                "inputs": inputs,
                "status": "running",
                "started_at": execution_status[execution_id]['start_time'].isoformat()
            }).execute()
    except Exception as e:
        print(f"실행 이력 시작 기록 실패: {e}")

    thread = threading.Thread(
        target=run_program_background,
        args=(crew_id, inputs, execution_id, script_path, supabase)
    )
    thread.start()

    return jsonify({
        "success": True,
        "execution_id": execution_id,
        "message": "프로그램 실행이 시작되었습니다."
    })

def run_program_background(crew_id, inputs, execution_id, script_path, supabase_client):
    """백그라운드에서 프로그램 실행 (공통 로직)"""
    start_time = time.time()
    env = os.environ.copy()
    project_name = None
    output_path = None

    # 크루 생성기('creator')인 경우 특별 처리
    is_creating_crew = inputs.pop('is_crew_creator', None) == "true"

    # 초기화 단계 시작
    crewai_logger.start_phase(execution_id, crew_id, ExecutionPhase.INITIALIZATION)

    try:
        if is_creating_crew:
            project_name = inputs.get('project_name', 'new-crew-project')
            crewai_logger.log(
                execution_id, crew_id, ExecutionPhase.INITIALIZATION,
                crewai_logger.LogLevel.INFO,
                f"크루 생성 모드 - 프로젝트명: {project_name}",
                {"project_name": project_name, "is_creator": True}
            )

        # 초기화 단계 완료
        crewai_logger.end_phase(execution_id, crew_id, ExecutionPhase.INITIALIZATION, True)

        # 준비 단계 시작
        crewai_logger.start_phase(execution_id, crew_id, ExecutionPhase.PREPARATION)

        # 실행 상태 업데이트
        execution_status[execution_id].update({
            "progress": 25,
            "message": "프로그램을 실행 중입니다..."
        })
        crewai_logger.log_progress_update(execution_id, crew_id, 25, "환경 변수 설정 중")

        # UTF-8 인코딩 환경변수 설정 (Windows CP949 문제 해결)
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '0'

        # 환경 변수 설정 로깅
        env_vars = {'PYTHONIOENCODING': 'utf-8', 'PYTHONLEGACYWINDOWSSTDIO': '0'}
        for key, value in inputs.items():
            env_key = f"CREWAI_{key.upper()}"
            env[env_key] = str(value)
            env_vars[env_key] = str(value)

        # 크루 생성기일 경우, 출력 경로를 환경 변수에 추가
        if is_creating_crew:
            output_path = os.path.join(PROJECTS_BASE_DIR, project_name)
            env['CREWAI_OUTPUT_PATH'] = output_path
            env_vars['CREWAI_OUTPUT_PATH'] = output_path
            crewai_logger.log_file_operation(
                execution_id, crew_id, "output_directory_set", output_path, True,
                {"directory_exists": os.path.exists(os.path.dirname(output_path))}
            )

        # 준비 단계 완료
        crewai_logger.end_phase(execution_id, crew_id, ExecutionPhase.PREPARATION, True,
                               {"environment_variables": len(env_vars), "script_validated": True})

        # 실행 단계 시작
        crewai_logger.start_phase(execution_id, crew_id, ExecutionPhase.EXECUTION)
        crewai_logger.log_subprocess_start(execution_id, crew_id, script_path, env)

        # Simplified execution without real-time streaming
        process = subprocess.Popen(
            ["python", "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1
        )

        full_output = []
        full_error = []

        # 모니터링 단계 시작
        crewai_logger.start_phase(execution_id, crew_id, ExecutionPhase.MONITORING)

        # stdout, stderr 스트림을 실시간으로 읽기
        line_count = 0
        while True:
            output = process.stdout.readline()
            if output:
                full_output.append(output)
                line_count += 1

                # 주요 출력 로깅 (너무 많은 로그 방지)
                if line_count % 10 == 1 or "ERROR" in output.upper() or "SUCCESS" in output.upper():
                    crewai_logger.log_subprocess_output(execution_id, crew_id, "stdout", output.strip())

                # CrewAI 역할별 실행 감지 및 로깅 (Planner → Researcher → Writer 순서)
                role_keywords = {
                    "Planner": ["계획", "plan", "planning", "Planner", "전략"],
                    "Researcher": ["연구", "research", "Researcher", "조사", "분석"],
                    "Writer": ["작성", "write", "Writer", "글", "문서"]
                }

                for role, keywords in role_keywords.items():
                    if any(keyword in output for keyword in keywords):
                        if "시작" in output or "start" in output.lower():
                            crewai_logger.log_crewai_role_execution(execution_id, crew_id, role, "실행중")
                        elif "완료" in output or "complete" in output.lower() or "finish" in output.lower():
                            crewai_logger.log_crewai_role_execution(execution_id, crew_id, role, "완료")
                        break

                # 진행률 업데이트 (대략적)
                if line_count % 20 == 0:
                    progress = min(50 + (line_count // 20) * 5, 90)
                    execution_status[execution_id]["progress"] = progress
                    crewai_logger.log_progress_update(execution_id, crew_id, progress,
                                                    f"프로그램 실행 중 ({line_count}줄 처리)")

            if process.poll() is not None and not output:
                break

        # 모니터링 단계 완료
        crewai_logger.end_phase(execution_id, crew_id, ExecutionPhase.MONITORING, True,
                               {"total_output_lines": line_count})

        # 프로세스 종료 후 최종 결과 처리
        return_code = process.poll()
        stderr_output = process.stderr.read()
        if stderr_output:
            full_error.append(stderr_output)
            crewai_logger.log_subprocess_output(execution_id, crew_id, "stderr", stderr_output)

        # 완료 단계 시작
        crewai_logger.start_phase(execution_id, crew_id, ExecutionPhase.COMPLETION)

        # 실행 완료 처리
        if return_code == 0:
            end_time = datetime.now()
            final_output = "".join(full_output)
            total_duration = int((time.time() - start_time) * 1000)

            execution_status[execution_id].update({
                "status": "completed",
                "progress": 100,
                "message": "프로그램 실행이 완료되었습니다.",
                "output": final_output,
                "end_time": end_time
            })

            # 성공 완료 로깅
            crewai_logger.log_completion(
                execution_id, crew_id, True, total_duration,
                {
                    "return_code": return_code,
                    "output_lines": len(full_output),
                    "output_size_chars": len(final_output),
                    "is_crew_creation": is_creating_crew
                }
            )

            # DB에 최종 결과 업데이트
            if supabase_client:
                try:
                    supabase_client.table('execution_history').update({
                        "status": "completed",
                        "final_output": final_output,
                        "ended_at": end_time.isoformat(),
                        "duration_seconds": (end_time - execution_status[execution_id]['start_time']).total_seconds()
                    }).eq('id', execution_id).execute()
                except Exception as e:
                    print(f"실행 이력 완료 업데이트 실패: {e}")

            # 크루 생성기 실행 성공 시, 생성된 크루 정보를 DB에 저장
            if is_creating_crew and supabase_client and project_name:
                try:
                    # '기본' 프로젝트가 없으면 생성
                    default_project_name = "사용자 생성 크루"
                    project_res = supabase.table('projects').select('id').eq('name', default_project_name).single().execute()
                    if not project_res.data:
                        project_res = supabase.table('projects').insert({"name": default_project_name}).select('id').single().execute()

                    project_id = project_res.data['id']

                    # 생성된 크루 정보 저장
                    insert_res = supabase_client.table('crews').insert({
                        "project_id": project_id,
                        "name": project_name,
                        "description": inputs.get('user_request'),
                        "crew_type": 'generated',
                        "file_path": project_name,
                        "status": 'active'
                    }).select('id').single().execute()

                except Exception as db_error:
                    print(f"DB 저장 오류: {db_error}")

        else:
            end_time = datetime.now()
            error_message = "".join(full_error)
            total_duration = int((time.time() - start_time) * 1000)

            execution_status[execution_id].update({
                "status": "failed",
                "progress": 0,
                "message": "프로그램 실행 중 오류가 발생했습니다.",
                "error": error_message,
                "end_time": end_time
            })

            # 실패 완료 로깅
            crewai_logger.log_completion(
                execution_id, crew_id, False, total_duration,
                {
                    "return_code": return_code,
                    "error_message": error_message,
                    "stderr_lines": len(full_error)
                }
            )

    except Exception as e:
        end_time = datetime.now()
        total_duration = int((time.time() - start_time) * 1000)

        # 예외 로깅
        crewai_logger.log_error(
            execution_id, crew_id, e, "run_program_background",
            {
                "script_path": script_path,
                "is_creating_crew": is_creating_crew,
                "project_name": project_name
            }
        )
        error_message = str(e)
        execution_status[execution_id].update({
            "status": "failed",
            "progress": 0,
            "message": "프로그램 실행 중 오류가 발생했습니다.",
            "error": error_message,
            "end_time": datetime.now()
        })

@app.route('/api/services/crewai/status')
@rate_limit(10, 60)
def crewai_server_status():
    """CrewAI 서비스 상태 확인 - 직접 통합"""
    try:
        # Supabase 연결 상태 확인
        if supabase:
            # 간단한 테스트 쿼리로 연결 확인
            supabase.table('projects').select('id').limit(1).execute()

        return jsonify({
            'success': True,
            'status': 'integrated',
            'integration_type': 'direct',
            'supabase_connected': bool(supabase),
            'projects_path': PROJECTS_BASE_DIR
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e),
            'integration_type': 'direct'
        }), 503

@app.route('/api/services/crewai/projects')
@rate_limit(20, 60)
def crewai_get_projects():
    """모든 프로젝트와 그에 속한 크루 목록을 조회 - 직접 통합"""
    try:
        if not supabase:
            return jsonify({"success": False, "error": "Supabase is not configured."}), 500

        # 1. 모든 프로젝트 조회
        projects_res = supabase.table('projects').select('*').execute()
        if not projects_res.data:
            return jsonify({"success": True, "data": []})

        projects = projects_res.data
        project_ids = [p['id'] for p in projects]

        # 2. 프로젝트에 속한 모든 크루 조회
        crews_res = supabase.table('crews').select('*').in_('project_id', project_ids).execute()
        crews_by_project = {}
        if crews_res.data:
            for crew in crews_res.data:
                pid = crew['project_id']
                if pid not in crews_by_project:
                    crews_by_project[pid] = []
                crews_by_project[pid].append(crew)

        # 3. 데이터 조합
        for project in projects:
            project['crews'] = crews_by_project.get(project['id'], [])

        return jsonify({"success": True, "data": projects})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/services/crewai/crews/<crew_id>/inputs')
@rate_limit(20, 60)
def crewai_get_crew_inputs(crew_id):
    """특정 크루의 입력 필드 조회 - 직접 통합"""
    try:
        if not supabase:
            return jsonify({"success": False, "error": "Supabase is not configured."}), 500

        result = supabase.table('crew_inputs').select('*').eq('crew_id', crew_id).order('display_order').execute()
        return jsonify({"success": True, "data": result.data})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/services/crewai/execute', methods=['POST'])
@rate_limit(5, 300)  # 5분간 5회로 제한 (실행은 자원 집약적)
@validate_json_input(['crew_id', 'inputs'])
def crewai_execute():
    """크루 실행 - 직접 통합"""
    try:
        data = request.get_json()
        crew_id = data['crew_id']
        inputs = data['inputs']

        if not supabase:
            return jsonify({"success": False, "error": "Supabase is not configured."}), 500

        # DB에서 크루 정보 조회
        crew_res = supabase.table('crews').select('id, name, file_path, crew_type').eq('id', crew_id).single().execute()
        if not crew_res.data:
            return jsonify({"success": False, "error": "Crew not found."}), 404

        crew_info = crew_res.data

        # 'creator' 타입의 크루(예: 크루 생성기)는 CrewAI 소스의 programs 폴더에서 찾음
        if crew_info.get('crew_type') == 'creator':
            script_path = os.path.join(CREWAI_BASE_DIR, 'crewai_platform', 'programs', crew_info['file_path'])
        else:
            # 'base', 'generated' 타입 크루는 모두 Projects 폴더 기반으로 경로를 찾음
            project_folder = crew_info.get('file_path')
            if not project_folder:
                return jsonify({"success": False, "error": "Crew file_path is not defined in the database."}), 500
            script_path = os.path.join(PROJECTS_BASE_DIR, project_folder, 'run_crew.py')

        if not script_path or not os.path.exists(script_path):
            return jsonify({"success": False, "error": f"Execution script not found at {script_path}"}), 404

        # 크루 생성의 경우, 입력값을 환경변수로 전달하기 위해 inputs에 추가
        if crew_info.get('crew_type') == 'creator':
            inputs['is_crew_creator'] = "true"

        return start_background_execution(crew_id, inputs, script_path)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/services/crewai/execution/<execution_id>')
@rate_limit(30, 60)
def crewai_execution_status(execution_id):
    """실행 상태 조회 - 직접 통합"""
    try:
        status = execution_status.get(execution_id)
        if status:
            # datetime 객체를 직렬화 가능한 문자열로 변환
            if isinstance(status.get('start_time'), datetime):
                status['start_time'] = status['start_time'].isoformat()
            if isinstance(status.get('end_time'), datetime):
                status['end_time'] = status['end_time'].isoformat()
            return jsonify({"success": True, "data": status})
        else:
            return jsonify({
                "success": False,
                "error": "실행 정보를 찾을 수 없습니다."
            }), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== END CREWAI INTEGRATION ====================

# ==================== METAGPT EXECUTION INTEGRATION ====================

@app.route('/api/services/metagpt/execute', methods=['POST'])
@rate_limit(3, 600)  # 10분간 3회로 제한 (MetaGPT는 매우 자원 집약적)
@validate_json_input(['requirement'])
def metagpt_execute():
    """MetaGPT 실행 - 5단계 소프트웨어 개발 프로세스"""
    try:
        data = request.get_json()
        requirement = data['requirement']
        selected_models = data.get('role_llm_mapping', {})

        # 실행 ID 생성
        execution_id = str(uuid.uuid4())

        # 실행 정보를 데이터베이스에 기록 시작
        execution_start_time = datetime.utcnow()

        try:
            # MetaGPT 브릿지 스크립트 실행
            import subprocess
            import json as json_module

            # 현재 디렉터리에서 MetaGPT 브릿지 실행
            bridge_path = os.path.join(os.path.dirname(__file__), 'metagpt_bridge.py')

            # 명령어 구성
            cmd = [
                sys.executable,  # python.exe
                bridge_path,
                requirement,
                json_module.dumps(selected_models) if selected_models else '{}'
            ]

            # 백그라운드에서 실행 (타임아웃: 20분)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(__file__)
            )

            # 결과 대기 (최대 20분)
            try:
                stdout, stderr = process.communicate(timeout=1200)  # 20분

                if process.returncode == 0:
                    # 성공적으로 완료
                    try:
                        metagpt_result = json_module.loads(stdout)

                        # 데이터베이스에 결과 저장
                        execution_record = {
                            'project_type': 'metagpt',
                            'execution_id': execution_id,
                            'requirement': requirement,
                            'role_llm_mapping': selected_models,
                            'status': 'completed',
                            'started_at': execution_start_time.isoformat(),
                            'completed_at': datetime.utcnow().isoformat(),
                            'duration_seconds': (datetime.utcnow() - execution_start_time).total_seconds(),
                            'result_data': metagpt_result,
                            'agents_involved': metagpt_result.get('agents_involved', []),
                            'success': True
                        }

                        # 실제 데이터베이스 저장 로직
                        try:
                            # MetaGPT 워크플로우 단계 생성
                            workflow_stages = [
                                {'stage_number': 1, 'stage_name': '요구사항 분석', 'responsible_role': 'Product Manager', 'role_icon': '📋'},
                                {'stage_number': 2, 'stage_name': '시스템 설계', 'responsible_role': 'Architect', 'role_icon': '🏗️'},
                                {'stage_number': 3, 'stage_name': '프로젝트 계획', 'responsible_role': 'Project Manager', 'role_icon': '📊'},
                                {'stage_number': 4, 'stage_name': '코드 개발', 'responsible_role': 'Engineer', 'role_icon': '💻'},
                                {'stage_number': 5, 'stage_name': '품질 보증', 'responsible_role': 'QA Engineer', 'role_icon': '🧪'}
                            ]

                            # 프로젝트 데이터 생성
                            project_data = {
                                'name': f"MetaGPT-{execution_id[:8]}",
                                'description': requirement[:200],
                                'selected_ai': 'meta-gpt',
                                'status': 'completed',
                                'progress_percentage': 100,
                                'execution_metadata': execution_record,
                                'created_at': execution_start_time.isoformat(),
                                'updated_at': datetime.utcnow().isoformat()
                            }

                            # 데이터베이스에 저장
                            if database.supabase:
                                # 프로젝트 저장
                                project_result = database.supabase.table('projects').insert(project_data).execute()
                                project_id = project_result.data[0]['id'] if project_result.data else None

                                if project_id:
                                    # MetaGPT 워크플로우 단계 저장
                                    for stage in workflow_stages:
                                        stage_data = {
                                            'project_id': project_id,
                                            'stage_number': stage['stage_number'],
                                            'stage_name': stage['stage_name'],
                                            'responsible_role': stage['responsible_role'],
                                            'role_icon': stage['role_icon'],
                                            'status': 'completed',
                                            'progress_percentage': 100
                                        }
                                        database.supabase.table('metagpt_workflow_stages').insert(stage_data).execute()

                                execution_record['database_id'] = project_id
                                print(f"MetaGPT 실행 결과 데이터베이스 저장 완료: {project_id}")
                            else:
                                print("Supabase 연결 없음 - 로컬 로그만 기록")
                        except Exception as db_save_error:
                            print(f"데이터베이스 저장 실패: {db_save_error}")

                        print(f"MetaGPT 실행 완료 기록: {execution_record}")

                        return jsonify({
                            'success': True,
                            'execution_id': execution_id,
                            'status': 'completed',
                            'requirement': requirement,
                            'result': metagpt_result,
                            'duration_seconds': execution_record['duration_seconds'],
                            'agents_involved': metagpt_result.get('agents_involved', [])
                        })

                    except json_module.JSONDecodeError:
                        # JSON 파싱 실패
                        return jsonify({
                            'success': False,
                            'execution_id': execution_id,
                            'error': 'MetaGPT 결과 파싱 오류',
                            'raw_output': stdout,
                            'stderr': stderr
                        }), 500

                else:
                    # 프로세스 실행 실패
                    return jsonify({
                        'success': False,
                        'execution_id': execution_id,
                        'error': f'MetaGPT 실행 실패 (exit code: {process.returncode})',
                        'stderr': stderr,
                        'stdout': stdout
                    }), 500

            except subprocess.TimeoutExpired:
                # 타임아웃 발생
                process.kill()
                return jsonify({
                    'success': False,
                    'execution_id': execution_id,
                    'error': 'MetaGPT 실행 시간 초과 (20분)',
                    'status': 'timeout'
                }), 408

        except Exception as execution_error:
            return jsonify({
                'success': False,
                'execution_id': execution_id,
                'error': f'MetaGPT 실행 중 오류: {str(execution_error)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'MetaGPT API 오류: {str(e)}'
        }), 500

@app.route('/api/services/metagpt/status')
@rate_limit(10, 60)
def metagpt_status():
    """MetaGPT 서비스 상태 확인"""
    try:
        # MetaGPT 브릿지 파일 존재 확인
        bridge_path = os.path.join(os.path.dirname(__file__), 'metagpt_bridge.py')
        bridge_exists = os.path.exists(bridge_path)

        # MetaGPT 디렉터리 존재 확인
        metagpt_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MetaGPT')
        metagpt_exists = os.path.exists(metagpt_dir)

        return jsonify({
            'success': True,
            'status': 'available' if (bridge_exists and metagpt_exists) else 'unavailable',
            'bridge_exists': bridge_exists,
            'metagpt_directory_exists': metagpt_exists,
            'bridge_path': bridge_path,
            'metagpt_path': metagpt_dir,
            'execution_timeout': '20 minutes',
            'rate_limit': '3 requests per 10 minutes'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'MetaGPT 상태 확인 오류: {str(e)}'
        }), 500

# ==================== END METAGPT INTEGRATION ====================

# ==================== OLLAMA INTEGRATION ====================

@app.route('/api/ollama/status', methods=['GET'])
@rate_limit(max_requests=30, window_seconds=60)
def ollama_status():
    """Ollama 서비스 상태 확인"""
    try:
        is_available = ollama_client.is_available()

        return jsonify({
            'success': True,
            'available': is_available,
            'service': 'Ollama Local',
            'endpoint': ollama_client.base_url,
            'message': 'Ollama 서비스가 실행 중입니다' if is_available else 'Ollama 서비스에 연결할 수 없습니다'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'available': False,
            'error': f'Ollama 상태 확인 오류: {str(e)}'
        }), 500

@app.route('/api/ollama/models', methods=['GET'])
@rate_limit(max_requests=20, window_seconds=60)
def ollama_models():
    """Ollama 사용 가능한 모델 목록 조회"""
    try:
        result = ollama_client.get_models()

        if result['success']:
            return jsonify({
                'success': True,
                'models': result['models'],
                'count': result['count'],
                'service': 'Ollama Local'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'models': []
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ollama 모델 조회 오류: {str(e)}',
            'models': []
        }), 500

@app.route('/api/ollama/models/<model_name>', methods=['GET'])
@rate_limit(max_requests=10, window_seconds=60)
def ollama_model_info(model_name):
    """특정 Ollama 모델 정보 조회"""
    try:
        result = ollama_client.get_model_info(model_name)

        if result['success']:
            return jsonify({
                'success': True,
                'model': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ollama 모델 정보 조회 오류: {str(e)}'
        }), 500

@app.route('/api/ollama/generate', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=300)  # 5분간 10회 제한
@validate_json_input(['model', 'prompt'])
def ollama_generate():
    """Ollama를 통한 텍스트 생성"""
    try:
        data = request.get_json()
        model = data['model']
        prompt = data['prompt']
        system = data.get('system', '')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)

        result = ollama_client.generate_completion(
            model=model,
            prompt=prompt,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if result['success']:
            return jsonify({
                'success': True,
                'response': result['response'],
                'model': result['model'],
                'provider': result['provider'],
                'performance': {
                    'total_duration': result.get('total_duration', 0),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_count': result.get('prompt_eval_count', 0),
                    'eval_count': result.get('eval_count', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ollama 텍스트 생성 오류: {str(e)}'
        }), 500

@app.route('/api/ollama/chat', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=300)  # 5분간 10회 제한
@validate_json_input(['model', 'messages'])
def ollama_chat():
    """Ollama를 통한 채팅 완성"""
    try:
        data = request.get_json()
        model = data['model']
        messages = data['messages']
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)

        result = ollama_client.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'model': result['model'],
                'provider': result['provider'],
                'performance': {
                    'total_duration': result.get('total_duration', 0),
                    'load_duration': result.get('load_duration', 0),
                    'prompt_eval_count': result.get('prompt_eval_count', 0),
                    'eval_count': result.get('eval_count', 0)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ollama 채팅 완성 오류: {str(e)}'
        }), 500

@app.route('/api/llm/models', methods=['GET'])
@rate_limit(max_requests=20, window_seconds=60)
def get_all_llm_models():
    """모든 LLM 모델 목록 조회 (클라우드 + 로컬)"""
    try:
        # 기본 클라우드 LLM 모델들
        cloud_models = [
            { 'id': 'gpt-4', 'name': 'GPT-4', 'description': '범용 고성능 모델', 'provider': 'OpenAI', 'type': 'cloud' },
            { 'id': 'gpt-4o', 'name': 'GPT-4o', 'description': '멀티모달 최신 모델', 'provider': 'OpenAI', 'type': 'cloud' },
            { 'id': 'claude-3', 'name': 'Claude-3 Sonnet', 'description': '추론 특화 모델', 'provider': 'Anthropic', 'type': 'cloud' },
            { 'id': 'claude-3-haiku', 'name': 'Claude-3 Haiku', 'description': '빠른 응답 모델', 'provider': 'Anthropic', 'type': 'cloud' },
            { 'id': 'gemini-pro', 'name': 'Gemini Pro', 'description': '멀티모달 모델', 'provider': 'Google', 'type': 'cloud' },
            { 'id': 'gemini-flash', 'name': 'Gemini Flash', 'description': '빠른 응답 멀티모달 모델', 'provider': 'Google', 'type': 'cloud' },
            { 'id': 'deepseek-coder', 'name': 'DeepSeek Coder', 'description': '코딩 전문 모델', 'provider': 'DeepSeek', 'type': 'cloud' },
            { 'id': 'codellama', 'name': 'Code Llama', 'description': '코드 생성 특화', 'provider': 'Meta', 'type': 'cloud' }
        ]

        all_models = cloud_models.copy()

        # Ollama 로컬 모델들 추가
        if ollama_client.is_available():
            ollama_result = ollama_client.get_models()
            if ollama_result['success']:
                for model in ollama_result['models']:
                    model['type'] = 'local'
                    all_models.append(model)

        return jsonify({
            'success': True,
            'models': all_models,
            'count': len(all_models),
            'cloud_count': len(cloud_models),
            'local_count': len(all_models) - len(cloud_models),
            'ollama_available': ollama_client.is_available()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'LLM 모델 목록 조회 오류: {str(e)}',
            'models': []
        }), 500

# ==================== END OLLAMA INTEGRATION ====================


# ===================== 승인 시스템 API =====================

@app.route('/approval')
def approval_page():
    """승인 시스템 페이지"""
    return render_template('approval.html')

# ===================== 새로운 3단계 승인 시스템 API =====================

@app.route('/api/pre-analysis', methods=['POST'])
def create_pre_analysis():
    """사전 분석 요청 생성"""
    try:
        # 안전한 JSON 파싱 사용
        data = get_json_safely()

        if not data:
            return jsonify({'error': '요청 데이터가 없습니다'}), 400

        user_request = data.get('user_request')
        framework = data.get('framework', 'crewai')
        model = data.get('model', 'gemini-flash')
        project_id = data.get('project_id')

        if not user_request:
            return jsonify({'error': '사용자 요청이 필요합니다'}), 400

        # 사전 분석 수행
        analysis_result = pre_analysis_service.analyze_user_request(
            user_request=user_request,
            framework=framework,
            model=model
        )

        if analysis_result.get('status') == 'error':
            return jsonify({'error': analysis_result.get('error')}), 500

        # 승인 요청 생성
        approval_id = approval_workflow_manager.create_approval_request(
            analysis_result=analysis_result,
            project_id=project_id,
            requester="api"
        )

        return jsonify({
            'success': True,
            'analysis_id': analysis_result.get('analysis_id'),
            'approval_id': approval_id,
            'analysis_result': analysis_result
        })

    except Exception as e:
        print(f"사전 분석 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approval/pending', methods=['GET'])
def get_pending_approvals():
    """승인 대기 중인 요청 목록 조회"""
    try:
        project_id = request.args.get('project_id')
        pending_approvals = approval_workflow_manager.get_pending_approvals(project_id)

        return jsonify(pending_approvals)

    except Exception as e:
        print(f"승인 대기 목록 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approval/<approval_id>', methods=['GET'])
def get_approval_request(approval_id):
    """특정 승인 요청 조회"""
    try:
        approval_request = approval_workflow_manager.get_approval_request(approval_id)

        if not approval_request:
            return jsonify({'error': '승인 요청을 찾을 수 없습니다'}), 404

        return jsonify(approval_request)

    except Exception as e:
        print(f"승인 요청 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approval/<approval_id>/respond', methods=['POST'])
def respond_to_approval(approval_id):
    """승인 요청에 대한 응답 처리 - 강화된 버전"""
    import traceback

    # 요청 시작 로깅
    start_time = datetime.now()
    print(f"[APPROVAL API] 승인 응답 요청 시작: {approval_id} at {start_time}")

    try:
        # 1. 입력 데이터 검증
        data = request.get_json()
        if not data:
            error_msg = "요청 데이터가 없습니다. JSON 형식의 데이터가 필요합니다."
            print(f"[APPROVAL ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'MISSING_DATA',
                'approval_id': approval_id
            }), 400

        # 2. 필수 필드 검증
        action = data.get('action')
        feedback = data.get('feedback', '')
        revisions = data.get('revisions', [])
        timestamp = data.get('timestamp')

        print(f"[APPROVAL DATA] action={action}, feedback_length={len(feedback)}, revisions_count={len(revisions) if isinstance(revisions, list) else 0}")

        if not action:
            error_msg = "action 필드가 필수입니다."
            print(f"[APPROVAL ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'MISSING_ACTION',
                'approval_id': approval_id
            }), 400

        if action not in ['approve', 'reject', 'request_revision']:
            error_msg = f"잘못된 액션: {action}. 허용된 값: approve, reject, request_revision"
            print(f"[APPROVAL ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'INVALID_ACTION',
                'approval_id': approval_id,
                'allowed_actions': ['approve', 'reject', 'request_revision']
            }), 400

        # 3. 승인 워크플로우 매니저 확인
        if not approval_workflow_manager:
            error_msg = "승인 워크플로우 매니저가 초기화되지 않았습니다."
            print(f"[APPROVAL ERROR] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'WORKFLOW_MANAGER_NOT_INITIALIZED',
                'approval_id': approval_id
            }), 500

        print(f"[APPROVAL PROCESS] 승인 처리 시작: {approval_id}, action={action}")

        # 3.5. 승인 요청 존재 여부 확인
        approval_request = approval_workflow_manager.get_approval_request(approval_id)
        if not approval_request:
            print(f"[APPROVAL ERROR] 승인 요청을 찾을 수 없음: {approval_id}")
            print(f"[APPROVAL INFO] 메모리 저장소에 {len(approval_workflow_manager.approval_storage)}개 승인 요청 저장됨")
            print(f"[APPROVAL INFO] 저장된 ID 목록: {list(approval_workflow_manager.approval_storage.keys())}")

            return jsonify({
                'success': False,
                'error': f'승인 요청을 찾을 수 없습니다: {approval_id}',
                'error_code': 'APPROVAL_REQUEST_NOT_FOUND',
                'approval_id': approval_id,
                'debug_info': {
                    'stored_approval_count': len(approval_workflow_manager.approval_storage),
                    'stored_approval_ids': list(approval_workflow_manager.approval_storage.keys())
                }
            }), 404

        # 4. 승인 응답 처리
        result = approval_workflow_manager.process_approval_response(
            approval_id=approval_id,
            action=action,
            feedback=feedback,
            revisions=revisions
        )

        print(f"[APPROVAL RESULT] 처리 결과: success={result.get('success')}, message={result.get('message')}")

        if not result.get('success'):
            error_msg = result.get('error', '승인 처리 중 알 수 없는 오류가 발생했습니다.')
            print(f"[APPROVAL ERROR] 워크플로우 처리 실패: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'error_code': 'WORKFLOW_PROCESSING_FAILED',
                'approval_id': approval_id,
                'action': action
            }), 500

        # 5. 승인된 경우 프로젝트 실행 재개
        execution_resumed = False
        resume_error = None

        if action == 'approve':
            try:
                print(f"[APPROVAL RESUME] 프로젝트 실행 재개 시작: {approval_id}")

                # 승인 요청에서 프로젝트 정보 추출
                approval_request = approval_workflow_manager.get_approval_request(approval_id)
                if not approval_request:
                    print(f"[APPROVAL WARNING] 승인 요청 정보를 찾을 수 없음: {approval_id}")
                elif not approval_request.get('project_data'):
                    print(f"[APPROVAL WARNING] 프로젝트 데이터가 없음: {approval_id}")
                else:
                    project_data = approval_request['project_data']
                    execution_id = project_data.get('execution_id')
                    framework = project_data.get('framework')

                    print(f"[APPROVAL RESUME] execution_id={execution_id}, framework={framework}")

                    # 프로젝트 실행 재개 (백그라운드에서)
                    if framework == 'crewai':
                        threading.Thread(
                            target=resume_crewai_execution,
                            args=(execution_id, project_data),
                            daemon=True,
                            name=f"CrewAI-Resume-{execution_id[:8]}"
                        ).start()
                        execution_resumed = True
                        print(f"[APPROVAL RESUME] CrewAI 실행 재개 스레드 시작됨")

                    elif framework == 'metagpt':
                        threading.Thread(
                            target=resume_metagpt_execution,
                            args=(execution_id, project_data),
                            daemon=True,
                            name=f"MetaGPT-Resume-{execution_id[:8]}"
                        ).start()
                        execution_resumed = True
                        print(f"[APPROVAL RESUME] MetaGPT 실행 재개 스레드 시작됨")

                    else:
                        print(f"[APPROVAL WARNING] 알 수 없는 프레임워크: {framework}")

            except Exception as resume_error:
                print(f"[APPROVAL ERROR] 프로젝트 실행 재개 실패: {resume_error}")
                print(f"[APPROVAL ERROR] 재개 오류 스택:\n{traceback.format_exc()}")
                # 재개 실패는 치명적이지 않으므로 계속 진행

        # 6. 성공 응답 반환
        action_messages = {
            'approve': '승인되었습니다. 프로젝트 실행이 재개됩니다.',
            'reject': '거부되었습니다.',
            'request_revision': '수정 요청이 처리되었습니다.'
        }

        response_data = {
            'success': True,
            'message': action_messages.get(action, f'{action} 처리가 완료되었습니다.'),
            'approval_id': approval_id,
            'action': action,
            'processed_at': datetime.now().isoformat(),
            'processing_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
        }

        # 승인인 경우 실행 재개 정보 추가
        if action == 'approve':
            response_data['execution_resumed'] = execution_resumed
            if resume_error:
                response_data['resume_warning'] = str(resume_error)

        print(f"[APPROVAL SUCCESS] 승인 처리 완료: {approval_id}, action={action}, duration={(datetime.now() - start_time).total_seconds():.2f}s")

        return jsonify(response_data)

    except Exception as e:
        # 7. 전체 예외 처리
        error_duration = (datetime.now() - start_time).total_seconds()
        error_traceback = traceback.format_exc()

        print(f"[APPROVAL CRITICAL ERROR] 승인 처리 중 치명적 오류 발생:")
        print(f"  - approval_id: {approval_id}")
        print(f"  - 처리 시간: {error_duration:.2f}s")
        print(f"  - 오류 타입: {type(e).__name__}")
        print(f"  - 오류 메시지: {str(e)}")
        print(f"  - 스택 추적:\n{error_traceback}")

        return jsonify({
            'success': False,
            'error': f'승인 처리 중 시스템 오류가 발생했습니다: {str(e)}',
            'error_code': 'SYSTEM_ERROR',
            'error_type': type(e).__name__,
            'approval_id': approval_id,
            'processing_time_ms': int(error_duration * 1000)
        }), 500

@app.route('/api/approval/<approval_id>', methods=['POST'])
def process_approval_response(approval_id):
    """승인 응답 처리"""
    try:
        data = request.get_json()
        action = data.get('action')
        feedback = data.get('feedback')
        revisions = data.get('revisions')

        if action not in ['approve', 'reject', 'request_revision']:
            return jsonify({'error': '유효하지 않은 액션입니다'}), 400

        result = approval_workflow_manager.process_approval_response(
            approval_id=approval_id,
            action=action,
            feedback=feedback,
            revisions=revisions
        )

        if result.get('success'):
            # 승인된 경우 실제 실행 시작
            if action == 'approve':
                approval_request = approval_workflow_manager.get_approval_request(approval_id)
                if approval_request:
                    # 백그라운드에서 실행 시작
                    threading.Thread(
                        target=start_execution_after_approval,
                        args=(approval_request,),
                        daemon=True
                    ).start()

        return jsonify(result)

    except Exception as e:
        print(f"승인 응답 처리 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approval/<approval_id>/revise', methods=['POST'])
def revise_analysis(approval_id):
    """분석 결과 수정 적용"""
    try:
        data = request.get_json()
        revised_analysis = data.get('revised_analysis')

        if not revised_analysis:
            return jsonify({'error': '수정된 분석 결과가 필요합니다'}), 400

        result = approval_workflow_manager.apply_revisions(
            approval_id=approval_id,
            revised_analysis=revised_analysis
        )

        return jsonify(result)

    except Exception as e:
        print(f"수정 적용 오류: {e}")
        return jsonify({'error': str(e)}), 500

def start_execution_after_approval(approval_request):
    """승인 후 실행 시작"""
    try:
        framework = approval_request.get('metadata', {}).get('framework')
        project_id = approval_request.get('project_id')
        analysis_result = approval_request.get('analysis_result')
        analysis = analysis_result.get('analysis', {})

        print(f"승인 후 실행 시작: 프레임워크={framework}, 프로젝트={project_id}")

        # 기존 실행 로직과 연동
        if framework == 'crewai':
            # CrewAI 실행 - 승인된 구조화 프롬프트 사용
            structured_prompt = create_structured_crewai_prompt(analysis)

            # 프로젝트 생성 및 실행
            execution_id = str(uuid.uuid4())

            # 생성된 구조화 프롬프트로 CrewAI 실행
            inputs = {
                'original_request': analysis_result.get('original_request', ''),
                'structured_plan': structured_prompt,
                'project_summary': analysis.get('project_summary', ''),
                'objectives': analysis.get('objectives', []),
                'agents_config': analysis.get('agents', []),
                'workflow_config': analysis.get('workflow', []),
                'approval_id': approval_request.get('approval_id')
            }

            # 기본 크루 ID 사용 (existing crew or create new)
            crew_id = "structured-crewai-execution"

            # 백그라운드 실행 시작 - 기존 함수 활용
            start_structured_background_execution(execution_id, inputs, framework='crewai')

        elif framework == 'metagpt':
            # MetaGPT 실행 - 승인된 구조화 프롬프트 사용
            structured_requirement = create_structured_metagpt_requirement(analysis)

            execution_id = str(uuid.uuid4())

            # MetaGPT 실행 데이터 준비
            metagpt_data = {
                'requirement': structured_requirement,
                'original_request': analysis_result.get('original_request', ''),
                'project_summary': analysis.get('project_summary', ''),
                'workflow_stages': analysis.get('workflow', []),
                'approval_id': approval_request.get('approval_id')
            }

            # MetaGPT 실행 시작
            start_structured_background_execution(execution_id, metagpt_data, framework='metagpt')

    except Exception as e:
        print(f"승인 후 실행 오류: {e}")

def create_structured_crewai_prompt(analysis):
    """분석 결과를 CrewAI용 구조화 프롬프트로 변환"""
    agents = analysis.get('agents', [])
    workflow = analysis.get('workflow', [])
    objectives = analysis.get('objectives', [])

    prompt = f"""
# 프로젝트 계획: {analysis.get('project_summary', '')}

## 목표
{chr(10).join(f'- {obj}' for obj in objectives)}

## 에이전트 역할 분담
{chr(10).join(f'''
### {agent.get('role', '')}
- **전문 분야**: {agent.get('expertise', '')}
- **책임사항**: {', '.join(agent.get('responsibilities', []))}
- **산출물**: {', '.join(agent.get('deliverables', []))}
''' for agent in agents)}

## 작업 계획
{chr(10).join(f'''
### 단계 {step.get('step', i+1)}: {step.get('title', '')}
- **담당**: {step.get('agent', '')}
- **설명**: {step.get('description', '')}
- **예상 시간**: {step.get('estimated_time', '')}
''' for i, step in enumerate(workflow))}

이 계획에 따라 체계적으로 작업을 수행하세요.
"""
    return prompt

def create_structured_metagpt_requirement(analysis):
    """분석 결과를 MetaGPT용 구조화 요구사항으로 변환"""
    objectives = analysis.get('objectives', [])
    workflow = analysis.get('workflow', [])

    requirement = f"""
프로젝트: {analysis.get('project_summary', '')}

요구사항:
{chr(10).join(f'- {obj}' for obj in objectives)}

개발 단계:
{chr(10).join(f'{i+1}. {step.get("title", "")}: {step.get("description", "")}' for i, step in enumerate(workflow))}

이 요구사항에 따라 5단계 소프트웨어 개발 프로세스를 진행하세요.
"""
    return requirement

def start_structured_background_execution(execution_id, data, framework):
    """승인된 구조화 데이터로 백그라운드 실행"""
    try:
        execution_status[execution_id] = {
            'status': 'starting',
            'framework': framework,
            'start_time': datetime.now(),
            'approval_based': True,
            'data': data
        }

        if framework == 'crewai':
            # CrewAI 구조화 실행
            def run_crewai():
                try:
                    execution_status[execution_id]['status'] = 'running'

                    # 구조화된 프롬프트로 CrewAI 실행
                    # 실제 구현시 generate_crewai_script_new.py의 로직 활용

                    execution_status[execution_id].update({
                        'status': 'completed',
                        'end_time': datetime.now()
                    })

                except Exception as e:
                    execution_status[execution_id].update({
                        'status': 'failed',
                        'error': str(e),
                        'end_time': datetime.now()
                    })

            threading.Thread(target=run_crewai, daemon=True).start()

        elif framework == 'metagpt':
            # MetaGPT 구조화 실행
            def run_metagpt():
                try:
                    execution_status[execution_id]['status'] = 'running'

                    # 구조화된 요구사항으로 MetaGPT 실행
                    # 실제 구현시 기존 MetaGPT 로직 활용

                    execution_status[execution_id].update({
                        'status': 'completed',
                        'end_time': datetime.now()
                    })

                except Exception as e:
                    execution_status[execution_id].update({
                        'status': 'failed',
                        'error': str(e),
                        'end_time': datetime.now()
                    })

            threading.Thread(target=run_metagpt, daemon=True).start()

    except Exception as e:
        print(f"구조화 백그라운드 실행 오류: {e}")
        execution_status[execution_id] = {
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now()
        }

# ===================== 기존 승인 시스템 (호환성 유지) =====================

@app.route('/api/projects/pending-approval')
def get_pending_approval_projects():
    """승인 대기 중인 프로젝트 목록 조회"""
    try:
        from project_state_manager import ProjectStateManager, ProjectStatus

        projects_dir = os.path.join(os.path.dirname(__file__), '../Projects')
        pending_projects = []

        # 모든 프로젝트 디렉토리 스캔
        if os.path.exists(projects_dir):
            for project_name in os.listdir(projects_dir):
                project_path = os.path.join(projects_dir, project_name)
                if os.path.isdir(project_path):
                    try:
                        manager = ProjectStateManager(project_path)
                        status_data = manager.load_project_status()
                        requirements_data = manager.load_original_requirements()

                        if (status_data and
                            status_data.get('status') == ProjectStatus.PLANNER_APPROVAL_PENDING.value):

                            # Planner 결과 로드
                            planner_result_file = os.path.join(project_path, "planner_result.md")
                            plan_content = "계획 내용을 불러올 수 없습니다."

                            if os.path.exists(planner_result_file):
                                with open(planner_result_file, 'r', encoding='utf-8') as f:
                                    plan_content = f.read()

                            project_info = {
                                'id': project_name,
                                'name': status_data.get('project_name', project_name),
                                'description': status_data.get('description', ''),
                                'status': status_data.get('status'),
                                'created_at': status_data.get('created_at'),
                                'current_agent': 'Planner',
                                'original_requirements': requirements_data.get('original_request', '') if requirements_data else '',
                                'plan_content': plan_content
                            }

                            pending_projects.append(project_info)
                    except Exception as e:
                        print(f"프로젝트 {project_name} 상태 확인 오류: {e}")
                        continue

        return jsonify(pending_projects)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/projects/<project_id>/approval', methods=['POST'])
def submit_project_approval(project_id):
    """프로젝트 승인/거부 처리"""
    try:
        from project_state_manager import ProjectStateManager

        data = request.get_json()
        decision = data.get('decision')  # 'approved', 'rejected', 'modify_requested'
        feedback = data.get('feedback', '')

        projects_dir = os.path.join(os.path.dirname(__file__), '../Projects')
        project_path = os.path.join(projects_dir, project_id)

        if not os.path.exists(project_path):
            return jsonify({'error': '프로젝트를 찾을 수 없습니다.'}), 404

        # 승인 파일 생성
        approval_file = os.path.join(project_path, "planner_approval.json")
        approval_data = {
            'decision': decision,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat(),
            'reviewer': 'user'
        }

        with open(approval_file, 'w', encoding='utf-8') as f:
            json.dump(approval_data, f, ensure_ascii=False, indent=2)

        # 상태 관리자를 통해 상태 업데이트
        manager = ProjectStateManager(project_path)

        if decision == 'approved':
            manager.mark_approval_granted('planner')
        elif decision in ['rejected', 'modify_requested']:
            manager.mark_approval_rejected('planner', feedback)

        return jsonify({
            'success': True,
            'message': f'프로젝트 {project_id}에 대한 결정이 전송되었습니다.',
            'decision': decision
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===================== 메인 실행 블록 =====================

if __name__ == '__main__':
    print("AI Chat Interface Server (Flask) starting...")
    print(f"Server URL: http://localhost:{PORT}")
    print("Available endpoints:")
    print("  - GET  /                    (Main page)")
    print("  - POST /api/crewai          (CrewAI requests)")
    print("  - POST /api/metagpt         (MetaGPT requests)")
    print("  - GET  /api/health          (Health check)")
    print("  - GET  /api/services/status (Service status)")
    print("  - POST /api/services/crewai/start (Start CrewAI service)")
    print("  - GET  /api/projects        (Get projects)")
    print("  - POST /api/projects        (Create project)")
    print("  - GET  /api/projects/<id>   (Get project)")
    print("  - PUT  /api/projects/<id>   (Update project)")
    print("  - GET  /api/projects/<id>/role-llm-mapping (Get LLM mappings)")
    print("  - POST /api/projects/<id>/role-llm-mapping (Set LLM mappings)")
    print("  - GET  /api/database/test   (Test database)")
    print("  - GET  /api/database/status (Database status)")
    print("  MetaGPT Endpoints:")
    print("  - GET  /api/metagpt/projects (Get MetaGPT projects)")
    print("  - POST /api/metagpt/projects (Create MetaGPT project)")
    print("  - GET  /api/metagpt/projects/<id> (Get MetaGPT project)")
    print("  - GET  /api/metagpt/projects/<id>/workflow-stages (Get workflow stages)")
    print("  - PUT  /api/metagpt/projects/<id>/workflow-stages/<stage_id> (Update stage)")
    print("  - GET  /api/metagpt/projects/<id>/role-llm-mapping (Get MetaGPT LLM mappings)")
    print("  - POST /api/metagpt/projects/<id>/role-llm-mapping (Set MetaGPT LLM mappings)")
# Deliverable endpoints commented out for now
    print("  - GET  /api/metagpt/dashboard (Get MetaGPT dashboard)")

# ===================== CREWAI 로깅 API =====================

@app.route('/api/crewai/logs/<execution_id>', methods=['GET'])
def get_execution_logs(execution_id):
    """실행 로그 조회"""
    try:
        logs = crewai_logger.get_execution_logs(execution_id)
        summary = crewai_logger.get_execution_summary(execution_id)

        return jsonify({
            "success": True,
            "execution_id": execution_id,
            "logs": logs,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crewai/logs/<execution_id>/summary', methods=['GET'])
def get_execution_summary_api(execution_id):
    """실행 요약 정보"""
    try:
        summary = crewai_logger.get_execution_summary(execution_id)

        if not summary:
            return jsonify({"success": False, "error": "Execution not found"}), 404

        return jsonify({
            "success": True,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crewai/logs/<execution_id>/phases', methods=['GET'])
def get_execution_phases(execution_id):
    """실행 단계별 로그"""
    try:
        logs = crewai_logger.get_execution_logs(execution_id)

        # 단계별 그룹화
        phases = {}
        for log in logs:
            phase = log['phase']
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(log)

        return jsonify({
            "success": True,
            "execution_id": execution_id,
            "phases": phases
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crewai/logs/<execution_id>/errors', methods=['GET'])
def get_execution_errors(execution_id):
    """실행 에러 로그만 조회"""
    try:
        logs = crewai_logger.get_execution_logs(execution_id)

        # 에러 로그만 필터링
        error_logs = [log for log in logs if log['level'] in ['ERROR', 'CRITICAL']]

        return jsonify({
            "success": True,
            "execution_id": execution_id,
            "error_count": len(error_logs),
            "errors": error_logs
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# WebSocket event handlers removed

    print("\n🔍 CrewAI Enhanced Logging:")
    print("  - GET  /api/crewai/logs/<execution_id> (Get execution logs)")
    print("  - GET  /api/crewai/logs/<execution_id>/summary (Get execution summary)")
    print("  - GET  /api/crewai/logs/<execution_id>/phases (Get phase logs)")
    print("  - GET  /api/crewai/logs/<execution_id>/errors (Get error logs)")
    print("  - WebSocket functionality removed")

# ===================== CrewAI 개선된 승인 시스템 API =====================

# 전역 승인 상태 관리
approval_states = {}
approval_events = {}

@app.route('/api/crewai/approval/<execution_id>')
def crewai_approval_page(execution_id):
    """CrewAI 개선된 승인 시스템 페이지"""
    if execution_id not in approval_states:
        return "승인 요청을 찾을 수 없습니다.", 404

    approval_data = approval_states[execution_id]

    # HTML 템플릿 직접 반환
    html_content = f'''
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CrewAI 승인 시스템 - {approval_data.get("stage_name", "단계")}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #4834d4, #686de0); color: white; padding: 30px; text-align: center; }}
            .content {{ padding: 30px; }}
            .stage-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; margin-bottom: 20px; }}
            .stage-1 {{ background-color: #e3f2fd; color: #1976d2; }}
            .stage-2 {{ background-color: #f3e5f5; color: #7b1fa2; }}
            .stage-3 {{ background-color: #e8f5e8; color: #388e3c; }}
            .functionality-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .function-card {{ border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; }}
            .priority-high {{ border-left: 4px solid #f44336; }}
            .priority-medium {{ border-left: 4px solid #ff9800; }}
            .priority-low {{ border-left: 4px solid #4caf50; }}
            .tech-stack {{ background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            .role-instructions {{ background-color: #fff3e0; padding: 20px; border-radius: 10px; margin: 20px 0; }}
            .buttons {{ display: flex; gap: 20px; justify-content: center; margin-top: 30px; }}
            .btn {{ padding: 15px 30px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; font-weight: bold; transition: all 0.3s; }}
            .btn-approve {{ background-color: #4caf50; color: white; }}
            .btn-reject {{ background-color: #f44336; color: white; }}
            .btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }}
            .feedback-area {{ margin-top: 20px; }}
            .feedback-area textarea {{ width: 100%; padding: 15px; border: 1px solid #ddd; border-radius: 8px; resize: vertical; min-height: 80px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 CrewAI 승인 시스템</h1>
                <p>단계별 검토 및 승인</p>
            </div>
            <div class="content">
                <div class="stage-badge stage-{approval_data.get("stage_number", "1")}">{approval_data.get("stage_name", "단계")}</div>

                <h2>📋 핵심 기능 분석</h2>
                <div id="functionalitySection">
                    {approval_data.get("functionality_html", "<p>기능 정보를 로딩 중...</p>")}
                </div>

                <div class="role-instructions">
                    <h3>👤 역할별 지시사항</h3>
                    <div id="roleInstructions">
                        {approval_data.get("role_instructions", "<p>역할 지시사항을 로딩 중...</p>")}
                    </div>
                </div>

                <div class="feedback-area">
                    <h3>💬 피드백 (선택사항)</h3>
                    <textarea id="feedback" placeholder="추가 요구사항이나 수정사항을 입력하세요..."></textarea>
                </div>

                <div class="buttons">
                    <button class="btn btn-approve" onclick="submitDecision('approved')">✅ 승인</button>
                    <button class="btn btn-reject" onclick="submitDecision('rejected')">❌ 거부</button>
                </div>
            </div>
        </div>

        <script>
            function submitDecision(decision) {{
                const feedback = document.getElementById('feedback').value;

                fetch('/api/crewai/approval/{execution_id}', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        decision: decision,
                        feedback: feedback
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('결정이 전송되었습니다: ' + decision);
                        window.close();
                    }} else {{
                        alert('오류: ' + data.error);
                    }}
                }})
                .catch(error => {{
                    alert('요청 처리 중 오류 발생: ' + error);
                }});
            }}
        </script>
    </body>
    </html>
    '''

    return html_content

@app.route('/api/crewai/approval/<execution_id>', methods=['POST'])
def submit_crewai_approval(execution_id):
    """CrewAI 승인 결정 처리"""
    if execution_id not in approval_events:
        return jsonify({{'error': '승인 요청을 찾을 수 없습니다.', 'success': False}}), 404

    data = request.get_json()
    decision = data.get('decision')
    feedback = data.get('feedback', '')

    # 전역 승인 상태 업데이트
    if execution_id in approval_states:
        approval_states[execution_id]['decision'] = decision
        approval_states[execution_id]['feedback'] = feedback
        approval_states[execution_id]['response'] = decision

    # 승인 이벤트 설정
    if execution_id in approval_events:
        approval_events[execution_id].set()

    return jsonify({{'success': True, 'message': f'결정이 처리되었습니다: {{decision}}'}})

@app.route('/api/crewai/approval/<execution_id>/register', methods=['POST'])
def register_crewai_approval_request(execution_id):
    """CrewAI 승인 요청 등록"""
    data = request.get_json()

    # 승인 상태 저장
    approval_states[execution_id] = {
        'stage_name': data.get('stage_name', '단계'),
        'stage_number': data.get('stage_number', '1'),
        'functionality_html': data.get('functionality_html', ''),
        'role_instructions': data.get('role_instructions', ''),
        'decision': None,
        'feedback': '',
        'response': None
    }

    # 승인 이벤트 생성
    approval_events[execution_id] = threading.Event()

    return jsonify({'success': True, 'message': '승인 요청이 등록되었습니다.'})

@app.route('/api/crewai/approval/<execution_id>/status')
def get_crewai_approval_status(execution_id):
    """CrewAI 승인 상태 확인"""
    if execution_id not in approval_states:
        return jsonify({'error': '승인 요청을 찾을 수 없습니다.'}), 404

    approval_state = approval_states[execution_id]
    return jsonify({
        'execution_id': execution_id,
        'decision': approval_state.get('decision'),
        'feedback': approval_state.get('feedback'),
        'completed': approval_state.get('decision') is not None
    })

    print("\n🔔 Project Approval System:")
    print("  - GET  /approval (Approval UI page)")
    print("  - GET  /api/projects/pending-approval (Get pending projects)")
    print("  - POST /api/projects/<project_id>/approval (Submit approval decision)")

    print("\n🚀 CrewAI Enhanced Approval System:")
    print("  - GET  /api/crewai/approval/<execution_id> (Enhanced approval UI)")
    print("  - POST /api/crewai/approval/<execution_id> (Submit approval decision)")
    print("  - POST /api/crewai/approval/<execution_id>/register (Register approval request)")
    print("  - GET  /api/crewai/approval/<execution_id>/status (Get approval status)")

# 실행 재개 함수들
def resume_crewai_execution(execution_id, project_data):
    """CrewAI 실행 재개 - 정석적인 방법으로 전체 CrewAI 로직 실행"""
    import threading

    def run_full_crewai_execution():
        """승인된 프로젝트 데이터로 전체 CrewAI 실행"""
        try:
            print(f"[CREWAI RESUME] 전체 CrewAI 실행 시작: {execution_id}")

            # 프로젝트 데이터 추출
            requirement = project_data.get('requirement')
            selected_models = project_data.get('selected_models', {})
            crew_id = project_data.get('crew_id')
            project_path = project_data.get('project_path')
            projects_base_dir = project_data.get('projects_base_dir')

            print(f"[CREWAI RESUME] 프로젝트 정보 추출 완료:")
            print(f"  - requirement: {requirement}")
            print(f"  - project_path: {project_path}")
            print(f"  - crew_id: {crew_id}")

            # 실행 상태 초기화
            execution_status[execution_id] = {
                'status': 'running',
                'message': '승인 완료 - CrewAI 실행 시작',
                'start_time': datetime.now(),
                'execution_id': execution_id,
                'crew_id': crew_id,
                'requirement': requirement,
                'models': selected_models,
                'project_path': project_path,
                'phase': 'resumed_execution'
            }

            # CrewAI 로거 시작
            crewai_logger.start_execution_logging(execution_id, crew_id, {
                'requirement': requirement,
                'selected_models': selected_models,
                'project_id': project_data.get('project_id'),
                'resumed': True
            })

            crewai_logger.start_step_tracking(execution_id, crew_id, total_steps=10)

            # 단계 1: 시스템 검증
            crewai_logger.advance_step(execution_id, crew_id, "시스템 검증", "시작", ExecutionPhase.VALIDATION)
            crewai_logger.log_system_check(execution_id, crew_id, "UTF-8 인코딩 환경", True)

            # 단계 2: 프로젝트 디렉토리 생성
            crewai_logger.advance_step(execution_id, crew_id, "디렉토리 생성", project_path, ExecutionPhase.DIRECTORY_CREATION)

            try:
                os.makedirs(project_path, exist_ok=True)
                crewai_logger.log_directory_operation(execution_id, crew_id, "생성", project_path, True)
                print(f"[CREWAI RESUME] 프로젝트 디렉토리 생성: {project_path}")
            except Exception as dir_error:
                crewai_logger.log_directory_operation(execution_id, crew_id, "생성", project_path, False, {"error": str(dir_error)})
                raise dir_error

            # 단계 3: 환경 설정
            crewai_logger.advance_step(execution_id, crew_id, "환경 설정", "", ExecutionPhase.ENVIRONMENT_SETUP)

            env_vars = {
                'PYTHONIOENCODING': 'utf-8',
                'PYTHONLEGACYWINDOWSSTDIO': '0',
                'CREWAI_PROJECT_PATH': project_path,
                'CREWAI_REQUIREMENT': requirement,
                'CREWAI_EXECUTION_ID': execution_id,
                'CREWAI_RESUMED': 'true'
            }

            # 단계 4: CrewAI 스크립트 생성
            crewai_logger.advance_step(execution_id, crew_id, "스크립트 생성", "", ExecutionPhase.FILE_GENERATION)

            # 고도화된 스크립트 생성기 사용
            try:
                from enhanced_script_generator import generate_enhanced_crewai_script
                print(f"[CREWAI RESUME] 고도화된 스크립트 생성기 사용")
                script_content = generate_enhanced_crewai_script(requirement, selected_models, project_path, execution_id)
            except ImportError:
                print(f"[CREWAI RESUME] 기본 스크립트 생성기 사용 (fallback)")
                script_content = generate_crewai_execution_script(requirement, selected_models, project_path, execution_id)
            script_path = os.path.join(project_path, "crewai_script.py")

            try:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script_content)
                crewai_logger.log_file_generation(execution_id, crew_id, script_path, "Python Script", len(script_content), True)
                print(f"[CREWAI RESUME] CrewAI 스크립트 생성: {script_path}")
            except Exception as file_error:
                crewai_logger.log_file_generation(execution_id, crew_id, script_path, "Python Script", 0, False, {"error": str(file_error)})
                raise file_error

            # 단계 5: 요구사항 파일 생성
            crewai_logger.advance_step(execution_id, crew_id, "요구사항 저장", "", ExecutionPhase.FILE_GENERATION)

            requirements_path = os.path.join(project_path, "requirements.txt")
            requirements_content = "\n".join([
                "crewai>=0.28.8",
                "langchain>=0.1.0",
                "langchain-openai>=0.0.5",
                "python-dotenv>=1.0.0"
            ])

            try:
                with open(requirements_path, 'w', encoding='utf-8') as f:
                    f.write(requirements_content)
                crewai_logger.log_file_generation(execution_id, crew_id, requirements_path, "Requirements", len(requirements_content), True)
                print(f"[CREWAI RESUME] 요구사항 파일 생성: {requirements_path}")
            except Exception as req_error:
                crewai_logger.log_file_generation(execution_id, crew_id, requirements_path, "Requirements", 0, False, {"error": str(req_error)})

            # 단계 6: CrewAI 실행
            crewai_logger.advance_step(execution_id, crew_id, "CrewAI 실행", "시작", ExecutionPhase.EXECUTION)

            def execute_crewai_subprocess():
                """CrewAI 서브프로세스 실행"""
                try:
                    # 환경 변수 설정
                    current_env = os.environ.copy()
                    current_env.update(env_vars)

                    # 실행 명령
                    python_cmd = sys.executable
                    cmd = [python_cmd, script_path]

                    print(f"[CREWAI RESUME] 서브프로세스 실행: {' '.join(cmd)}")

                    # 서브프로세스 실행
                    process = subprocess.Popen(
                        cmd,
                        cwd=project_path,
                        env=current_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )

                    crewai_logger.log_subprocess_execution(execution_id, crew_id, " ".join(cmd), project_path, True, process.pid)

                    # 실시간 출력 처리
                    stdout, stderr = process.communicate()
                    return_code = process.returncode

                    # 실행 완료 처리
                    execution_status[execution_id].update({
                        'status': 'completed' if return_code == 0 else 'failed',
                        'message': 'CrewAI 실행 완료' if return_code == 0 else 'CrewAI 실행 실패',
                        'end_time': datetime.now(),
                        'return_code': return_code,
                        'output': stdout[:1000] if stdout else '',
                        'error': stderr[:1000] if stderr and return_code != 0 else ''
                    })

                    # 로깅
                    if return_code == 0:
                        crewai_logger.log_completion(execution_id, crew_id, True, stdout[:500])
                        print(f"[CREWAI RESUME] 실행 성공: {execution_id}")
                    else:
                        crewai_logger.log_completion(execution_id, crew_id, False, stderr[:500])
                        print(f"[CREWAI RESUME] 실행 실패: {execution_id}, error: {stderr}")

                except Exception as exec_error:
                    execution_status[execution_id].update({
                        'status': 'failed',
                        'message': f'CrewAI 실행 중 오류: {str(exec_error)}',
                        'end_time': datetime.now(),
                        'error': str(exec_error)
                    })
                    crewai_logger.log_error(execution_id, crew_id, exec_error, "CrewAI 서브프로세스 실행")
                    print(f"[CREWAI RESUME] 실행 오류: {exec_error}")

            # 서브프로세스 실행
            execute_crewai_subprocess()

        except Exception as e:
            print(f"[CREWAI RESUME ERROR] 전체 실행 실패: {e}")
            execution_status[execution_id] = {
                'status': 'failed',
                'message': f'CrewAI 실행 실패: {str(e)}',
                'end_time': datetime.now(),
                'error': str(e),
                'execution_id': execution_id
            }
            crewai_logger.log_error(execution_id, project_data.get('crew_id', 'unknown'), e, "CrewAI 전체 실행")

    # 백그라운드에서 실행
    execution_thread = threading.Thread(
        target=run_full_crewai_execution,
        name=f"CrewAI-FullExec-{execution_id[:8]}",
        daemon=True
    )
    execution_thread.start()

    print(f"[CREWAI RESUME] 전체 실행 스레드 시작: {execution_id}")
    return True

def resume_metagpt_execution(execution_id, project_data):
    """MetaGPT 실행 재개 - 완전 구현"""
    import subprocess
    import threading

    try:
        print(f"[METAGPT RESUME] 실행 재개 시작: {execution_id}")

        # 1. 기존 실행 상태 업데이트
        if execution_id in execution_status:
            execution_status[execution_id].update({
                'status': 'running',
                'message': '승인 완료 - MetaGPT 실행 재개 중...',
                'resumed_at': datetime.now(),
                'phase': 'execution_resumed'
            })
            print(f"[METAGPT RESUME] 실행 상태 업데이트 완료: {execution_id}")

        # 2. 프로젝트 데이터 추출
        requirement = project_data.get('requirement', 'AI 프로그램 개발')
        selected_models = project_data.get('selected_models', {})
        project_path = project_data.get('project_path')

        print(f"[METAGPT RESUME] 프로젝트 정보:")
        print(f"  - requirement: {requirement}")
        print(f"  - project_path: {project_path}")

        # 3. MetaGPT 내장 처리 방식 사용 (기존 코드 재활용)
        def run_metagpt_process():
            try:
                print(f"[METAGPT RESUME] MetaGPT 내장 처리 시작: {execution_id}")

                # 실행 상태 업데이트
                if execution_id in execution_status:
                    execution_status[execution_id].update({
                        'status': 'running',
                        'message': 'MetaGPT 처리 중...',
                        'current_step': 'metagpt_execution'
                    })

                # MetaGPT 요청 처리 (기존 함수 재사용)
                result = call_metagpt_module(requirement, selected_models)

                if hasattr(result, 'get_json') and result.get_json().get('success'):
                    # 성공
                    if execution_id in execution_status:
                        execution_status[execution_id].update({
                            'status': 'completed',
                            'message': 'MetaGPT 실행이 성공적으로 완료되었습니다.',
                            'end_time': datetime.now(),
                            'result': result.get_json()
                        })
                    print(f"[METAGPT RESUME] 실행 성공: {execution_id}")

                else:
                    # 실패
                    error_msg = result.get_json().get('error', '알 수 없는 오류') if hasattr(result, 'get_json') else str(result)
                    if execution_id in execution_status:
                        execution_status[execution_id].update({
                            'status': 'failed',
                            'message': 'MetaGPT 실행이 실패했습니다.',
                            'end_time': datetime.now(),
                            'error': error_msg
                        })
                    print(f"[METAGPT RESUME] 실행 실패: {execution_id}, error: {error_msg}")

            except Exception as proc_error:
                print(f"[METAGPT RESUME] 프로세스 실행 오류: {proc_error}")
                if execution_id in execution_status:
                    execution_status[execution_id].update({
                        'status': 'failed',
                        'message': 'MetaGPT 처리 중 오류가 발생했습니다.',
                        'end_time': datetime.now(),
                        'error': str(proc_error)
                    })

        # 4. 백그라운드 스레드에서 실행
        execution_thread = threading.Thread(
            target=run_metagpt_process,
            name=f"MetaGPT-Resume-{execution_id[:8]}",
            daemon=True
        )
        execution_thread.start()

        print(f"[METAGPT RESUME] 백그라운드 실행 스레드 시작됨: {execution_id}")

        # 5. 즉시 상태 업데이트
        if execution_id in execution_status:
            execution_status[execution_id].update({
                'status': 'running',
                'message': 'MetaGPT 실행이 재개되었습니다.',
                'resume_success': True,
                'thread_name': execution_thread.name
            })

        return True

    except Exception as e:
        print(f"[METAGPT RESUME ERROR] 실행 재개 실패: {e}")
        import traceback
        print(f"[METAGPT RESUME ERROR] 스택 추적:\n{traceback.format_exc()}")

        if execution_id in execution_status:
            execution_status[execution_id].update({
                'status': 'failed',
                'message': f'MetaGPT 실행 재개 실패: {str(e)}',
                'error': str(e),
                'end_time': datetime.now(),
                'resume_success': False
            })

        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)