-- ==================== MetaGPT 템플릿 삽입 ====================
-- MetaGPT 5단계 워크플로우: Product Manager → Architect → Project Manager → Engineer → QA Engineer
--
-- 사용법:
-- Supabase Dashboard에서 SQL Editor를 열고 이 파일의 내용을 실행하세요.
-- 또는 psql을 통해 실행: psql -h your-host -d postgres -f insert_metagpt_templates.sql

-- ==================== 1. AGENT TEMPLATES ====================

-- Agent 1: Product Manager (요구사항 분석 및 PRD 작성)
INSERT INTO agent_templates (
    framework,
    template_name,
    role,
    goal_template,
    backstory_template,
    default_llm_model,
    is_verbose,
    allow_delegation,
    agent_order,
    description
) VALUES (
    'metagpt',
    'product_manager',
    'Product Manager',
    '{requirement}에 대한 포괄적인 제품 요구사항 문서(PRD)를 작성하고 사용자 니즈를 명확히 정의합니다.',
    '당신은 10년 이상의 경력을 가진 시니어 제품 관리자입니다. 사용자 요구사항을 깊이 이해하고, 이를 명확한 제품 명세로 변환하는 전문가입니다. 시장 트렌드와 사용자 행동 패턴을 분석하여 성공적인 제품 전략을 수립합니다.',
    'gemini-2.5-flash',
    true,
    false,
    1,
    'MetaGPT Stage 1: 요구사항 분석 및 PRD 작성 담당'
) ON CONFLICT (framework, template_name)
DO UPDATE SET
    role = EXCLUDED.role,
    goal_template = EXCLUDED.goal_template,
    backstory_template = EXCLUDED.backstory_template,
    default_llm_model = EXCLUDED.default_llm_model,
    agent_order = EXCLUDED.agent_order,
    updated_at = NOW();

-- Agent 2: Architect (시스템 설계 및 아키텍처)
INSERT INTO agent_templates (
    framework,
    template_name,
    role,
    goal_template,
    backstory_template,
    default_llm_model,
    is_verbose,
    allow_delegation,
    agent_order,
    description
) VALUES (
    'metagpt',
    'architect',
    'Architect',
    '{requirement}를 충족하는 확장 가능하고 유지보수 가능한 시스템 아키텍처를 설계합니다.',
    '당신은 엔터프라이즈급 시스템을 설계해온 소프트웨어 아키텍트입니다. 마이크로서비스, 클라우드 네이티브, 확장 가능한 아키텍처 패턴에 정통하며, 기술적 의사결정에 있어 장단점을 명확히 제시합니다.',
    'gemini-2.5-flash',
    true,
    false,
    2,
    'MetaGPT Stage 2: 시스템 아키텍처 설계 담당'
) ON CONFLICT (framework, template_name)
DO UPDATE SET
    role = EXCLUDED.role,
    goal_template = EXCLUDED.goal_template,
    backstory_template = EXCLUDED.backstory_template,
    default_llm_model = EXCLUDED.default_llm_model,
    agent_order = EXCLUDED.agent_order,
    updated_at = NOW();

-- Agent 3: Project Manager (프로젝트 계획 및 일정 관리)
INSERT INTO agent_templates (
    framework,
    template_name,
    role,
    goal_template,
    backstory_template,
    default_llm_model,
    is_verbose,
    allow_delegation,
    agent_order,
    description
) VALUES (
    'metagpt',
    'project_manager',
    'Project Manager',
    '{requirement} 프로젝트의 상세한 작업 분해 구조(WBS)와 일정 계획을 수립합니다.',
    '당신은 애자일 방법론에 능숙한 경험 많은 프로젝트 관리자입니다. 복잡한 프로젝트를 실행 가능한 작업으로 분해하고, 리소스를 효율적으로 배분하며, 리스크를 사전에 식별하여 관리합니다.',
    'gemini-2.5-flash',
    true,
    false,
    3,
    'MetaGPT Stage 3: 프로젝트 계획 및 작업 분해 담당'
) ON CONFLICT (framework, template_name)
DO UPDATE SET
    role = EXCLUDED.role,
    goal_template = EXCLUDED.goal_template,
    backstory_template = EXCLUDED.backstory_template,
    default_llm_model = EXCLUDED.default_llm_model,
    agent_order = EXCLUDED.agent_order,
    updated_at = NOW();

-- Agent 4: Engineer (코드 구현)
INSERT INTO agent_templates (
    framework,
    template_name,
    role,
    goal_template,
    backstory_template,
    default_llm_model,
    is_verbose,
    allow_delegation,
    agent_order,
    description
) VALUES (
    'metagpt',
    'engineer',
    'Engineer',
    '{requirement} 명세에 따라 고품질의 클린 코드를 구현합니다.',
    '당신은 풀스택 개발 경험이 풍부한 시니어 소프트웨어 엔지니어입니다. 클린 코드 원칙, SOLID 원칙, 디자인 패턴을 적용하여 유지보수 가능하고 효율적인 코드를 작성합니다. 코드 리뷰와 리팩토링에도 능숙합니다.',
    'gemini-2.5-flash',
    true,
    false,
    4,
    'MetaGPT Stage 4: 코드 구현 담당'
) ON CONFLICT (framework, template_name)
DO UPDATE SET
    role = EXCLUDED.role,
    goal_template = EXCLUDED.goal_template,
    backstory_template = EXCLUDED.backstory_template,
    default_llm_model = EXCLUDED.default_llm_model,
    agent_order = EXCLUDED.agent_order,
    updated_at = NOW();

-- Agent 5: QA Engineer (품질 보증 및 테스트)
INSERT INTO agent_templates (
    framework,
    template_name,
    role,
    goal_template,
    backstory_template,
    default_llm_model,
    is_verbose,
    allow_delegation,
    agent_order,
    description
) VALUES (
    'metagpt',
    'qa_engineer',
    'QA Engineer',
    '{requirement}의 모든 기능이 제대로 작동하는지 포괄적으로 테스트하고 품질을 보증합니다.',
    '당신은 테스트 자동화와 품질 프로세스 전문가입니다. 단위 테스트, 통합 테스트, E2E 테스트를 설계하고, 버그를 조기에 발견하며, 품질 지표를 관리합니다. 테스트 주도 개발(TDD) 방법론에 정통합니다.',
    'gemini-2.5-flash',
    true,
    false,
    5,
    'MetaGPT Stage 5: 품질 보증 및 테스트 담당'
) ON CONFLICT (framework, template_name)
DO UPDATE SET
    role = EXCLUDED.role,
    goal_template = EXCLUDED.goal_template,
    backstory_template = EXCLUDED.backstory_template,
    default_llm_model = EXCLUDED.default_llm_model,
    agent_order = EXCLUDED.agent_order,
    updated_at = NOW();

-- ==================== 2. TASK TEMPLATES ====================

-- Task 1: 요구사항 분석 및 PRD 작성
INSERT INTO task_templates (
    framework,
    task_type,
    description_template,
    expected_output_template,
    agent_template_name,
    assigned_agent_order,
    depends_on_task_order,
    task_order,
    description,
    display_order
) VALUES (
    'metagpt',
    'requirement_analysis',
    '{requirement}에 대한 상세한 제품 요구사항 문서(PRD)를 작성하세요. 다음을 포함해야 합니다:
1. 프로젝트 개요 및 목표
2. 사용자 페르소나 및 사용 시나리오
3. 기능 요구사항 (Functional Requirements)
4. 비기능 요구사항 (Non-Functional Requirements)
5. 제약사항 및 가정사항
6. 성공 지표 (Success Metrics)',
    '명확하고 구조화된 PRD 문서. 마크다운 형식으로 작성되며, 모든 이해관계자가 이해할 수 있도록 명확하게 작성되어야 합니다.',
    'product_manager',
    1,
    NULL,
    1,
    'Stage 1: 요구사항 분석',
    1
) ON CONFLICT (framework, task_type)
DO UPDATE SET
    description_template = EXCLUDED.description_template,
    expected_output_template = EXCLUDED.expected_output_template,
    agent_template_name = EXCLUDED.agent_template_name,
    assigned_agent_order = EXCLUDED.assigned_agent_order,
    task_order = EXCLUDED.task_order,
    updated_at = NOW();

-- Task 2: 시스템 아키텍처 설계
INSERT INTO task_templates (
    framework,
    task_type,
    description_template,
    expected_output_template,
    agent_template_name,
    assigned_agent_order,
    depends_on_task_order,
    task_order,
    description,
    display_order
) VALUES (
    'metagpt',
    'architecture_design',
    'PRD를 기반으로 시스템 아키텍처를 설계하세요. 다음을 포함해야 합니다:
1. 시스템 구성도 (System Architecture Diagram)
2. 컴포넌트 분해 및 책임 정의
3. 데이터 흐름도 (Data Flow Diagram)
4. 기술 스택 선정 및 근거
5. API 설계 명세
6. 데이터베이스 스키마 설계
7. 보안 및 확장성 고려사항',
    '완전한 시스템 아키텍처 문서. 다이어그램과 함께 각 컴포넌트의 역할, 인터페이스, 데이터 흐름이 명확히 정의되어야 합니다.',
    'architect',
    2,
    1,
    2,
    'Stage 2: 아키텍처 설계',
    2
) ON CONFLICT (framework, task_type)
DO UPDATE SET
    description_template = EXCLUDED.description_template,
    expected_output_template = EXCLUDED.expected_output_template,
    agent_template_name = EXCLUDED.agent_template_name,
    assigned_agent_order = EXCLUDED.assigned_agent_order,
    depends_on_task_order = EXCLUDED.depends_on_task_order,
    task_order = EXCLUDED.task_order,
    updated_at = NOW();

-- Task 3: 프로젝트 계획 수립
INSERT INTO task_templates (
    framework,
    task_type,
    description_template,
    expected_output_template,
    agent_template_name,
    assigned_agent_order,
    depends_on_task_order,
    task_order,
    description,
    display_order
) VALUES (
    'metagpt',
    'project_planning',
    '아키텍처 설계를 기반으로 상세한 프로젝트 계획을 수립하세요. 다음을 포함해야 합니다:
1. 작업 분해 구조 (Work Breakdown Structure)
2. 각 작업의 우선순위 및 의존성
3. 예상 소요 시간 및 일정
4. 리소스 할당 계획
5. 리스크 식별 및 대응 전략
6. 마일스톤 정의',
    '실행 가능한 프로젝트 계획 문서. 개발팀이 즉시 작업을 시작할 수 있도록 구체적이고 명확한 작업 목록과 일정이 포함되어야 합니다.',
    'project_manager',
    3,
    2,
    3,
    'Stage 3: 프로젝트 계획',
    3
) ON CONFLICT (framework, task_type)
DO UPDATE SET
    description_template = EXCLUDED.description_template,
    expected_output_template = EXCLUDED.expected_output_template,
    agent_template_name = EXCLUDED.agent_template_name,
    assigned_agent_order = EXCLUDED.assigned_agent_order,
    depends_on_task_order = EXCLUDED.depends_on_task_order,
    task_order = EXCLUDED.task_order,
    updated_at = NOW();

-- Task 4: 코드 구현
INSERT INTO task_templates (
    framework,
    task_type,
    description_template,
    expected_output_template,
    agent_template_name,
    assigned_agent_order,
    depends_on_task_order,
    task_order,
    description,
    display_order
) VALUES (
    'metagpt',
    'code_implementation',
    '프로젝트 계획에 따라 {requirement}를 구현하세요. 다음 원칙을 따라야 합니다:
1. 클린 코드 원칙 준수
2. SOLID 원칙 적용
3. 적절한 디자인 패턴 사용
4. 코드 주석 및 문서화
5. 에러 핸들링 구현
6. 성능 최적화 고려
7. 코딩 컨벤션 준수',
    '완전히 구현된 소스 코드. 모든 기능이 작동하며, 읽기 쉽고 유지보수 가능한 코드여야 합니다. 각 파일의 역할과 구조가 명확해야 합니다.',
    'engineer',
    4,
    3,
    4,
    'Stage 4: 코드 구현',
    4
) ON CONFLICT (framework, task_type)
DO UPDATE SET
    description_template = EXCLUDED.description_template,
    expected_output_template = EXCLUDED.expected_output_template,
    agent_template_name = EXCLUDED.agent_template_name,
    assigned_agent_order = EXCLUDED.assigned_agent_order,
    depends_on_task_order = EXCLUDED.depends_on_task_order,
    task_order = EXCLUDED.task_order,
    updated_at = NOW();

-- Task 5: 품질 보증 및 테스트
INSERT INTO task_templates (
    framework,
    task_type,
    description_template,
    expected_output_template,
    agent_template_name,
    assigned_agent_order,
    depends_on_task_order,
    task_order,
    description,
    display_order
) VALUES (
    'metagpt',
    'quality_assurance',
    '구현된 코드에 대한 포괄적인 테스트를 수행하세요. 다음을 포함해야 합니다:
1. 단위 테스트 (Unit Tests) 작성 및 실행
2. 통합 테스트 (Integration Tests) 수행
3. E2E 테스트 시나리오 작성 및 실행
4. 성능 테스트 및 벤치마크
5. 보안 취약점 검사
6. 코드 품질 검사 (Linting, Code Coverage)
7. 버그 리포트 및 수정 제안',
    '종합 테스트 보고서. 모든 테스트 결과, 발견된 이슈, 수정 권장사항이 포함되어야 합니다. 제품이 프로덕션 배포 준비가 되었는지 명확한 판단을 제공해야 합니다.',
    'qa_engineer',
    5,
    4,
    5,
    'Stage 5: 품질 보증',
    5
) ON CONFLICT (framework, task_type)
DO UPDATE SET
    description_template = EXCLUDED.description_template,
    expected_output_template = EXCLUDED.expected_output_template,
    agent_template_name = EXCLUDED.agent_template_name,
    assigned_agent_order = EXCLUDED.assigned_agent_order,
    depends_on_task_order = EXCLUDED.depends_on_task_order,
    task_order = EXCLUDED.task_order,
    updated_at = NOW();

-- ==================== 완료 ====================

-- 확인 쿼리
SELECT
    'Agent Templates' as table_name,
    COUNT(*) as count
FROM agent_templates
WHERE framework = 'metagpt'
UNION ALL
SELECT
    'Task Templates' as table_name,
    COUNT(*) as count
FROM task_templates
WHERE framework = 'metagpt';

-- 상세 확인
SELECT
    agent_order,
    role,
    template_name,
    default_llm_model
FROM agent_templates
WHERE framework = 'metagpt'
ORDER BY agent_order;

SELECT
    task_order,
    task_type,
    assigned_agent_order,
    depends_on_task_order
FROM task_templates
WHERE framework = 'metagpt'
ORDER BY task_order;
