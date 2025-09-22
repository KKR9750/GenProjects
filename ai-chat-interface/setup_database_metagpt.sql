-- MetaGPT Platform Database Schema Extension
-- MetaGPT 5단계 워크플로우 지원 추가 스키마

-- ==================== METAGPT SPECIFIC TABLES ====================

-- 1. MetaGPT 워크플로우 단계 정의 (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS metagpt_workflow_stages (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,

    -- 단계 정보
    stage_number INTEGER NOT NULL CHECK (stage_number BETWEEN 1 AND 5),
    stage_name VARCHAR(50) NOT NULL,
    stage_description TEXT,
    responsible_role VARCHAR(50) NOT NULL,
    role_icon VARCHAR(10),

    -- 상태 관리
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'review_needed', 'approved', 'completed', 'blocked')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- 승인 프로세스
    requires_approval BOOLEAN DEFAULT true,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    rejection_reason TEXT,

    -- 시간 추적
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    start_time TIMESTAMP,
    end_time TIMESTAMP,

    -- 결과물
    output_content TEXT,
    output_files JSONB DEFAULT '[]',
    quality_score INTEGER CHECK (quality_score BETWEEN 1 AND 10),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. MetaGPT 역할별 LLM 매핑 (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS metagpt_role_llm_mapping (
    project_id SERIAL PRIMARY KEY,
    projects_project_id VARCHAR(13) REFERENCES projects(project_id) ON DELETE CASCADE,

    -- MetaGPT 5개 역할
    product_manager_llm VARCHAR(50) DEFAULT 'gpt-4',
    architect_llm VARCHAR(50) DEFAULT 'claude-3-sonnet',
    project_manager_llm VARCHAR(50) DEFAULT 'gpt-4o',
    engineer_llm VARCHAR(50) DEFAULT 'deepseek-coder',
    qa_engineer_llm VARCHAR(50) DEFAULT 'claude-3-haiku',

    -- 설정 메타데이터
    configuration_notes TEXT,
    performance_preferences JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 프로젝트당 하나의 매핑만
    UNIQUE(projects_project_id)
);

-- 3. MetaGPT 단계별 산출물 (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS metagpt_deliverables (
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

-- 4. MetaGPT 팀 커뮤니케이션 로그 (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS metagpt_communication_log (
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

-- 5. MetaGPT 프로젝트 성과 지표 (project_id SERIAL PK)
CREATE TABLE IF NOT EXISTS metagpt_project_metrics (
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

-- ==================== INDEXES FOR METAGPT ====================

-- 워크플로우 단계 인덱스 (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_metagpt_workflow_project_id ON metagpt_workflow_stages(project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_workflow_projects_project_id ON metagpt_workflow_stages(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_workflow_project_stage ON metagpt_workflow_stages(projects_project_id, stage_number);
CREATE INDEX IF NOT EXISTS idx_metagpt_workflow_status ON metagpt_workflow_stages(status);
CREATE INDEX IF NOT EXISTS idx_metagpt_workflow_role ON metagpt_workflow_stages(responsible_role);

-- 역할 매핑 인덱스 (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_metagpt_role_mapping_project_id ON metagpt_role_llm_mapping(project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_role_mapping_projects_project_id ON metagpt_role_llm_mapping(projects_project_id);

-- 산출물 인덱스 (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_metagpt_deliverables_project_id ON metagpt_deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_deliverables_projects_project_id ON metagpt_deliverables(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_deliverables_workflow_stage_project_id ON metagpt_deliverables(workflow_stage_project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_deliverables_type ON metagpt_deliverables(deliverable_type);

-- 커뮤니케이션 인덱스 (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_metagpt_comm_project_id ON metagpt_communication_log(project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_comm_projects_project_id ON metagpt_communication_log(projects_project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_comm_workflow_stage_project_id ON metagpt_communication_log(workflow_stage_project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_comm_roles ON metagpt_communication_log(from_role, to_role);

-- 성과 지표 인덱스 (project_id SERIAL)
CREATE INDEX IF NOT EXISTS idx_metagpt_metrics_project_id ON metagpt_project_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_metagpt_metrics_projects_project_id ON metagpt_project_metrics(projects_project_id);

-- ==================== TRIGGERS FOR METAGPT ====================

-- 워크플로우 단계 업데이트 트리거
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

DROP TRIGGER IF EXISTS trigger_metagpt_workflow_update ON metagpt_workflow_stages;
CREATE TRIGGER trigger_metagpt_workflow_update
    BEFORE UPDATE ON metagpt_workflow_stages
    FOR EACH ROW
    EXECUTE FUNCTION update_metagpt_workflow_timestamp();

-- 산출물 버전 관리 트리거
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

DROP TRIGGER IF EXISTS trigger_metagpt_deliverable_version ON metagpt_deliverables;
CREATE TRIGGER trigger_metagpt_deliverable_version
    BEFORE INSERT ON metagpt_deliverables
    FOR EACH ROW
    EXECUTE FUNCTION increment_metagpt_deliverable_version();

-- ==================== SAMPLE DATA FOR METAGPT ====================

-- 샘플 MetaGPT 프로젝트 초기화 (project_id SERIAL 사용)
INSERT INTO metagpt_workflow_stages (projects_project_id, stage_number, stage_name, stage_description, responsible_role, role_icon, status)
VALUES
    ('project_00001', 1, '요구사항 분석', 'PRD 작성 및 요구사항 정의', 'Product Manager', '📋', 'completed'),
    ('project_00001', 2, '시스템 설계', '아키텍처 설계 및 API 명세', 'Architect', '🏗️', 'in_progress'),
    ('project_00001', 3, '프로젝트 계획', '작업 분석 및 일정 수립', 'Project Manager', '📊', 'pending'),
    ('project_00001', 4, '코드 개발', '실제 코드 구현', 'Engineer', '💻', 'pending'),
    ('project_00001', 5, '품질 보증', '테스트 및 품질 검증', 'QA Engineer', '🧪', 'pending')
ON CONFLICT (projects_project_id, stage_number) DO NOTHING;

-- 샘플 MetaGPT LLM 매핑 (project_id SERIAL 사용)
INSERT INTO metagpt_role_llm_mapping (projects_project_id, product_manager_llm, architect_llm, project_manager_llm, engineer_llm, qa_engineer_llm)
VALUES
    ('project_00001', 'gpt-4', 'claude-3-sonnet', 'gpt-4o', 'deepseek-coder', 'claude-3-haiku')
ON CONFLICT (projects_project_id) DO NOTHING;

-- ==================== VIEWS FOR METAGPT ====================

-- MetaGPT 프로젝트 대시보드 뷰 (project_id SERIAL 기반)
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

-- MetaGPT 성과 대시보드 뷰 (project_id SERIAL 기반)
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

-- 완료
COMMENT ON TABLE metagpt_workflow_stages IS 'MetaGPT 5단계 워크플로우 관리';
COMMENT ON TABLE metagpt_role_llm_mapping IS 'MetaGPT 역할별 LLM 모델 매핑';
COMMENT ON TABLE metagpt_deliverables IS 'MetaGPT 단계별 산출물 및 결과';
COMMENT ON TABLE metagpt_communication_log IS 'MetaGPT 팀 간 커뮤니케이션 추적';
COMMENT ON TABLE metagpt_project_metrics IS 'MetaGPT 프로젝트 성과 및 지표';