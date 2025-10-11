-- AI Chat Interface Database Schema
-- Execute this in your Supabase SQL editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    settings_data JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by VARCHAR(50) DEFAULT 'system',
    version VARCHAR(10) DEFAULT '1.0',
    description TEXT
);

-- ==================== CORE TABLES ====================

-- Projects 시퀀스 생성 (project_id 자동 생성용)
CREATE SEQUENCE IF NOT EXISTS projects_seq START 1;

-- ==================== APPROVAL SYSTEM TABLES ====================

-- Approval Requests table
CREATE TABLE IF NOT EXISTS approval_requests (
    approval_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE SET NULL,

    -- Analysis Information
    analysis_result JSONB NOT NULL,
    framework VARCHAR(20) DEFAULT 'crewai' CHECK (framework IN ('crewai', 'metagpt')),

    -- Approval Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'revision_requested', 'expired')),
    requester VARCHAR(50) DEFAULT 'system',

    -- Response Information
    response JSONB DEFAULT '{}',

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Approval History table
CREATE TABLE IF NOT EXISTS approval_history (
    history_id SERIAL PRIMARY KEY,
    approval_id UUID REFERENCES approval_requests(approval_id) ON DELETE CASCADE,

    -- Action Information
    action VARCHAR(20) NOT NULL CHECK (action IN ('created', 'approve', 'reject', 'request_revision', 'expired')),
    feedback TEXT,
    revisions JSONB DEFAULT '{}',

    -- Actor Information
    actor VARCHAR(50) DEFAULT 'system',
    actor_role VARCHAR(50),

    -- Timestamp
    timestamp TIMESTAMP DEFAULT NOW()
);

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
    project_id VARCHAR(13) PRIMARY KEY DEFAULT 'project_' || LPAD(nextval('projects_seq')::text, 5, '0'),
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
    review_iterations INTEGER DEFAULT 1 CHECK (review_iterations >= 0 AND review_iterations <= 5),

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

-- Project Tools table
CREATE TABLE IF NOT EXISTS project_tools (
    id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    tool_key VARCHAR(100) NOT NULL,
    tool_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(projects_project_id, tool_key)
);

-- 2. Project Stages table (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS project_stages (
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

-- 3. Project Role-LLM Mapping table (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS project_role_llm_mapping (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL CHECK (role_name IN (
        'Researcher', 'Writer', 'Planner',
        'Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'
    )),
    llm_model VARCHAR(50) NOT NULL CHECK (llm_model IN (
        'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
        'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
        'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
    )),
    llm_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint for active role mappings per project
    UNIQUE(projects_project_id, role_name)
);

-- 4. Project Deliverables table (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS project_deliverables (
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

-- 5. Deliverable Access Log table (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS deliverable_access_log (
    project_id SERIAL PRIMARY KEY,
    deliverable_project_id INTEGER REFERENCES project_deliverables(project_id) ON DELETE CASCADE,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,
    accessed_by_role VARCHAR(50) NOT NULL,
    access_type VARCHAR(20) NOT NULL CHECK (access_type IN ('read', 'edit', 'download', 'share')),
    access_details JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==================== INDEXES ====================

-- Approval System indexes
CREATE INDEX IF NOT EXISTS idx_approval_requests_approval_id ON approval_requests(approval_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status);
CREATE INDEX IF NOT EXISTS idx_approval_requests_project_id ON approval_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_approval_requests_framework ON approval_requests(framework);
CREATE INDEX IF NOT EXISTS idx_approval_requests_created_at ON approval_requests(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_approval_history_approval_id ON approval_history(approval_id);
CREATE INDEX IF NOT EXISTS idx_approval_history_action ON approval_history(action);
CREATE INDEX IF NOT EXISTS idx_approval_history_timestamp ON approval_history(timestamp DESC);

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

-- Project Stages indexes (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_project_stages_project_id ON project_stages(project_id);
CREATE INDEX IF NOT EXISTS idx_project_stages_projects_project_id ON project_stages(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_project_stages_order ON project_stages(projects_project_id, stage_order);

-- Role-LLM Mapping indexes (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_role_mapping_project_id ON project_role_llm_mapping(project_id);
CREATE INDEX IF NOT EXISTS idx_role_mapping_projects_project_id ON project_role_llm_mapping(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_role_mapping_active ON project_role_llm_mapping(projects_project_id, is_active);

-- Deliverables indexes (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_deliverables_project_id ON project_deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_projects_project_id ON project_deliverables(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_stage_project_id ON project_deliverables(stage_project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON project_deliverables(projects_project_id, deliverable_type);

-- Access Log indexes (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_access_log_project_id ON deliverable_access_log(project_id);
CREATE INDEX IF NOT EXISTS idx_access_log_deliverable_project_id ON deliverable_access_log(deliverable_project_id);
CREATE INDEX IF NOT EXISTS idx_access_log_projects_project_id ON deliverable_access_log(projects_project_id);

-- ==================== TRIGGERS ====================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables (safe creation)
DROP TRIGGER IF EXISTS update_approval_requests_updated_at ON approval_requests;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
DROP TRIGGER IF EXISTS update_project_stages_updated_at ON project_stages;
DROP TRIGGER IF EXISTS update_role_mapping_updated_at ON project_role_llm_mapping;
DROP TRIGGER IF EXISTS update_deliverables_updated_at ON project_deliverables;

CREATE TRIGGER update_approval_requests_updated_at BEFORE UPDATE ON approval_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_project_stages_updated_at BEFORE UPDATE ON project_stages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_role_mapping_updated_at BEFORE UPDATE ON project_role_llm_mapping FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deliverables_updated_at BEFORE UPDATE ON project_deliverables FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== SAMPLE DATA ====================

-- Insert sample project
INSERT INTO projects (project_id, name, description, selected_ai, project_type, status, progress_percentage)
VALUES
    ('project_00001', 'E-commerce 플랫폼', '온라인 쇼핑몰 개발 프로젝트', 'meta-gpt', 'web_app', 'in_progress', 30),
    ('project_00002', 'AI 챗봇 시스템', '고객 서비스용 AI 챗봇', 'crew-ai', 'api', 'planning', 10)
ON CONFLICT (project_id) DO NOTHING;

-- Insert sample role mappings for first project (using new project_id SERIAL structure)
INSERT INTO project_role_llm_mapping (projects_project_id, role_name, llm_model)
VALUES
    ('project_00001', 'Product Manager', 'gpt-4'),
    ('project_00001', 'Architect', 'claude-3-sonnet'),
    ('project_00001', 'Engineer', 'deepseek-coder'),
    ('project_00001', 'QA Engineer', 'llama-3')
ON CONFLICT (projects_project_id, role_name) DO NOTHING;

-- Insert sample role mappings for second project (using new project_id SERIAL structure)
INSERT INTO project_role_llm_mapping (projects_project_id, role_name, llm_model)
VALUES
    ('project_00002', 'Researcher', 'gemini-pro'),
    ('project_00002', 'Writer', 'gpt-4'),
    ('project_00002', 'Planner', 'claude-3-sonnet')
ON CONFLICT (projects_project_id, role_name) DO NOTHING;

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

-- LLM Usage Analytics View (project_id SERIAL)
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

-- Project Summary View (project_id SERIAL)
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
