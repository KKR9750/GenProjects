# AI Chat Interface 관리자 시스템 사용 가이드

## 🛡️ 개요

AI Chat Interface 관리자 시스템은 시스템 모니터링, 프로젝트 관리, LLM 모델 관리, 사용자 관리 등을 포괄하는 통합 관리 플랫폼입니다.

## 🔐 접근 방법

### 관리자 페이지 접속
```
http://localhost:3000/admin
```

### 로그인 정보
- **사용자명**: `admin`
- **패스워드**: 환경변수 `ADMIN_PASSWORD`에 설정된 값 (`.env` 파일 참조)

**⚠️ 보안 중요**: 최초 설정 시 반드시 강력한 비밀번호로 변경하세요!

## 📊 주요 기능

### 1. 시스템 상태 모니터링

#### 📈 실시간 시스템 리소스 모니터링
- **CPU 사용률**: 실시간 CPU 사용량 표시
- **메모리 사용률**: 물리 메모리 사용 현황
- **디스크 사용률**: 저장 공간 사용 상태

#### 🔍 서비스 헬스체크
- **데이터베이스**: Supabase 연결 상태
- **Flask 서버**: 메인 서버 상태
- **WebSocket**: 실시간 통신 상태
- **CrewAI 서비스**: CrewAI 프레임워크 연결 상태
- **MetaGPT 서비스**: MetaGPT 프레임워크 연결 상태

#### 📊 전체 시스템 상태
- **정상 (🟢)**: 모든 서비스가 정상 작동
- **주의 (🟡)**: 일부 서비스에 문제가 있지만 시스템 운영 가능

### 2. 프로젝트 관리

#### 📁 프로젝트 현황 대시보드
- **전체 프로젝트 수**: 생성된 모든 프로젝트 수
- **완료 프로젝트**: 성공적으로 완료된 프로젝트 수
- **진행 중 프로젝트**: 현재 진행 중인 프로젝트 수

#### 📋 프로젝트 목록 관리
각 프로젝트에 대해 다음 정보 표시:
- **프로젝트명**: 사용자가 지정한 프로젝트 이름
- **AI 프레임워크**: CrewAI 또는 MetaGPT
- **상태**: planning, in_progress, completed
- **진행률**: 프로젝트 완료 비율 (0-100%)
- **생성일**: 프로젝트 생성 날짜

#### 🔧 프로젝트 관리 액션
- **완료 처리**: 진행 중인 프로젝트를 강제로 완료 상태로 변경

### 3. LLM 모델 관리

#### 🤖 지원 LLM 모델 현황
12개의 주요 LLM 모델 지원:

**OpenAI 모델**
- GPT-4: 범용 고성능 모델
- GPT-4o: 멀티모달 최신 모델

**Anthropic 모델**
- Claude-3 Sonnet: 추론 특화 모델
- Claude-3 Haiku: 빠른 응답 모델

**Google 모델**
- Gemini Pro: 멀티모달 모델
- Gemini Ultra: 최고 성능 모델

**Meta 모델**
- Llama-3 70B: 오픈소스 모델
- Llama-3 8B: 경량 오픈소스 모델
- Code Llama: 코드 생성 특화

**기타 모델**
- Mistral Large: 효율성 중심 모델
- Mistral 7B: 경량 효율 모델
- DeepSeek Coder: 코딩 전문 모델

#### 📊 모델 사용 통계
- **사용 횟수**: 각 모델이 프로젝트에서 사용된 횟수
- **활성 상태**: 모델의 현재 활성화 상태

### 4. 설정 관리
- 시스템 설정 기능 (개발 중)

## 🔧 API 엔드포인트

### 인증 API
```bash
# 로그인
POST /api/admin/login
Content-Type: application/json
{
  "username": "admin",
  "password": "your-password-from-env"
}

# 토큰 검증
GET /api/admin/verify
Authorization: Bearer <token>

# 로그아웃
POST /api/admin/logout
Authorization: Bearer <token>
```

### 시스템 모니터링 API
```bash
# 시스템 상태 조회
GET /api/admin/system/status
Authorization: Bearer <token>

# 헬스체크
GET /api/admin/system/health
Authorization: Bearer <token>
```

### 프로젝트 관리 API
```bash
# 모든 프로젝트 조회
GET /api/admin/projects
Authorization: Bearer <token>

# 프로젝트 강제 완료
PUT /api/admin/projects/{project_id}/force-complete
Authorization: Bearer <token>
```

### LLM 모델 관리 API
```bash
# LLM 모델 목록 및 사용 통계
GET /api/admin/llm-models
Authorization: Bearer <token>
```

## 🚀 시작하기

### 1. 관리자 페이지 접속
브라우저에서 `http://localhost:3000/admin`으로 접속

### 2. 로그인
- 사용자명: `admin`
- 패스워드: 환경변수 `ADMIN_PASSWORD`에 설정된 값

### 3. 대시보드 탐색
- **시스템 상태**: 실시간 시스템 모니터링
- **프로젝트 관리**: 생성된 프로젝트 관리
- **LLM 관리**: 모델 현황 및 사용 통계
- **설정**: 시스템 설정 (개발 예정)

## 🔒 보안 기능

### JWT 토큰 기반 인증
- 24시간 유효한 JWT 토큰 사용
- 자동 토큰 만료 처리
- 권한 기반 접근 제어

### 패스워드 보안
- SHA256 해시 기반 패스워드 저장
- 환경변수를 통한 보안 키 관리

### API 보안
- Bearer 토큰 검증
- 권한별 API 접근 제어
- CORS 정책 적용

## 🛠️ 기술 스택

### Frontend
- **React.js**: 사용자 인터페이스
- **Axios**: HTTP 클라이언트
- **Chart.js**: 데이터 시각화 (준비됨)

### Backend
- **Flask**: Python 웹 프레임워크
- **PyJWT**: JWT 토큰 처리
- **psutil**: 시스템 모니터링
- **Supabase**: 데이터베이스 연동

### 보안
- **JWT**: 토큰 기반 인증
- **Flask-CORS**: 교차 도메인 요청 처리
- **환경변수**: 민감 정보 보호

## 📈 향후 개발 계획

### 단기 계획
- **사용자 관리**: 다중 사용자 지원
- **활동 로그**: 사용자 활동 기록 및 분석
- **시스템 설정**: 고급 설정 관리 인터페이스

### 장기 계획
- **대시보드 커스터마이징**: 개인화된 대시보드
- **알림 시스템**: 시스템 이벤트 알림
- **백업/복원**: 데이터 백업 및 복원 기능
- **API 사용량 모니터링**: LLM API 사용량 추적

## 🐛 문제 해결

### 로그인 실패
- 사용자명과 패스워드 확인
- 환경변수 `ADMIN_PASSWORD`가 올바르게 설정되었는지 확인

### 시스템 상태 오류
- 데이터베이스 연결 확인: Supabase 설정 점검
- 서비스 연결 확인: CrewAI/MetaGPT 서비스 실행 상태

### API 접근 오류
- JWT 토큰 만료 확인 (24시간)
- Authorization 헤더 형식 확인: `Bearer <token>`

## 📞 지원

시스템 문제나 기능 요청이 있을 경우, 개발팀에 문의하시기 바랍니다.

**시스템 위치**: `D:\GenProjects\ai-chat-interface\`
**접속 URL**: `http://localhost:3000/admin`
**개발 환경**: React.js + Flask + Supabase