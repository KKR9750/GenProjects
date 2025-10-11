-- Gemini 2.5 모델을 위한 데이터베이스 제약 조건 업데이트
-- 2025-09-28: gemini-2.5-flash, gemini-2.5-pro 추가

-- 1. 기존 제약 조건 제거
ALTER TABLE project_role_llm_mapping
DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;

-- 2. 새로운 제약 조건 추가 (Gemini 2.5 모델 포함)
ALTER TABLE project_role_llm_mapping
ADD CONSTRAINT project_role_llm_mapping_llm_model_check
CHECK (llm_model IN (
    'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
    'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
    'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
));

-- 3. 변경 사항 확인
SELECT constraint_name, check_clause
FROM information_schema.check_constraints
WHERE constraint_name = 'project_role_llm_mapping_llm_model_check';