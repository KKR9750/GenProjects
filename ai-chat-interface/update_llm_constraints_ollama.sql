-- Ollama 로컬 모델을 위한 데이터베이스 제약 조건 업데이트
-- 2025-10-01: ollama-gemma2-2b, ollama-deepseek-coder-6.7b, ollama-llama3.1, ollama-qwen3-coder-30b 추가

-- 1. 기존 제약 조건 제거
ALTER TABLE project_role_llm_mapping
DROP CONSTRAINT IF EXISTS project_role_llm_mapping_llm_model_check;

-- 2. 새로운 제약 조건 추가 (Ollama 로컬 모델 포함)
ALTER TABLE project_role_llm_mapping
ADD CONSTRAINT project_role_llm_mapping_llm_model_check
CHECK (llm_model IN (
    -- Cloud Models
    'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku', 'claude-3-sonnet',
    'gemini-pro', 'gemini-ultra', 'gemini-flash', 'gemini-2.5-flash', 'gemini-2.5-pro',
    'llama-3', 'llama-3-8b', 'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama',
    -- Ollama Local Models (sync with model_config.json and security_utils.py)
    'ollama-gemma2-2b', 'ollama-deepseek-coder-6.7b', 'ollama-llama3.1', 'ollama-qwen3-coder-30b'
));

-- 3. 변경 사항 확인
SELECT constraint_name, check_clause
FROM information_schema.check_constraints
WHERE constraint_name = 'project_role_llm_mapping_llm_model_check';
