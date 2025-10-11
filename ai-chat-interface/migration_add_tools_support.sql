-- ========================================
-- Tools 및 Review Iterations 지원 추가
-- 마이그레이션 스크립트
-- ========================================

-- ==================== 1. project_agents에 tools 컬럼 추가 ====================

ALTER TABLE project_agents
ADD COLUMN IF NOT EXISTS tools TEXT[] DEFAULT '{}',  -- 선택된 도구 키 목록
ADD COLUMN IF NOT EXISTS tool_config JSONB DEFAULT '{}';  -- 도구별 설정 (API 키 등)

COMMENT ON COLUMN project_agents.tools IS 'Agent에게 할당된 도구 목록 (mcp_registry.json 키 배열)';
COMMENT ON COLUMN project_agents.tool_config IS '도구별 설정 및 환경 변수 (JSON)';

-- ==================== 2. projects에 review_iterations 확인 ====================
-- (이미 setup_database.sql에 존재하므로, 없을 경우만 추가)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'review_iterations'
    ) THEN
        ALTER TABLE projects
        ADD COLUMN review_iterations INTEGER DEFAULT 1 CHECK (review_iterations >= 0 AND review_iterations <= 5);

        COMMENT ON COLUMN projects.review_iterations IS '품질 검토 반복 횟수 (0~5회)';
    END IF;
END $$;

-- ==================== 3. project_tools 테이블 확인 ====================
-- (이미 setup_database.sql에 존재하므로 패스)

-- ==================== 완료 ====================

-- 마이그레이션 성공 확인
SELECT
    'Migration completed successfully!' AS status,
    NOW() AS timestamp;
