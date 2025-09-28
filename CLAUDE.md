# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소의 코드 작업을 할 때 필요한 가이드를 제공합니다.

> 📈 **프로젝트 현황**: 개발 진행 상황은 [PROJECT_STATUS.md](ai-chat-interface/PROJECT_STATUS.md)를 참조하세요.

---

## 📋 프로젝트 개요

### 📚 문서 관리 체계
- **CLAUDE.md** (현재 문서): **"어떻게"** 개발하는지에 대한 기술적 가이드 및 개발 명령어
- **PROJECT_STATUS.md**: **"무엇을"** 개발했는지에 대한 프로젝트 진행 상황 및 완료된 기능

**GenProjects**는 AI 프로그램 생성을 위한 포괄적인 통합 플랫폼입니다:

1. **AI Chat Interface** (메인 시스템): Flask 서버(포트 3000)로 모든 AI 프레임워크를 통합 관리
2. **CrewAI**: 3역할 협업 AI 에이전트 시스템 (Researcher, Writer, Planner)
3. **MetaGPT**: 5단계 소프트웨어 개발 프로세스 (PM → Architect → PM → Engineer → QA)

### 🎯 핵심 특징
- **프로젝트 템플릿 시스템**: 5개 사전 정의 템플릿 (웹앱, 모바일앱, API 서버, 데이터 분석, ML)
- **자동 실행 연동**: 템플릿 선택 → 프로젝트 생성 → AI 실행 자동 시작
- **실시간 모니터링**: WebSocket 기반 실시간 진행 상황 추적
- **통합 프로젝트 관리**: 생성된 모든 프로젝트 통합 대시보드
- **12개 LLM 모델 지원**: 역할별 최적화된 LLM 매핑
- **승인 워크플로우**: 사전 분석 및 단계별 승인 시스템
- **지능형 라우팅**: 메시지 분류 및 최적 프레임워크 자동 선택
- **다국어 지원**: UTF-8 한글 완벽 지원 및 국제화 대응

## 🚀 주요 실행 명령어

### 메인 서버 실행
```bash
cd ai-chat-interface/
python start.py                    # 포트 3000
```

### 접근 지점
```bash
http://localhost:3000/                # 통합 대시보드
http://localhost:3000/crewai          # CrewAI 전용 인터페이스 (보라색 테마)
http://localhost:3000/metagpt         # MetaGPT 전용 인터페이스 (녹색 테마)
http://localhost:3000/templates       # 프로젝트 템플릿 선택
http://localhost:3000/projects        # 프로젝트 관리 대시보드
```

### 상태 확인
```bash
curl http://localhost:3000/api/health        # 시스템 상태
curl http://localhost:3000/api/templates/    # 템플릿 목록
curl http://localhost:3000/api/projects      # 생성된 프로젝트 목록
```

## 🏗️ 아키텍처

### 시스템 아키텍처
```
┌─────────────────────────────────────┐
│       웹 브라우저 (포트 3000)        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      Flask 통합 서버                │
│  ┌─────────────┐ ┌─────────────────┐│
│  │ 템플릿 시스템│ │ 프로젝트 관리   ││
│  │ 실시간 통신 │ │ 자동 실행       ││
│  └─────────────┘ └─────────────────┘│
└─────────┬───────────────┬───────────┘
          │               │
┌─────────▼──────┐ ┌──────▼──────────┐
│ CrewAI 서버    │ │ MetaGPT 로컬    │
│ (포트 3001)    │ │ 실행 환경       │
└────────────────┘ └─────────────────┘
          │               │
┌─────────▼───────────────▼───────────┐
│     D:\GenProjects\Projects\        │
│     (생성된 프로젝트 저장소)          │
└─────────────────────────────────────┘
```

### 데이터 플로우
```
템플릿 선택 → 프로젝트 생성 → 자동 실행 시작 → 실시간 모니터링 → 결과 저장
```

## 📁 핵심 파일 구조

```
ai-chat-interface/
├── 🚀 서버 시스템
│   ├── app.py                          # 메인 Flask 통합 서버
│   ├── start.py                        # 서버 실행 스크립트
│   └── app_websocket_enhanced.py       # WebSocket 실시간 통신
├── 📋 프로젝트 관리
│   ├── project_template_system.py      # 템플릿 관리 시스템
│   ├── project_initializer.py          # 프로젝트 초기화 (D:\GenProjects\Projects\ 저장)
│   ├── enhanced_project_initializer.py # 강화된 프로젝트 초기화
│   ├── project_executor.py             # 자동 실행 시스템
│   ├── project_state_manager.py        # 프로젝트 상태 관리
│   └── template_api_routes.py          # 템플릿 API 라우트
├── 🎯 사용자 인터페이스
│   ├── dashboard.{html,js,css}         # 통합 대시보드
│   ├── crewai.{html,js,css}           # CrewAI 전용 인터페이스 (보라색)
│   ├── metagpt.{html,js,css}          # MetaGPT 전용 인터페이스 (녹색)
│   ├── templates.html                  # 프로젝트 템플릿 선택
│   ├── projects.html                   # 프로젝트 관리 대시보드
│   └── admin.html                      # 관리자 대시보드
├── 🔧 유틸리티 및 지능형 시스템
│   ├── error_handler.py               # 지능형 에러 처리
│   ├── realtime_progress_tracker.py   # 실시간 진행 추적
│   ├── websocket_manager.py           # WebSocket 연결 관리
│   ├── pre_analysis_service.py        # 사전 분석 서비스
│   ├── approval_workflow.py           # 승인 워크플로우 관리
│   ├── message_classifier.py          # 메시지 분류기
│   └── enhanced_crewai_executor.py    # 강화된 CrewAI 실행기
├── 📊 데이터베이스 (Supabase 통합)
│   ├── database.py                    # ORM 및 CRUD
│   ├── setup_database.sql             # 핵심 스키마
│   ├── approval_tables_update.sql     # 승인 시스템 스키마
│   └── security_utils.py              # 보안 및 검증
└── 🛡️ 관리자 시스템
    ├── admin_api.py                   # 관리자 API
    └── admin_auth.py                  # 관리자 인증
```

## 🎯 주요 특징

### 완성된 핵심 시스템
- **프로젝트 템플릿 시스템**: 5개 사전 정의 템플릿으로 즉시 시작
- **자동 실행 연동**: 템플릿 선택 후 AI 프레임워크 자동 실행
- **실시간 모니터링**: WebSocket 기반 실시간 진행 상황 추적
- **통합 프로젝트 관리**: 생성된 모든 프로젝트 통합 대시보드
- **지능형 에러 처리**: 사용자 친화적 에러 메시지 및 복구 가이드
- **승인 워크플로우**: LLM 기반 사전 분석 및 단계별 승인 시스템
- **메시지 분류**: 사용자 요청 의도 자동 분류 및 최적 라우팅
- **관리자 시스템**: JWT 인증 기반 통합 시스템 관리 대시보드

### LLM 및 AI 시스템
- **12개 LLM 모델 지원**: GPT-4, Claude-3, DeepSeek Coder, Gemini Pro 등
- **역할별 LLM 매핑**: 각 역할마다 최적화된 모델 선택
- **프레임워크별 특화**: CrewAI(3역할 협업), MetaGPT(5단계 워크플로우)
- **프레임워크별 테마**: 보라색(CrewAI), 녹색(MetaGPT)

### 기술적 특징
- **단일 포트 통합**: 포트 3000에서 모든 서비스 제공
- **크로스 플랫폼**: Windows/Linux 자동 경로 처리
- **프로젝트 저장**: D:\GenProjects\Projects\ 통합 저장
- **Supabase 통합**: PostgreSQL 기반 완전한 데이터베이스 시스템

## 🔧 주요 API 엔드포인트

### 시스템 상태 및 관리
```
GET /api/health                     # 시스템 상태 확인
GET /api/services/status             # 서비스 가용성 확인
```

### 프로젝트 템플릿 시스템
```
GET /api/templates/                  # 모든 템플릿 조회
GET /api/templates/featured          # 추천 템플릿
GET /api/templates/search?q=웹앱     # 템플릿 검색
GET /api/templates/{id}              # 특정 템플릿 상세
POST /api/templates/{id}/create-project  # 템플릿으로 프로젝트 생성
```

### 프로젝트 관리 및 실행
```
GET /api/templates/projects          # 생성된 프로젝트 목록
GET /api/templates/projects/{id}     # 프로젝트 상태 조회
POST /api/templates/projects/{id}/execute      # 프로젝트 실행 시작
GET /api/templates/projects/{id}/execution/status  # 실행 상태 확인
POST /api/templates/projects/{id}/execution/cancel # 실행 취소
```

### AI 프레임워크 연동
```
POST /api/crewai                     # CrewAI 요청 처리
POST /api/metagpt                    # MetaGPT 요청 처리
POST /api/services/crewai/start      # CrewAI 서비스 시작
```

### 승인 워크플로우 및 분석
```
POST /api/pre-analysis               # 사전 분석 요청
GET /api/approval/{id}               # 승인 상태 조회
POST /api/approval/{id}/approve      # 승인 처리
POST /api/approval/{id}/reject       # 거부 처리
POST /api/classify                   # 메시지 분류
```

### 관리자 시스템
```
POST /api/admin/auth/login           # 관리자 로그인
GET /api/admin/system/status         # 시스템 상태 조회
GET /api/admin/projects              # 전체 프로젝트 관리
GET /api/admin/users                 # 사용자 관리
```

## 🛠️ 개발 패턴

### 프로젝트 생성 워크플로우
1. **템플릿 선택** (`/templates`) → 사용자가 프로젝트 유형 선택
2. **프로젝트 초기화** (`project_initializer.py`) → D:\GenProjects\Projects\{project_id}\ 생성
3. **자동 실행** (`project_executor.py`) → AI 프레임워크 자동 시작
4. **실시간 모니터링** (WebSocket) → 진행 상황 실시간 추적
5. **결과 관리** (`/projects`) → 생성된 프로젝트 통합 관리

### 새로운 템플릿 추가
1. `project_template_system.py`에 새 템플릿 정의
2. 프로젝트 유형별 LLM 매핑 설정
3. `templates.html`에 UI 카드 추가
4. 템플릿별 실행 스크립트 생성 로직 구현

### 새로운 AI 프레임워크 추가
1. `{framework}.{html,js,css}` 전용 인터페이스 생성
2. `app.py`에 라우팅 및 API 프록시 추가
3. `project_initializer.py`에 초기화 로직 추가
4. `project_executor.py`에 실행 로직 추가
5. 헬스 체크 및 상태 모니터링 구현

### UI 개발 가이드라인
- **React.js 기반**: 상태 관리 및 컴포넌트 구조
- **프레임워크별 테마**: 고유 색상 및 브랜딩
- **반응형 디자인**: 모바일/데스크톱 호환
- **실시간 업데이트**: WebSocket 연동 필수
- **사용자 경험**: 직관적인 워크플로우 설계

## 🔍 문제 해결

### ✅ 해결된 주요 문제들
- ✅ **포트 통합**: 단일 포트 3000으로 모든 서비스 통합 완료
- ✅ **경로 처리**: 크로스 플랫폼 자동 경로 처리 구현
- ✅ **에러 처리**: 지능형 에러 분석 및 자동 복구 시스템
- ✅ **템플릿 시스템**: 완전 자동화된 프로젝트 생성 및 실행
- ✅ **한글 지원**: UTF-8 인코딩 완벽 지원 및 다국어 대응

### 현재 알려진 문제
- **LLM API 키**: 각 프레임워크별 환경변수 설정 필요 (사용자 설정)
- **승인 대기**: 장시간 승인 대기 시 자동 만료 (24시간)

### 디버깅 도구
```bash
# 시스템 상태 확인
curl http://localhost:3000/api/health

# 템플릿 시스템 확인
curl http://localhost:3000/api/templates/

# 프로젝트 목록 확인
curl http://localhost:3000/api/templates/projects

# 실행 상태 확인
curl http://localhost:3000/api/templates/projects/{project_id}/execution/status
```

### 개발 환경 설정
```bash
# 필수 패키지 설치
pip install -r ai-chat-interface/requirements.txt

# 환경 변수 설정 (.env 파일)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key

# 개발 서버 실행 (핫 리로드)
cd ai-chat-interface/
python start.py
```

**핵심**: 프로젝트 템플릿 기반 AI 프로그램 자동 생성 및 관리 플랫폼