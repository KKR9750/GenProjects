# DB 기반 동적 AI 프레임워크 관리 시스템 가이드

## 📋 개요

이 시스템은 **하드코딩된 Agent/Task 정의를 완전히 제거**하고, **데이터베이스 기반 동적 관리**를 가능하게 합니다.

### 🎯 핵심 개념

1. **사전분석 분리**: UI에서 LLM과 대화 → 요구사항 확정 → DB 생성
2. **템플릿 시스템**: Agent/Task 템플릿을 재사용하여 프로젝트 생성
3. **동적 스크립트 생성**: DB 데이터 → Jinja2 템플릿 → 실행 스크립트
4. **직관적 복합키**: (project_id, framework, agent_order)로 즉시 식별

---

## 🚀 사용자 워크플로우

### 1단계: 사전분석 대화 (요구사항 명확화)

**URL**: `http://localhost:3000/pre_analysis.html`

```
1. 프레임워크 선택 (CrewAI/MetaGPT)
2. LLM과 대화하며 요구사항 구체화
   - 프로젝트 목적은?
   - 핵심 기능은?
   - 대상 사용자는?
   - 기술 스택 선호도는?
3. AI가 요구사항 정리 제시
4. "확정하고 프로젝트 생성" 클릭
```

**자동 실행**:
- `POST /api/v2/projects/{id}/initialize`
- Agent/Task 템플릿 → DB 복사
- `{requirement}` 플레이스홀더 치환

### 2단계: Agent/Task 관리

**URL**: `http://localhost:3000/agent_manager.html?project_id=xxx&framework=crewai`

```
1. 생성된 Agent 목록 확인
2. 필요시 Agent 추가/수정/삭제
   - Role, Goal, Backstory 편집
   - LLM 모델 변경
   - Verbose/Delegation 설정
3. Task 관리 (task_manager.html)
   - Task 설명 및 예상 출력 편집
   - Agent 할당
   - 의존성 설정
```

### 3단계: 스크립트 생성 및 실행

```
1. "스크립트 생성 및 실행" 버튼 클릭
2. 자동 실행:
   - DB 조회 → Jinja2 렌더링
   - Projects/{project_id}/crewai_script.py 생성
   - 기존 실행 시스템과 연동
```

---

## 🗄️ 데이터베이스 스키마

### 핵심 테이블

#### 1. `project_agents`
**복합 PRIMARY KEY**: `(project_id, framework, agent_order)`

```sql
CREATE TABLE project_agents (
    project_id VARCHAR(13) NOT NULL,
    framework VARCHAR(20) NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
    agent_order INTEGER NOT NULL,

    role VARCHAR(100) NOT NULL,
    goal TEXT NOT NULL,
    backstory TEXT NOT NULL,

    llm_model VARCHAR(50) NOT NULL,
    is_verbose BOOLEAN DEFAULT true,
    allow_delegation BOOLEAN DEFAULT false,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (project_id, framework, agent_order),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
```

**직관적 조회**:
```sql
-- Agent 즉시 식별
SELECT * FROM project_agents
WHERE project_id = 'project_00042'
  AND framework = 'crewai'
  AND agent_order = 2;  -- Planner 에이전트
```

#### 2. `project_tasks`
**복합 PRIMARY KEY**: `(project_id, framework, task_order)`

```sql
CREATE TABLE project_tasks (
    project_id VARCHAR(13) NOT NULL,
    framework VARCHAR(20) NOT NULL,
    task_order INTEGER NOT NULL,

    task_type VARCHAR(50),
    description TEXT NOT NULL,
    expected_output TEXT NOT NULL,

    -- Agent 연결 (복합 FK)
    agent_project_id VARCHAR(13),
    agent_framework VARCHAR(20),
    agent_order INTEGER,

    -- Task 의존성 (복합 FK)
    depends_on_project_id VARCHAR(13),
    depends_on_framework VARCHAR(20),
    depends_on_task_order INTEGER,

    PRIMARY KEY (project_id, framework, task_order),
    FOREIGN KEY (agent_project_id, agent_framework, agent_order)
        REFERENCES project_agents(project_id, framework, agent_order)
);
```

#### 3. `agent_templates`
**재사용 가능한 템플릿**

```sql
CREATE TABLE agent_templates (
    framework VARCHAR(20) NOT NULL,
    template_name VARCHAR(100) NOT NULL,

    role VARCHAR(100) NOT NULL,
    goal_template TEXT NOT NULL,          -- {requirement} 포함
    backstory_template TEXT NOT NULL,     -- {requirement} 포함

    default_llm_model VARCHAR(50),
    is_verbose BOOLEAN DEFAULT true,
    allow_delegation BOOLEAN DEFAULT false,
    agent_order INTEGER NOT NULL,

    PRIMARY KEY (framework, template_name)
);
```

**템플릿 예시**:
```sql
INSERT INTO agent_templates VALUES (
    'crewai',
    'planner',
    'Planner',
    '다음 프로젝트의 체계적인 개발 계획을 수립합니다: {requirement}',
    '당신은 프로젝트 관리 전문가입니다. {requirement} 프로젝트의 성공적인 실행 계획 수립에 전문성을 가지고 있습니다.',
    'gemini-2.0-flash-exp',
    true,
    false,
    1
);
```

#### 4. `task_templates`

```sql
CREATE TABLE task_templates (
    framework VARCHAR(20) NOT NULL,
    task_type VARCHAR(50) NOT NULL,

    description_template TEXT NOT NULL,        -- {requirement} 포함
    expected_output_template TEXT NOT NULL,    -- {requirement} 포함

    assigned_agent_order INTEGER,
    depends_on_task_order INTEGER,
    task_order INTEGER NOT NULL,

    PRIMARY KEY (framework, task_type)
);
```

---

## 🔌 API 엔드포인트

### 사전분석 API

#### `POST /api/pre-analysis/initial`
초기 질문 생성

**Request**:
```json
{
  "framework": "crewai",
  "model": "gemini-2.0-flash-exp"
}
```

**Response**:
```json
{
  "initialQuestion": "안녕하세요! CrewAI 프로젝트 생성을 시작합니다..."
}
```

#### `POST /api/pre-analysis/chat`
대화 처리

**Request**:
```json
{
  "userMessage": "전자상거래 웹사이트를 만들고 싶어요",
  "conversationHistory": [
    {"role": "assistant", "content": "어떤 프로젝트를..."},
    {"role": "user", "content": "쇼핑몰..."}
  ],
  "model": "gemini-2.0-flash-exp"
}
```

**Response**:
```json
{
  "analysis": "AI의 분석 및 질문",
  "canFinalize": true,
  "suggestedRequirement": "전자상거래 웹사이트: 상품 목록, 장바구니, 결제 기능"
}
```

### 프로젝트 초기화 API

#### `POST /api/v2/projects/{project_id}/initialize`
프로젝트 초기화 (템플릿 → DB)

**Request**:
```json
{
  "framework": "crewai",
  "finalRequirement": "전자상거래 웹사이트를 만들고 싶습니다. 상품 목록, 장바구니, 결제 기능이 필요합니다.",
  "preAnalysisHistory": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "project_id": "project_12345678",
  "framework": "crewai",
  "agents_created": 3,
  "tasks_created": 5
}
```

**내부 동작**:
1. `projects` 테이블 업데이트 (final_requirement, framework)
2. `agent_templates` 조회 → `{requirement}` 치환 → `project_agents` 삽입
3. `task_templates` 조회 → `{requirement}` 치환 → `project_tasks` 삽입

### Agent CRUD API

#### `GET /api/v2/projects/{project_id}/agents?framework=crewai`
Agent 목록 조회

#### `POST /api/v2/projects/{project_id}/agents`
Agent 추가

**Request**:
```json
{
  "framework": "crewai",
  "agentOrder": 4,
  "role": "Reviewer",
  "goal": "코드 품질을 검토합니다",
  "backstory": "품질 보증 전문가입니다",
  "llmModel": "gemini-2.0-flash-exp",
  "isVerbose": true,
  "allowDelegation": false
}
```

#### `PUT /api/v2/projects/{project_id}/agents/{agent_order}`
Agent 수정

#### `DELETE /api/v2/projects/{project_id}/agents/{agent_order}`
Agent 삭제 (soft delete)

### Task CRUD API

동일한 패턴으로 Task 관리

### 스크립트 생성 API

#### `POST /api/generate-script`
동적 스크립트 생성

**Request**:
```json
{
  "projectId": "project_12345678"
}
```

**Response**:
```json
{
  "project_id": "project_12345678",
  "framework": "crewai",
  "script_path": "D:\\GenProjects\\Projects\\project_12345678\\crewai_script.py",
  "status": "success"
}
```

---

## 🔧 동적 스크립트 생성 엔진

### 핵심 클래스: `DynamicScriptGenerator`

```python
from dynamic_script_generator import generate_script

# 프로젝트 ID만 제공하면 자동 생성
result = generate_script('project_12345678')

# result:
# {
#     'project_id': 'project_12345678',
#     'framework': 'crewai',
#     'script_path': 'D:\\GenProjects\\Projects\\project_12345678\\crewai_script.py',
#     'status': 'success'
# }
```

### 생성 프로세스

1. **DB 조회**:
```python
# 프로젝트 정보
project = db.query("SELECT * FROM projects WHERE project_id = %s")

# Agent 목록
agents = db.query("""
    SELECT * FROM project_agents
    WHERE project_id = %s AND framework = %s
    ORDER BY agent_order
""")

# Task 목록
tasks = db.query("""
    SELECT * FROM project_tasks
    WHERE project_id = %s AND framework = %s
    ORDER BY task_order
""")
```

2. **Jinja2 렌더링**:
```python
template = env.get_template('crewai_dynamic.py.j2')
script = template.render(
    project=project,
    agents=agents,
    tasks=tasks
)
```

3. **파일 저장**:
```python
script_path = f"D:\\GenProjects\\Projects\\{project_id}\\crewai_script.py"
with open(script_path, 'w', encoding='utf-8') as f:
    f.write(script)
```

### Jinja2 템플릿 구조

**crewai_dynamic.py.j2**:
```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
프로젝트: {{ project.project_name }}
요구사항: {{ project.final_requirement }}
"""

from crewai import Agent, Task, Crew, Process

# Agents 정의
{% for agent in agents %}
{{ agent.role|lower|replace(' ', '_') }}_agent = Agent(
    role="{{ agent.role }}",
    goal="{{ agent.goal }}",
    backstory="{{ agent.backstory }}",
    verbose={{ agent.is_verbose|lower }},
    allow_delegation={{ agent.allow_delegation|lower }},
    llm=get_llm("{{ agent.llm_model }}")
)
{% endfor %}

# Tasks 정의
{% for task in tasks %}
task_{{ task.task_order }} = Task(
    description="{{ task.description }}",
    expected_output="{{ task.expected_output }}",
    agent={{ task.agent_role|lower|replace(' ', '_') }}_agent
)
{% endfor %}

# Crew 구성 및 실행
crew = Crew(
    agents=[{% for agent in agents %}{{ agent.role|lower|replace(' ', '_') }}_agent{{ "," if not loop.last }}{% endfor %}],
    tasks=[{% for task in tasks %}task_{{ task.task_order }}{{ "," if not loop.last }}{% endfor %}],
    process=Process.sequential
)

result = crew.kickoff()
```

---

## 📊 데이터 흐름도

```
┌─────────────────────────────────────┐
│  1. 사전분석 UI (pre_analysis.html) │
│     - LLM과 대화                     │
│     - 요구사항 명확화                │
└────────────────┬────────────────────┘
                 │
                 ▼ POST /api/v2/projects/{id}/initialize
┌─────────────────────────────────────┐
│  2. 프로젝트 초기화                  │
│     - agent_templates 조회           │
│     - {requirement} 치환             │
│     - project_agents 삽입            │
│     - task_templates 조회            │
│     - project_tasks 삽입             │
└────────────────┬────────────────────┘
                 │
                 ▼ GET /api/v2/projects/{id}/agents
┌─────────────────────────────────────┐
│  3. Agent 관리 UI (agent_manager)    │
│     - Agent 목록 조회/수정           │
│     - Task 관리                      │
└────────────────┬────────────────────┘
                 │
                 ▼ POST /api/generate-script
┌─────────────────────────────────────┐
│  4. 동적 스크립트 생성               │
│     - DB 조회                        │
│     - Jinja2 렌더링                  │
│     - crewai_script.py 저장          │
└────────────────┬────────────────────┘
                 │
                 ▼ 기존 실행 시스템
┌─────────────────────────────────────┐
│  5. 스크립트 실행                    │
│     - python crewai_script.py        │
│     - 실시간 모니터링                │
└─────────────────────────────────────┘
```

---

## 🎨 UI 스크린샷 설명

### 1. 사전분석 대화 UI
- **URL**: `/pre_analysis.html`
- **기능**:
  - CrewAI/MetaGPT 프레임워크 선택
  - LLM과 실시간 채팅
  - 요구사항 정리 및 확정
  - 자동 프로젝트 생성

### 2. Agent 관리 UI
- **URL**: `/agent_manager.html?project_id=xxx&framework=crewai`
- **기능**:
  - Agent 카드 뷰
  - Agent 추가/수정/삭제
  - LLM 모델 변경
  - 스크립트 생성 버튼

---

## 🔑 핵심 혁신 포인트

### 1. 하드코딩 완전 제거
**Before** (기존):
```python
# crewai_script.py (하드코딩)
planner = Agent(
    role="Planner",
    goal="Develop a comprehensive project plan...",
    backstory="You are an expert project manager...",
    llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
)
```

**After** (DB 기반):
```python
# dynamic_script_generator.py
agents = db.query("SELECT * FROM project_agents WHERE project_id = %s")
# Jinja2 템플릿으로 자동 생성
```

### 2. 직관적 복합키
**Before** (SERIAL ID):
```sql
SELECT * FROM agents WHERE agent_id = 42;  -- 42가 뭐지?
```

**After** (복합키):
```sql
SELECT * FROM project_agents
WHERE project_id = 'project_00042'
  AND framework = 'crewai'
  AND agent_order = 2;  -- 명확: CrewAI 프로젝트의 2번째 Agent
```

### 3. 템플릿 재사용
**Before**: 프로젝트마다 Agent/Task 수동 정의

**After**:
```sql
-- 템플릿 한 번 정의
INSERT INTO agent_templates VALUES ('crewai', 'planner', ...);

-- 무한 재사용
-- {requirement} 플레이스홀더만 치환하면 끝
```

### 4. 사전분석 분리
**Before**: Agent 테이블에 사전분석 Agent 포함 (혼란)

**After**:
- **UI 대화**: 요구사항 명확화 (메모리에만 존재)
- **DB Agent**: 실행용 Agent만 저장 (깔끔)

---

## 🚨 중요 설정

### PostgreSQL 연결 설정

**환경 변수** (.env):
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_DB_PASSWORD=your-database-password  # psycopg2 직접 연결용
```

**⚠️ 보안 주의**: 실제 자격증명은 `.env` 파일에만 저장하고 Git에 커밋하지 마세요!

**database.py**:
```python
def get_db_connection():
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(
        host="aws-0-ap-northeast-2.pooler.supabase.com",
        port=6543,
        database="postgres",
        user="postgres.vpbkitxgisxbqtxrwjvo",
        password=os.getenv("SUPABASE_DB_PASSWORD"),
        sslmode="require"
    )
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn
```

### 필수 패키지
```bash
pip install psycopg2-binary jinja2 langchain langchain-google-genai langchain-openai
```

---

## 📝 사용 예시

### 예시 1: 전자상거래 프로젝트

**1. 사전분석 대화**:
```
User: "전자상거래 웹사이트를 만들고 싶어요"
AI: "어떤 핵심 기능이 필요하신가요?"
User: "상품 목록, 장바구니, 결제 기능입니다"
AI: "다음과 같이 요구사항을 정리했습니다:
     전자상거래 웹사이트: 상품 목록 표시, 장바구니 관리, 결제 기능 구현"
```

**2. 프로젝트 초기화** (자동):
```sql
-- agent_templates 'planner' 조회
goal_template = "다음 프로젝트의 계획을 수립합니다: {requirement}"
→ goal = "다음 프로젝트의 계획을 수립합니다: 전자상거래 웹사이트: 상품 목록..."

-- project_agents 삽입
INSERT INTO project_agents VALUES (
    'project_00042', 'crewai', 1,
    'Planner',
    '다음 프로젝트의 계획을 수립합니다: 전자상거래 웹사이트: 상품 목록 표시, 장바구니 관리, 결제 기능 구현',
    '당신은 프로젝트 관리 전문가입니다. 전자상거래 웹사이트: 상품 목록... 프로젝트의 성공적인 실행 계획 수립에 전문성을 가지고 있습니다.',
    'gemini-2.0-flash-exp', true, false
);
```

**3. Agent 관리** (UI):
- Agent 3개 생성 확인: Planner, Researcher, Writer
- Planner의 LLM을 gpt-4로 변경
- Reviewer Agent 추가 (agent_order=4)

**4. 스크립트 생성**:
```python
# POST /api/generate-script {"projectId": "project_00042"}
# → D:\GenProjects\Projects\project_00042\crewai_script.py 생성

#!/usr/bin/env python
# 프로젝트: 전자상거래 웹사이트
# 요구사항: 상품 목록 표시, 장바구니 관리, 결제 기능 구현

planner_agent = Agent(
    role="Planner",
    goal="다음 프로젝트의 계획을 수립합니다: 전자상거래 웹사이트...",
    backstory="당신은 프로젝트 관리 전문가입니다...",
    llm=get_llm("gpt-4")  # UI에서 변경한 모델
)

researcher_agent = Agent(...)
writer_agent = Agent(...)
reviewer_agent = Agent(...)  # UI에서 추가한 Agent

task_1 = Task(
    description="전자상거래 웹사이트: 상품 목록... 프로젝트의 개발 계획을 수립하세요",
    expected_output="상세한 개발 계획 문서",
    agent=planner_agent
)

crew = Crew(
    agents=[planner_agent, researcher_agent, writer_agent, reviewer_agent],
    tasks=[task_1, task_2, task_3],
    process=Process.sequential
)
```

---

## 🔧 커스터마이징 가이드

### 새로운 Agent 템플릿 추가

```sql
INSERT INTO agent_templates (
    framework, template_name, role,
    goal_template, backstory_template,
    default_llm_model, agent_order
) VALUES (
    'crewai',
    'tester',
    'QA Tester',
    '다음 프로젝트의 품질을 검증합니다: {requirement}',
    '당신은 QA 전문가입니다. {requirement} 프로젝트의 품질 보증을 담당합니다.',
    'gemini-2.0-flash-exp',
    4
);
```

### 새로운 Task 템플릿 추가

```sql
INSERT INTO task_templates (
    framework, task_type,
    description_template, expected_output_template,
    assigned_agent_order, task_order
) VALUES (
    'crewai',
    'testing',
    '{requirement} 프로젝트의 테스트 계획을 수립하고 실행하세요',
    '테스트 케이스 목록과 테스트 결과 리포트',
    4,  -- QA Tester agent
    4
);
```

### 새로운 프레임워크 추가

1. **agent_templates 추가**:
```sql
INSERT INTO agent_templates VALUES ('newframework', 'agent1', ...);
```

2. **task_templates 추가**:
```sql
INSERT INTO task_templates VALUES ('newframework', 'task1', ...);
```

3. **Jinja2 템플릿 생성**:
```bash
templates/scripts/newframework_dynamic.py.j2
```

4. **dynamic_script_generator.py 수정**:
```python
def generate_newframework_script(self, project_id: str) -> str:
    template = self.env.get_template('newframework_dynamic.py.j2')
    # ...
```

---

## 🐛 트러블슈팅

### 문제 1: psycopg2 import 오류
```bash
pip install psycopg2-binary
```

### 문제 2: Jinja2 템플릿 not found
```python
# templates/scripts/ 디렉토리 확인
template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'scripts')
```

### 문제 3: Agent 생성 실패
```sql
-- 복합키 충돌 확인
SELECT * FROM project_agents
WHERE project_id = 'xxx'
  AND framework = 'crewai'
  AND agent_order = 1;

-- 이미 존재하면 UPDATE 또는 agent_order 변경
```

### 문제 4: {requirement} 치환 안 됨
```python
# template에서 확인
goal_template = "... {requirement} ..."

# 치환 실행
goal = goal_template.replace('{requirement}', final_requirement)
```

---

## 📚 참고 문서

- **데이터베이스 스키마**: [setup_database_dynamic.sql](setup_database_dynamic.sql)
- **동적 스크립트 생성기**: [dynamic_script_generator.py](dynamic_script_generator.py)
- **프로젝트 초기화 API**: [project_initialization_api.py](project_initialization_api.py)
- **Agent CRUD API**: [agent_task_crud_api.py](agent_task_crud_api.py)
- **Pre-analysis API**: [pre_analysis_chat_api.py](pre_analysis_chat_api.py)
- **Jinja2 템플릿**: [templates/scripts/](templates/scripts/)

---

## 🎯 다음 단계

1. **Task 관리 UI 구현** (task_manager.html)
2. **실시간 실행 모니터링 연동**
3. **MetaGPT 템플릿 완성**
4. **프로젝트 히스토리 관리**
5. **템플릿 마켓플레이스** (커뮤니티 템플릿 공유)
