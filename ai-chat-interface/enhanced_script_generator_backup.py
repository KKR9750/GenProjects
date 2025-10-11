#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고도화된 CrewAI 스크립트 생성 엔진
도메인별 전문 템플릿과 지능형 요구사항 분석 기능 포함
"""

import os
import re
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class DomainPattern:
    """도메인 패턴 정의"""
    keywords: List[str]
    libraries: List[str]
    agents: List[Dict]
    output_format: str
    confidence_threshold: float = 0.3

class EnhancedCrewAIGenerator:
    """고도화된 CrewAI 스크립트 생성기"""

    def __init__(self):
        self.domain_patterns = self._initialize_domain_patterns()

    def _initialize_domain_patterns(self) -> Dict[str, DomainPattern]:
        """도메인별 패턴 초기화"""
        return {
            "data_processing": DomainPattern(
                keywords=["이력서", "파싱", "추출", "JSON", "CSV", "PDF", "문서", "데이터", "파일", "변환", "구조화"],
                libraries=["PyPDF2", "python-docx", "pandas", "openpyxl", "pdfplumber", "spacy", "re"],
                agents=[
                    {
                        "role": "Document Parser",
                        "goal": "다양한 형식의 문서 파일을 텍스트로 변환",
                        "backstory": "디지털 문서 분석 전문가로서 PDF, DOCX, TXT 등 모든 형식의 파일에서 정확한 텍스트를 추출하는 베테랑입니다.",
                        "tools": ["PyPDF2", "python-docx", "pdfplumber"]
                    },
                    {
                        "role": "Information Extractor",
                        "goal": "텍스트에서 구조화된 정보를 추출하고 정규화",
                        "backstory": "NLP와 정규표현식을 활용하여 비정형 텍스트에서 핵심 정보를 찾아내는 데이터 탐정입니다.",
                        "tools": ["re", "spacy", "pandas"]
                    },
                    {
                        "role": "Data Structurer",
                        "goal": "추출된 정보를 지정된 형식으로 구조화",
                        "backstory": "혼재된 데이터를 체계적이고 일관된 구조로 변환하는 데이터 아키텍트입니다.",
                        "tools": ["json", "pandas", "jsonschema"]
                    },
                    {
                        "role": "Quality Manager",
                        "goal": "전체 프로세스 관리 및 결과물 품질 검증",
                        "backstory": "데이터 품질과 프로세스 완성도를 보장하는 수석 관리자입니다.",
                        "tools": ["logging", "unittest", "json"]
                    }
                ],
                output_format="structured_json"
            ),

            "web_development": DomainPattern(
                keywords=["웹사이트", "웹앱", "홈페이지", "프론트엔드", "백엔드", "API", "데이터베이스", "서버", "뉴스"],
                libraries=["flask", "django", "fastapi", "react", "vue", "bootstrap", "sqlalchemy"],
                agents=[
                    {
                        "role": "System Architect",
                        "goal": "웹 애플리케이션 전체 구조 설계",
                        "backstory": "확장 가능하고 유지보수가 쉬운 웹 아키텍처를 설계하는 시니어 아키텍트입니다.",
                        "tools": ["system_design", "database_design", "api_design"]
                    },
                    {
                        "role": "Frontend Developer",
                        "goal": "사용자 인터페이스 구현",
                        "backstory": "직관적이고 반응형인 사용자 경험을 만드는 프론트엔드 전문가입니다.",
                        "tools": ["html", "css", "javascript", "react", "vue"]
                    },
                    {
                        "role": "Backend Developer",
                        "goal": "서버 로직 및 API 구현",
                        "backstory": "안정적이고 성능 좋은 서버 시스템을 구축하는 백엔드 엔지니어입니다.",
                        "tools": ["python", "flask", "django", "fastapi", "sqlalchemy"]
                    },
                    {
                        "role": "Integration Tester",
                        "goal": "전체 시스템 통합 및 테스트",
                        "backstory": "프론트엔드와 백엔드를 완벽하게 연결하고 품질을 보장하는 통합 전문가입니다.",
                        "tools": ["pytest", "selenium", "postman", "jest"]
                    }
                ],
                output_format="full_web_application"
            ),

            "api_development": DomainPattern(
                keywords=["API", "REST", "GraphQL", "엔드포인트", "서비스", "마이크로서비스"],
                libraries=["fastapi", "flask", "django-rest-framework", "pydantic", "uvicorn"],
                agents=[
                    {
                        "role": "API Designer",
                        "goal": "RESTful API 설계 및 명세 작성",
                        "backstory": "확장 가능하고 직관적인 API를 설계하는 API 아키텍트입니다.",
                        "tools": ["openapi", "swagger", "postman"]
                    },
                    {
                        "role": "Backend Developer",
                        "goal": "API 엔드포인트 구현",
                        "backstory": "고성능 API 서버를 구축하는 백엔드 개발 전문가입니다.",
                        "tools": ["fastapi", "pydantic", "sqlalchemy", "redis"]
                    },
                    {
                        "role": "Security Specialist",
                        "goal": "API 보안 및 인증 구현",
                        "backstory": "API 보안과 인증 시스템을 전담하는 보안 전문가입니다.",
                        "tools": ["jwt", "oauth2", "bcrypt", "rate_limiting"]
                    },
                    {
                        "role": "Documentation Writer",
                        "goal": "API 문서화 및 사용 가이드 작성",
                        "backstory": "개발자가 쉽게 이해할 수 있는 완벽한 API 문서를 작성하는 기술 문서 전문가입니다.",
                        "tools": ["swagger_ui", "redoc", "markdown", "postman"]
                    }
                ],
                output_format="api_server_with_docs"
            )
        }

    def analyze_requirement(self, requirement: str) -> Tuple[str, float, Dict]:
        """요구사항 분석 및 도메인 감지"""
        requirement_lower = requirement.lower()
        best_domain = "general"
        best_confidence = 0.0
        domain_analysis = {}

        for domain_name, pattern in self.domain_patterns.items():
            # 키워드 매칭 점수 계산
            matched_keywords = [kw for kw in pattern.keywords if kw in requirement_lower]
            confidence = len(matched_keywords) / len(pattern.keywords)

            domain_analysis[domain_name] = {
                "confidence": confidence,
                "matched_keywords": matched_keywords,
                "total_keywords": len(pattern.keywords)
            }

            if confidence > best_confidence and confidence >= pattern.confidence_threshold:
                best_confidence = confidence
                best_domain = domain_name

        return best_domain, best_confidence, domain_analysis

    def extract_output_requirements(self, requirement: str, domain: str) -> Dict:
        """출력 요구사항 추출"""
        output_hints = {
            "json": ["json", "구조화", "데이터"],
            "web": ["웹사이트", "홈페이지", "웹앱"],
            "api": ["api", "서비스", "엔드포인트"],
            "file": ["파일", "저장", "출력"],
            "database": ["데이터베이스", "db", "저장소"]
        }

        detected_outputs = []
        requirement_lower = requirement.lower()

        for output_type, hints in output_hints.items():
            if any(hint in requirement_lower for hint in hints):
                detected_outputs.append(output_type)

        return {
            "primary_output": detected_outputs[0] if detected_outputs else "general",
            "all_outputs": detected_outputs,
            "domain_default": self.domain_patterns.get(domain, DomainPattern([], [], [], "general")).output_format
        }

    def generate_enhanced_script(self, requirement: str, selected_models: dict,
                                project_path: str, execution_id: str) -> str:
        """고도화된 CrewAI 스크립트 생성"""

        # 1. 요구사항 분석
        domain, confidence, analysis = self.analyze_requirement(requirement)
        output_req = self.extract_output_requirements(requirement, domain)

        print(f"🔍 도메인 분석: {domain} (신뢰도: {confidence:.2f})")
        print(f"📤 출력 형식: {output_req['primary_output']}")

        # 2. 도메인별 전문 스크립트 생성
        if domain in self.domain_patterns:
            return self._generate_specialized_script(
                requirement, selected_models, project_path, execution_id,
                domain, confidence, output_req
            )
        else:
            return self._generate_general_script(
                requirement, selected_models, project_path, execution_id
            )

    def _generate_specialized_script(self, requirement: str, selected_models: dict,
                                   project_path: str, execution_id: str,
                                   domain: str, confidence: float, output_req: Dict) -> str:
        """도메인별 전문 스크립트 생성"""

        pattern = self.domain_patterns[domain]

        # 안전한 텍스트 처리
        safe_requirement = requirement.replace('"', '\\"').replace('\n', '\\n')
        safe_project_path = project_path.replace('\\', '\\\\')

        # 도메인별 특화된 스크립트 템플릿
        if domain == "data_processing":
            return self._generate_data_processing_script(
                safe_requirement, selected_models, safe_project_path, execution_id, pattern
            )
        elif domain == "web_development":
            return self._generate_web_development_script(
                safe_requirement, selected_models, safe_project_path, execution_id, pattern
            )
        elif domain == "api_development":
            return self._generate_api_development_script(
                safe_requirement, selected_models, safe_project_path, execution_id, pattern
            )
        else:
            return self._generate_general_script(requirement, selected_models, project_path, execution_id)

    def _generate_data_processing_script(self, requirement: str, selected_models: dict,
                                       project_path: str, execution_id: str, pattern: DomainPattern) -> str:
        """데이터 처리 전문 스크립트 생성"""

        # 모델 매핑 (4개 에이전트용)
        agent_models = {
            "parser": selected_models.get("researcher", "gemini-flash"),
            "extractor": selected_models.get("writer", "gemini-flash"),
            "structurer": selected_models.get("planner", "gemini-flash"),
            "manager": selected_models.get("researcher", "gemini-flash")
        }

        libraries_str = ", ".join(pattern.libraries)

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 처리 전문 CrewAI 스크립트
실행 ID: {execution_id}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
도메인: 데이터 처리 (이력서, 문서 등)
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# CrewAI 임포트
from crewai import Agent, Task, Crew, Process, LLM

# 데이터 처리 라이브러리
try:
    import PyPDF2
    import pandas as pd
    from docx import Document
    import pdfplumber
except ImportError as e:
    print(f"⚠️  필수 라이브러리 누락: {{e}}")
    print("다음 명령어로 설치하세요: pip install {libraries_str}")
    sys.exit(1)

# UTF-8 환경 설정
def setup_environment():
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.platform.startswith('win'):
        os.system('chcp 65001 > nul 2>&1')

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

setup_environment()

print("🚀 데이터 처리 전문 CrewAI 시스템 시작")
print(f"📋 요구사항: {requirement}")
print(f"📁 프로젝트 경로: {project_path}")
print("=" * 50)

# LLM 모델 설정
def get_llm_model(role_name: str) -> LLM:
    model_mapping = {json.dumps(agent_models, ensure_ascii=False)}
    model_id = model_mapping.get(role_name, 'gemini-flash')

    print(f"🤖 {{role_name}} → {{model_id}}")

    if 'gemini' in model_id:
        return LLM(model=f"gemini/{{model_id}}", temperature=0.7)
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_id, temperature=0.7)

# 전문 에이전트 정의
print("👥 데이터 처리 전문가 팀 구성...")

document_parser = Agent(
    role="Document Parser",
    goal="다양한 형식(PDF, DOCX, TXT)의 문서 파일을 정확한 텍스트로 변환합니다.",
    backstory="""당신은 20년 경력의 디지털 문서 분석 전문가입니다.
    PDF, Word, 텍스트 파일 등 어떤 형식이든 그 안의 모든 텍스트를 완벽하게 추출해내는 능력을 가지고 있습니다.
    파일 형식의 장벽을 허무는 데 특화되어 있으며, 깨진 인코딩도 복구할 수 있습니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("parser")
)

information_extractor = Agent(
    role="Information Extractor",
    goal="텍스트에서 구조화된 핵심 정보를 정확하게 추출하고 정규화합니다.",
    backstory="""당신은 NLP와 정규표현식의 마스터입니다.
    비정형 텍스트 속에서 보석같은 정보를 찾아내는 데이터 탐정으로,
    특히 이름, 이메일, 전화번호 같은 개인정보를 99.9% 정확도로 추출할 수 있습니다.
    잘못된 정보는 절대 생성하지 않으며, 확실하지 않으면 빈 값으로 처리합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("extractor")
)

data_structurer = Agent(
    role="Data Structurer",
    goal="추출된 정보를 지정된 JSON 형식으로 완벽하게 구조화합니다.",
    backstory="""당신은 데이터 아키텍처의 장인입니다.
    혼재된 정보들을 질서정연하고 일관된 구조로 변환하는 것이 전문 분야입니다.
    JSON 스키마 준수에 완벽주의적이며, 누락된 필드는 반드시 빈 값으로 처리합니다.
    데이터 무결성과 일관성을 최우선으로 생각합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("structurer")
)

quality_manager = Agent(
    role="Quality Manager",
    goal="전체 프로세스를 관리하고 최종 결과물의 품질을 검증합니다.",
    backstory="""당신은 프로젝트 총괄 관리자이자 품질 보증 전문가입니다.
    20년간 데이터 프로젝트를 성공으로 이끌어온 베테랑으로,
    코드 품질, 데이터 정확성, 프로세스 효율성을 모두 보장합니다.
    완벽한 결과물만을 인정하며, 문제가 있으면 즉시 수정을 요구합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("manager")
)

# 전문 태스크 체인 정의
print("📋 데이터 처리 전문 태스크 설정...")

task1_parse_documents = Task(
    description=f'''
다음 요구사항에 따라 문서 파싱 시스템을 구현하세요:

**요구사항**: {requirement}

**구현할 내용:**
1. 지정된 폴더의 모든 파일 스캔 (PDF, DOCX, TXT 등)
2. 파일 형식별 전용 파서 구현:
   - PDF: PyPDF2 또는 pdfplumber 사용
   - DOCX: python-docx 사용
   - TXT: 직접 읽기
3. 인코딩 문제 해결 (UTF-8, CP949 등)
4. 추출된 텍스트 정규화 및 정제
5. 다음 단계로 전달할 수 있는 깨끗한 텍스트 생성

**출력**: 완전히 동작하는 문서 파싱 함수와 테스트 코드
''',
    expected_output="문서 파싱 시스템 구현 코드 (Python 함수, 테스트 코드, 사용 예시 포함)",
    agent=document_parser
)

email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
phone_pattern = r'010-\d{4}-\d{4}'

task2_extract_information = Task(
    description=f'''
파싱된 텍스트에서 구조화된 정보를 추출하는 시스템을 구현하세요:

**추출할 정보 유형:**
1. 개인정보: 이름, 이메일, 전화번호 (정규표현식 활용)
2. 학력사항: 학교명, 전공, 학위, 기간
3. 경력사항: 회사명, 직책, 기간, 담당업무
4. 기술 스택: 프로그래밍 언어, 프레임워크, 도구
5. 기타 정보: 자격증, 어학능력 등

**중요 규칙:**
- 이메일 패턴: {email_pattern}
- 전화번호 패턴: {phone_pattern} 등
- 정보가 없으면 빈 문자열 또는 빈 리스트로 처리
- 추측하거나 생성하지 말고 명시된 정보만 추출

**출력**: 정보 추출 함수와 검증 로직
프로젝트 경로: {project_path}
실행 ID: {execution_id}
''',
    expected_output="정보 추출 시스템 (정규표현식 패턴, 추출 함수, 검증 로직 포함)",
    agent=information_extractor
)

task3_structure_data = Task(
    description='''
추출된 정보를 다음 JSON 구조로 완벽하게 변환하세요:

**목표 JSON 구조:**
```json
[
  {{
    "personal_info": {{
      "name": "홍길동",
      "email": "gildong.hong@example.com",
      "phone_number": "010-1234-5678"
    }},
    "education": [
      {{
        "school_name": "대한대학교",
        "major": "컴퓨터공학",
        "status": "졸업",
        "start_date": "2015-03-01",
        "end_date": "2020-02-28"
      }}
    ],
    "work_experience": [
      {{
        "company_name": "스마트 IT",
        "position": "소프트웨어 엔지니어",
        "start_date": "2021-03-01",
        "end_date": "2024-08-31",
        "responsibilities": "웹 애플리케이션 백엔드 개발 및 유지보수"
      }}
    ],
    "skills": ["Python", "Java", "Spring Boot", "AWS", "Docker"]
  }}
]
```

**구현 요구사항:**
1. JSON 스키마 검증 기능
2. 필수 필드 누락 시 빈 값 처리
3. 다중 이력서 처리 (배열 형태)
4. 최종 JSON 파일 저장 (resumes_output.json)

**출력**: JSON 구조화 시스템과 검증 로직
''',
    expected_output="JSON 구조화 시스템 (스키마 검증, 데이터 변환, 파일 저장 포함)",
    agent=data_structurer
)

task4_integrate_and_finalize = Task(
    description='''
모든 구성 요소를 통합하여 완전한 이력서 처리 프로그램을 완성하세요:

**통합 요구사항:**
1. 전체 프로세스 오케스트레이션
2. 에러 핸들링 및 로깅 시스템
3. 진행 상황 표시 및 사용자 피드백
4. 최종 결과 검증 및 품질 확인
5. 실행 가능한 메인 스크립트 작성

**최종 결과물:**
1. 실행 가능한 Python 프로그램
2. requirements.txt 파일
3. README.md (설치 및 사용법)
4. 테스트 데이터와 예시
5. 결과 검증 스크립트

**품질 기준:**
- 모든 코드가 실제로 동작해야 함
- 에러 상황에 대한 적절한 처리
- 사용자 친화적인 인터페이스
- 완전한 문서화

**출력**: 완성된 이력서 처리 프로그램 전체
''',
    expected_output="완전한 이력서 처리 프로그램 (메인 스크립트, 설정 파일, 문서, 테스트 포함)",
    agent=quality_manager
)

# CrewAI 팀 실행
print("🚀 데이터 처리 전문가 팀 실행...")

crew = Crew(
    agents=[document_parser, information_extractor, data_structurer, quality_manager],
    tasks=[task1_parse_documents, task2_extract_information, task3_structure_data, task4_integrate_and_finalize],
    verbose=2,
    process=Process.sequential
)

try:
    start_time = datetime.now()
    print(f"⏰ 실행 시작: {{start_time.strftime('%H:%M:%S')}}")

    result = crew.kickoff()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\\n" + "=" * 50)
    print("🎉 데이터 처리 프로젝트 완료!")
    print(f"⏱️  총 소요시간: {{duration}}")
    print("=" * 50)

    # 결과 저장
    result_file = os.path.join("{project_path}", "data_processing_result.md")

    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("# 데이터 처리 CrewAI 프로젝트 결과\\n\\n")
        f.write(f"**실행 ID**: {execution_id}\\n")
        f.write(f"**실행 시간**: {{start_time}} ~ {{end_time}}\\n")
        f.write(f"**소요 시간**: {{duration}}\\n\\n")
        f.write(f"**요구사항**: {requirement}\\n\\n")
        f.write("---\\n\\n")
        f.write("## 생성된 결과\\n\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {{os.path.abspath(result_file)}}")
    print("✅ 모든 작업 완료!")

except Exception as e:
    import traceback
    print(f"\\n❌ 실행 오류: {{e}}")
    print(f"상세 정보:\\n{{traceback.format_exc()}}")

    # 오류 로그 저장
    error_file = os.path.join("{project_path}", "error_log.txt")
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"오류 시간: {{datetime.now()}}\\n")
        f.write(f"오류 내용: {{e}}\\n\\n")
        f.write(f"상세 추적:\\n{{traceback.format_exc()}}")

    print(f"🗂️  오류 로그: {{os.path.abspath(error_file)}}")
    sys.exit(1)
'''

    def _generate_web_development_script(self, requirement: str, selected_models: dict,
                                       project_path: str, execution_id: str, pattern: DomainPattern) -> str:
        """웹 개발 전문 스크립트 생성"""

        # 모델 매핑 (4개 에이전트용)
        agent_models = {
            "architect": selected_models.get("planner", "gemini-flash"),
            "frontend": selected_models.get("writer", "gemini-flash"),
            "backend": selected_models.get("researcher", "gemini-flash"),
            "tester": selected_models.get("planner", "gemini-flash")
        }

        libraries_str = ", ".join(pattern.libraries)

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 개발 전문 CrewAI 스크립트
실행 ID: {execution_id}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
도메인: 웹 개발 (풀스택 웹 애플리케이션)
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM

# 환경 설정
def setup_environment():
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.platform.startswith('win'):
        os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

setup_environment()

print("🚀 웹 개발 전문 CrewAI 시스템 시작")
print(f"📋 요구사항: {requirement}")
print(f"📁 프로젝트 경로: {project_path}")
print("=" * 50)

# LLM 모델 설정
def get_llm_model(role_name: str) -> LLM:
    model_mapping = {json.dumps(agent_models, ensure_ascii=False)}
    model_id = model_mapping.get(role_name, 'gemini-flash')
    print(f"🤖 {{role_name}} → {{model_id}}")

    if 'gemini' in model_id:
        return LLM(model=f"gemini/{{model_id}}", temperature=0.7)
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_id, temperature=0.7)

# 웹 개발 전문가 팀 구성
print("👥 웹 개발 전문가 팀 구성...")

system_architect = Agent(
    role="System Architect",
    goal="확장 가능하고 유지보수가 쉬운 웹 애플리케이션 아키텍처를 설계합니다.",
    backstory="""당신은 15년 경력의 시니어 웹 아키텍트입니다.
    대규모 웹 서비스부터 소규모 웹사이트까지 다양한 프로젝트의 아키텍처를 설계해왔습니다.
    기술 스택 선택, 데이터베이스 설계, API 구조, 보안 고려사항까지 모든 것을 종합적으로 고려합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("architect")
)

frontend_developer = Agent(
    role="Frontend Developer",
    goal="사용자 친화적이고 반응형인 웹 인터페이스를 구현합니다.",
    backstory="""당신은 모던 프론트엔드 개발의 전문가입니다.
    HTML5, CSS3, JavaScript, React/Vue.js 등을 능숙하게 다루며,
    사용자 경험(UX)과 접근성을 최우선으로 고려하는 개발자입니다.
    반응형 디자인과 최신 웹 표준을 준수합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("frontend")
)

backend_developer = Agent(
    role="Backend Developer",
    goal="안정적이고 성능이 우수한 서버 시스템과 API를 구현합니다.",
    backstory="""당신은 백엔드 개발의 베테랑입니다.
    Python Flask/Django, Node.js, 데이터베이스 설계, API 개발,
    서버 최적화, 보안 등 백엔드 전 영역에 전문성을 가지고 있습니다.
    확장 가능하고 안전한 서버 아키텍처를 구축합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("backend")
)

integration_tester = Agent(
    role="Integration Tester",
    goal="프론트엔드와 백엔드의 완벽한 통합과 전체 시스템의 품질을 보장합니다.",
    backstory="""당신은 웹 애플리케이션 품질 보증 전문가입니다.
    단위 테스트부터 통합 테스트, E2E 테스트까지 모든 레벨의 테스트를 설계하고 실행합니다.
    성능 테스트, 보안 테스트, 접근성 테스트도 담당하며, CI/CD 파이프라인 구축 경험이 풍부합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("tester")
)

# 웹 개발 전문 태스크 체인
print("📋 웹 개발 전문 태스크 설정...")

task1_system_design = Task(
    description=f'''
다음 요구사항에 따라 웹 애플리케이션의 전체 아키텍처를 설계하세요:

**요구사항**: {requirement}

**설계할 내용:**
1. 전체 시스템 아키텍처 다이어그램
2. 기술 스택 선정 및 근거
   - 프론트엔드: HTML5, CSS3, JavaScript, 프레임워크 선택
   - 백엔드: Python (Flask/Django), Node.js 등
   - 데이터베이스: SQLite, PostgreSQL, MySQL 등
3. 프로젝트 디렉토리 구조
4. API 설계 및 엔드포인트 정의
5. 데이터베이스 스키마 설계
6. 보안 고려사항 (인증, 권한, 데이터 보호)
7. 성능 최적화 방안

**출력**: 완전한 시스템 설계서 및 기술 선택 근거
''',
    expected_output="웹 애플리케이션 시스템 설계서 (아키텍처, 기술 스택, DB 스키마 포함)",
    agent=system_architect
)

task2_frontend_implementation = Task(
    description='''
시스템 아키텍트의 설계를 바탕으로 프론트엔드를 구현하세요:

**구현할 내용:**
1. HTML 구조 및 시맨틱 마크업
2. 반응형 CSS 스타일링 (모바일 우선)
3. JavaScript 인터랙션 로직
4. 필요시 React/Vue.js 컴포넌트
5. 사용자 인터페이스 (UI) 컴포넌트
6. API 통신 로직 (AJAX/Fetch)
7. 에러 처리 및 사용자 피드백
8. 접근성 (ARIA, 키보드 네비게이션)

**품질 요구사항:**
- 모든 브라우저 호환성
- 모바일 반응형 디자인
- 빠른 로딩 속도
- 직관적인 사용자 경험

**출력**: 완성된 프론트엔드 코드 및 에셋
''',
    expected_output="완전한 프론트엔드 구현 (HTML, CSS, JavaScript, 컴포넌트)",
    agent=frontend_developer
)

task3_backend_implementation = Task(
    description='''
설계된 아키텍처에 따라 백엔드 서버와 API를 구현하세요:

**구현할 내용:**
1. 웹 서버 구성 (Flask/Django/FastAPI)
2. 데이터베이스 연결 및 ORM 설정
3. RESTful API 엔드포인트 구현
4. 사용자 인증 및 세션 관리
5. 데이터 검증 및 에러 처리
6. 로깅 및 모니터링 시스템
7. 보안 미들웨어 (CORS, CSRF 등)
8. 데이터베이스 마이그레이션 스크립트

**성능 요구사항:**
- 효율적인 데이터베이스 쿼리
- 적절한 캐싱 전략
- 에러 처리 및 복구 메커니즘
- API 응답 시간 최적화

**출력**: 완성된 백엔드 서버 및 API
''',
    expected_output="완전한 백엔드 구현 (서버, API, 데이터베이스, 인증)",
    agent=backend_developer
)

task4_integration_and_testing = Task(
    description='''
프론트엔드와 백엔드를 통합하고 전체 시스템을 테스트하세요:

**통합 작업:**
1. 프론트엔드-백엔드 API 연동
2. 데이터 플로우 검증
3. 사용자 시나리오 테스트
4. 성능 테스트 및 최적화
5. 보안 테스트 (XSS, SQL Injection 등)
6. 브라우저 호환성 테스트
7. 모바일 반응형 테스트

**최종 결과물:**
1. 완전히 작동하는 웹 애플리케이션
2. 설치 및 배포 가이드
3. 사용자 매뉴얼
4. 개발자 문서
5. 테스트 결과 보고서
6. requirements.txt 및 package.json
7. 실행 스크립트

**품질 기준:**
- 모든 기능이 정상 작동
- 에러 없는 깨끗한 코드
- 완전한 문서화
- 즉시 배포 가능한 상태

**출력**: 완성된 웹 애플리케이션 전체
''',
    expected_output="완전한 웹 애플리케이션 (통합 테스트 완료, 배포 준비 상태)",
    agent=integration_tester
)

# CrewAI 팀 실행
print("🚀 웹 개발 전문가 팀 실행...")

crew = Crew(
    agents=[system_architect, frontend_developer, backend_developer, integration_tester],
    tasks=[task1_system_design, task2_frontend_implementation, task3_backend_implementation, task4_integration_and_testing],
    verbose=2,
    process=Process.sequential
)

try:
    start_time = datetime.now()
    print(f"⏰ 실행 시작: {{start_time.strftime('%H:%M:%S')}}")

    result = crew.kickoff()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\\n" + "=" * 50)
    print("🎉 웹 개발 프로젝트 완료!")
    print(f"⏱️ 총 소요시간: {{duration}}")
    print("=" * 50)

    # 결과 저장
    result_file = os.path.join("{project_path}", "web_development_result.md")

    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("# 웹 개발 CrewAI 프로젝트 결과\\n\\n")
        f.write(f"**실행 ID**: {execution_id}\\n")
        f.write(f"**실행 시간**: {{start_time}} ~ {{end_time}}\\n")
        f.write(f"**소요 시간**: {{duration}}\\n\\n")
        f.write(f"**요구사항**: {requirement}\\n\\n")
        f.write("---\\n\\n")
        f.write("## 생성된 웹 애플리케이션\\n\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {{os.path.abspath(result_file)}}")
    print("✅ 모든 작업 완료!")

except Exception as e:
    import traceback
    print(f"\\n❌ 실행 오류: {{e}}")
    print(f"상세 정보:\\n{{traceback.format_exc()}}")

    # 오류 로그 저장
    error_file = os.path.join("{project_path}", "error_log.txt")
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"오류 시간: {{datetime.now()}}\\n")
        f.write(f"오류 내용: {{e}}\\n\\n")
        f.write(f"상세 추적:\\n{{traceback.format_exc()}}")

    print(f"🗂️ 오류 로그: {{os.path.abspath(error_file)}}")
    sys.exit(1)
'''

    def _generate_general_script(self, requirement: str, selected_models: dict,
                               project_path: str, execution_id: str) -> str:
        """일반 용도 스크립트 생성 (기존 로직 개선)"""

        # 기본 3개 에이전트 구성
        safe_requirement = requirement.replace('"', '\\"').replace('\n', '\\n')
        safe_project_path = project_path.replace('\\', '\\\\')

        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고품질 일반 용도 CrewAI 스크립트
실행 ID: {execution_id}
생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import os
import sys
from datetime import datetime
from crewai import Agent, Task, Crew, Process, LLM

# 환경 설정
def setup_environment():
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if sys.platform.startswith('win'):
        os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

setup_environment()

print("🚀 고품질 CrewAI 시스템 시작...")
print(f"📋 요구사항: {safe_requirement}")
print(f"📁 프로젝트 경로: {safe_project_path}")
print("=" * 50)

# LLM 모델 설정
def get_llm_model(role_name: str):
    models = {json.dumps(selected_models, ensure_ascii=False)}
    model_id = models.get(role_name.lower(), 'gemini-flash')
    print(f"🤖 {{role_name}} → {{model_id}}")

    if 'gemini' in model_id:
        return LLM(model=f"gemini/{{model_id}}", temperature=0.7)
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_id, temperature=0.7)

# 전문 에이전트 정의
print("👥 전문가 팀 구성...")

strategic_planner = Agent(
    role="Strategic Project Planner",
    goal="복잡한 요구사항을 체계적이고 실행 가능한 단계로 분해합니다.",
    backstory="""당신은 20년 경력의 프로젝트 전략 기획자입니다.
    복잡하고 모호한 요구사항을 명확하고 구체적인 실행 계획으로 변환하는 전문가입니다.
    사용자의 진짜 니즈를 파악하고, 최적의 솔루션을 제시할 수 있습니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("planner")
)

technical_researcher = Agent(
    role="Senior Technical Researcher",
    goal="최신 기술과 베스트 프랙티스를 조사하여 최적의 구현 방법을 제안합니다.",
    backstory="""당신은 기술 연구 분야의 권위자입니다.
    최신 프레임워크, 라이브러리, 도구들을 깊이 있게 연구하며,
    프로젝트 요구사항에 가장 적합한 기술 조합을 찾아내는 능력이 탁월합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("researcher")
)

master_implementer = Agent(
    role="Master Implementation Specialist",
    goal="연구 결과를 바탕으로 완벽하게 동작하는 고품질 코드와 문서를 작성합니다.",
    backstory="""당신은 구현의 마스터입니다.
    어떤 복잡한 요구사항이든 실제로 동작하는 완성도 높은 코드로 구현할 수 있습니다.
    클린 코드, 에러 처리, 테스트, 문서화까지 모든 것을 완벽하게 처리합니다.""",
    verbose=True,
    allow_delegation=False,
    llm=get_llm_model("writer")
)

# 고품질 태스크 정의
print("📋 고품질 태스크 설정...")

task1_strategic_planning = Task(
    description=f'''
다음 요구사항을 깊이 있게 분석하고 전략적 실행 계획을 수립하세요:

**요구사항**: {safe_requirement}

**분석할 내용:**
1. 요구사항의 핵심 목적과 가치 분석
2. 사용자/이해관계자 니즈 파악
3. 기능 요구사항과 비기능 요구사항 분리
4. 우선순위 및 중요도 평가
5. 기술적/비즈니스적 제약사항 식별
6. 위험 요소 및 완화 방안
7. 성공 기준 및 측정 지표 정의

**계획 수립:**
1. 프로젝트 목표 및 범위 명확화
2. 주요 기능 및 모듈 구조화
3. 개발 단계별 마일스톤
4. 필요 자원 및 기술 요구사항
5. 품질 보증 및 테스트 전략

**출력**: 상세하고 실행 가능한 전략적 프로젝트 계획서
''',
    expected_output="전략적 프로젝트 계획서 (요구사항 분석, 아키텍처 개요, 실행 계획 포함)",
    agent=strategic_planner
)

task2_technical_research = Task(
    description='''
전략적 계획을 바탕으로 기술적 구현 방안을 상세히 연구하세요:

**연구 영역:**
1. 최적 기술 스택 선정 (언어, 프레임워크, 라이브러리)
2. 아키텍처 패턴 및 디자인 원칙
3. 성능 최적화 방안
4. 보안 고려사항 및 베스트 프랙티스
5. 테스트 전략 및 도구
6. 배포 및 운영 방안
7. 확장성 및 유지보수성 고려사항

**상세 기술 조사:**
1. 각 기술 선택의 장단점 분석
2. 구현 복잡도 및 학습 곡선 평가
3. 커뮤니티 지원 및 생태계 현황
4. 라이선스 및 비용 고려사항
5. 레퍼런스 아키텍처 및 모범 사례

**출력**: 상세한 기술 연구 보고서 및 구현 가이드
''',
    expected_output="종합적인 기술 연구 보고서 (기술 스택, 아키텍처, 구현 방법론 포함)",
    agent=technical_researcher
)

task3_master_implementation = Task(
    description='''
계획과 연구 결과를 바탕으로 완벽한 구현을 수행하세요:

**구현 요구사항:**
1. 완전히 동작하는 소스 코드
2. 모듈화되고 재사용 가능한 구조
3. 포괄적인 에러 처리 및 예외 상황 대응
4. 단위 테스트 및 통합 테스트 코드
5. 상세한 주석 및 문서화
6. 설치 및 실행 가이드
7. 사용자 매뉴얼 및 예시

**코드 품질 기준:**
1. 클린 코드 원칙 준수
2. SOLID 설계 원칙 적용
3. 적절한 디자인 패턴 활용
4. 성능 최적화 고려
5. 보안 위협 대응
6. 접근성 및 사용성 고려

**최종 산출물:**
1. 실행 가능한 메인 프로그램
2. 의존성 관리 파일 (requirements.txt, package.json 등)
3. 설정 파일 및 환경 변수 가이드
4. README.md (설치, 설정, 사용법)
5. 개발자 문서 (API 명세, 아키텍처 설명)
6. 테스트 스위트 및 CI/CD 스크립트
7. 배포 가이드 및 운영 매뉴얼

**품질 검증:**
- 모든 기능이 요구사항을 만족
- 에러 없는 완전한 실행
- 확장성과 유지보수성 확보
- 프로덕션 배포 준비 완료

**출력**: 프로덕션 레벨의 완성된 솔루션
''',
    expected_output="완전한 프로덕션 레벨 구현 (코드, 테스트, 문서, 배포 스크립트 포함)",
    agent=master_implementer
)

# 고품질 CrewAI 팀 실행
print("🚀 전문가 팀 실행...")

crew = Crew(
    agents=[strategic_planner, technical_researcher, master_implementer],
    tasks=[task1_strategic_planning, task2_technical_research, task3_master_implementation],
    verbose=2,
    process=Process.sequential
)

try:
    start_time = datetime.now()
    print(f"⏰ 실행 시작: {{start_time.strftime('%H:%M:%S')}}")

    result = crew.kickoff()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\\n" + "=" * 50)
    print("🎉 고품질 프로젝트 완료!")
    print(f"⏱️ 총 소요시간: {{duration}}")
    print("=" * 50)

    # 결과 저장
    result_file = os.path.join("{safe_project_path}", "high_quality_result.md")

    with open(result_file, 'w', encoding='utf-8') as f:
        f.write("# 고품질 CrewAI 프로젝트 결과\\n\\n")
        f.write(f"**실행 ID**: {execution_id}\\n")
        f.write(f"**실행 시간**: {{start_time}} ~ {{end_time}}\\n")
        f.write(f"**소요 시간**: {{duration}}\\n\\n")
        f.write(f"**요구사항**: {safe_requirement}\\n\\n")
        f.write("---\\n\\n")
        f.write("## 완성된 고품질 솔루션\\n\\n")
        f.write(str(result))

    print(f"📄 결과 저장: {{os.path.abspath(result_file)}}")
    print("✅ 모든 작업 완료!")

except Exception as e:
    import traceback
    print(f"\\n❌ 실행 오류: {{e}}")
    print(f"상세 정보:\\n{{traceback.format_exc()}}")

    # 오류 로그 저장
    error_file = os.path.join("{safe_project_path}", "error_log.txt")
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"오류 시간: {{datetime.now()}}\\n")
        f.write(f"오류 내용: {{e}}\\n\\n")
        f.write(f"상세 추적:\\n{{traceback.format_exc()}}")

    print(f"🗂️ 오류 로그: {{os.path.abspath(error_file)}}")
    sys.exit(1)
'''

# 글로벌 인스턴스 생성
enhanced_generator = EnhancedCrewAIGenerator()

def generate_enhanced_crewai_script(requirement: str, selected_models: dict,
                                  project_path: str, execution_id: str) -> str:
    """외부에서 호출할 메인 함수"""
    return enhanced_generator.generate_enhanced_script(
        requirement, selected_models, project_path, execution_id
    )