# AI 프로그램 생성 채팅 인터페이스 프로젝트 현황

## 📋 프로젝트 개요

### 🎯 목적
AI 프로그램 생성을 위한 대화형 인터페이스 개발
- **CrewAI**와 **MetaGPT** 프레임워크를 활용한 멀티 에이전트 시스템
- 역할별 LLM 모델 선택을 통한 최적화된 AI 협업 환경 구축
- 오프라인 환경에서의 로컬 LLM 모델 지원

### 🏗️ 아키텍처
```
┌─────────────────┬─────────────────┐
│   Frontend      │   Backend       │
│   (React.js)    │   (Flask)       │
├─────────────────┼─────────────────┤
│ - UI Components │ - API Server    │
│ - State Mgmt    │ - Project Mgmt  │
│ - LLM Selection │ - File System   │
└─────────────────┴─────────────────┘
```

---

## 🚀 현재 구현 상태

### ✅ 완료된 기능

#### 1. **통합 대시보드 시스템**
- **메인 대시보드**: CrewAI와 MetaGPT 통합 관리 중앙 제어 센터 (`dashboard.js`)
- **시스템 상태 모니터링**: 실시간 시스템 상태 체크 및 표시
- **시스템 카드 인터페이스**: 각 AI 프레임워크별 상세 정보 및 접근 버튼
- **반응형 디자인**: 모바일/데스크톱 호환

#### 8. **개별 AI 프레임워크 전용 인터페이스** ⭐ **신규 완성 (2025-09-17)**
- **CrewAI 전용 페이지** (`crewai.html`, `crewai.js`, `crewai.css`)
  - 보라색 테마의 독립적인 UI 디자인
  - 3개 역할별 인터페이스: Researcher, Writer, Planner
  - 역할별 독립적인 LLM 모델 선택 시스템
  - 실시간 연결 상태 모니터링
  - 프로젝트 관리 기능 통합

- **MetaGPT 전용 페이지** (`metagpt.html`, `metagpt.js`, `metagpt.css`)
  - 녹색 테마의 독립적인 UI 디자인
  - 5단계 소프트웨어 개발 프로세스 워크플로우
  - 단계별 역할 자동 전환: Product Manager → Architect → Project Manager → Engineer → QA Engineer
  - 각 단계별 산출물 정의 및 추적
  - 승인 기반 워크플로우 시스템

#### 9. **통합 Flask 서버 아키텍처** ⭐ **완전 개편 (2025-09-17)**
- **단일 포트 통합**: 포트 3000에서 모든 서비스 통합 제공
- **내부 라우팅 시스템**: CrewAI(5000), MetaGPT(8000) 내부 연동
- **통합 API 엔드포인트**: `/api/crewai/`, `/api/metagpt/` 라우팅
- **크로스 플랫폼 경로 지원**: Windows/Linux 호환성
- **실시간 상태 관리**: 각 프레임워크별 독립적인 실행 상태 추적

#### 2. **메인 UI 인터페이스**
- **좌측 사이드바**: AI 프레임워크 및 역할 선택 영역 (`app_simple.js`)
- **우측 채팅 영역**: 대화형 인터페이스
- **반응형 디자인**: 모바일/데스크톱 호환

#### 3. **AI 프레임워크 선택 시스템**
```javascript
// 지원하는 AI 프레임워크
CREW AI: {
  roles: ["Researcher", "Writer", "Planner"] // 3개 역할
}

MetaGPT: {
  roles: [
    "Product Manager",    // 요구사항 정리 및 PRD 작성
    "Architect",         // 시스템 설계 및 구조 계획
    "Project Manager",   // 작업 분석 및 계획 수립
    "Engineer",          // 코드 개발 및 구현
    "QA Engineer"       // 테스트 및 품질 보증
  ] // 5개 역할
}
```

#### 4. **역할별 LLM 모델 선택**
```javascript
// 지원하는 LLM 모델
const llmOptions = [
  { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델' },
  { id: 'gpt-4o', name: 'GPT-4o', description: '멀티모달 최신 모델' },
  { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델' },
  { id: 'claude-3-haiku', name: 'Claude-3 Haiku', description: '빠른 응답 모델' },
  { id: 'gemini-pro', name: 'Gemini Pro', description: '멀티모달 모델' },
  { id: 'gemini-ultra', name: 'Gemini Ultra', description: '최고 성능 모델' },
  { id: 'llama-3', name: 'Llama-3 70B', description: '오픈소스 모델' },
  { id: 'llama-3-8b', name: 'Llama-3 8B', description: '경량 오픈소스 모델' },
  { id: 'mistral-large', name: 'Mistral Large', description: '효율성 중심 모델' },
  { id: 'mistral-7b', name: 'Mistral 7B', description: '경량 효율 모델' },
  { id: 'deepseek-coder', name: 'DeepSeek Coder', description: '코딩 전문 모델' },
  { id: 'codellama', name: 'Code Llama', description: '코드 생성 특화' }
];
```

#### 5. **역할-LLM 매핑 시스템**
- **개별 설정**: 각 역할마다 독립적인 LLM 모델 선택
- **실시간 표시**: 🎭 역할별 LLM 설정 섹션에서 매핑 상태 확인
- **동적 관리**: 역할 변경 시 자동으로 해당 LLM 설정 반영

#### 6. **프로젝트 관리 시스템**
- **신규 프로젝트** 생성 기능
- **기존 프로젝트** 불러오기 및 이어서 작업
- **프로젝트 상태** 추적 (진행률, 단계별 상태)
- **실시간 데이터** 연동 (`D:\GenProjects\Projects` 디렉토리)

#### 7. **백엔드 API 시스템**
```python
# Flask 서버 (포트 3000)
/api/projects  # 프로젝트 목록 조회
- 실제 프로젝트 메타데이터 읽기
- JSON 형태로 프로젝트 정보 제공
```

---

## 🛠️ 기술 스택

### Frontend
- **React.js 18**: 컴포넌트 기반 UI 개발
- **Babel**: JSX 트랜스파일링
- **CSS3**: 그라데이션 및 반응형 디자인
- **Vanilla JavaScript**: 상태 관리

### Backend
- **Flask**: Python 웹 프레임워크
- **File System API**: 프로젝트 데이터 관리
- **JSON**: 데이터 교환 형식

### 데이터베이스 시스템 (CrewAI 기반)
- **Supabase**: PostgreSQL 기반 BaaS (Backend as a Service)
- **실시간 데이터 동기화**: WebSocket 지원으로 실시간 업데이트
- **RESTful API**: 자동 생성되는 CRUD API 엔드포인트
- **인증 시스템**: 내장된 사용자 관리 및 권한 제어
- **파일 저장소**: 대용량 파일 및 미디어 관리

### 개발 환경 ⭐ **업데이트됨 (2025-09-17)**
- **통합 Flask Server**: 모든 AI 프레임워크 통합 관리 (포트 3000)
  - 내부 라우팅: CrewAI (5000), MetaGPT (8000)
  - 정적 파일 서빙: HTML, CSS, JS
  - API 프록시: `/api/crewai/`, `/api/metagpt/`
- **개별 프레임워크 인터페이스**:
  - CrewAI 전용 페이지: `http://localhost:3000/crewai.html`
  - MetaGPT 전용 페이지: `http://localhost:3000/metagpt.html`
  - 통합 대시보드: `http://localhost:3000/dashboard.html`
- **Chrome DevTools**: 디버깅 및 테스트

---

## 🗄️ 데이터베이스 스키마 (CrewAI 기반)

### 📊 **핵심 테이블 구조**

#### 1. **projects** (확장된 프로젝트 관리)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    description TEXT,

    -- AI 프레임워크 선택
    selected_ai VARCHAR DEFAULT 'crew-ai', -- 'crew-ai', 'meta-gpt'

    -- 프로젝트 진행 상태
    status VARCHAR DEFAULT 'planning', -- 'planning', 'in_progress', 'review', 'completed', 'paused'
    current_stage VARCHAR DEFAULT 'requirement', -- 'requirement', 'design', 'architecture', 'development', 'testing', 'deployment'
    progress_percentage INTEGER DEFAULT 0,

    -- 프로젝트 설정
    project_type VARCHAR DEFAULT 'web_app', -- 'web_app', 'mobile_app', 'api', 'desktop', 'data_analysis'
    target_audience TEXT,
    technical_requirements JSONB, -- 기술적 요구사항 (JSON 형태)

    -- 메타데이터
    workspace_path VARCHAR, -- 실제 프로젝트 생성 경로
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    deadline TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. **crews** (AI 크루 정보)
```sql
CREATE TABLE crews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    description TEXT,
    crew_type VARCHAR DEFAULT 'base', -- 'base', 'generated', 'creator'
    file_path VARCHAR, -- 프로젝트 폴더 경로
    status VARCHAR DEFAULT 'active', -- 'active', 'inactive'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. **agents** (AI 에이전트 정보)
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id UUID REFERENCES crews(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL, -- 'Researcher', 'Writer', 'Engineer' 등
    goal TEXT NOT NULL,
    backstory TEXT,
    llm_model VARCHAR DEFAULT 'gpt-4', -- 할당된 LLM 모델
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. **tasks** (작업 정의)
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id UUID REFERENCES crews(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    description TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    execution_order INTEGER DEFAULT 0,
    status VARCHAR DEFAULT 'pending', -- 'pending', 'running', 'completed'
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. **crew_inputs** (크루 입력 필드)
```sql
CREATE TABLE crew_inputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    crew_id UUID REFERENCES crews(id) ON DELETE CASCADE,
    field_name VARCHAR NOT NULL,
    field_type VARCHAR DEFAULT 'text', -- 'text', 'textarea', 'select'
    field_label VARCHAR NOT NULL,
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. **execution_history** (실행 이력)
```sql
CREATE TABLE execution_history (
    id UUID PRIMARY KEY,
    crew_id UUID REFERENCES crews(id) ON DELETE CASCADE,
    inputs JSONB, -- 실행 시 입력된 파라미터들
    status VARCHAR DEFAULT 'running', -- 'running', 'completed', 'failed'
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds FLOAT,
    final_output TEXT,
    error_message TEXT
);
```

#### 7. **project_role_llm_mapping** (프로젝트별 역할-LLM 매핑)
```sql
CREATE TABLE project_role_llm_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    role_name VARCHAR NOT NULL, -- 'Researcher', 'Writer', 'Product Manager' 등
    llm_model VARCHAR NOT NULL, -- 'gpt-4', 'claude-3', 'gemini-pro' 등
    llm_config JSONB, -- LLM별 세부 설정 (temperature, max_tokens 등)
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 프로젝트 내에서 역할별로 유일한 LLM 매핑
    UNIQUE(project_id, role_name)
);
```

#### 8. **project_stages** (프로젝트 진행 단계 정의)
```sql
CREATE TABLE project_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    stage_name VARCHAR NOT NULL, -- 'requirement', 'design', 'architecture' 등
    stage_order INTEGER NOT NULL, -- 단계 순서
    stage_status VARCHAR DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'blocked'
    responsible_role VARCHAR, -- 담당 역할 (Researcher, Architect 등)
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 프로젝트 내에서 단계별 순서는 유일
    UNIQUE(project_id, stage_order)
);
```

#### 9. **project_deliverables** (프로젝트 산출물 관리)
```sql
CREATE TABLE project_deliverables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE CASCADE,

    -- 산출물 정보
    deliverable_type VARCHAR NOT NULL, -- 'requirement', 'design_doc', 'ui_wireframe', 'api_spec', 'code', 'test_plan' 등
    title VARCHAR NOT NULL,
    description TEXT,

    -- 문서/파일 정보
    content TEXT, -- 문서 내용 (Markdown 형태)
    file_path VARCHAR, -- 파일 경로 (이미지, PDF 등)
    file_type VARCHAR, -- 'markdown', 'pdf', 'image', 'code', 'json'
    file_size INTEGER, -- 바이트 단위

    -- 버전 관리
    version VARCHAR DEFAULT '1.0',
    is_latest BOOLEAN DEFAULT true,
    parent_deliverable_id UUID REFERENCES project_deliverables(id), -- 이전 버전 참조

    -- 상태 및 승인
    status VARCHAR DEFAULT 'draft', -- 'draft', 'review', 'approved', 'rejected'
    created_by_role VARCHAR, -- 생성한 역할
    reviewed_by_role VARCHAR, -- 검토한 역할
    approved_by_role VARCHAR, -- 승인한 역할

    -- 메타데이터
    tags JSONB, -- 태그 및 분류
    metadata JSONB, -- 추가 메타데이터

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 10. **deliverable_access_log** (산출물 접근 이력)
```sql
CREATE TABLE deliverable_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deliverable_id UUID REFERENCES project_deliverables(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    accessed_by_role VARCHAR NOT NULL,
    access_type VARCHAR NOT NULL, -- 'read', 'edit', 'download', 'share'
    access_details JSONB, -- 접근 관련 상세 정보
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 🔄 **확장된 데이터 플로우**

#### **프로젝트 생성 및 설정**
```
사용자 → AI 선택 (CREW AI/MetaGPT) → projects 테이블에 저장
   ↓
역할별 LLM 매핑 설정 → project_role_llm_mapping 테이블에 저장
   ↓
프로젝트 단계 자동 생성 → project_stages 테이블에 저장
```

#### **프로젝트 진행 워크플로우**
```
단계 시작 → project_stages.status = 'in_progress'
   ↓
AI 에이전트 실행 → 해당 역할의 LLM 모델 조회 (project_role_llm_mapping)
   ↓
산출물 생성 → project_deliverables 테이블에 저장
   ↓
다른 역할들이 산출물 접근 → deliverable_access_log 기록
   ↓
단계 완료 → project_stages.status = 'completed' → 다음 단계로 진행
```

#### **문서 공유 및 협업**
```
역할A가 요구사항서 작성 → project_deliverables (type: 'requirement')
   ↓
역할B가 해당 문서 조회 → deliverable_access_log 기록
   ↓
역할B가 설계서 작성 → project_deliverables (type: 'design_doc')
   ↓
모든 산출물이 다음 단계의 입력으로 활용 → 단계별 연계 진행
```

### 🚀 **향후 데이터베이스 통합 계획**

#### **1단계: 기본 연동** (현재 진행 중)
- AI 채팅 인터페이스에서 CrewAI 데이터베이스 읽기 전용 접근
- 프로젝트 목록 및 크루 정보 표시

#### **2단계: 데이터 동기화**
- 역할별 LLM 매핑을 `project_role_llm_mapping` 테이블에 저장
- 실시간 상태 업데이트를 위한 WebSocket 연동
- 프로젝트 진행 상태 자동 업데이트

#### **3단계: 완전 통합**
- 통합 사용자 관리 (Supabase Auth)
- 크로스 플랫폼 데이터 공유
- 통합 대시보드 구현

### 🔐 **보안 및 권한 관리**

#### **데이터 접근 제어**
```sql
-- Row Level Security (RLS) 정책 예시
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_deliverables ENABLE ROW LEVEL SECURITY;

-- 프로젝트 소유자만 접근 가능
CREATE POLICY project_access ON projects
FOR ALL USING (auth.uid() = owner_id);

-- 역할별 산출물 접근 권한
CREATE POLICY deliverable_role_access ON project_deliverables
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM project_role_llm_mapping prm
    WHERE prm.project_id = project_deliverables.project_id
    AND prm.role_name = auth.jwt() ->> 'role'
  )
);
```

#### **API 인증 및 권한**
- **JWT 토큰 기반 인증**
- **역할 기반 접근 제어 (RBAC)**
- **프로젝트별 권한 분리**
- **API Rate Limiting**

### 🚨 **에러 처리 및 복구**

#### **데이터 무결성 보장**
```sql
-- 외래키 제약조건
ALTER TABLE project_role_llm_mapping
ADD CONSTRAINT valid_llm_model
CHECK (llm_model IN ('gpt-4', 'claude-3', 'gemini-pro', 'llama-3', 'deepseek-coder', 'mistral-large'));

-- 단계 순서 검증
ALTER TABLE project_stages
ADD CONSTRAINT valid_stage_order
CHECK (stage_order > 0 AND stage_order <= 10);

-- 진행률 검증
ALTER TABLE projects
ADD CONSTRAINT valid_progress
CHECK (progress_percentage >= 0 AND progress_percentage <= 100);
```

#### **백업 및 복구 전략**
- **자동 일일 백업** (Supabase 자동 백업)
- **실시간 복제** (Read Replica)
- **Point-in-Time Recovery**
- **산출물 파일 백업** (Supabase Storage)

### 📊 **성능 최적화**

#### **데이터베이스 인덱스**
```sql
-- 자주 조회되는 컬럼에 인덱스 생성
CREATE INDEX idx_projects_selected_ai ON projects(selected_ai);
CREATE INDEX idx_projects_status ON projects(status, current_stage);
CREATE INDEX idx_deliverables_project_type ON project_deliverables(project_id, deliverable_type);
CREATE INDEX idx_deliverables_stage ON project_deliverables(stage_id, created_at);
CREATE INDEX idx_role_mapping_project ON project_role_llm_mapping(project_id, role_name);

-- 복합 인덱스
CREATE INDEX idx_projects_composite ON projects(selected_ai, status, created_at);
```

#### **캐싱 전략**
- **Redis 캐싱**: 프로젝트 목록, 역할-LLM 매핑
- **CDN**: 정적 산출물 (이미지, PDF)
- **쿼리 결과 캐싱**: 대시보드 통계 데이터

### 🔄 **데이터 마이그레이션**

#### **기존 데이터 이전**
```sql
-- 기존 crews 테이블에서 새로운 구조로 마이그레이션
INSERT INTO projects (name, description, selected_ai, status)
SELECT name, description,
       CASE WHEN crew_type = 'meta-gpt' THEN 'meta-gpt' ELSE 'crew-ai' END,
       CASE WHEN status = 'active' THEN 'in_progress' ELSE 'completed' END
FROM crews WHERE crew_type IN ('meta-gpt', 'crew-ai');

-- agents 테이블에서 역할-LLM 매핑 추출
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
SELECT p.id, a.role, COALESCE(a.llm_model, 'gpt-4')
FROM projects p
JOIN crews c ON c.name = p.name
JOIN agents a ON a.crew_id = c.id;
```

### 📈 **모니터링 및 분석**

#### **시스템 메트릭스**
- **프로젝트 완료율**: 단계별 성공률
- **LLM 사용량**: 모델별 사용 빈도 및 비용
- **평균 프로젝트 완료 시간**: AI별, 프로젝트 타입별
- **산출물 품질**: 승인/반려 비율

#### **비즈니스 인텔리전스**
```sql
-- 프로젝트 성과 분석 뷰
CREATE VIEW project_analytics AS
SELECT
  p.selected_ai,
  p.project_type,
  COUNT(*) as total_projects,
  AVG(p.progress_percentage) as avg_progress,
  AVG(EXTRACT(EPOCH FROM (p.updated_at - p.created_at))/3600) as avg_duration_hours,
  COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed_count
FROM projects p
GROUP BY p.selected_ai, p.project_type;

-- LLM 효율성 분석 뷰
CREATE VIEW llm_efficiency AS
SELECT
  prm.llm_model,
  prm.role_name,
  COUNT(DISTINCT prm.project_id) as projects_count,
  AVG(ps.actual_hours) as avg_hours_per_stage,
  COUNT(pd.id) as deliverables_created,
  COUNT(CASE WHEN pd.status = 'approved' THEN 1 END) as approved_deliverables
FROM project_role_llm_mapping prm
JOIN project_stages ps ON ps.project_id = prm.project_id AND ps.responsible_role = prm.role_name
LEFT JOIN project_deliverables pd ON pd.stage_id = ps.id
GROUP BY prm.llm_model, prm.role_name;
```

---

## 📁 프로젝트 구조

```
ai-chat-interface/
├── 📄 index.html              # 메인 HTML 엔트리 포인트 (통합 대시보드)
├── 📄 dashboard.html          # 통합 대시보드 HTML
├── 📄 dashboard.js            # 통합 대시보드 React 컴포넌트
├── 📄 dashboard.css           # 대시보드 전용 스타일
├── 📄 crewai.html            # CrewAI 전용 페이지 ⭐ 신규
├── 📄 crewai.js              # CrewAI React 컴포넌트 ⭐ 신규
├── 📄 crewai.css             # CrewAI 테마 스타일 (보라색) ⭐ 신규
├── 📄 metagpt.html           # MetaGPT 전용 페이지 ⭐ 신규
├── 📄 metagpt.js             # MetaGPT React 컴포넌트 ⭐ 신규
├── 📄 metagpt.css            # MetaGPT 테마 스타일 (녹색) ⭐ 신규
├── 📄 app_simple.js           # 레거시 AI 채팅 인터페이스
├── 📄 styles.css              # 공통 스타일시트
├── 📄 app.py                  # 통합 Flask 백엔드 서버 ⭐ 완전 개편
├── 📄 metagpt_bridge.py       # MetaGPT 연동 브리지
├── 📄 start.py                # 서버 실행 스크립트
├── 📁 screen_shot/            # 스크린샷 저장소
├── 📁 workspace/              # 작업 공간
└── 📄 PROJECT_STATUS.md       # 현재 문서 (프로젝트 현황)
```

---

## 🎮 사용자 인터페이스 플로우

### 1. **AI 프레임워크 선택**
```
사용자 → [CREW AI / MetaGPT 선택] → 해당 역할 목록 표시
```

### 2. **역할별 LLM 설정**
```
역할 선택 → LLM 모델 선택 → 매핑 저장 → 실시간 표시 업데이트
```

### 3. **프로젝트 워크플로우**
```
[신규 프로젝트] → 요구사항 입력 → AI 처리 → 결과 표시
[기존 프로젝트] → 프로젝트 선택 → 이어서 작업 → 단계별 진행
```

---

## 🔧 주요 구현 특징 ⭐ **업데이트됨 (2025-09-17)**

### 🎯 **독립적인 AI 프레임워크 인터페이스**
- **CrewAI 전용 인터페이스**: 3개 역할 기반 협업 (Researcher, Writer, Planner)
  - 보라색 테마로 브랜드 아이덴티티 구축
  - 역할별 독립적인 대화 세션 관리
  - 실시간 연결 상태 모니터링

- **MetaGPT 전용 인터페이스**: 5단계 소프트웨어 개발 프로세스
  1. Product Manager → 요구사항 분석 (PRD 작성)
  2. Architect → 시스템 설계 (아키텍처 설계)
  3. Project Manager → 작업 계획 (일정 수립)
  4. Engineer → 코드 구현 (개발 실행)
  5. QA Engineer → 테스트 및 검증 (품질 보증)
  - 녹색 테마로 차별화된 시각적 경험
  - 단계별 워크플로우 자동 진행 시스템
  - 승인 기반 단계 전환 메커니즘

### 🤖 **고도화된 LLM 모델 관리**
- **프레임워크별 최적화**: CrewAI와 MetaGPT 각각의 특성에 맞는 모델 선택
- **역할별 전문화**: 각 역할의 업무 특성에 최적화된 LLM 매핑
  - 연구/분석: GPT-4, Gemini Pro
  - 코딩: DeepSeek Coder, Code Llama
  - 문서작성: Claude-3, GPT-4o
  - 빠른응답: Claude-3 Haiku, Mistral 7B
- **동적 모델 전환**: 실시간으로 LLM 모델 변경 및 적용
- **설정 영속성**: 프로젝트별 LLM 매핑 설정 저장

### 📊 **통합 상태 관리 시스템**
- **대시보드 중앙 제어**: 모든 AI 프레임워크 상태를 한 눈에 모니터링
- **실시간 연결 체크**: 각 프레임워크별 독립적인 상태 확인
- **프로젝트 진행률**: 단계별 완료 상태 시각화
- **크로스 플랫폼 호환**: 통합 서버를 통한 일관된 상태 관리

### 🎨 **차별화된 사용자 경험**
- **프레임워크별 테마**: 시각적으로 구분되는 브랜드 경험
- **직관적인 워크플로우**: 단계별 진행 상황을 명확하게 표시
- **반응형 디자인**: 모든 디바이스에서 최적화된 인터페이스
- **실시간 피드백**: 사용자 액션에 대한 즉각적인 시각적 반응

---

## 🚀 향후 개발 계획

### 🔄 **단기 목표 (1-2주)**

#### ✅ **완료된 항목**

**2025-01-17 완료**
1. **통합 대시보드 구현**
   - ✅ CrewAI와 MetaGPT 통합 관리 대시보드 완성
   - ✅ 시스템 상태 실시간 모니터링 기능
   - ✅ 각 시스템별 상세 정보 카드 인터페이스
   - ✅ 최근 프로젝트 표시 기능 제거 (각 시스템 페이지에서 확인)

**2025-09-17 완료** ⭐ **주요 업데이트**
2. **개별 AI 프레임워크 전용 인터페이스 완성**
   - ✅ CrewAI 전용 페이지 및 UI 시스템 구축
   - ✅ MetaGPT 전용 페이지 및 워크플로우 시스템 구축
   - ✅ 각 프레임워크별 독립적인 테마 및 UX 설계
   - ✅ 역할별 LLM 모델 매핑 시스템 고도화

3. **통합 서버 아키텍처 완전 개편**
   - ✅ Flask 기반 단일 포트(3000) 통합 서버 구축
   - ✅ 내부 라우팅 시스템으로 CrewAI/MetaGPT 연동
   - ✅ 크로스 플랫폼 호환성 확보 (Windows/Linux)
   - ✅ 실시간 상태 관리 및 API 엔드포인트 통합

4. **사용자 경험(UX) 대폭 개선**
   - ✅ 프레임워크별 색상 테마 분리 (CrewAI: 보라색, MetaGPT: 녹색)
   - ✅ 직관적인 단계별 워크플로우 시각화
   - ✅ 실시간 연결 상태 표시 및 피드백 시스템
   - ✅ 반응형 디자인 최적화

#### 🔄 **진행 중인 항목**
1. **CrewAI 데이터베이스 통합**
   - Supabase 연동을 위한 환경 설정
   - 프로젝트/크루 데이터 실시간 동기화
   - 역할별 LLM 매핑을 DB에 저장

2. **보안 및 권한 시스템 구축**
   - JWT 기반 인증 시스템
   - Row Level Security (RLS) 정책 구현
   - 역할 기반 접근 제어 (RBAC)

3. **LLM 모델 동적 관리**
   - 설정 파일 기반 모델 추가/제거
   - 관리자 UI를 통한 모델 등록
   - DB 기반 모델 목록 관리

4. **로컬 LLM 연동**
   - Ollama 연동
   - Hugging Face Transformers 지원

5. **프로젝트 템플릿**
   - 웹 앱, 모바일 앱, API 서버 등 템플릿 제공

### 🎯 **중기 목표 (1-2개월)**
1. **데이터베이스 고도화**
   - WebSocket 기반 실시간 데이터 동기화
   - 실행 이력 및 성능 모니터링
   - 백업 및 복구 시스템 구축

2. **고급 워크플로우**
   - 코드 리뷰 자동화
   - 테스트 케이스 자동 생성
   - 배포 파이프라인 구성

3. **협업 기능**
   - Supabase Auth 기반 다중 사용자 지원
   - 실시간 협업 인터페이스
   - 역할 기반 권한 관리 시스템

4. **성능 최적화**
   - PostgreSQL 쿼리 최적화
   - 캐싱 시스템 (Redis 연동)
   - 백그라운드 처리
   - 점진적 로딩

### 🌟 **장기 목표 (3-6개월)**
1. **AI 에이전트 확장**
   - 커스텀 역할 생성
   - 플러그인 시스템
   - 에이전트 마켓플레이스

2. **엔터프라이즈 기능**
   - 보안 강화 (인증/인가)
   - 감사 로그
   - 대용량 처리 지원

3. **클라우드 배포 및 스케일링**
   - Docker 컨테이너화
   - Kubernetes 오케스트레이션
   - 오토스케일링 구현
   - CDN 연동

---

## 🚀 **배포 및 운영 환경**

### 🐳 **컨테이너 배포**

#### **Docker 구성**
```dockerfile
# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

#### **Docker Compose 설정**
```yaml
version: '3.8'
services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:5000
    depends_on:
      - backend

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5000:5000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### ☁️ **클라우드 배포 옵션**

#### **1. Vercel + Supabase (권장)**
```yaml
# vercel.json
{
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build"
    },
    {
      "src": "backend/app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/app.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

#### **2. AWS 배포**
```yaml
# AWS ECS Task Definition
{
  "family": "ai-chat-interface",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "frontend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ai-chat-frontend:latest",
      "portMappings": [{"containerPort": 3000}],
      "memory": 512,
      "cpu": 256
    },
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ai-chat-backend:latest",
      "portMappings": [{"containerPort": 5000}],
      "memory": 1024,
      "cpu": 512,
      "environment": [
        {"name": "SUPABASE_URL", "value": "https://your-project.supabase.co"}
      ]
    }
  ]
}
```

#### **3. Google Cloud Run**
```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ai-chat-interface
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containers:
      - image: gcr.io/your-project/ai-chat-interface:latest
        ports:
        - containerPort: 8080
        env:
        - name: SUPABASE_URL
          value: "https://your-project.supabase.co"
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
```

### 🔧 **환경 변수 관리**

#### **환경별 설정**
```bash
# .env.development
REACT_APP_API_URL=http://localhost:5000
SUPABASE_URL=https://dev-project.supabase.co
SUPABASE_ANON_KEY=dev-anon-key
LOG_LEVEL=debug

# .env.staging
REACT_APP_API_URL=https://staging-api.yourdomain.com
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_ANON_KEY=staging-anon-key
LOG_LEVEL=info

# .env.production
REACT_APP_API_URL=https://api.yourdomain.com
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_ANON_KEY=prod-anon-key
LOG_LEVEL=error
```

### 📊 **모니터링 및 로깅**

#### **애플리케이션 모니터링**
```python
# monitoring.py
import logging
from prometheus_client import Counter, Histogram, start_http_server

# 메트릭 정의
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

#### **헬스 체크**
```python
@app.route('/health')
def health_check():
    """시스템 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        result = supabase.table('projects').select('count').execute()

        # Redis 연결 확인 (캐시 사용시)
        # redis_client.ping()

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "version": "1.0.0"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```

### 🔒 **보안 고려사항**

#### **프로덕션 보안 체크리스트**
- [ ] HTTPS 강제 적용
- [ ] CORS 정책 적절히 설정
- [ ] API Rate Limiting 구현
- [ ] SQL Injection 방지
- [ ] XSS 방지 (Content Security Policy)
- [ ] 환경 변수 암호화
- [ ] 정기적인 의존성 보안 업데이트
- [ ] 접근 로그 모니터링

---

## 🔍 참조 프레임워크

### 📚 **MetaGPT Framework**
- **Repository**: `D:\GenProjects\MetaGPT\`
- **핵심 철학**: `Code = SOP(Team)` - 표준 운영 절차를 LLM 팀에 적용
- **멀티 에이전트**: Product Manager, Architect, Engineer, QA Engineer 등
- **문서 참조**:
  - `README.md`: 전체 프레임워크 개요
  - `CLAUDE.md`: 개발 가이드라인 및 아키텍처

### 🤝 **CrewAI Framework**
- **Repository**: `D:\GenProjects\CrewAi\`
- **특징**: 협업 기반 AI 에이전트 시스템
- **역할 구성**: Researcher, Writer, Planner
- **플랫폼**: `crewai_platform/` 디렉토리 구조

---

## 💡 혁신 포인트

### 🎯 **차별화 요소**
1. **하이브리드 접근**: 클라우드 + 로컬 LLM 동시 지원
2. **역할별 최적화**: 각 역할에 특화된 LLM 모델 선택
3. **실무 중심**: 실제 소프트웨어 개발 프로세스 반영
4. **확장성**: 모듈형 구조로 새로운 AI 프레임워크 쉽게 추가

### 🛡️ **엔터프라이즈 대응**
- **오프라인 환경**: 인터넷 연결 없이도 작동
- **보안 준수**: 로컬 데이터 처리로 정보 유출 방지
- **비용 효율**: 적재적소 LLM 활용으로 비용 최적화

---

## ⚙️ 데이터베이스 연동 설정

### 🔧 **Supabase 환경 설정**

1. **환경 변수 설정** (`D:\GenProjects\CrewAi\.env`)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

2. **필수 Python 패키지**
```bash
pip install supabase-py flask flask-sockets gevent geventwebsocket python-dotenv
```

3. **데이터베이스 연결 테스트**
```python
from supabase import create_client
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(supabase_url, supabase_key)

# 연결 테스트
result = supabase.table('projects').select('*').execute()
print(f"연결 성공! 프로젝트 수: {len(result.data)}")
```

### 📡 **확장된 API 엔드포인트**

#### **프로젝트 관리 API**
```javascript
// 프로젝트 생성 (AI 선택 포함)
POST http://localhost:5000/api/projects
Content-Type: application/json
{
  "name": "E-commerce 웹사이트",
  "description": "온라인 쇼핑몰 개발",
  "selected_ai": "meta-gpt",
  "project_type": "web_app",
  "target_audience": "온라인 쇼핑 고객",
  "technical_requirements": {
    "frontend": "React.js",
    "backend": "Node.js",
    "database": "PostgreSQL"
  }
}

// 프로젝트별 역할-LLM 매핑 설정
POST http://localhost:5000/api/projects/{project_id}/role-llm-mapping
Content-Type: application/json
{
  "mappings": [
    {"role_name": "Product Manager", "llm_model": "gpt-4"},
    {"role_name": "Architect", "llm_model": "claude-3"},
    {"role_name": "Engineer", "llm_model": "deepseek-coder"},
    {"role_name": "QA Engineer", "llm_model": "llama-3"}
  ]
}

// 프로젝트 진행 상태 조회
GET http://localhost:5000/api/projects/{project_id}/status
```

#### **프로젝트 단계 관리 API**
```javascript
// 프로젝트 단계 목록 조회
GET http://localhost:5000/api/projects/{project_id}/stages

// 특정 단계 시작
PUT http://localhost:5000/api/projects/{project_id}/stages/{stage_id}/start
Content-Type: application/json
{
  "responsible_role": "Product Manager",
  "estimated_hours": 8
}

// 단계 완료 처리
PUT http://localhost:5000/api/projects/{project_id}/stages/{stage_id}/complete
Content-Type: application/json
{
  "actual_hours": 10,
  "notes": "요구사항 분석 완료. 총 15개 기능 식별."
}
```

#### **산출물 관리 API**
```javascript
// 산출물 생성
POST http://localhost:5000/api/projects/{project_id}/deliverables
Content-Type: application/json
{
  "stage_id": "uuid-stage-id",
  "deliverable_type": "requirement",
  "title": "E-commerce 요구사항 명세서",
  "content": "# 요구사항 명세서\n\n## 1. 기능 요구사항...",
  "created_by_role": "Product Manager",
  "tags": ["requirement", "specification", "functional"]
}

// 프로젝트별 모든 산출물 조회
GET http://localhost:5000/api/projects/{project_id}/deliverables

// 특정 단계의 산출물 조회
GET http://localhost:5000/api/projects/{project_id}/stages/{stage_id}/deliverables

// 산출물 내용 조회 (역할별 접근 로그 기록)
GET http://localhost:5000/api/deliverables/{deliverable_id}?accessed_by_role=Architect
```

#### **문서 공유 및 협업 API**
```javascript
// 역할이 접근 가능한 산출물 목록
GET http://localhost:5000/api/projects/{project_id}/accessible-deliverables?role=Engineer

// 산출물 검색
GET http://localhost:5000/api/projects/{project_id}/deliverables/search?q=요구사항&type=requirement

// 산출물 승인/반려
PUT http://localhost:5000/api/deliverables/{deliverable_id}/review
Content-Type: application/json
{
  "status": "approved",
  "reviewed_by_role": "Architect",
  "review_comments": "설계 요구사항이 명확하게 정의되었습니다."
}
```

#### **실시간 협업 WebSocket**
```javascript
// 프로젝트별 실시간 업데이트 구독
ws://localhost:5000/ws/projects/{project_id}/updates

// 메시지 예시:
{
  "type": "stage_started",
  "data": {
    "stage_name": "design",
    "responsible_role": "Architect",
    "started_at": "2025-01-15T10:30:00Z"
  }
}

{
  "type": "deliverable_created",
  "data": {
    "deliverable_type": "design_doc",
    "title": "시스템 아키텍처 설계서",
    "created_by_role": "Architect"
  }
}
```

---

## 🎯 **실제 활용 시나리오 예시**

### 📋 **시나리오 1: E-commerce 웹사이트 개발**

#### **1단계: 프로젝트 생성 및 설정**
```javascript
// 1. 프로젝트 생성
POST /api/projects
{
  "name": "Modern E-commerce Platform",
  "selected_ai": "meta-gpt",
  "project_type": "web_app"
}

// 2. 역할별 LLM 매핑 설정
POST /api/projects/{project_id}/role-llm-mapping
{
  "mappings": [
    {"role_name": "Product Manager", "llm_model": "gpt-4"},      // 기획 특화
    {"role_name": "Architect", "llm_model": "claude-3"},        // 설계 특화
    {"role_name": "Engineer", "llm_model": "deepseek-coder"},   // 코딩 특화
    {"role_name": "QA Engineer", "llm_model": "llama-3"}        // 테스트 특화
  ]
}
```

#### **2단계: 순차적 단계별 진행**
```javascript
// 1단계: 요구사항 정리 (Product Manager + GPT-4)
PUT /api/projects/{project_id}/stages/requirement/start
→ 산출물: "E-commerce 요구사항 명세서" (deliverable_type: 'requirement')

// 2단계: 시스템 설계 (Architect + Claude-3)
// - 이전 단계 산출물 자동 참조
GET /api/projects/{project_id}/deliverables?type=requirement
→ 산출물: "시스템 아키텍처 설계서" (deliverable_type: 'architecture')

// 3단계: 코드 개발 (Engineer + DeepSeek Coder)
// - 요구사항서 + 설계서 참조
→ 산출물: "프론트엔드/백엔드 코드" (deliverable_type: 'code')

// 4단계: 테스트 (QA Engineer + Llama-3)
// - 모든 이전 산출물 참조
→ 산출물: "테스트 계획서 및 결과" (deliverable_type: 'test_plan')
```

#### **3단계: 실시간 협업 및 문서 공유**
```javascript
// 실시간 진행 상황 모니터링
ws://localhost:5000/ws/projects/{project_id}/updates

// 역할 간 산출물 공유
- Product Manager가 요구사항서 작성
- Architect가 실시간으로 요구사항서 조회 및 설계 진행
- Engineer가 설계서 기반으로 코드 개발
- QA Engineer가 모든 문서 기반으로 테스트 설계

// 접근 이력 추적
deliverable_access_log 테이블에 모든 문서 접근 기록
```

### 🔄 **시나리오 2: 모바일 앱 개발 (CREW AI 활용)**

#### **프로젝트 설정**
```javascript
POST /api/projects
{
  "name": "Health Tracking Mobile App",
  "selected_ai": "crew-ai",
  "project_type": "mobile_app",
  "target_audience": "헬스케어 사용자"
}

// CREW AI 3역할 LLM 매핑
{
  "mappings": [
    {"role_name": "Researcher", "llm_model": "gemini-pro"},    // 리서치 특화
    {"role_name": "Writer", "llm_model": "gpt-4"},           // 문서 작성 특화
    {"role_name": "Planner", "llm_model": "claude-3"}       // 전략 수립 특화
  ]
}
```

#### **협업 워크플로우**
```javascript
// 동시 병렬 작업
- Researcher: 시장 조사 및 사용자 분석
- Writer: 기술 문서 및 사용자 가이드 작성
- Planner: 개발 일정 및 리소스 계획

// 산출물 상호 참조
- Writer가 Researcher의 조사 결과를 참조하여 문서 작성
- Planner가 모든 산출물을 종합하여 실행 계획 수립
```

### 📊 **시나리오 3: 대시보드를 통한 프로젝트 모니터링**

#### **관리자 뷰**
```javascript
// 전체 프로젝트 현황
GET /api/admin/dashboard
{
  "total_projects": 15,
  "active_projects": 8,
  "completed_projects": 7,
  "total_deliverables": 127,
  "projects_by_stage": {
    "requirement": 3,
    "design": 2,
    "development": 2,
    "testing": 1
  }
}

// 프로젝트별 상세 진행 현황
GET /api/projects/{project_id}/analytics
{
  "progress_percentage": 65,
  "stages_completed": 3,
  "total_stages": 5,
  "deliverables_created": 12,
  "average_stage_duration": "2.5 days",
  "role_activity": {
    "Product Manager": {"hours": 24, "deliverables": 4},
    "Architect": {"hours": 18, "deliverables": 3},
    "Engineer": {"hours": 32, "deliverables": 5}
  }
}
```

---

## 📞 개발팀 연락처

**프로젝트 위치**: `D:\GenProjects\ai-chat-interface\`
**AI 채팅 서버**: `http://localhost:3000`
**CrewAI 플랫폼**: `http://localhost:5000`
**데이터베이스**: Supabase (PostgreSQL)
**개발 환경**: React.js + Flask + Python + Supabase

---

*본 문서는 AI 프로그램 생성 채팅 인터페이스 프로젝트의 현재 상태를 정리한 것으로, CrewAI 데이터베이스 통합 계획을 포함하여 지속적으로 업데이트될 예정입니다.*