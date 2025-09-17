# -*- coding: utf-8 -*-
"""
AI Chat Interface - Flask Integration Server
Single Python server integrating CrewAI and MetaGPT
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime
import requests

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
CORS(app)

# Port configuration - 통합 포트
PORT = 3000

# 라우팅 설정
CREWAI_URL = "http://localhost:5000"  # 내부 CrewAI 서버
METAGPT_URL = "http://localhost:8000"  # 내부 MetaGPT 서버

# Global variables
execution_status = {}


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


@app.route('/<path:filename>')
def serve_static(filename):
    """Static file serving"""
    return send_from_directory('.', filename)


# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'message': 'AI Chat Interface Server is running',
        'server': 'Flask (Python)',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'crewai': check_crewai_service(),
            'metagpt': check_metagpt_service()
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


@app.route('/api/projects', methods=['GET'])
def get_projects_list():
    """프로젝트 목록 조회"""
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

    app.run(host='0.0.0.0', port=PORT, debug=True)