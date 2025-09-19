# -*- coding: utf-8 -*-
"""
AI Chat Interface - Flask Integration Server
Single Python server integrating CrewAI and MetaGPT
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
import requests
from functools import wraps
from dotenv import load_dotenv
import uuid
import gevent
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Import database module
from database import db
from security_utils import validate_request_data, check_request_security
from template_api import template_bp
from ollama_client import ollama_client
from websocket_manager import init_websocket_manager, get_websocket_manager
from realtime_progress_tracker import global_progress_tracker

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

# Flask-SocketIO 설정
socketio = SocketIO(app,
                   cors_allowed_origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
                   async_mode='threading',
                   logger=True,
                   engineio_logger=True)

# CORS 설정 강화
CORS(app,
     origins=['http://localhost:3000', 'http://127.0.0.1:3000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True,
     max_age=3600)

# Register blueprints
app.register_blueprint(template_bp)

# Import and register template routes
try:
    from template_api_routes import template_routes
    app.register_blueprint(template_routes)
    print("✅ 템플릿 API 라우트 등록 완료")
except ImportError as e:
    print(f"⚠️ 템플릿 API 라우트 등록 실패: {e}")

# Supabase 클라이언트 설정
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
else:
    supabase = None
    print("⚠️ Supabase 설정이 필요합니다. .env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY를 추가하세요.")

# CrewAI 관련 설정
PROJECTS_BASE_DIR = os.path.join(os.path.dirname(current_dir), 'CrewAi')
execution_status = {}  # 전역 변수로 실행 상태 관리
clients = {}  # WebSocket 클라이언트 관리

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' http://localhost:*"

    return response

# Port configuration - 통합 포트
PORT = 3000

# 라우팅 설정
CREWAI_URL = "http://localhost:5000"  # 내부 CrewAI 서버
METAGPT_URL = "http://localhost:8000"  # 내부 MetaGPT 서버

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

@app.route('/metagpt')
def metagpt_interface():
    """MetaGPT 인터페이스"""
    return send_from_directory('.', 'metagpt.html')

@app.route('/templates')
def templates_interface():
    """프로젝트 템플릿 인터페이스"""
    return send_from_directory('.', 'templates.html')


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
        'services': {
            'crewai': check_crewai_service(),
            'metagpt': check_metagpt_service()
        },
        'database': {
            'connected': database_status.get('connected', False),
            'message': database_status.get('message', ''),
            'simulation_mode': database_status.get('simulation_mode', False)
        }
    })


def check_crewai_service():
    """Check CrewAI service status"""
    try:
        # Check if CrewAI server is running
        response = requests.get(f'{CREWAI_URL}/api/projects', timeout=2)
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
    """Handle CrewAI requests"""
    data = request.get_json()
    requirement = data.get('requirement')
    selected_models = data.get('selectedModels', {})

    if not requirement:
        return jsonify({'error': 'Requirement is required'}), 400

    try:
        print(f'CrewAI request: {requirement}')
        print(f'Selected models: {selected_models}')

        # Check if CrewAI server is running
        if check_crewai_service() == 'available':
            # Forward request to CrewAI server
            crewai_response = requests.post(f'{CREWAI_URL}/api/crews', {
                'requirement': requirement,
                'models': selected_models
            }, timeout=30)

            if crewai_response.status_code == 200:
                return jsonify(crewai_response.json())
            else:
                return jsonify({
                    'error': 'CrewAI server error',
                    'details': crewai_response.text
                }), 500
        else:
            # Simulation response if CrewAI server is not running
            return jsonify({
                'success': True,
                'requirement': requirement,
                'result': f'CrewAI team analyzed "{requirement}" project.\n\nProceeding with collaboration-based approach.',
                'models_used': selected_models,
                'agents_involved': ["Manager", "Researcher", "Designer", "Developer", "Tester"],
                'note': 'CrewAI server is not running, responding in simulation mode. To start CrewAI server, please run it on port 5000.'
            })

    except requests.RequestException as e:
        return jsonify({
            'error': 'CrewAI connection failed',
            'details': str(e)
        }), 500
    except Exception as e:
        return jsonify({
            'error': 'Error processing CrewAI request',
            'details': str(e)
        }), 500


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
                'url': 'http://localhost:5000'
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
            'url': 'http://localhost:5000'
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
    result = db.get_projects(limit)

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

@app.route('/api/v2/auth/token', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
@validate_json_input()
def generate_auth_token():
    """Generate authentication token"""
    data = request.get_json()

    # For demo purposes, generate token with provided user data
    user_data = {
        'id': data.get('user_id', 'demo-user'),
        'email': data.get('email', 'demo@example.com'),
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
    env = os.environ.copy()
    project_name = None
    output_path = None

    # 크루 생성기('creator')인 경우 특별 처리
    is_creating_crew = inputs.pop('is_crew_creator', None) == "true"

    try:
        if is_creating_crew:
            project_name = inputs.get('project_name', 'new-crew-project')

        # 실행 상태 업데이트
        execution_status[execution_id].update({
            "progress": 25,
            "message": "프로그램을 실행 중입니다..."
        })

        for key, value in inputs.items():
            env_key = f"CREWAI_{key.upper()}"
            env[env_key] = str(value)

        # 크루 생성기일 경우, 출력 경로를 환경 변수에 추가
        if is_creating_crew:
            output_path = os.path.join(PROJECTS_BASE_DIR, project_name)
            env['CREWAI_OUTPUT_PATH'] = output_path

        # 실시간 로그 스트리밍을 위한 subprocess.Popen 사용
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

        # stdout, stderr 스트림을 실시간으로 읽기
        while True:
            output = process.stdout.readline()
            if output:
                full_output.append(output)

            if process.poll() is not None and not output:
                break

        # 프로세스 종료 후 최종 결과 처리
        return_code = process.poll()
        stderr_output = process.stderr.read()
        full_error.append(stderr_output)

        # 실행 완료 처리
        if return_code == 0:
            end_time = datetime.now()
            final_output = "".join(full_output)
            execution_status[execution_id].update({
                "status": "completed",
                "progress": 100,
                "message": "프로그램 실행이 완료되었습니다.",
                "output": final_output,
                "end_time": end_time
            })

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
            execution_status[execution_id].update({
                "status": "failed",
                "progress": 0,
                "message": "프로그램 실행 중 오류가 발생했습니다.",
                "error": error_message,
                "end_time": end_time
            })

    except Exception as e:
        end_time = datetime.now()
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

        # 'creator' 타입의 크루(예: 크루 생성기)는 programs 폴더에서 찾음
        if crew_info.get('crew_type') == 'creator':
            script_path = os.path.join(PROJECTS_BASE_DIR, 'crewai_platform', 'programs', crew_info['file_path'])
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

    app.run(host='0.0.0.0', port=PORT, debug=True)