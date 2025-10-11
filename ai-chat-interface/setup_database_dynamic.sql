-- ========================================
-- DB 기반 동적 AI 프레임워크 관리 시스템
-- 데이터베이스 스키마
-- ========================================

-- ==================== 1. PROJECTS 테이블 수정 ====================

-- projects 테이블에 새 컬럼 추가
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS pre_analysis_history JSONB DEFAULT '[]',  -- 사전분석 대화 이력 (참고용)
ADD COLUMN IF NOT EXISTS final_requirement TEXT,                   -- 확정된 최종 요구사항
ADD COLUMN IF NOT EXISTS framework VARCHAR(20) DEFAULT 'crewai' CHECK (framework IN ('crewai', 'metagpt'));

-- ==================== 2. PROJECT_AGENTS 테이블 ====================

CREATE TABLE IF NOT EXISTS project_agents (
    -- 복합 PRIMARY KEY (직관적)
    project_id VARCHAR(13) NOT NULL,
    framework VARCHAR(20) NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
    agent_order INTEGER NOT NULL,

    -- Agent 기본 정보
    role VARCHAR(100) NOT NULL,
    goal TEXT NOT NULL,
    backstory TEXT NOT NULL,

    -- 실행 설정
    llm_model VARCHAR(50) NOT NULL,
    is_verbose BOOLEAN DEFAULT true,
    allow_delegation BOOLEAN DEFAULT false,

    -- 메타데이터
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 복합 PRIMARY KEY
    PRIMARY KEY (project_id, framework, agent_order),

    -- FOREIGN KEY
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_project_agents_lookup
    ON project_agents(project_id, framework, is_active);
CREATE INDEX IF NOT EXISTS idx_project_agents_framework
    ON project_agents(framework);

-- ==================== 3. PROJECT_TASKS 테이블 ====================

CREATE TABLE IF NOT EXISTS project_tasks (
    -- 복합 PRIMARY KEY (직관적)
    project_id VARCHAR(13) NOT NULL,
    framework VARCHAR(20) NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
    task_order INTEGER NOT NULL,

    -- Task 기본 정보
    task_type VARCHAR(50),  -- 'planning', 'research', 'implementation', 'review', 'revision'
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

    -- 메타데이터
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 복합 PRIMARY KEY
    PRIMARY KEY (project_id, framework, task_order),

    -- FOREIGN KEY (프로젝트)
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,

    -- FOREIGN KEY (Agent 연결)
    FOREIGN KEY (agent_project_id, agent_framework, agent_order)
        REFERENCES project_agents(project_id, framework, agent_order)
        ON DELETE CASCADE,

    -- FOREIGN KEY (Task 의존성)
    FOREIGN KEY (depends_on_project_id, depends_on_framework, depends_on_task_order)
        REFERENCES project_tasks(project_id, framework, task_order)
        ON DELETE SET NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_project_tasks_lookup
    ON project_tasks(project_id, framework, is_active);
CREATE INDEX IF NOT EXISTS idx_project_tasks_agent
    ON project_tasks(agent_project_id, agent_framework, agent_order);
CREATE INDEX IF NOT EXISTS idx_project_tasks_depends
    ON project_tasks(depends_on_project_id, depends_on_framework, depends_on_task_order);

-- ==================== 4. AGENT_TEMPLATES 테이블 ====================

CREATE TABLE IF NOT EXISTS agent_templates (
    -- 복합 PRIMARY KEY (직관적)
    framework VARCHAR(20) NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
    template_name VARCHAR(100) NOT NULL,

    -- Template 내용
    role VARCHAR(100) NOT NULL,
    goal_template TEXT NOT NULL,          -- {requirement} 플레이스홀더 포함
    backstory_template TEXT NOT NULL,     -- {requirement} 플레이스홀더 포함

    -- 기본값
    default_llm_model VARCHAR(50),
    is_verbose BOOLEAN DEFAULT true,
    allow_delegation BOOLEAN DEFAULT false,

    -- 메타데이터
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 복합 PRIMARY KEY
    PRIMARY KEY (framework, template_name)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_agent_templates_framework
    ON agent_templates(framework);

-- ==================== 5. TASK_TEMPLATES 테이블 ====================

CREATE TABLE IF NOT EXISTS task_templates (
    -- 복합 PRIMARY KEY (직관적)
    framework VARCHAR(20) NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
    task_type VARCHAR(50) NOT NULL,

    -- Template 내용
    description_template TEXT NOT NULL,
    expected_output_template TEXT NOT NULL,

    -- Agent 연결 (템플릿 이름)
    agent_template_name VARCHAR(100),

    -- 메타데이터
    description TEXT,
    display_order INTEGER DEFAULT 0,  -- 표시 순서
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 복합 PRIMARY KEY
    PRIMARY KEY (framework, task_type),

    -- FOREIGN KEY (Agent Template 연결)
    FOREIGN KEY (framework, agent_template_name)
        REFERENCES agent_templates(framework, template_name)
        ON DELETE SET NULL
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_task_templates_framework
    ON task_templates(framework);
CREATE INDEX IF NOT EXISTS idx_task_templates_agent
    ON task_templates(framework, agent_template_name);

-- ==================== 6. 기본 템플릿 데이터 삽입 ====================

-- CrewAI Agent 템플릿 (3개 - 사전분석 제외)
INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('crewai', 'planner', 'Planner',
 '다음 프로젝트의 체계적인 개발 계획을 수립하고 품질을 검토합니다: {requirement}',
 '당신은 프로젝트 관리 및 품질 보증 전문가입니다. {requirement} 같은 프로젝트의 성공적인 실행 계획 수립과 지속적인 품질 개선에 전문성을 가지고 있습니다.',
 'gemini-2.5-flash',
 'CrewAI Planner & Quality Reviewer 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('crewai', 'researcher', 'Researcher',
 '다음 프로젝트 구현에 필요한 최적의 기술 스택, 도구, 방법론을 조사하고 제안합니다: {requirement}',
 '당신은 기술 리서치 전문가입니다. {requirement}와 같은 프로젝트에 최적화된 기술 솔루션을 찾아내고 검증하는 전문성을 가지고 있습니다.',
 'gemini-2.5-flash',
 'CrewAI Researcher 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('crewai', 'writer', 'Writer',
 '연구 결과를 바탕으로 다음 프로젝트를 완전히 구현하고 피드백을 반영하여 개선합니다: {requirement}',
 '당신은 기술 구현 및 문서화 전문가입니다. {requirement} 프로젝트를 실제 동작하는 고품질 코드로 구현하고 피드백을 통해 지속적으로 개선하는 전문성을 가지고 있습니다.',
 'gemini-2.5-flash',
 'CrewAI Writer & Implementer 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

-- MetaGPT Agent 템플릿 (5개)
INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('metagpt', 'product_manager', 'Product Manager',
 '제품 요구사항을 분석하고 상세한 PRD(Product Requirements Document)를 작성합니다: {requirement}',
 '당신은 제품 관리 전문가입니다. {requirement} 같은 요구사항을 명확한 제품 명세로 전환하고 성공적인 제품 출시를 위한 전략을 수립하는 능력을 가지고 있습니다.',
 'gpt-4o',
 'MetaGPT Product Manager 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('metagpt', 'architect', 'Architect',
 'PRD를 바탕으로 시스템 아키텍처를 설계하고 기술 스택을 선정합니다: {requirement}',
 '당신은 소프트웨어 아키텍트입니다. {requirement}를 위한 확장 가능하고 유지보수 가능한 아키텍처를 설계하며, 최적의 기술적 의사결정을 내리는 전문성을 가지고 있습니다.',
 'claude-3-sonnet',
 'MetaGPT Architect 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('metagpt', 'project_manager', 'Project Manager',
 '프로젝트 일정을 계획하고 개발 프로세스를 관리합니다: {requirement}',
 '당신은 프로젝트 매니저입니다. {requirement} 프로젝트의 성공적인 완수를 위해 리소스를 관리하고 일정을 조율하는 전문성을 가지고 있습니다.',
 'gemini-2.5-pro',
 'MetaGPT Project Manager 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('metagpt', 'engineer', 'Engineer',
 '설계를 바탕으로 실제 코드를 작성하고 구현합니다: {requirement}',
 '당신은 소프트웨어 엔지니어입니다. {requirement}를 고품질의 실행 가능한 코드로 구현하며, 모범 사례와 코딩 표준을 준수하는 전문성을 가지고 있습니다.',
 'deepseek-coder',
 'MetaGPT Engineer 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

INSERT INTO agent_templates (framework, template_name, role, goal_template, backstory_template, default_llm_model, description) VALUES
('metagpt', 'qa_engineer', 'QA Engineer',
 '구현된 코드를 테스트하고 품질을 보증합니다: {requirement}',
 '당신은 QA 엔지니어입니다. {requirement} 프로젝트의 품질을 보증하기 위해 체계적인 테스트를 수행하고 버그를 발견하는 전문성을 가지고 있습니다.',
 'gemini-2.5-flash',
 'MetaGPT QA Engineer 기본 템플릿')
ON CONFLICT (framework, template_name) DO NOTHING;

-- CrewAI Task 템플릿 (5개 - 사전분석 제외)
INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('crewai', 'planning',
 '다음 프로젝트의 체계적인 개발 계획을 수립하세요:

**요구사항**: {requirement}

**계획 수립 내용**:
1. 개발 단계별 로드맵
2. 기능별 우선순위 매트릭스
3. 기술 스택 선정 가이드라인
4. 개발 일정 및 마일스톤
5. 품질 보증 체크포인트

실무진이 바로 실행할 수 있는 상세한 계획을 작성하세요.',
 '프로젝트 개발 계획서 (마크다운 형식, 실행 가능한 단계별 가이드)',
 'planner',
 'CrewAI Planning Task 템플릿',
 1)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('crewai', 'research',
 'Planner의 계획을 바탕으로 기술적 조사를 수행하세요:

**요구사항**: {requirement}

**조사 항목**:
1. 권장 기술 스택 및 라이브러리
2. 아키텍처 패턴 및 설계 원칙
3. 개발 도구 및 환경 설정
4. 보안 고려사항 및 베스트 프랙티스
5. 성능 최적화 방안
6. 테스트 및 배포 전략

각 기술 선택의 근거와 대안을 명시하세요.',
 '기술 조사 보고서 (마크다운 형식, 기술 선택 근거 포함)',
 'researcher',
 'CrewAI Research Task 템플릿',
 2)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('crewai', 'implementation',
 '계획과 조사 결과를 바탕으로 프로젝트를 구현하세요:

**요구사항**: {requirement}

**구현 내용**:
1. 완전한 프로젝트 디렉토리 구조
2. 핵심 기능별 소스 코드 (실제 동작)
3. 설정 파일 및 의존성 관리
4. 상세한 README.md 및 사용법
5. 기본 테스트 코드
6. 실행 및 배포 가이드

모든 코드는 실제로 동작해야 하며 충분한 주석을 포함하세요.',
 '완전한 프로젝트 구현체 (실행 가능한 코드, 문서, 설정 파일 포함)',
 'writer',
 'CrewAI Implementation Task 템플릿',
 3)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('crewai', 'review',
 'Writer가 작성한 구현체를 검토하고 개선사항을 도출하세요:

**검토 항목**:
1. 요구사항 충족도 평가
2. 코드 품질 및 구조 분석
3. 기능 완성도 점검
4. 문서화 수준 평가
5. 테스트 커버리지 검토
6. 사용성 및 접근성 평가

구체적인 개선 방향과 우선순위를 제시하세요.',
 '검토 보고서 및 개선 지시사항 (구체적 수정 항목 포함)',
 'planner',
 'CrewAI Review Task 템플릿',
 4)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('crewai', 'revision',
 'Planner의 검토 피드백을 바탕으로 프로젝트를 개선하세요:

**개선 작업**:
1. 지적된 문제점 수정
2. 제안된 기능 추가
3. 코드 품질 개선
4. 문서 보완
5. 테스트 추가

모든 피드백을 반영하여 프로덕션 레벨의 품질을 달성하세요.',
 '개선된 프로젝트 구현체 (피드백 반영 완료)',
 'writer',
 'CrewAI Revision Task 템플릿',
 5)
ON CONFLICT (framework, task_type) DO NOTHING;

-- MetaGPT Task 템플릿 (5개)
INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('metagpt', 'prd_writing',
 '제품 요구사항 문서(PRD)를 작성하세요:

**요구사항**: {requirement}

**PRD 포함 내용**:
1. 제품 개요 및 목표
2. 사용자 스토리 및 시나리오
3. 기능 요구사항 (상세)
4. 비기능 요구사항
5. 제약사항 및 가정
6. 성공 지표',
 'PRD (Product Requirements Document, 마크다운 형식)',
 'product_manager',
 'MetaGPT PRD Writing Task 템플릿',
 1)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('metagpt', 'system_design',
 'PRD를 바탕으로 시스템 아키텍처를 설계하세요:

**설계 내용**:
1. 시스템 아키텍처 다이어그램
2. 데이터 모델 및 스키마
3. API 설계
4. 기술 스택 선정
5. 보안 및 성능 고려사항',
 '시스템 설계 문서 (다이어그램 및 상세 명세)',
 'architect',
 'MetaGPT System Design Task 템플릿',
 2)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('metagpt', 'project_planning',
 '프로젝트 실행 계획을 수립하세요:

**계획 내용**:
1. 개발 일정 (Gantt Chart)
2. 리소스 할당
3. 마일스톤 정의
4. 리스크 관리 계획',
 '프로젝트 관리 계획서 (일정 및 리소스 계획)',
 'project_manager',
 'MetaGPT Project Planning Task 템플릿',
 3)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('metagpt', 'coding',
 '설계를 바탕으로 코드를 작성하세요:

**구현 내용**:
1. 프로젝트 구조 생성
2. 모든 모듈 및 클래스 구현
3. API 엔드포인트 구현
4. 데이터베이스 연동
5. 에러 처리 및 로깅',
 '완전한 소스 코드 (실행 가능)',
 'engineer',
 'MetaGPT Coding Task 템플릿',
 4)
ON CONFLICT (framework, task_type) DO NOTHING;

INSERT INTO task_templates (framework, task_type, description_template, expected_output_template, agent_template_name, description, display_order) VALUES
('metagpt', 'qa_testing',
 '구현된 코드를 테스트하세요:

**테스트 내용**:
1. 단위 테스트 작성 및 실행
2. 통합 테스트 수행
3. 버그 리포트 작성
4. 품질 메트릭 측정
5. 개선 제안',
 'QA 보고서 (테스트 결과, 버그 리스트, 품질 메트릭)',
 'qa_engineer',
 'MetaGPT QA Testing Task 템플릿',
 5)
ON CONFLICT (framework, task_type) DO NOTHING;

-- ==================== 7. 업데이트 트리거 ====================

-- projects 테이블 updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_projects_updated_at ON projects;
CREATE TRIGGER trigger_update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_projects_updated_at();

-- project_agents 테이블 updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_project_agents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_project_agents_updated_at ON project_agents;
CREATE TRIGGER trigger_update_project_agents_updated_at
    BEFORE UPDATE ON project_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_project_agents_updated_at();

-- project_tasks 테이블 updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_project_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_project_tasks_updated_at ON project_tasks;
CREATE TRIGGER trigger_update_project_tasks_updated_at
    BEFORE UPDATE ON project_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_project_tasks_updated_at();

-- ==================== 완료 ====================

COMMENT ON TABLE project_agents IS 'DB 기반 동적 Agent 관리 테이블 (복합 PK: project_id, framework, agent_order)';
COMMENT ON TABLE project_tasks IS 'DB 기반 동적 Task 관리 테이블 (복합 PK: project_id, framework, task_order)';
COMMENT ON TABLE agent_templates IS 'Agent 재사용 템플릿 (복합 PK: framework, template_name)';
COMMENT ON TABLE task_templates IS 'Task 재사용 템플릿 (복합 PK: framework, task_type)';
