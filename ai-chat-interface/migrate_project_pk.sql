-- AI Chat Interface Database Migration Script
-- Project PK Migration: UUID -> project_id (project_00001 format)
-- 기존 데이터 삭제 후 새 스키마 적용

-- ==================== STEP 1: 기존 테이블 삭제 ====================

-- 외래키 의존성 순서로 삭제 (CASCADE 사용)
DROP TABLE IF EXISTS deliverable_access_log CASCADE;
DROP TABLE IF EXISTS project_deliverables CASCADE;
DROP TABLE IF EXISTS project_role_llm_mapping CASCADE;
DROP TABLE IF EXISTS project_stages CASCADE;
DROP TABLE IF EXISTS projects CASCADE;

-- 관련 뷰들도 삭제
DROP VIEW IF EXISTS project_analytics CASCADE;
DROP VIEW IF EXISTS llm_usage_analytics CASCADE;
DROP VIEW IF EXISTS project_summary CASCADE;

-- ==================== STEP 2: 시퀀스 및 함수 생성 ====================

-- project_id 자동 생성을 위한 시퀀스 생성
CREATE SEQUENCE IF NOT EXISTS project_id_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    MAXVALUE 99999
    CACHE 1;

-- project_id 생성 함수
CREATE OR REPLACE FUNCTION generate_project_id()
RETURNS VARCHAR(13) AS $$
BEGIN
    RETURN 'project_' || LPAD(nextval('project_id_seq')::text, 5, '0');
END;
$$ LANGUAGE plpgsql;

-- ==================== STEP 3: 새로운 테이블 생성 ====================

-- 1. Projects table (새 PK 구조)
CREATE TABLE IF NOT EXISTS projects (
    project_id VARCHAR(13) PRIMARY KEY DEFAULT generate_project_id(),
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- User Ownership
    created_by_user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE SET NULL,

    -- AI Framework Selection
    selected_ai VARCHAR(20) DEFAULT 'crew-ai' CHECK (selected_ai IN ('crew-ai', 'meta-gpt')),

    -- Project Status
    status VARCHAR(20) DEFAULT 'planning' CHECK (status IN ('planning', 'in_progress', 'review', 'completed', 'paused')),
    current_stage VARCHAR(20) DEFAULT 'requirement' CHECK (current_stage IN ('requirement', 'design', 'architecture', 'development', 'testing', 'deployment')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Project Configuration
    project_type VARCHAR(20) DEFAULT 'web_app' CHECK (project_type IN ('web_app', 'mobile_app', 'api', 'desktop', 'data_analysis')),
    target_audience TEXT,
    technical_requirements JSONB DEFAULT '{}',

    -- Metadata
    workspace_path VARCHAR(500),
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    deadline TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Project Stages table
CREATE TABLE IF NOT EXISTS project_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
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
    UNIQUE(project_id, stage_order)
);

-- 3. Project Role-LLM Mapping table
CREATE TABLE IF NOT EXISTS project_role_llm_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL CHECK (role_name IN (
        'Researcher', 'Writer', 'Planner',
        'Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'
    )),
    llm_model VARCHAR(50) NOT NULL CHECK (llm_model IN (
        'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku',
        'gemini-pro', 'gemini-ultra', 'gemini-flash', 'llama-3', 'llama-3-8b',
        'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
    )),
    llm_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint for active role mappings per project
    UNIQUE(project_id, role_name)
);

-- 4. Project Deliverables table
CREATE TABLE IF NOT EXISTS project_deliverables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    stage_id UUID REFERENCES project_stages(id) ON DELETE CASCADE,

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
    parent_deliverable_id UUID REFERENCES project_deliverables(id),

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

-- 5. Deliverable Access Log table
CREATE TABLE IF NOT EXISTS deliverable_access_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deliverable_id UUID REFERENCES project_deliverables(id) ON DELETE CASCADE,
    project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    accessed_by_role VARCHAR(50) NOT NULL,
    access_type VARCHAR(20) NOT NULL CHECK (access_type IN ('read', 'edit', 'download', 'share')),
    access_details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================== STEP 4: 인덱스 재생성 ====================

-- Projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_project_id ON projects(project_id);
CREATE INDEX IF NOT EXISTS idx_projects_selected_ai ON projects(selected_ai);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status, current_stage);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by_user_id);

-- Project Stages indexes
CREATE INDEX IF NOT EXISTS idx_project_stages_project_id ON project_stages(project_id);
CREATE INDEX IF NOT EXISTS idx_project_stages_order ON project_stages(project_id, stage_order);

-- Role-LLM Mapping indexes
CREATE INDEX IF NOT EXISTS idx_role_mapping_project ON project_role_llm_mapping(project_id);
CREATE INDEX IF NOT EXISTS idx_role_mapping_active ON project_role_llm_mapping(project_id, is_active);

-- Deliverables indexes
CREATE INDEX IF NOT EXISTS idx_deliverables_project ON project_deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_stage ON project_deliverables(stage_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON project_deliverables(project_id, deliverable_type);

-- Access Log indexes
CREATE INDEX IF NOT EXISTS idx_access_log_deliverable ON deliverable_access_log(deliverable_id);
CREATE INDEX IF NOT EXISTS idx_access_log_project ON deliverable_access_log(project_id);

-- ==================== STEP 5: 트리거 재생성 ====================

-- Apply triggers to tables
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_project_stages_updated_at BEFORE UPDATE ON project_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_mapping_updated_at BEFORE UPDATE ON project_role_llm_mapping FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deliverables_updated_at BEFORE UPDATE ON project_deliverables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== STEP 6: 뷰 재생성 ====================

-- Project Analytics View
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

-- LLM Usage Analytics View
CREATE OR REPLACE VIEW llm_usage_analytics AS
SELECT
    prm.llm_model,
    prm.role_name,
    COUNT(DISTINCT prm.project_id) as projects_count,
    COUNT(*) as total_mappings
FROM project_role_llm_mapping prm
WHERE prm.is_active = true
GROUP BY prm.llm_model, prm.role_name
ORDER BY projects_count DESC;

-- Project Summary View
CREATE OR REPLACE VIEW project_summary AS
SELECT
    p.project_id,
    p.name,
    p.selected_ai,
    p.status,
    p.progress_percentage,
    p.created_at,
    COUNT(ps.id) as total_stages,
    COUNT(CASE WHEN ps.stage_status = 'completed' THEN 1 END) as completed_stages,
    COUNT(pd.id) as total_deliverables,
    COUNT(prm.id) as role_mappings_count
FROM projects p
LEFT JOIN project_stages ps ON ps.project_id = p.project_id
LEFT JOIN project_deliverables pd ON pd.project_id = p.project_id
LEFT JOIN project_role_llm_mapping prm ON prm.project_id = p.project_id AND prm.is_active = true
GROUP BY p.project_id, p.name, p.selected_ai, p.status, p.progress_percentage, p.created_at
ORDER BY p.created_at DESC;

-- ==================== STEP 7: 샘플 데이터 삽입 ====================

-- Insert sample projects with new PK format
INSERT INTO projects (name, description, selected_ai, project_type, status, progress_percentage)
VALUES
    ('E-commerce 플랫폼', '온라인 쇼핑몰 개발 프로젝트', 'meta-gpt', 'web_app', 'in_progress', 30),
    ('AI 챗봇 시스템', '고객 서비스용 AI 챗봇', 'crew-ai', 'api', 'planning', 10),
    ('데이터 분석 대시보드', '비즈니스 인텔리전스 대시보드', 'crew-ai', 'data_analysis', 'planning', 5)
ON CONFLICT DO NOTHING;

-- Insert sample role mappings for first project (project_00001)
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
VALUES
    ('project_00001', 'Product Manager', 'gpt-4'),
    ('project_00001', 'Architect', 'claude-3'),
    ('project_00001', 'Engineer', 'deepseek-coder'),
    ('project_00001', 'QA Engineer', 'llama-3')
ON CONFLICT (project_id, role_name) DO NOTHING;

-- Insert sample role mappings for second project (project_00002) - CrewAI 올바른 순서
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
VALUES
    ('project_00002', 'Planner', 'claude-3'),
    ('project_00002', 'Researcher', 'gemini-pro'),
    ('project_00002', 'Writer', 'gpt-4')
ON CONFLICT (project_id, role_name) DO NOTHING;

-- Insert sample role mappings for third project (project_00003) - CrewAI 올바른 순서
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
VALUES
    ('project_00003', 'Planner', 'gemini-pro'),
    ('project_00003', 'Researcher', 'claude-3'),
    ('project_00003', 'Writer', 'gpt-4o')
ON CONFLICT (project_id, role_name) DO NOTHING;

-- ==================== VERIFICATION ====================

-- 마이그레이션 확인 쿼리
SELECT 'Migration completed successfully!' as status;
SELECT 'Projects created:' as info, COUNT(*) as count FROM projects;
SELECT 'Role mappings created:' as info, COUNT(*) as count FROM project_role_llm_mapping;
SELECT 'Sample project IDs:' as info, project_id, name FROM projects ORDER BY project_id;