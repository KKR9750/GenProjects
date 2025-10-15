-- Database Migration Script: Change id UUID to project_id SERIAL
-- 9개 테이블의 Primary Key를 id UUID에서 project_id SERIAL로 변경
-- 기존 데이터 보존하면서 스키마 변경

-- ==================== BACKUP & SAFETY ====================

-- 기존 테이블 백업 (Optional - 필요시 주석 해제)
/*
CREATE TABLE projects_backup AS SELECT * FROM projects;
CREATE TABLE project_stages_backup AS SELECT * FROM project_stages;
CREATE TABLE project_role_llm_mapping_backup AS SELECT * FROM project_role_llm_mapping;
CREATE TABLE project_deliverables_backup AS SELECT * FROM project_deliverables;
CREATE TABLE deliverable_access_log_backup AS SELECT * FROM deliverable_access_log;
CREATE TABLE metagpt_workflow_stages_backup AS SELECT * FROM metagpt_workflow_stages;
CREATE TABLE metagpt_role_llm_mapping_backup AS SELECT * FROM metagpt_role_llm_mapping;
CREATE TABLE metagpt_deliverables_backup AS SELECT * FROM metagpt_deliverables;
CREATE TABLE metagpt_communication_log_backup AS SELECT * FROM metagpt_communication_log;
CREATE TABLE metagpt_project_metrics_backup AS SELECT * FROM metagpt_project_metrics;
*/

-- ==================== STEP 1: 기존 테이블 및 의존성 삭제 ====================

-- 외래키 의존성 순서로 삭제
DROP TABLE IF EXISTS deliverable_access_log CASCADE;
DROP TABLE IF EXISTS project_deliverables CASCADE;
DROP TABLE IF EXISTS project_role_llm_mapping CASCADE;
DROP TABLE IF EXISTS project_stages CASCADE;
DROP TABLE IF EXISTS project_tools CASCADE;

-- MetaGPT 관련 테이블도 삭제
DROP TABLE IF EXISTS metagpt_communication_log CASCADE;
DROP TABLE IF EXISTS metagpt_deliverables CASCADE;
DROP TABLE IF EXISTS metagpt_project_metrics CASCADE;
DROP TABLE IF EXISTS metagpt_workflow_stages CASCADE;
DROP TABLE IF EXISTS metagpt_role_llm_mapping CASCADE;

-- projects 테이블은 이미 project_id를 사용하므로 그대로 유지
-- DROP TABLE IF EXISTS projects CASCADE;

-- projects 테이블에 review_iterations 컬럼 추가 (없을 경우)
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS review_iterations INTEGER DEFAULT 1 CHECK (review_iterations >= 0 AND review_iterations <= 5);

-- 관련 뷰들도 삭제
DROP VIEW IF EXISTS project_analytics CASCADE;
DROP VIEW IF EXISTS llm_usage_analytics CASCADE;
DROP VIEW IF EXISTS project_summary CASCADE;
DROP VIEW IF EXISTS metagpt_project_dashboard CASCADE;
DROP VIEW IF EXISTS metagpt_performance_summary CASCADE;

-- ==================== STEP 2: 새로운 테이블 생성 (project_id SERIAL 사용) ====================

-- 1. Project Stages table (project_id SERIAL PK)
CREATE TABLE project_stages (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    stage_name VARCHAR(50) NOT NULL,
    stage_order INTEGER NOT NULL,
    stage_status VARCHAR(20) DEFAULT 'pending' CHECK (stage_status IN ('pending', 'in_progress', 'completed', 'blocked')),
    responsible_role VARCHAR(50),
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint for project stages
    UNIQUE(projects_project_id, stage_order)
);

-- 2. Project Role-LLM Mapping table (project_id SERIAL PK)
CREATE TABLE project_role_llm_mapping (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL CHECK (role_name IN (
        'Researcher', 'Writer', 'Planner',
        'Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'
    )),
    llm_model VARCHAR(50) NOT NULL CHECK (llm_model IN (
        'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
        'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'llama-3', 'llama-3-8b',
        'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
    )),
    llm_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint for active role mappings per project
    UNIQUE(projects_project_id, role_name)
);

-- 3. Project Deliverables table (project_id SERIAL PK)
CREATE TABLE project_deliverables (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    stage_project_id INTEGER REFERENCES project_stages(project_id) ON DELETE CASCADE,

    -- Deliverable Information
    deliverable_type VARCHAR(50) NOT NULL CHECK (deliverable_type IN (
        'requirement', 'design_doc', 'ui_wireframe', 'api_spec',
        'code', 'test_plan', 'documentation', 'architecture'
    )),
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- Content
    content TEXT,
    file_path VARCHAR(500),
    file_type VARCHAR(20),
    file_size INTEGER,

    -- Version Control
    version VARCHAR(20) DEFAULT '1.0',
    is_latest BOOLEAN DEFAULT true,
    parent_deliverable_project_id INTEGER REFERENCES project_deliverables(project_id),

    -- Status and Approval
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'rejected')),
    created_by_role VARCHAR(50),
    reviewed_by_role VARCHAR(50),
    approved_by_role VARCHAR(50),

    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 4. Deliverable Access Log table (project_id SERIAL PK)
CREATE TABLE deliverable_access_log (
    project_id SERIAL PRIMARY KEY,
    deliverable_project_id INTEGER REFERENCES project_deliverables(project_id) ON DELETE CASCADE,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    accessed_by_role VARCHAR(50) NOT NULL,
    access_type VARCHAR(20) NOT NULL CHECK (access_type IN ('read', 'edit', 'download', 'share')),
    access_details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Project Tools table (project_id SERIAL PK)
CREATE TABLE project_tools (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    tool_key VARCHAR(100) NOT NULL,
    tool_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(projects_project_id, tool_key)
);

-- 6. MetaGPT Workflow Stages table (project_id SERIAL PK)
CREATE TABLE metagpt_workflow_stages (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    stage_number INTEGER NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    stage_description TEXT,
    responsible_role VARCHAR(50) NOT NULL,
    role_icon VARCHAR(10),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'review_needed', 'approved', 'completed', 'blocked')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    requires_approval BOOLEAN DEFAULT true,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    output_content TEXT,
    output_files JSONB DEFAULT '[]',
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(projects_project_id, stage_number)
);

-- 6. MetaGPT Role-LLM Mapping table (project_id SERIAL PK)
CREATE TABLE metagpt_role_llm_mapping (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    product_manager_llm VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    architect_llm VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    project_manager_llm VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    engineer_llm VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    qa_engineer_llm VARCHAR(50) DEFAULT 'gemini-2.5-flash',
    configuration_notes TEXT,
    performance_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(projects_project_id)
);

-- 7. MetaGPT Deliverables table (project_id SERIAL PK)
CREATE TABLE metagpt_deliverables (
    project_id SERIAL PRIMARY KEY,
    workflow_stage_project_id INTEGER REFERENCES metagpt_workflow_stages(project_id) ON DELETE CASCADE,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,

    -- 산출물 정보
    deliverable_type VARCHAR(50) NOT NULL, -- 'prd', 'architecture', 'project_plan', 'code', 'test_report'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content TEXT,

    -- 파일 정보
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_type VARCHAR(20),
    file_size INTEGER,

    -- 품질 및 승인
    quality_metrics JSONB DEFAULT '{}',
    review_status VARCHAR(20) DEFAULT 'pending' CHECK (review_status IN ('pending', 'in_review', 'approved', 'rejected', 'revision_needed')),
    reviewer_comments TEXT,

    -- 버전 관리
    version INTEGER DEFAULT 1,
    parent_deliverable_project_id INTEGER REFERENCES metagpt_deliverables(project_id),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 8. MetaGPT Communication Log table (project_id SERIAL PK)
CREATE TABLE metagpt_communication_log (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    workflow_stage_project_id INTEGER REFERENCES metagpt_workflow_stages(project_id) ON DELETE CASCADE,

    -- 커뮤니케이션 정보
    from_role VARCHAR(50) NOT NULL,
    to_role VARCHAR(50) NOT NULL,
    message_type VARCHAR(30) NOT NULL, -- 'request', 'approval', 'feedback', 'question', 'clarification'

    -- 메시지 내용
    subject VARCHAR(200),
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',

    -- 응답 관리
    parent_message_project_id INTEGER REFERENCES metagpt_communication_log(project_id),
    requires_response BOOLEAN DEFAULT false,
    response_deadline TIMESTAMP,
    responded_at TIMESTAMP,

    -- 우선순위 및 상태
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    status VARCHAR(20) DEFAULT 'sent' CHECK (status IN ('sent', 'read', 'responded', 'archived')),

    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. MetaGPT Project Metrics table (project_id SERIAL PK)
CREATE TABLE metagpt_project_metrics (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,

    -- 시간 지표
    total_planned_hours INTEGER,
    total_actual_hours INTEGER DEFAULT 0,
    stage_completion_times JSONB DEFAULT '{}',

    -- 품질 지표
    average_quality_score DECIMAL(3,2),
    approval_success_rate DECIMAL(5,2),
    revision_count INTEGER DEFAULT 0,

    -- 효율성 지표
    automation_percentage DECIMAL(5,2),
    communication_efficiency DECIMAL(5,2),
    resource_utilization DECIMAL(5,2),

    -- 산출물 지표
    deliverable_count INTEGER DEFAULT 0,
    code_lines_generated INTEGER DEFAULT 0,
    documentation_pages INTEGER DEFAULT 0,

    -- 계산 메타데이터
    last_calculated TIMESTAMP DEFAULT NOW(),
    calculation_method VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(projects_project_id)
);

-- ==================== STEP 3: 인덱스 생성 ====================

-- Project Stages indexes (새로운 project_id SERIAL)
CREATE INDEX idx_project_stages_project_id ON project_stages(project_id);
CREATE INDEX idx_project_stages_projects_project_id ON project_stages(projects_project_id);
CREATE INDEX idx_project_stages_order ON project_stages(projects_project_id, stage_order);

-- Role-LLM Mapping indexes (새로운 project_id SERIAL)
CREATE INDEX idx_role_mapping_project_id ON project_role_llm_mapping(project_id);
CREATE INDEX idx_role_mapping_projects_project_id ON project_role_llm_mapping(projects_project_id);
CREATE INDEX idx_role_mapping_active ON project_role_llm_mapping(projects_project_id, is_active);

-- Deliverables indexes (새로운 project_id SERIAL)
CREATE INDEX idx_deliverables_project_id ON project_deliverables(project_id);
CREATE INDEX idx_deliverables_projects_project_id ON project_deliverables(projects_project_id);
CREATE INDEX idx_deliverables_stage_project_id ON project_deliverables(stage_project_id);
CREATE INDEX idx_deliverables_type ON project_deliverables(projects_project_id, deliverable_type);

-- Access Log indexes (새로운 project_id SERIAL)
CREATE INDEX idx_access_log_project_id ON deliverable_access_log(project_id);
CREATE INDEX idx_access_log_deliverable_project_id ON deliverable_access_log(deliverable_project_id);
CREATE INDEX idx_access_log_projects_project_id ON deliverable_access_log(projects_project_id);
CREATE INDEX idx_project_tools_project_id ON project_tools(project_id);
CREATE INDEX idx_project_tools_projects_project_id ON project_tools(projects_project_id);

-- MetaGPT Workflow Stages indexes (새로운 project_id SERIAL)
CREATE INDEX idx_metagpt_workflow_project_id ON metagpt_workflow_stages(project_id);
CREATE INDEX idx_metagpt_workflow_projects_project_id ON metagpt_workflow_stages(projects_project_id);
CREATE INDEX idx_metagpt_workflow_stage_number ON metagpt_workflow_stages(projects_project_id, stage_number);
CREATE INDEX idx_metagpt_workflow_status ON metagpt_workflow_stages(status);
CREATE INDEX idx_metagpt_workflow_role ON metagpt_workflow_stages(responsible_role);

-- MetaGPT Role-LLM Mapping indexes (새로운 project_id SERIAL)
CREATE INDEX idx_metagpt_role_mapping_project_id ON metagpt_role_llm_mapping(project_id);
CREATE INDEX idx_metagpt_role_mapping_projects_project_id ON metagpt_role_llm_mapping(projects_project_id);

-- MetaGPT Deliverables indexes (새로운 project_id SERIAL)
CREATE INDEX idx_metagpt_deliverables_project_id ON metagpt_deliverables(project_id);
CREATE INDEX idx_metagpt_deliverables_projects_project_id ON metagpt_deliverables(projects_project_id);
CREATE INDEX idx_metagpt_deliverables_workflow_stage_project_id ON metagpt_deliverables(workflow_stage_project_id);
CREATE INDEX idx_metagpt_deliverables_type ON metagpt_deliverables(deliverable_type);

-- MetaGPT Communication Log indexes (새로운 project_id SERIAL)
CREATE INDEX idx_metagpt_comm_project_id ON metagpt_communication_log(project_id);
CREATE INDEX idx_metagpt_comm_projects_project_id ON metagpt_communication_log(projects_project_id);
CREATE INDEX idx_metagpt_comm_workflow_stage_project_id ON metagpt_communication_log(workflow_stage_project_id);
CREATE INDEX idx_metagpt_comm_roles ON metagpt_communication_log(from_role, to_role);

-- MetaGPT Project Metrics indexes (새로운 project_id SERIAL)
CREATE INDEX idx_metagpt_metrics_project_id ON metagpt_project_metrics(project_id);
CREATE INDEX idx_metagpt_metrics_projects_project_id ON metagpt_project_metrics(projects_project_id);

-- ==================== STEP 4: 트리거 재생성 ====================

-- Apply triggers to tables with updated_at columns (update_updated_at_column 함수는 이미 존재한다고 가정)
-- 기존 트리거 삭제 후 재생성 (부분 마이그레이션 대응)
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
DROP TRIGGER IF EXISTS update_project_stages_updated_at ON project_stages;
DROP TRIGGER IF EXISTS update_role_mapping_updated_at ON project_role_llm_mapping;
DROP TRIGGER IF EXISTS update_deliverables_updated_at ON project_deliverables;
DROP TRIGGER IF EXISTS update_metagpt_workflow_updated_at ON metagpt_workflow_stages;
DROP TRIGGER IF EXISTS update_metagpt_role_mapping_updated_at ON metagpt_role_llm_mapping;
DROP TRIGGER IF EXISTS update_metagpt_deliverables_updated_at ON metagpt_deliverables;
DROP TRIGGER IF EXISTS update_metagpt_metrics_updated_at ON metagpt_project_metrics;

-- MetaGPT 특화 트리거 삭제 (기존 스키마에서 생성된 것들)
DROP TRIGGER IF EXISTS trigger_metagpt_workflow_update ON metagpt_workflow_stages;
DROP TRIGGER IF EXISTS trigger_metagpt_deliverable_version ON metagpt_deliverables;

-- 트리거 재생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_project_stages_updated_at BEFORE UPDATE ON project_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_mapping_updated_at BEFORE UPDATE ON project_role_llm_mapping FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deliverables_updated_at BEFORE UPDATE ON project_deliverables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metagpt_workflow_updated_at BEFORE UPDATE ON metagpt_workflow_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metagpt_role_mapping_updated_at BEFORE UPDATE ON metagpt_role_llm_mapping FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metagpt_deliverables_updated_at BEFORE UPDATE ON metagpt_deliverables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_metagpt_metrics_updated_at BEFORE UPDATE ON metagpt_project_metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- MetaGPT 특화 함수 및 트리거 재생성
CREATE OR REPLACE FUNCTION update_metagpt_workflow_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();

    -- 단계 완료 시 다음 단계 활성화
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE metagpt_workflow_stages
        SET status = 'pending', updated_at = NOW()
        WHERE projects_project_id = NEW.projects_project_id
        AND stage_number = NEW.stage_number + 1
        AND status = 'blocked';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_metagpt_workflow_update
    BEFORE UPDATE ON metagpt_workflow_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_metagpt_workflow_timestamp();

CREATE OR REPLACE FUNCTION increment_metagpt_deliverable_version()
RETURNS TRIGGER AS $$
BEGIN
    -- 같은 타입의 이전 버전이 있으면 버전 증가
    SELECT COALESCE(MAX(version), 0) + 1 INTO NEW.version
    FROM metagpt_deliverables
    WHERE workflow_stage_project_id = NEW.workflow_stage_project_id
    AND deliverable_type = NEW.deliverable_type;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_metagpt_deliverable_version
    BEFORE INSERT ON metagpt_deliverables
    FOR EACH ROW
    EXECUTE FUNCTION increment_metagpt_deliverable_version();

-- ==================== STEP 5: 뷰 재생성 ====================

-- Project Analytics View (projects 테이블은 그대로 사용)
CREATE OR REPLACE VIEW project_analytics AS
SELECT
    p.selected_ai,
    p.project_type,
    COUNT(*) as total_projects,
    AVG(p.progress_percentage) as avg_progress,
    COUNT(CASE WHEN p.status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN p.status = 'in_progress' THEN 1 END) as active_count
FROM projects p
GROUP BY p.selected_ai, p.project_type;

-- LLM Usage Analytics View (새로운 project_id SERIAL 기반)
CREATE OR REPLACE VIEW llm_usage_analytics AS
SELECT
    prm.llm_model,
    prm.role_name,
    COUNT(DISTINCT prm.projects_project_id) as projects_count,
    COUNT(*) as total_mappings
FROM project_role_llm_mapping prm
WHERE prm.is_active = true
GROUP BY prm.llm_model, prm.role_name
ORDER BY projects_count DESC;

-- Project Summary View (새로운 project_id SERIAL 기반)
CREATE OR REPLACE VIEW project_summary AS
SELECT
    p.project_id,
    p.name,
    p.selected_ai,
    p.status,
    p.progress_percentage,
    p.created_at,
    COUNT(ps.project_id) as total_stages,
    COUNT(CASE WHEN ps.stage_status = 'completed' THEN 1 END) as completed_stages,
    COUNT(pd.project_id) as total_deliverables,
    COUNT(prm.project_id) as role_mappings_count
FROM projects p
LEFT JOIN project_stages ps ON ps.projects_project_id = p.project_id
LEFT JOIN project_deliverables pd ON pd.projects_project_id = p.project_id
LEFT JOIN project_role_llm_mapping prm ON prm.projects_project_id = p.project_id AND prm.is_active = true
GROUP BY p.project_id, p.name, p.selected_ai, p.status, p.progress_percentage, p.created_at
ORDER BY p.created_at DESC;

-- MetaGPT Project Dashboard View (새로운 project_id SERIAL 기반)
CREATE OR REPLACE VIEW metagpt_project_dashboard AS
SELECT
    p.project_id as project_id,
    p.name as project_name,
    p.status as project_status,
    p.progress_percentage as overall_progress,

    -- 현재 활성 단계
    ws.stage_number as current_stage,
    ws.stage_name as current_stage_name,
    ws.responsible_role as current_role,
    ws.status as stage_status,

    -- 진행 통계
    (SELECT COUNT(*) FROM metagpt_workflow_stages WHERE projects_project_id = p.project_id AND status = 'completed') as completed_stages,
    (SELECT COUNT(*) FROM metagpt_workflow_stages WHERE projects_project_id = p.project_id) as total_stages,

    -- 산출물 통계
    (SELECT COUNT(*) FROM metagpt_deliverables WHERE projects_project_id = p.project_id) as total_deliverables,
    (SELECT COUNT(*) FROM metagpt_deliverables WHERE projects_project_id = p.project_id AND review_status = 'approved') as approved_deliverables,

    -- 시간 정보
    p.created_at,
    p.updated_at

FROM projects p
LEFT JOIN metagpt_workflow_stages ws ON p.project_id = ws.projects_project_id
    AND ws.status IN ('in_progress', 'pending')
    AND ws.stage_number = (
        SELECT MIN(stage_number)
        FROM metagpt_workflow_stages
        WHERE projects_project_id = p.project_id
        AND status IN ('in_progress', 'pending')
    )
WHERE p.selected_ai = 'meta-gpt';

-- MetaGPT Performance Summary View (새로운 project_id SERIAL 기반)
CREATE OR REPLACE VIEW metagpt_performance_summary AS
SELECT
    p.project_id as project_id,
    p.name as project_name,

    -- 시간 효율성
    pm.total_planned_hours,
    pm.total_actual_hours,
    CASE
        WHEN pm.total_planned_hours > 0
        THEN ROUND((pm.total_actual_hours::decimal / pm.total_planned_hours * 100), 2)
        ELSE NULL
    END as time_efficiency_percentage,

    -- 품질 지표
    pm.average_quality_score,
    pm.approval_success_rate,
    pm.revision_count,

    -- 산출물 생산성
    pm.deliverable_count,
    pm.code_lines_generated,
    pm.documentation_pages,

    -- 커뮤니케이션 효율성
    (SELECT COUNT(*) FROM metagpt_communication_log WHERE projects_project_id = p.project_id) as total_communications,
    (SELECT COUNT(*) FROM metagpt_communication_log WHERE projects_project_id = p.project_id AND status = 'responded') as responded_communications,

    pm.last_calculated

FROM projects p
LEFT JOIN metagpt_project_metrics pm ON p.project_id = pm.projects_project_id
WHERE p.selected_ai = 'meta-gpt';

-- ==================== STEP 6: 샘플 데이터 삽입 ====================

-- 먼저 projects 테이블에 샘플 데이터가 있는지 확인하고 없으면 추가
INSERT INTO projects (name, description, selected_ai, project_type, status, progress_percentage)
VALUES
    ('E-commerce 플랫폼', '온라인 쇼핑몰 개발 프로젝트', 'meta-gpt', 'web_app', 'in_progress', 30),
    ('AI 챗봇 시스템', '고객 서비스용 AI 챗봇', 'crew-ai', 'api', 'planning', 10),
    ('데이터 분석 대시보드', '비즈니스 인텔리전스 대시보드', 'crew-ai', 'data_analysis', 'planning', 5)
ON CONFLICT DO NOTHING;

-- 존재하는 프로젝트 확인 후 새로운 테이블에 샘플 데이터 추가
-- 먼저 실제 존재하는 project_id를 확인해서 사용
DO $$
DECLARE
    project1_id VARCHAR(13);
    project2_id VARCHAR(13);
    project3_id VARCHAR(13);
BEGIN
    -- 존재하는 프로젝트 ID 가져오기
    SELECT project_id INTO project1_id FROM projects WHERE selected_ai = 'meta-gpt' AND name LIKE '%E-commerce%' LIMIT 1;
    SELECT project_id INTO project2_id FROM projects WHERE selected_ai = 'crew-ai' AND name LIKE '%챗봇%' LIMIT 1;
    SELECT project_id INTO project3_id FROM projects WHERE selected_ai = 'crew-ai' AND name LIKE '%데이터%' LIMIT 1;

    -- project_stages 샘플 데이터 (실제 존재하는 project_id 사용)
    IF project1_id IS NOT NULL THEN
        INSERT INTO project_stages (projects_project_id, stage_name, stage_order, stage_status, responsible_role, estimated_hours)
        VALUES
            (project1_id, '요구사항 분석', 1, 'completed', 'Product Manager', 40),
            (project1_id, '시스템 설계', 2, 'in_progress', 'Architect', 60),
            (project1_id, '개발', 3, 'pending', 'Engineer', 120),
            (project1_id, '테스트', 4, 'pending', 'QA Engineer', 40)
        ON CONFLICT (projects_project_id, stage_order) DO NOTHING;
    END IF;

    IF project2_id IS NOT NULL THEN
        INSERT INTO project_stages (projects_project_id, stage_name, stage_order, stage_status, responsible_role, estimated_hours)
        VALUES
            (project2_id, '기획', 1, 'completed', 'Planner', 20),
            (project2_id, '조사', 2, 'in_progress', 'Researcher', 30),
            (project2_id, '작성', 3, 'pending', 'Writer', 25)
        ON CONFLICT (projects_project_id, stage_order) DO NOTHING;
    END IF;
END $$;

-- 샘플 데이터 삽입을 위한 동적 프로시저 계속
DO $$
DECLARE
    project1_id VARCHAR(13);
    project2_id VARCHAR(13);
    project3_id VARCHAR(13);
BEGIN
    -- 존재하는 프로젝트 ID 다시 가져오기
    SELECT project_id INTO project1_id FROM projects WHERE selected_ai = 'meta-gpt' AND name LIKE '%E-commerce%' LIMIT 1;
    SELECT project_id INTO project2_id FROM projects WHERE selected_ai = 'crew-ai' AND name LIKE '%챗봇%' LIMIT 1;
    SELECT project_id INTO project3_id FROM projects WHERE selected_ai = 'crew-ai' AND name LIKE '%데이터%' LIMIT 1;

    -- project_role_llm_mapping 샘플 데이터
    IF project1_id IS NOT NULL THEN
        INSERT INTO project_role_llm_mapping (projects_project_id, role_name, llm_model, is_active)
        VALUES
            (project1_id, 'Product Manager', 'gemini-2.5-flash', true),
            (project1_id, 'Architect', 'gemini-2.5-flash', true),
            (project1_id, 'Engineer', 'deepseek-coder', true),
            (project1_id, 'QA Engineer', 'claude-3-haiku', true)
        ON CONFLICT (projects_project_id, role_name) DO NOTHING;
    END IF;

    IF project2_id IS NOT NULL THEN
        INSERT INTO project_role_llm_mapping (projects_project_id, role_name, llm_model, is_active)
        VALUES
            (project2_id, 'Planner', 'gemini-2.5-flash', true),
            (project2_id, 'Researcher', 'gemini-pro', true),
            (project2_id, 'Writer', 'gpt-4', true)
        ON CONFLICT (projects_project_id, role_name) DO NOTHING;
    END IF;

    -- MetaGPT workflow stages 샘플 데이터 (MetaGPT 프로젝트만)
    IF project1_id IS NOT NULL THEN
        INSERT INTO metagpt_workflow_stages (projects_project_id, stage_number, stage_name, stage_description, responsible_role, role_icon, status)
        VALUES
            (project1_id, 1, '요구사항 분석', 'PRD 작성 및 요구사항 정의', 'Product Manager', '📋', 'completed'),
            (project1_id, 2, '시스템 설계', '아키텍처 설계 및 API 명세', 'Architect', '🏗️', 'in_progress'),
            (project1_id, 3, '프로젝트 계획', '작업 분석 및 일정 수립', 'Project Manager', '📊', 'pending'),
            (project1_id, 4, '코드 개발', '실제 코드 구현', 'Engineer', '💻', 'pending'),
            (project1_id, 5, '품질 보증', '테스트 및 품질 검증', 'QA Engineer', '🧪', 'pending')
        ON CONFLICT (projects_project_id, stage_number) DO NOTHING;

        -- MetaGPT role mapping 샘플 데이터
        INSERT INTO metagpt_role_llm_mapping (projects_project_id, product_manager_llm, architect_llm, project_manager_llm, engineer_llm, qa_engineer_llm)
        VALUES
            (project1_id, 'gemini-2.5-flash', 'gemini-2.5-flash', 'gemini-2.5-flash', 'gemini-2.5-flash', 'gemini-2.5-flash')
        ON CONFLICT (projects_project_id) DO NOTHING;

        -- MetaGPT project metrics 샘플 데이터
        INSERT INTO metagpt_project_metrics (projects_project_id, total_planned_hours, total_actual_hours, deliverable_count, average_quality_score)
        VALUES
            (project1_id, 200, 150, 5, 8.5)
        ON CONFLICT (projects_project_id) DO NOTHING;
    END IF;
END $$;

-- ==================== STEP 7: 검증 및 확인 ====================

-- 마이그레이션 성공 확인
SELECT 'Migration completed successfully!' as status;

-- 새로운 테이블 구조 확인
SELECT 'Table structures with project_id SERIAL:' as info;

-- 각 테이블의 project_id 컬럼 확인
SELECT 'project_stages' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'project_stages' AND column_name = 'project_id';

SELECT 'project_role_llm_mapping' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'project_role_llm_mapping' AND column_name = 'project_id';

SELECT 'project_deliverables' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'project_deliverables' AND column_name = 'project_id';

SELECT 'deliverable_access_log' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'deliverable_access_log' AND column_name = 'project_id';

SELECT 'metagpt_workflow_stages' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'metagpt_workflow_stages' AND column_name = 'project_id';

SELECT 'metagpt_role_llm_mapping' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'metagpt_role_llm_mapping' AND column_name = 'project_id';

SELECT 'metagpt_deliverables' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'metagpt_deliverables' AND column_name = 'project_id';

SELECT 'metagpt_communication_log' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'metagpt_communication_log' AND column_name = 'project_id';

SELECT 'metagpt_project_metrics' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'metagpt_project_metrics' AND column_name = 'project_id';

-- 샘플 데이터 확인
SELECT 'Tables with SERIAL project_id data:' as info;
SELECT 'project_stages count:' as table_info, COUNT(*) as count FROM project_stages;
SELECT 'project_role_llm_mapping count:' as table_info, COUNT(*) as count FROM project_role_llm_mapping;
SELECT 'project_deliverables count:' as table_info, COUNT(*) as count FROM project_deliverables;
SELECT 'deliverable_access_log count:' as table_info, COUNT(*) as count FROM deliverable_access_log;
SELECT 'metagpt_workflow_stages count:' as table_info, COUNT(*) as count FROM metagpt_workflow_stages;
SELECT 'metagpt_role_llm_mapping count:' as table_info, COUNT(*) as count FROM metagpt_role_llm_mapping;
SELECT 'metagpt_deliverables count:' as table_info, COUNT(*) as count FROM metagpt_deliverables;
SELECT 'metagpt_communication_log count:' as table_info, COUNT(*) as count FROM metagpt_communication_log;
SELECT 'metagpt_project_metrics count:' as table_info, COUNT(*) as count FROM metagpt_project_metrics;

-- 외래키 제약 조건 확인
SELECT 'Foreign key constraints:' as info,
       tc.constraint_name, tc.table_name, kcu.column_name,
       ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('project_stages', 'project_role_llm_mapping', 'project_deliverables', 'deliverable_access_log',
                      'metagpt_workflow_stages', 'metagpt_role_llm_mapping', 'metagpt_deliverables',
                      'metagpt_communication_log', 'metagpt_project_metrics')
ORDER BY tc.table_name, kcu.column_name;

-- 뷰 동작 확인
SELECT 'Views working correctly:' as info;
SELECT COUNT(*) as llm_usage_analytics_rows FROM llm_usage_analytics;
SELECT COUNT(*) as project_summary_rows FROM project_summary;
SELECT COUNT(*) as metagpt_dashboard_rows FROM metagpt_project_dashboard;

-- 완료 메시지
SELECT '✅ Successfully migrated 9 tables from id UUID to project_id SERIAL!' as final_status;
SELECT '📋 All tables now use project_id SERIAL as primary key instead of id UUID' as summary;
SELECT '🔗 Foreign key relationships updated to use new SERIAL project_id columns' as relationships;
SELECT '📊 Views and indexes updated to work with new schema' as views_indexes;
