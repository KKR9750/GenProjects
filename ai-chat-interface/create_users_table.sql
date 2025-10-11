-- Users 테이블 생성 스크립트
-- Supabase SQL Editor에서 실행하세요

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

-- 2. Projects 테이블에 사용자 관계 추가
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS created_by_user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE SET NULL;

-- 3. Users 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- 4. Projects 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by_user_id);

-- 5. Updated_at 트리거 추가 (기존 트리거 삭제 후 생성)
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. 기본 관리자 계정 생성
-- ⚠️ 보안: 운영 환경에서는 반드시 강력한 비밀번호로 변경하세요!
INSERT INTO users (user_id, email, display_name, role, password_hash)
VALUES (
    'admin',
    'admin@genprojects.com',
    '시스템 관리자',
    'admin',
    '$2b$12$sxHPo8qPPoahqbUh/SheZu9Qo1JqNTY7C345KITMhebix45wk2kRW' -- 초기 해시 (반드시 변경 필요)
) ON CONFLICT (user_id) DO NOTHING;

-- 확인 쿼리
SELECT 'Users 테이블 생성 완료' as message;
SELECT * FROM users LIMIT 5;