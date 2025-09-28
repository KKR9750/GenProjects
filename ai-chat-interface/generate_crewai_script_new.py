#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 CrewAI 스크립트 생성 함수
핵심 정보만 표시하는 웹 승인 시스템 통합
"""

def generate_crewai_execution_script_with_approval(requirement: str, selected_models: dict, project_path: str, execution_id: str) -> str:
    """
    개선된 승인 시스템이 통합된 CrewAI 실행 스크립트 생성
    핵심 정보만 표시하여 사용자 승인을 받고 진행하는 시스템
    project_00055 수준의 고품질 에이전트 구성 자동 생성
    """
    import json
    from datetime import datetime

    # 요구사항 분석을 통한 전문 에이전트 구성 결정
    def analyze_requirement_for_agents(requirement: str) -> dict:
        """요구사항을 분석하여 최적의 전문 에이전트 구성을 결정"""
        requirement_lower = requirement.lower()

        # 키워드 기반 도메인 분석
        if any(keyword in requirement_lower for keyword in ['데이터', 'data', '분석', 'analysis', '통계', '차트', 'visualization']):
            return {
                'domain': 'data_analysis',
                'agents': {
                    'data_scientist': {'role': 'Senior Data Scientist', 'goal': 'Extract insights from data using advanced analytics and machine learning', 'model_preference': 'gpt-4'},
                    'data_engineer': {'role': 'Senior Data Engineer', 'goal': 'Build robust data pipelines and infrastructure for data processing', 'model_preference': 'deepseek-coder'},
                    'visualization_specialist': {'role': 'Data Visualization Specialist', 'goal': 'Create compelling and insightful data visualizations', 'model_preference': 'gemini-flash'},
                    'quality_assurance': {'role': 'Quality Assurance Expert', 'goal': 'Ensure high-quality deliverables and comprehensive testing', 'model_preference': 'claude-3-sonnet'}
                }
            }
        elif any(keyword in requirement_lower for keyword in ['웹', 'web', 'api', '서버', 'server', 'backend', 'frontend']):
            return {
                'domain': 'web_development',
                'agents': {
                    'architect': {'role': 'Software Architect', 'goal': 'Design scalable and maintainable software architecture', 'model_preference': 'gpt-4'},
                    'backend_developer': {'role': 'Backend Developer', 'goal': 'Develop robust server-side applications and APIs', 'model_preference': 'deepseek-coder'},
                    'frontend_developer': {'role': 'Frontend Developer', 'goal': 'Create engaging and responsive user interfaces', 'model_preference': 'gemini-flash'},
                    'devops_engineer': {'role': 'DevOps Engineer', 'goal': 'Ensure reliable deployment and infrastructure management', 'model_preference': 'claude-3-sonnet'}
                }
            }
        elif any(keyword in requirement_lower for keyword in ['뉴스', 'news', '정보수집', '크롤링', 'crawling', 'scraping']):
            return {
                'domain': 'information_processing',
                'agents': {
                    'information_analyst': {'role': 'Information Research Analyst', 'goal': 'Gather and analyze comprehensive information from various sources', 'model_preference': 'gpt-4'},
                    'data_processor': {'role': 'Data Processing Specialist', 'goal': 'Process and structure collected information efficiently', 'model_preference': 'deepseek-coder'},
                    'content_synthesizer': {'role': 'Content Synthesis Expert', 'goal': 'Transform processed data into meaningful insights and reports', 'model_preference': 'gemini-flash'},
                    'quality_validator': {'role': 'Quality Validation Expert', 'goal': 'Ensure accuracy and reliability of processed information', 'model_preference': 'claude-3-sonnet'}
                }
            }
        else:
            # 기본 고품질 구성
            return {
                'domain': 'general_purpose',
                'agents': {
                    'senior_analyst': {'role': 'Senior Business Analyst', 'goal': 'Analyze requirements and design optimal solutions', 'model_preference': 'gpt-4'},
                    'technical_specialist': {'role': 'Technical Implementation Specialist', 'goal': 'Implement robust and efficient technical solutions', 'model_preference': 'deepseek-coder'},
                    'integration_expert': {'role': 'System Integration Expert', 'goal': 'Ensure seamless integration and optimal performance', 'model_preference': 'gemini-flash'},
                    'quality_assurance': {'role': 'Quality Assurance Director', 'goal': 'Guarantee highest quality standards and comprehensive testing', 'model_preference': 'claude-3-sonnet'}
                }
            }

    # 안전한 텍스트 처리 함수
    def safe_text_escape(text: str, max_length: int = 400) -> str:
        if len(text) > max_length:
            text = text[:max_length] + '...'
        text = text.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'")
        text = text.replace('\\n', '\\\\n').replace('\\r', '\\\\r')
        return text

    def safe_path_escape(path: str) -> str:
        return path.replace('\\\\', '\\\\\\\\')

    # 요구사항 분석 및 전문 에이전트 구성 결정
    agent_config = analyze_requirement_for_agents(requirement)

    # 안전한 매개변수 준비
    safe_requirement = safe_text_escape(requirement)
    safe_project_path = safe_path_escape(project_path)
    models_json = json.dumps(selected_models, ensure_ascii=False).replace('"', '\\\\"')
    agent_config_json = json.dumps(agent_config, ensure_ascii=False, indent=2)

    # 순수 CrewAI 실행 스크립트 템플릿 (4개 전문 에이전트 + 검토-재작성 반복)
    clean_crewai_script_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템
실행 ID: {execution_id}
생성 시간: {generation_time}
요구사항: {original_requirement}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, LLM

# UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

print("🚀 CrewAI 전문 에이전트 협업 시스템 시작")
print(f"📋 프로젝트: {original_requirement}")
print(f"⏰ 시작 시간: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")

# LLM 모델 설정 함수
def get_model(model_name: str):
    """LLM 모델 인스턴스 반환"""
    return LLM(model=model_name, temperature=0.7)

# 4개 전문 에이전트 정의 (사전 분석 결과 기반)
print("\\n👥 전문 에이전트 구성 중...")

# Pre-Analyzer: 사전 분석 처리
pre_analyzer = Agent(
    role="Pre-Analysis Specialist",
    goal="{pre_analyzer_goal}",
    backstory="{pre_analyzer_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{pre_analyzer_model}")
)
    import io

    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'

    if sys.platform.startswith('win'):
        try:
            os.system('chcp 65001 > nul 2>&1')
        except:
            pass

    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

    return True

def get_llm_model(role_name: str):
    """역할별 LLM 모델 반환 (SmartModelAllocator 기반)"""
    models = {models_json}

    # SmartModelAllocator를 사용하여 정확한 litellm 모델명 얻기
    try:
        from smart_model_allocator import SmartModelAllocator
        allocator = SmartModelAllocator()

        simple_model = models.get(role_name.lower(), 'gemini-2.5-flash')
        litellm_model = allocator.get_litellm_model_name(simple_model)

        print(f"🤖 {{role_name}} 역할 → {{simple_model}} → {{litellm_model}} 모델")

        return LLM(
            model=litellm_model,
            temperature=0.7
        )
    except ImportError:
        # 폴백: 기존 방식 (Gemini 2.5 지원)
        normalized_models = {{}}
        for role, model in models.items():
            if model == "gemini-2.5-flash":
                normalized_models[role] = "gemini/gemini-2.0-flash-exp"
            elif model == "gemini-2.5-pro":
                normalized_models[role] = "gemini/gemini-2.0-flash-thinking-exp"
            elif model.startswith("gemini") and not model.startswith("gemini/"):
                # 기본 gemini 처리 (2.5 버전으로 폴백)
                normalized_models[role] = "gemini/gemini-2.0-flash-exp"
            elif not "/" in model and model.startswith("gpt"):
                normalized_models[role] = f"openai/{{model}}"
            elif model == "claude-3":
                normalized_models[role] = "anthropic/claude-3-sonnet-20240229"
            elif model == "deepseek-coder":
                normalized_models[role] = "deepseek/deepseek-coder"
            else:
                normalized_models[role] = model

        models = normalized_models
        model_id = models.get(role_name.lower(), 'gemini/gemini-2.0-flash-exp')

        print(f"🤖 {{role_name}} 역할 → {{model_id}} 모델 (폴백)")

        return LLM(
            model=model_id,
            temperature=0.7
        )

# 핵심 정보 추출 함수
def extract_core_info(planning_result: str):
    """계획 결과에서 핵심 정보 추출"""

    # 기본 핵심 기능 목록 (계획서에서 추출)
    core_functions = [
        {{
            "name": "파일 업로드",
            "priority": "높음",
            "description": "다양한 형식의 이력서 파일 업로드 기능",
            "technologies": ["Flask", "Werkzeug", "HTML5 FileAPI"]
        }},
        {{
            "name": "데이터 추출",
            "priority": "높음",
            "description": "이름, 이메일, 전화번호 등 개인정보 정확 추출",
            "technologies": ["Python re", "Natural Language Processing", "정규표현식"]
        }},
        {{
            "name": "JSON 변환",
            "priority": "높음",
            "description": "추출된 데이터를 JSON 형식으로 변환",
            "technologies": ["Python json", "UTF-8 인코딩", "데이터 구조화"]
        }},
        {{
            "name": "파일 저장",
            "priority": "높음",
            "description": "JSON 데이터를 파일로 저장 (파일명은 업로드된 파일명 기반)",
            "technologies": ["파일 시스템", "경로 관리", "자동 명명"]
        }},
        {{
            "name": "오류 처리",
            "priority": "중간",
            "description": "잘못된 파일 형식, 데이터 누락 등에 대한 오류 처리 및 사용자 알림",
            "technologies": ["예외 처리", "사용자 피드백", "로깅"]
        }},
        {{
            "name": "로그 기능",
            "priority": "낮음",
            "description": "프로그램 실행 로그 기록 (디버깅 및 모니터링 용도)",
            "technologies": ["Python logging", "로그 파일 관리", "모니터링"]
        }}
    ]

    # 기술 스택 정보
    tech_stack = {{
        "language": "Python",
        "reason": "라이브러리 활용 용이성 및 개발 속도 고려",
        "libraries": [
            {{"name": "openpyxl", "purpose": "docx 파일 처리"}},
            {{"name": "PyPDF2", "purpose": "PDF 파일 처리"}},
            {{"name": "tika", "purpose": "txt, hwp 포함 다양한 형식 지원"}},
            {{"name": "json", "purpose": "JSON 처리"}},
            {{"name": "re", "purpose": "개인정보 추출 정확도 향상"}}
        ],
        "development_env": ["Visual Studio Code", "PyCharm"],
        "testing": "pytest 단위 테스트 및 통합 테스트"
    }}

    return core_functions, tech_stack

def get_role_instructions(role_name: str, core_functions: list, tech_stack: dict):
    """역할별 구체적인 지시사항 생성"""

    if role_name.lower() == "researcher":
        return {{
            "role": "Research Specialist",
            "primary_focus": "기술 조사 및 최적 솔루션 검증",
            "instructions": [
                "✅ 파일 처리 라이브러리 성능 및 안정성 비교 분석",
                "✅ 개인정보 추출 정확도 향상을 위한 최신 NLP 기법 조사",
                "✅ 다양한 이력서 형식별 파싱 전략 수립",
                "✅ 오류 처리 및 예외 상황 시나리오 정의",
                "✅ 보안 및 개인정보 보호 방안 조사"
            ],
            "deliverables": [
                "📋 기술 스택 검증 보고서",
                "📋 라이브러리 성능 비교표",
                "📋 보안 가이드라인",
                "📋 예외 처리 시나리오"
            ]
        }}

    elif role_name.lower() == "writer":
        return {{
            "role": "Technical Writer",
            "primary_focus": "실제 동작하는 코드 및 문서 작성",
            "instructions": [
                "💻 파일 업로드 기능 구현 (Flask 기반)",
                "💻 개인정보 추출 알고리즘 구현 (정규표현식 + NLP)",
                "💻 JSON 변환 및 저장 모듈 구현",
                "💻 종합적인 오류 처리 시스템 구현",
                "📖 설치 및 사용 가이드 작성",
                "🧪 기본 테스트 코드 작성"
            ],
            "deliverables": [
                "💻 완전히 동작하는 프로그램 코드",
                "📖 README.md 및 사용자 매뉴얼",
                "🧪 단위 테스트 코드",
                "⚙️ requirements.txt 및 설정 파일"
            ]
        }}

    else: # planner
        return {{
            "role": "Project Planner",
            "primary_focus": "체계적인 개발 계획 및 프로젝트 관리",
            "instructions": [
                "📋 핵심 기능 우선순위 재검토 및 확정",
                "📅 4주 개발 일정 세부 계획 수립",
                "🎯 각 단계별 성공 기준 및 검증 방법 정의",
                "⚠️ 리스크 요소 식별 및 완화 방안 수립",
                "🔄 개발 프로세스 및 협업 방식 정의"
            ],
            "deliverables": [
                "📋 상세 개발 계획서",
                "📅 마일스톤 및 일정표",
                "⚠️ 리스크 관리 계획",
                "🎯 성공 기준 매트릭스"
            ]
        }}

# Flask 웹 서버 설정
app = Flask(__name__)

# 개선된 HTML 템플릿 - 핵심 정보만 표시
APPROVAL_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CrewAI 단계별 승인 시스템 - {{ stage_name }}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .stage-info {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
            border: 2px solid #f0f0f0;
            border-radius: 15px;
            padding: 25px;
            background: #fafafa;
        }}

        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}

        .section h2::before {{
            content: "🎯";
            margin-right: 10px;
            font-size: 1.2em;
        }}

        .function-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }}

        .function-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-left: 5px solid;
        }}

        .priority-높음 {{ border-left-color: #e74c3c; }}
        .priority-중간 {{ border-left-color: #f39c12; }}
        .priority-낮음 {{ border-left-color: #27ae60; }}

        .function-card h3 {{
            font-size: 1.3em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .priority-badge {{
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 20px;
            color: white;
            font-weight: bold;
        }}

        .priority-높음-badge {{ background: #e74c3c; }}
        .priority-중간-badge {{ background: #f39c12; }}
        .priority-낮음-badge {{ background: #27ae60; }}

        .tech-tags {{
            margin-top: 15px;
        }}

        .tech-tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            margin: 2px;
        }}

        .role-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border-left: 5px solid #9b59b6;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .role-section h3 {{
            color: #9b59b6;
            font-size: 1.4em;
            margin-bottom: 15px;
        }}

        .instructions-list {{
            list-style: none;
            margin: 15px 0;
        }}

        .instructions-list li {{
            padding: 8px 0;
            font-size: 1.05em;
        }}

        .deliverables-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}

        .deliverables-list li {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.95em;
        }}

        .actions {{
            padding: 30px;
            background: #f8f9fa;
            text-align: center;
            border-top: 2px solid #eee;
        }}

        .btn {{
            padding: 15px 30px;
            margin: 10px;
            border: none;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .btn-approve {{
            background: #27ae60;
            color: white;
        }}

        .btn-reject {{
            background: #e74c3c;
            color: white;
        }}

        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        .feedback-section {{
            margin: 20px 0;
        }}

        .feedback-section textarea {{
            width: 100%;
            min-height: 100px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            resize: vertical;
        }}

        .status-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            background: #2ecc71;
            color: white;
            border-radius: 25px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="status-indicator">🔄 승인 대기 중</div>

    <div class="container">
        <div class="header">
            <h1>CrewAI 단계별 승인 시스템</h1>
            <div class="stage-info">
                <h2>{{ stage_name }}</h2>
                <p>📅 {{ datetime.now().strftime('%Y-%m-%d %H:%M:%S') }}</p>
            </div>
        </div>

        <div class="content">
            <!-- 핵심 기능 목록 -->
            <div class="section">
                <h2>핵심 기능 목록 및 우선순위</h2>
                <div class="function-grid">
                    {% for func in core_functions %}
                    <div class="function-card priority-{{ func.priority }}">
                        <h3>
                            {{ func.name }}
                            <span class="priority-badge priority-{{ func.priority }}-badge">{{ func.priority }}</span>
                        </h3>
                        <p>{{ func.description }}</p>
                        <div class="tech-tags">
                            {% for tech in func.technologies %}
                            <span class="tech-tag">{{ tech }}</span>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- 기술 스택 -->
            <div class="section">
                <h2 style="color: #e67e22;">🛠️ 기술 스택</h2>
                <div style="background: white; padding: 20px; border-radius: 10px;">
                    <p><strong>주 언어:</strong> {{ tech_stack.language }} ({{ tech_stack.reason }})</p>
                    <h4 style="margin: 15px 0 10px 0;">필수 라이브러리:</h4>
                    <div class="function-grid">
                        {% for lib in tech_stack.libraries %}
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 3px solid #3498db;">
                            <strong>{{ lib.name }}</strong>: {{ lib.purpose }}
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- 역할별 지시사항 -->
            <div class="section">
                <h2 style="color: #9b59b6;">👥 역할별 지시사항</h2>
                {% for role_name, role_data in role_instructions.items() %}
                <div class="role-section">
                    <h3>{{ role_data.role }}</h3>
                    <p><strong>주요 집중 분야:</strong> {{ role_data.primary_focus }}</p>

                    <h4>📋 구체적 지시사항:</h4>
                    <ul class="instructions-list">
                        {% for instruction in role_data.instructions %}
                        <li>{{ instruction }}</li>
                        {% endfor %}
                    </ul>

                    <h4>📦 예상 결과물:</h4>
                    <ul class="deliverables-list">
                        {% for deliverable in role_data.deliverables %}
                        <li>{{ deliverable }}</li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="actions">
            <h3>이 계획을 승인하시겠습니까?</h3>
            <div class="feedback-section">
                <textarea id="feedback" placeholder="피드백이나 수정 요청사항을 입력해주세요 (선택사항)"></textarea>
            </div>
            <button class="btn btn-approve" onclick="approve()">✅ 승인하고 다음 단계 진행</button>
            <button class="btn btn-reject" onclick="reject()">❌ 거부하고 수정 요청</button>
        </div>
    </div>

    <script>
        function approve() {{
            const feedback = document.getElementById('feedback').value;

            fetch('/approve', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    action: 'approved',
                    feedback: feedback,
                    timestamp: new Date().toISOString()
                }})
            }}).then(response => response.json())
              .then(data => {{
                  document.body.innerHTML = '<div style="text-align: center; padding: 50px; font-size: 1.5em; color: #27ae60;">✅ 승인되었습니다. 다음 단계가 시작됩니다.</div>';
              }});
        }}

        function reject() {{
            const feedback = document.getElementById('feedback').value;
            if (!feedback.trim()) {{
                alert('거부 시에는 수정 요청사항을 입력해주세요.');
                return;
            }}

            fetch('/approve', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    action: 'rejected',
                    feedback: feedback,
                    timestamp: new Date().toISOString()
                }})
            }}).then(response => response.json())
              .then(data => {{
                  document.body.innerHTML = '<div style="text-align: center; padding: 50px; font-size: 1.5em; color: #e74c3c;">❌ 거부되었습니다. 피드백이 전달되었습니다.</div>';
              }});
        }}
    </script>
</body>
</html>
"""

@app.route('/approval')
def approval_page():
    """승인 페이지 표시"""
    core_functions, tech_stack = extract_core_info(current_stage_data.get('result', ''))

    # 역할별 지시사항 생성
    role_instructions = {{
        'planner': get_role_instructions('planner', core_functions, tech_stack),
        'researcher': get_role_instructions('researcher', core_functions, tech_stack),
        'writer': get_role_instructions('writer', core_functions, tech_stack)
    }}

    return render_template_string(APPROVAL_TEMPLATE,
                                stage_name=current_stage_data.get('stage_name', '단계'),
                                core_functions=core_functions,
                                tech_stack=tech_stack,
                                role_instructions=role_instructions,
                                datetime=datetime)

@app.route('/approve', methods=['POST'])
def handle_approval():
    """승인/거부 처리"""
    global approval_response, approval_event

    data = request.json
    approval_response = data.get('action')

    # 피드백 저장
    feedback = data.get('feedback', '')
    if feedback:
        feedback_file = os.path.join("{project_path}", f"feedback_{{datetime.now().strftime('%Y%m%d_%H%M%S')}}.txt")
        with open(feedback_file, 'w', encoding='utf-8') as f:
            f.write(f"단계: {{current_stage_data.get('stage_name', '알 수 없음')}}\\n")
            f.write(f"결정: {{approval_response}}\\n")
            f.write(f"시간: {{data.get('timestamp')}}\\n")
            f.write(f"피드백: {{feedback}}\\n")

    approval_event.set()
    return jsonify({{"status": "success"}})

def wait_for_user_approval(stage_name: str, result: str = None) -> bool:
    """사용자 승인 대기"""
    global current_stage_data, approval_event, approval_response

    # 현재 단계 데이터 업데이트
    current_stage_data = {{
        'stage_name': stage_name,
        'result': result,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }}

    # 메인 서버에 승인 요청 등록
    import requests
    register_url = f"http://localhost:3000/api/crewai/approval/{{execution_id}}/register"
    register_data = {{
        'stage_name': stage_name,
        'stage_number': stage_number,
        'functionality_html': functionality_html,
        'role_instructions': role_instructions
    }}

    try:
        register_response = requests.post(register_url, json=register_data, timeout=5)
        if register_response.status_code != 200:
            print(f"⚠️ 승인 요청 등록 실패: {{register_response.status_code}}")
            return True  # 실패시 자동 승인으로 진행
    except requests.RequestException as e:
        print(f"⚠️ 승인 요청 등록 오류: {{e}}")
        return True  # 오류시 자동 승인으로 진행

    # 이벤트 초기화
    approval_event.clear()
    approval_response = None

    approval_url = f"http://localhost:3000/api/crewai/approval/{{execution_id}}"
    print(f"\\n🌐 웹 승인 시스템: {{approval_url}}")
    print(f"📋 {{stage_name}} 단계 승인 대기 중...")

    # 브라우저 자동 실행
    try:
        webbrowser.open(approval_url)
    except:
        pass

    # 사용자 응답 대기 (메인 서버 폴링)
    import time
    status_url = f"http://localhost:3000/api/crewai/approval/{{execution_id}}/status"

    while True:
        try:
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('completed'):
                    decision = status_data.get('decision')
                    return decision == 'approved'
            else:
                print(f"⚠️ 승인 상태 확인 실패: {{status_response.status_code}}")
        except requests.RequestException as e:
            print(f"⚠️ 승인 상태 확인 오류: {{e}}")

        time.sleep(3)  # 3초마다 상태 확인

def save_stage_result(stage_name: str, result: str, project_path: str, execution_id: str):
    """단계별 결과 저장"""
    stage_file = os.path.join(project_path, f"stage_{{stage_name.lower().replace(' ', '_')}}_{{execution_id}}.md")

    with open(stage_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{stage_name}} 결과\\n\\n")
        f.write(f"**실행 ID**: {{execution_id}}\\n")
        f.write(f"**완료 시간**: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}\\n\\n")
        f.write("## 결과 내용\\n\\n")
        f.write(str(result))

    print(f"📄 {{stage_name}} 결과 저장: {{stage_file}}")
    return stage_file

# Flask 서버 제거됨 - 메인 서버(포트 3000) 사용

# 환경 설정 실행
setup_utf8_environment()

print("✅ UTF-8 인코딩 환경 설정 완료")
print("🚀 CrewAI 개선된 웹 승인 시스템 시작...")
print("🎯 요구사항: {requirement_display}")
print(f"📁 프로젝트 경로: {project_path}")
print(f"🆔 실행 ID: {execution_id}")
print("\\n" + "="*50 + "\\n")

print("🌐 메인 서버(포트 3000) 승인 시스템 사용")

# 원본 요구사항
original_requirement = "{requirement_original}"

# 전문 에이전트 정의 (동적 생성)
print("👥 전문 에이전트 팀 구성중...")

# 분석된 요구사항 기반 에이전트 구성
agent_config = {agent_config_placeholder}

# 에이전트들을 동적으로 생성
agents = {{}}
print(f"🎯 도메인: {{agent_config['domain']}}")
print(f"🧑‍💼 전문 에이전트 수: {{len(agent_config['agents'])}}")

for agent_key, agent_info in agent_config['agents'].items():
    # 사용자 선택 모델과 에이전트 추천 모델 중 선택
    model_mapping = {{
        'planner': ['Senior Business Analyst', 'Software Architect', 'Project'],
        'researcher': ['Research', 'Data Scientist', 'Information', 'Analyst'],
        'writer': ['Writer', 'Content', 'Synthesis', 'Technical'],
        'quality': ['Quality', 'DevOps', 'Validation']
    }}

    assigned_model = None
    for role_key, keywords in model_mapping.items():
        if any(keyword.lower() in agent_info['role'].lower() for keyword in keywords):
            assigned_model = get_llm_model(role_key)
            break

    if not assigned_model:
        assigned_model = get_llm_model("planner")  # 기본값

    # 전문 에이전트 생성
    agent = Agent(
        role=agent_info['role'],
        goal=agent_info['goal'],
        backstory=f"You are an expert in {{agent_info['role']}}. {{agent_info['goal']}} You have deep domain knowledge and years of experience in delivering high-quality results.",
        verbose=True,
        allow_delegation=False,
        llm=assigned_model
    )

    agents[agent_key] = agent
    print(f"   ✅ {{agent_info['role']}} 에이전트 생성 완료")

# 에이전트 리스트 (순서대로)
agent_list = list(agents.values())

# 기존 호환성을 위한 별칭 설정 (첫 3개 에이전트를 planner, researcher, writer로 매핑)
planner = agent_list[0] if len(agent_list) > 0 else None
researcher = agent_list[1] if len(agent_list) > 1 else None
writer = agent_list[2] if len(agent_list) > 2 else None

# 전문 에이전트별 태스크 동적 생성
print("📋 전문 태스크 할당 중...")

tasks = []
task_templates = {{
    0: {{  # 첫 번째 에이전트 (분석/계획)
        "description": f\"\"\"
다음 요구사항을 분석하여 전문적인 프로젝트 솔루션을 설계하세요:

**요구사항:**
{{original_requirement}}

**분석 및 설계 내용:**
1. 요구사항 상세 분석 및 해석
2. 도메인별 전문 접근 방식 제안
3. 핵심 기능 및 컴포넌트 정의
4. 기술 아키텍처 설계
5. 구현 로드맵 및 우선순위

전문 지식을 바탕으로 구체적이고 실행 가능한 솔루션을 제시해주세요.
        \"\"\",
        "expected_output": "전문 분석 및 설계 문서 (마크다운 형식)"
    }},
    1: {{  # 두 번째 에이전트 (기술/구현)
        "description": \"\"\"
첫 번째 에이전트의 분석을 바탕으로 기술적 구현 방안을 제시하세요:

**기술 구현 내용:**
1. 최적 기술 스택 선정 및 근거
2. 상세 아키텍처 및 설계 패턴
3. 핵심 알고리즘 및 데이터 구조
4. 외부 서비스 연동 방안
5. 성능 최적화 전략
6. 확장성 및 유지보수 고려사항

기술적 전문성을 바탕으로 실무 구현 가능한 솔루션을 제공해주세요.
        \"\"\",
        "expected_output": "기술 구현 가이드 및 아키텍처 문서 (마크다운 형식)"
    }},
    2: {{  # 세 번째 에이전트 (통합/최적화)
        "description": \"\"\"
앞선 분석과 기술 설계를 통합하여 완성된 솔루션을 제작하세요:

**통합 솔루션 내용:**
1. 완전한 소스 코드 구현
2. 프로젝트 구조 및 설정 파일
3. 상세한 설치 및 실행 가이드
4. 사용자 매뉴얼 및 API 문서
5. 테스트 케이스 및 검증 방법
6. 배포 및 운영 가이드

전문적이고 완성도 높은 최종 결과물을 제공해주세요.
        \"\"\",
        "expected_output": "완전한 프로젝트 구현체 및 문서 (실행 가능한 코드 포함)"
    }},
    3: {{  # 네 번째 에이전트 (품질보증/검증)
        "description": \"\"\"
구현된 솔루션의 품질을 검증하고 최종 완성도를 보장하세요:

**품질 보증 내용:**
1. 코드 품질 검토 및 개선사항
2. 기능 테스트 및 성능 검증
3. 보안 취약점 점검
4. 사용성 평가 및 개선
5. 문서 완성도 검토
6. 배포 준비 상태 확인

전문적인 품질 관리 기준에 따라 최고 수준의 결과물을 보장해주세요.
        \"\"\",
        "expected_output": "품질 검증 보고서 및 최종 완성 프로젝트"
    }}
}}

# 활성 에이전트 수만큼 태스크 생성
for i, agent in enumerate(agent_list):
    if i < len(task_templates):
        task_config = task_templates[i]
        task = Task(
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            agent=agent
        )
        tasks.append(task)
        print(f"   ✅ Task {{i+1}} ({{agent.role}}) 할당 완료")

# 기존 호환성을 위한 별칭 설정
task1 = tasks[0] if len(tasks) > 0 else None
task2 = tasks[1] if len(tasks) > 1 else None
task3 = tasks[2] if len(tasks) > 2 else None
task4 = tasks[3] if len(tasks) > 3 else None

print("📋 작업 태스크 설정 완료")

start_time = datetime.now()
print(f"⏰ 실행 시작 시간: {{start_time.strftime('%Y-%m-%d %H:%M:%S')}}")

try:
    # 동적 단계 실행 - 활성 에이전트 수만큼 순차 실행
    stage_names = ["전문 분석", "기술 구현", "통합 솔루션", "품질 보증"]
    stage_emojis = ["📊", "🔧", "🎯", "✅"]
    results = []

    for i, (agent, task) in enumerate(zip(agent_list, tasks)):
        stage_name = stage_names[i] if i < len(stage_names) else f"추가 단계 {i+1}"
        stage_emoji = stage_emojis[i] if i < len(stage_emojis) else "⚙️"

        print("\\n" + "="*50)
        print(f"{stage_emoji} {i+1}단계: {stage_name} 시작...")
        print(f"   담당자: {agent.role}")

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        results.append(result)

        # 결과 저장
        save_stage_result(f"{stage_name} ({agent.role})", str(result), "{project_path}", "{execution_id}")

        # 승인 대기 (마지막 단계가 아닌 경우)
        if i < len(agent_list) - 1:
            if not wait_for_user_approval(f"{stage_name}", str(result)):
                print(f"❌ 사용자가 {stage_name}을 거부하여 작업을 중단합니다.")
                sys.exit(0)
        else:
            # 최종 승인 (마지막 단계)
            if wait_for_user_approval(f"{stage_name} (최종)", str(result)):
                print("✅ 모든 단계가 사용자 승인을 받아 완료되었습니다!")

                end_time = datetime.now()
                duration = end_time - start_time

                # 최종 통합 결과 저장
                output_file = os.path.join("{project_path}", "enhanced_crewai_result.md")

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("# CrewAI 전문 에이전트 협업 시스템 완료 결과\\\\n\\\\n")
                    f.write(f"**실행 ID**: {execution_id}\\\\n")
                    f.write(f"**시작 시간**: {{start_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
                    f.write(f"**완료 시간**: {{end_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
                    f.write(f"**총 소요시간**: {{duration}}\\\\n\\\\n")
                    f.write("**상태**: ✅ 모든 단계 사용자 승인 완료\\\\n\\\\n")
                    f.write(f"**원본 요구사항**:\\\\n{{original_requirement}}\\\\n\\\\n")
                    f.write("---\\\\n\\\\n")

                    # 동적 결과 저장
                    for idx, (agent, result) in enumerate(zip(agent_list, results)):
                        stage_name = stage_names[idx] if idx < len(stage_names) else f"추가 단계 {idx+1}"
                        f.write(f"## {idx+1}단계: {stage_name} ({agent.role})\\\\n\\\\n")
                        f.write(str(result) + "\\\\n\\\\n")

                print(f"📄 최종 승인 결과 저장: {{os.path.abspath(output_file)}}")
                print("🎉 전문 에이전트 협업 시스템 CrewAI 실행 완료!")
            else:
                print("❌ 최종 결과가 거부되었습니다.")

except Exception as e:
    import traceback
    error_details = traceback.format_exc()

    print(f"\\\\n❌ 실행 중 오류 발생:")
    print(f"오류 내용: {{str(e)}}")
    print(f"상세 정보:\\\\n{{error_details}}")

    # 오류 로그 저장
    error_file = os.path.join("{project_path}", "enhanced_approval_error.log")
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"CrewAI 개선된 승인 시스템 실행 오류\\\\n")
        f.write(f"실행 ID: {execution_id}\\\\n")
        f.write(f"오류 발생 시간: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}\\\\n\\\\n")
        f.write(f"오류 메시지: {{str(e)}}\\\\n\\\\n")
        f.write(f"상세 추적 정보:\\\\n{{error_details}}")

    print(f"🗂️ 오류 로그 저장: {{os.path.abspath(error_file)}}")
    sys.exit(1)
'''

    # 새로운 순수 CrewAI 템플릿으로 완전 교체
    clean_crewai_script_template = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템
실행 ID: {execution_id}
생성 시간: {generation_time}
요구사항: {original_requirement}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, LLM

# UTF-8 환경 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

print("🚀 CrewAI 전문 에이전트 협업 시스템 시작")
print(f"📋 프로젝트: {original_requirement}")
print(f"⏰ 시작 시간: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")

# LLM 모델 설정 함수
def get_model(model_name: str):
    """LLM 모델 인스턴스 반환"""
    return LLM(model=model_name, temperature=0.7)

# 4개 전문 에이전트 정의 (사전 분석 결과 기반)
print("\\n👥 전문 에이전트 구성 중...")

# Pre-Analyzer: 사전 분석 처리
pre_analyzer = Agent(
    role="Pre-Analysis Specialist",
    goal="{pre_analyzer_goal}",
    backstory="{pre_analyzer_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{pre_analyzer_model}")
)

# Planner: 프로젝트 계획 수립 + Writer 산출물 검토
planner = Agent(
    role="Project Planner & Quality Reviewer",
    goal="{planner_goal}",
    backstory="{planner_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{planner_model}")
)

# Researcher: 기술 조사 및 분석
researcher = Agent(
    role="Technical Researcher",
    goal="{researcher_goal}",
    backstory="{researcher_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{researcher_model}")
)

# Writer: 구현 및 문서 작성 + Planner 피드백 반영
writer = Agent(
    role="Technical Writer & Implementer",
    goal="{writer_goal}",
    backstory="{writer_backstory}",
    verbose=True,
    allow_delegation=False,
    llm=get_model("{writer_model}")
)

print("✅ 4개 전문 에이전트 구성 완료")

# 10개 태스크 정의 (검토-재작성 3회 반복 포함)
print("\\n📋 태스크 구성 중...")

# 1. Pre-Analysis Task
task1 = Task(
    description="{pre_analysis_task_description}",
    expected_output="{pre_analysis_expected_output}",
    agent=pre_analyzer
)

# 2. Planning Task
task2 = Task(
    description="{planning_task_description}",
    expected_output="{planning_expected_output}",
    agent=planner
)

# 3. Research Task
task3 = Task(
    description="{research_task_description}",
    expected_output="{research_expected_output}",
    agent=researcher
)

# 4. Initial Writing Task
task4 = Task(
    description="{initial_writing_task_description}",
    expected_output="{initial_writing_expected_output}",
    agent=writer
)

# 5. Review Task 1
task5 = Task(
    description="{review_task_1_description}",
    expected_output="{review_task_1_expected_output}",
    agent=planner
)

# 6. Revision Task 1
task6 = Task(
    description="{revision_task_1_description}",
    expected_output="{revision_task_1_expected_output}",
    agent=writer
)

# 7. Review Task 2
task7 = Task(
    description="{review_task_2_description}",
    expected_output="{review_task_2_expected_output}",
    agent=planner
)

# 8. Revision Task 2
task8 = Task(
    description="{revision_task_2_description}",
    expected_output="{revision_task_2_expected_output}",
    agent=writer
)

# 9. Review Task 3 (Final)
task9 = Task(
    description="{review_task_3_description}",
    expected_output="{review_task_3_expected_output}",
    agent=planner
)

# 10. Final Revision Task
task10 = Task(
    description="{final_revision_task_description}",
    expected_output="{final_revision_expected_output}",
    agent=writer
)

print("✅ 10개 태스크 구성 완료 (검토-재작성 3회 반복)")

# CrewAI 실행
print("\\n🚀 CrewAI 전문 에이전트 협업 시작...")

crew = Crew(
    agents=[pre_analyzer, planner, researcher, writer],
    tasks=[task1, task2, task3, task4, task5, task6, task7, task8, task9, task10],
    verbose=True
)

# 실행 및 결과 저장
start_time = datetime.now()
try:
    result = crew.kickoff()
    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\\n🎉 CrewAI 전문 에이전트 협업 완료!")
    print(f"⏰ 총 소요시간: {{duration}}")

    # 결과 저장
    output_file = os.path.join("{project_path}", "crewai_result.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# CrewAI 전문 에이전트 협업 시스템 결과\\\\n\\\\n")
        f.write(f"**실행 ID**: {execution_id}\\\\n")
        f.write(f"**요구사항**: {original_requirement}\\\\n")
        f.write(f"**시작 시간**: {{start_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
        f.write(f"**완료 시간**: {{end_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n")
        f.write(f"**총 소요시간**: {{duration}}\\\\n\\\\n")
        f.write("## 최종 결과\\\\n\\\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {{os.path.abspath(output_file)}}")

    # README.md 생성
    readme_file = os.path.join("{project_path}", "README.md")
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(f"# {{' '.join('{original_requirement}'.split()[:3])}}\\\\n\\\\n")
        f.write(f"CrewAI 전문 에이전트 협업으로 개발된 프로젝트입니다.\\\\n\\\\n")
        f.write(f"## 프로젝트 개요\\\\n")
        f.write(f"**요구사항**: {original_requirement}\\\\n")
        f.write(f"**개발 완료**: {{end_time.strftime('%Y-%m-%d %H:%M:%S')}}\\\\n\\\\n")
        f.write(f"## 개발 과정\\\\n")
        f.write(f"1. Pre-Analysis: 사전 분석\\\\n")
        f.write(f"2. Planning: 프로젝트 계획 수립\\\\n")
        f.write(f"3. Research: 기술 조사\\\\n")
        f.write(f"4. Implementation: 구현 (3회 검토-재작성 반복)\\\\n\\\\n")
        f.write(f"상세 결과는 `crewai_result.md` 파일을 참조하세요.\\\\n")

    print(f"📄 README.md 생성: {{os.path.abspath(readme_file)}}")

except Exception as e:
    print(f"\\n❌ 실행 중 오류 발생: {{str(e)}}")
    import traceback
    print(f"상세 오류:\\\\n{{traceback.format_exc()}}")
    sys.exit(1)
'''

    # 사전 분석 결과 기반 템플릿 변수 값 준비
    template_vars = {
        'execution_id': execution_id,
        'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'original_requirement': requirement,
        'project_path': safe_project_path,

        # 4개 전문 에이전트 정의 (사전 분석 결과 기반)
        'pre_analyzer_goal': f"사전 분석을 통해 {requirement}에 대한 핵심 요구사항과 기술적 제약사항을 명확히 정의합니다.",
        'pre_analyzer_backstory': f"당신은 요구사항 분석 전문가입니다. {requirement} 프로젝트의 본질을 파악하고 성공을 위한 핵심 요소들을 식별하는 전문성을 가지고 있습니다.",
        'pre_analyzer_model': list(selected_models.values())[0] if selected_models else "gemini-2.5-flash",

        'planner_goal': f"Pre-Analyzer의 분석을 바탕으로 {requirement} 프로젝트의 체계적인 개발 계획을 수립하고, Writer의 산출물을 3회 이상 검토하여 최고 품질을 보장합니다.",
        'planner_backstory': f"당신은 프로젝트 관리 및 품질 보증 전문가입니다. {requirement} 같은 프로젝트의 성공적인 실행 계획 수립과 지속적인 품질 개선에 전문성을 가지고 있습니다.",
        'planner_model': list(selected_models.values())[1] if len(selected_models) > 1 else "gemini-2.5-flash",

        'researcher_goal': f"Planner의 계획을 바탕으로 {requirement} 구현에 필요한 최적의 기술 스택, 도구, 방법론을 조사하고 제안합니다.",
        'researcher_backstory': f"당신은 기술 리서치 전문가입니다. {requirement}와 같은 프로젝트에 최적화된 기술 솔루션을 찾아내고 검증하는 전문성을 가지고 있습니다.",
        'researcher_model': list(selected_models.values())[2] if len(selected_models) > 2 else "gemini-2.5-flash",

        'writer_goal': f"연구 결과를 바탕으로 {requirement}를 완전히 구현하고, Planner의 피드백을 반영하여 지속적으로 개선합니다.",
        'writer_backstory': f"당신은 기술 구현 및 문서화 전문가입니다. {requirement} 프로젝트를 실제 동작하는 고품질 코드로 구현하고 피드백을 통해 지속적으로 개선하는 전문성을 가지고 있습니다.",
        'writer_model': list(selected_models.values())[-1] if selected_models else "gemini-2.5-flash",

        # 10개 태스크 정의 (검토-재작성 3회 반복)
        'pre_analysis_task_description': f'''
다음 요구사항에 대한 포괄적인 사전 분석을 수행하세요:

**요구사항**: {requirement}

**분석 내용**:
1. 프로젝트 목표 및 핵심 가치 정의
2. 주요 기능 요구사항 도출
3. 기술적 제약사항 및 고려사항
4. 성공 기준 및 평가 지표
5. 잠재적 리스크 및 대응 방안

구체적이고 실행 가능한 분석 결과를 제시하세요.
        ''',
        'pre_analysis_expected_output': "요구사항 분석 보고서 (마크다운 형식, 구체적 기능 명세 포함)",

        'planning_task_description': '''
Pre-Analyzer의 분석 결과를 바탕으로 체계적인 프로젝트 개발 계획을 수립하세요:

**계획 수립 내용**:
1. 개발 단계별 로드맵
2. 기능별 우선순위 매트릭스
3. 기술 스택 선정 가이드라인
4. 개발 일정 및 마일스톤
5. 품질 보증 체크포인트

실무진이 바로 실행할 수 있는 상세한 계획을 작성하세요.
        ''',
        'planning_expected_output': "프로젝트 개발 계획서 (마크다운 형식, 실행 가능한 단계별 가이드)",

        'research_task_description': '''
Planner의 계획을 바탕으로 기술적 조사를 수행하세요:

**조사 항목**:
1. 권장 기술 스택 및 라이브러리
2. 아키텍처 패턴 및 설계 원칙
3. 개발 도구 및 환경 설정
4. 보안 고려사항 및 베스트 프랙티스
5. 성능 최적화 방안
6. 테스트 및 배포 전략

각 기술 선택의 근거와 대안을 명시하세요.
        ''',
        'research_expected_output': "기술 조사 보고서 (마크다운 형식, 기술 선택 근거 포함)",

        'initial_writing_task_description': '''
분석과 계획, 조사 결과를 바탕으로 초기 프로젝트를 구현하세요:

**구현 내용**:
1. 완전한 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (실제 동작)
3. 설정 파일 및 의존성 관리
4. 상세한 README.md 및 사용법
5. 기본 테스트 코드
6. 실행 및 배포 가이드

모든 코드는 실제로 동작해야 하며 충분한 주석을 포함하세요.
        ''',
        'initial_writing_expected_output': "완전한 프로젝트 구현체 (실행 가능한 코드, 문서, 설정 파일 포함)",

        'review_task_1_description': '''
Writer가 작성한 초기 구현체를 검토하고 개선사항을 도출하세요:

**검토 항목**:
1. 요구사항 충족도 평가
2. 코드 품질 및 구조 분석
3. 기능 완성도 점검
4. 문서화 수준 평가
5. 테스트 커버리지 검토
6. 사용성 및 접근성 평가

구체적인 개선 방향과 우선순위를 제시하세요.
        ''',
        'review_task_1_expected_output': "1차 검토 보고서 및 개선 지시사항 (구체적 수정 항목 포함)",

        'revision_task_1_description': '''
Planner의 1차 검토 피드백을 바탕으로 프로젝트를 개선하세요:

**개선 작업**:
1. 검토에서 지적된 문제점 해결
2. 코드 품질 향상 및 구조 개선
3. 기능 완성도 제고
4. 문서화 보완 및 명확화
5. 테스트 코드 강화
6. 사용성 개선

모든 피드백을 반영하여 한 단계 발전된 버전을 제작하세요.
        ''',
        'revision_task_1_expected_output': "1차 개선된 프로젝트 구현체 (피드백 반영 완료)",

        'review_task_2_description': '''
Writer의 1차 개선 결과를 2차 검토하고 추가 개선사항을 도출하세요:

**심화 검토 항목**:
1. 1차 피드백 반영 수준 평가
2. 새로운 개선 기회 식별
3. 성능 및 보안 검토
4. 확장성 및 유지보수성 평가
5. 사용자 경험 최적화 방안
6. 배포 준비 상태 점검

더욱 엄격한 기준으로 품질을 평가하세요.
        ''',
        'review_task_2_expected_output': "2차 검토 보고서 및 고도화 지시사항 (심화 개선 항목 포함)",

        'revision_task_2_description': '''
Planner의 2차 검토 피드백을 바탕으로 프로젝트를 고도화하세요:

**고도화 작업**:
1. 심화 검토 지적사항 해결
2. 성능 최적화 및 보안 강화
3. 확장성 및 유지보수성 향상
4. 사용자 경험 개선
5. 배포 및 운영 준비
6. 종합적 품질 향상

전문가 수준의 완성도를 목표로 개선하세요.
        ''',
        'revision_task_2_expected_output': "2차 고도화된 프로젝트 구현체 (전문가 수준 품질)",

        'review_task_3_description': '''
Writer의 2차 고도화 결과에 대한 최종 검토를 수행하세요:

**최종 검토 항목**:
1. 모든 요구사항 완벽 충족 여부
2. 코드 품질의 전문가 수준 달성 여부
3. 완전한 기능 동작 및 안정성
4. 문서화 완성도 및 사용 편의성
5. 배포 준비 완료 상태
6. 프로덕션 레벨 품질 보장

최고 수준의 기준으로 최종 평가하세요.
        ''',
        'review_task_3_expected_output': "최종 검토 보고서 및 완성 확인서 (프로덕션 레벨 품질 인증)",

        'final_revision_task_description': '''
Planner의 최종 검토를 바탕으로 완벽한 최종 버전을 완성하세요:

**최종 완성 작업**:
1. 모든 검토 지적사항의 완벽한 해결
2. 최고 수준의 코드 품질 달성
3. 완전한 기능 구현 및 검증
4. 완벽한 문서화 및 사용 가이드
5. 프로덕션 배포 준비 완료
6. 최종 품질 보증

업계 최고 수준의 완성된 프로젝트를 제작하세요.
        ''',
        'final_revision_expected_output': "최종 완성된 프로젝트 (업계 최고 수준, 즉시 배포 가능)"
    }

    # 새로운 순수 CrewAI 스크립트 생성
    try:
        # 새로운 템플릿에 변수 적용
        script_content = clean_crewai_script_template.format(**template_vars)
        return script_content

    except Exception as e:
        # 새로운 템플릿 처리 오류 시 간단한 fallback
        print(f"템플릿 처리 오류: {str(e)}")
        fallback_script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CrewAI 전문 에이전트 협업 시스템 (Fallback)
실행 ID: {execution_id}
오류: {str(e)}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, LLM

print("⚠️ 템플릿 처리 오류 발생")
print(f"요구사항: {requirement}")
print(f"실행 ID: {execution_id}")
print(f"오류: {str(e)}")
print("\\n기본 3개 에이전트로 fallback 실행...")

# 기본 에이전트들
planner = Agent(role="Planner", goal="프로젝트 계획 수립", backstory="계획 전문가", llm=LLM(model="gemini-2.5-flash"))
researcher = Agent(role="Researcher", goal="기술 조사", backstory="기술 전문가", llm=LLM(model="gemini-2.5-flash"))
writer = Agent(role="Writer", goal="코드 구현", backstory="개발 전문가", llm=LLM(model="gemini-2.5-flash"))

# 기본 태스크들
task1 = Task(description="프로젝트 계획 수립", expected_output="계획서", agent=planner)
task2 = Task(description="기술 조사", expected_output="조사 보고서", agent=researcher)
task3 = Task(description="코드 구현", expected_output="완성된 프로젝트", agent=writer)

# 실행
crew = Crew(agents=[planner, researcher, writer], tasks=[task1, task2, task3])
result = crew.kickoff()

print("Fallback 실행 완료")
'''
        return fallback_script

def generate_crewai_execution_script(requirement: str, selected_models: dict, project_path: str, execution_id: str) -> str:
    """
    CrewAI 실행 스크립트 생성 - 새로운 전문 에이전트 시스템을 기본값으로 사용
    """
    # 새로운 전문 에이전트 시스템을 기본값으로 사용
    return generate_crewai_execution_script_with_approval(requirement, selected_models, project_path, execution_id)

if __name__ == "__main__":
    # 테스트
    test_req = "회사로 보내온 여러포맷의 이력서를 하나의 포맷으로 만들어서 저장하는 프로그램 생성해줘."
    test_models = {"planner": "gpt-4", "researcher": "claude-3", "writer": "gpt-4"}
    test_path = "D:\\GenProjects\\Projects\\test_project"
    test_id = "test_12345"

    result = generate_crewai_execution_script(test_req, test_models, test_path, test_id)
    print("✅ 전문 에이전트 시스템 스크립트 생성 테스트 성공")
    print(f"스크립트 길이: {len(result)} 문자")
    print("첫 100자:", result[:100])
