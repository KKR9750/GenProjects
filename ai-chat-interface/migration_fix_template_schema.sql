-- ========================================
-- 긴급 마이그레이션: 템플릿 스키마 수정
-- 프로젝트 초기화 500 에러 해결
-- ========================================

-- ==================== 1. AGENT_TEMPLATES 테이블 수정 ====================

-- agent_order 컬럼 추가
ALTER TABLE agent_templates
ADD COLUMN IF NOT EXISTS agent_order INTEGER NOT NULL DEFAULT 0;

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_agent_templates_order
ON agent_templates(framework, agent_order);

-- ==================== 2. TASK_TEMPLATES 테이블 수정 ====================

-- task_order, assigned_agent_order, depends_on_task_order 컬럼 추가
ALTER TABLE task_templates
ADD COLUMN IF NOT EXISTS task_order INTEGER NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS assigned_agent_order INTEGER,
ADD COLUMN IF NOT EXISTS depends_on_task_order INTEGER;

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_task_templates_order
ON task_templates(framework, task_order);

-- ==================== 3. AGENT 템플릿 데이터 업데이트 ====================

-- CrewAI Agents
UPDATE agent_templates SET agent_order = 1
WHERE framework = 'crewai' AND template_name = 'planner';

UPDATE agent_templates SET agent_order = 2
WHERE framework = 'crewai' AND template_name = 'researcher';

UPDATE agent_templates SET agent_order = 3
WHERE framework = 'crewai' AND template_name = 'writer';

-- MetaGPT Agents
UPDATE agent_templates SET agent_order = 1
WHERE framework = 'metagpt' AND template_name = 'product_manager';

UPDATE agent_templates SET agent_order = 2
WHERE framework = 'metagpt' AND template_name = 'architect';

UPDATE agent_templates SET agent_order = 3
WHERE framework = 'metagpt' AND template_name = 'project_manager';

UPDATE agent_templates SET agent_order = 4
WHERE framework = 'metagpt' AND template_name = 'engineer';

UPDATE agent_templates SET agent_order = 5
WHERE framework = 'metagpt' AND template_name = 'qa_engineer';

-- ==================== 4. TASK 템플릿 데이터 업데이트 ====================

-- CrewAI Tasks
UPDATE task_templates SET
    task_order = 1,
    assigned_agent_order = 1,
    depends_on_task_order = NULL
WHERE framework = 'crewai' AND task_type = 'planning';

UPDATE task_templates SET
    task_order = 2,
    assigned_agent_order = 2,
    depends_on_task_order = 1
WHERE framework = 'crewai' AND task_type = 'research';

UPDATE task_templates SET
    task_order = 3,
    assigned_agent_order = 3,
    depends_on_task_order = 2
WHERE framework = 'crewai' AND task_type = 'implementation';

UPDATE task_templates SET
    task_order = 4,
    assigned_agent_order = 1,
    depends_on_task_order = 3
WHERE framework = 'crewai' AND task_type = 'review';

UPDATE task_templates SET
    task_order = 5,
    assigned_agent_order = 3,
    depends_on_task_order = 4
WHERE framework = 'crewai' AND task_type = 'revision';

-- MetaGPT Tasks
UPDATE task_templates SET
    task_order = 1,
    assigned_agent_order = 1,
    depends_on_task_order = NULL
WHERE framework = 'metagpt' AND task_type = 'prd_writing';

UPDATE task_templates SET
    task_order = 2,
    assigned_agent_order = 2,
    depends_on_task_order = 1
WHERE framework = 'metagpt' AND task_type = 'system_design';

UPDATE task_templates SET
    task_order = 3,
    assigned_agent_order = 3,
    depends_on_task_order = 2
WHERE framework = 'metagpt' AND task_type = 'project_planning';

UPDATE task_templates SET
    task_order = 4,
    assigned_agent_order = 4,
    depends_on_task_order = 3
WHERE framework = 'metagpt' AND task_type = 'coding';

UPDATE task_templates SET
    task_order = 5,
    assigned_agent_order = 5,
    depends_on_task_order = 4
WHERE framework = 'metagpt' AND task_type = 'qa_testing';

-- ==================== 5. 검증 쿼리 ====================

-- Agent 템플릿 검증
SELECT framework, template_name, agent_order
FROM agent_templates
ORDER BY framework, agent_order;

-- Task 템플릿 검증
SELECT framework, task_type, task_order, assigned_agent_order, depends_on_task_order
FROM task_templates
ORDER BY framework, task_order;

-- ==================== 완료 ====================

COMMENT ON COLUMN agent_templates.agent_order IS 'Agent 실행 순서 (1부터 시작)';
COMMENT ON COLUMN task_templates.task_order IS 'Task 실행 순서 (1부터 시작)';
COMMENT ON COLUMN task_templates.assigned_agent_order IS '할당된 Agent의 agent_order';
COMMENT ON COLUMN task_templates.depends_on_task_order IS '의존하는 Task의 task_order (NULL이면 의존성 없음)';
