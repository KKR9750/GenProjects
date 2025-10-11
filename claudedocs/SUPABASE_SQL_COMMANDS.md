# Supabase SQL Commands - creation_type 컬럼 추가

## 🎯 목적
`projects` 테이블에 `creation_type` 컬럼을 추가하여 템플릿 기반 프로젝트와 대화형 동적 프로젝트를 구분합니다.

## 📍 실행 위치
**Supabase Dashboard → SQL Editor**

URL: https://supabase.com/dashboard/project/vpbkitxgisxbqtxrwjvo/sql/new

## 📝 실행할 SQL

### 1단계: creation_type 컬럼 추가

```sql
-- Add creation_type column to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS creation_type VARCHAR(20) DEFAULT 'template';

-- Add check constraint to ensure only valid values
ALTER TABLE projects
ADD CONSTRAINT check_creation_type
CHECK (creation_type IN ('template', 'dynamic'));
```

### 2단계: 기존 프로젝트 업데이트

```sql
-- Update existing NULL or empty projects to 'template'
UPDATE projects
SET creation_type = 'template'
WHERE creation_type IS NULL OR creation_type = '';
```

### 3단계: 확인

```sql
-- Check if column was added successfully
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'projects' AND column_name = 'creation_type';

-- Check distribution of creation types
SELECT
    creation_type,
    COUNT(*) as count
FROM projects
GROUP BY creation_type;

-- View sample projects with creation_type
SELECT
    project_id,
    name,
    creation_type,
    created_at
FROM projects
ORDER BY created_at DESC
LIMIT 10;
```

## ✅ 예상 결과

### 1단계 실행 후:
```
ALTER TABLE
ALTER TABLE
```

### 2단계 실행 후:
```
UPDATE <N>  (N = 기존 프로젝트 수)
```

### 3단계 실행 후:
```
column_name    | data_type         | column_default
---------------|-------------------|---------------
creation_type  | character varying | 'template'::character varying

creation_type | count
--------------|------
template      | <N>
```

## 🔄 자동 동작

### 템플릿 프로젝트
- 기존 프로젝트 생성 API 사용 시 → `creation_type = 'template'` (기본값)

### 동적 프로젝트
- `/api/v2/projects/{id}/initialize` API 사용 시 → `creation_type = 'dynamic'` (자동 설정)
- `project_initialization_api.py`에서 자동으로 설정됨

## 📊 UI 표시

### CrewAI 탭
- "➕ 신규 프로젝트" 클릭 시 생성 방식 선택 모달 표시
- 🤖 대화형 생성 → `creation_type = 'dynamic'`
- 📋 기본 생성 → `creation_type = 'template'`

### Projects 탭 (향후 추가 예정)
- 🤖 대화형 뱃지: 보라색
- 📋 템플릿 뱃지: 파란색

## ⚠️ 주의사항

1. **SQL Editor에서 실행**: Python 스크립트는 연결 문제로 실행 불가
2. **순서대로 실행**: 1단계 → 2단계 → 3단계 순서 유지
3. **확인 필수**: 3단계에서 결과 확인

## 🔗 관련 파일

- `project_initialization_api.py` - Line 48에서 `creation_type = 'dynamic'` 설정
- `crewai.js` - 생성 방식 선택 모달 구현
- `crewai.css` - 타입 뱃지 스타일 정의
