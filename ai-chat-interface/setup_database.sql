-- AI Chat Interface Database Schema
-- Execute this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== CORE TABLES ====================

-- 1. Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(100),
    display_name VARCHAR(100),

    -- Authentication
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'viewer')),
    is_active BOOLEAN DEFAULT true,

    -- Profile
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    last_login_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
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
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL CHECK (role_name IN (
        'Researcher', 'Writer', 'Planner',
        'Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'
    )),
    llm_model VARCHAR(50) NOT NULL CHECK (llm_model IN (
        'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku',
        'gemini-pro', 'gemini-ultra', 'llama-3', 'llama-3-8b',
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
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
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
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    accessed_by_role VARCHAR(50) NOT NULL,
    access_type VARCHAR(20) NOT NULL CHECK (access_type IN ('read', 'edit', 'download', 'share')),
    access_details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================== INDEXES ====================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Projects indexes
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

-- ==================== TRIGGERS ====================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_project_stages_updated_at BEFORE UPDATE ON project_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_mapping_updated_at BEFORE UPDATE ON project_role_llm_mapping FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deliverables_updated_at BEFORE UPDATE ON project_deliverables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== SAMPLE DATA ====================

-- Insert sample project
INSERT INTO projects (name, description, selected_ai, project_type, status, progress_percentage)
VALUES
    ('E-commerce 플랫폼', '온라인 쇼핑몰 개발 프로젝트', 'meta-gpt', 'web_app', 'in_progress', 30),
    ('AI 챗봇 시스템', '고객 서비스용 AI 챗봇', 'crew-ai', 'api', 'planning', 10)
ON CONFLICT DO NOTHING;

-- Insert sample role mappings for first project
WITH sample_project AS (
    SELECT id FROM projects WHERE name = 'E-commerce 플랫폼' LIMIT 1
)
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
SELECT
    sample_project.id,
    role_mapping.role_name,
    role_mapping.llm_model
FROM sample_project,
(VALUES
    ('Product Manager', 'gpt-4'),
    ('Architect', 'claude-3'),
    ('Engineer', 'deepseek-coder'),
    ('QA Engineer', 'llama-3')
) AS role_mapping(role_name, llm_model)
ON CONFLICT (project_id, role_name) DO NOTHING;

-- Insert sample role mappings for second project
WITH sample_project AS (
    SELECT id FROM projects WHERE name = 'AI 챗봇 시스템' LIMIT 1
)
INSERT INTO project_role_llm_mapping (project_id, role_name, llm_model)
SELECT
    sample_project.id,
    role_mapping.role_name,
    role_mapping.llm_model
FROM sample_project,
(VALUES
    ('Researcher', 'gemini-pro'),
    ('Writer', 'gpt-4'),
    ('Planner', 'claude-3')
) AS role_mapping(role_name, llm_model)
ON CONFLICT (project_id, role_name) DO NOTHING;

-- ==================== VIEWS ====================

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
    p.id,
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
LEFT JOIN project_stages ps ON ps.project_id = p.id
LEFT JOIN project_deliverables pd ON pd.project_id = p.id
LEFT JOIN project_role_llm_mapping prm ON prm.project_id = p.id AND prm.is_active = true
GROUP BY p.id, p.name, p.selected_ai, p.status, p.progress_percentage, p.created_at
ORDER BY p.created_at DESC;