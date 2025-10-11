-- Approval System Tables Update
-- Supabase SQL 에디터에서 실행하세요

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

-- ==================== TRIGGERS ====================

-- Update updated_at timestamp function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to approval_requests table
DROP TRIGGER IF EXISTS update_approval_requests_updated_at ON approval_requests;
CREATE TRIGGER update_approval_requests_updated_at BEFORE UPDATE ON approval_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Select to verify tables creation
SELECT 'approval_requests table exists' as status,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'approval_requests') as exists_count;

SELECT 'approval_history table exists' as status,
       (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'approval_history') as exists_count;