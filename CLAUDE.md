# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소의 코드 작업을 할 때 필요한 가이드를 제공합니다.

> 📈 **프로젝트 현황**: 개발 진행 상황은 [PROJECT_STATUS.md](ai-chat-interface/PROJECT_STATUS.md)를 참조하세요.

---

## 프로젝트 개요

### 📚 문서 관리 체계
이 문서는 **"어떻게"** 개발하는지에 대한 기술적 가이드를 제공합니다.
- **CLAUDE.md** (현재 문서): 개발 명령어, 아키텍처 패턴, API 참조, 개발 가이드라인
- **PROJECT_STATUS.md**: **"무엇을"** 개발했는지에 대한 프로젝트 진행 상황 및 완료된 기능

GenProjects는 세 가지 통합 시스템으로 구성된 포괄적인 AI 개발 툴킷입니다:

1. **AI Chat Interface**: CrewAI와 MetaGPT 프레임워크를 통합하는 웹 플랫폼
2. **CrewAI**: 다중 역할 작업 실행을 위한 협업 AI 에이전트 시스템
3. **MetaGPT**: 소프트웨어 회사 워크플로우를 시뮬레이션하는 멀티 에이전트 프레임워크

메인 진입점은 AI Chat Interface로, 전용 UI 인터페이스를 통해 CrewAI와 MetaGPT를 조율하는 단일 Flask 서버(포트 3000)를 제공합니다.

## 개발 명령어

### AI Chat Interface (주요 시스템)

#### 설정 및 설치
```bash
# 메인 인터페이스로 이동
cd ai-chat-interface/

# Python 종속성 설치
pip install -r requirements.txt

# 필수 패키지: Flask==2.3.3, Flask-CORS==4.0.0, requests==2.31.0, python-dotenv==1.0.0
```

#### 서버 실행
```bash
# 방법 1: 시작 스크립트 사용 (권장)
python start.py

# 방법 2: 직접 실행
python app.py

# 서버는 http://localhost:3000 에서 실행됩니다
```

#### 인터페이스 접근 지점
```bash
# 메인 대시보드 (통합 인터페이스)
http://localhost:3000/

# CrewAI 전용 인터페이스 (보라색 테마)
http://localhost:3000/crewai

# MetaGPT 전용 인터페이스 (녹색 테마)
http://localhost:3000/metagpt
```

#### 상태 확인
```bash
# 전체 시스템 상태 확인
curl http://localhost:3000/api/health

# CrewAI와 MetaGPT 서비스 상태 반환
```

### 개별 프레임워크 명령어

#### CrewAI 플랫폼
```bash
cd CrewAi/crewai_platform/
python server.py  # 포트 5000에서 실행
```

#### MetaGPT
```bash
cd MetaGPT/
metagpt "Create a 2048 game"  # CLI 사용
python run_metagpt.py         # 대화형 모드
```

## 아키텍처 개요

### 통합 Flask 서버 (`ai-chat-interface/app.py`)
- **단일 진입점**: 포트 3000에서 모든 인터페이스 제공
- **내부 라우팅**: CrewAI(포트 5000)와 MetaGPT(포트 8000)로 프록시
- **정적 파일 서빙**: HTML, CSS, JS 직접 제공
- **서비스 검색**: 프레임워크 가용성 자동 감지

### 다중 프레임워크 통합
```
┌─────────────────────────────────────┐
│       웹 브라우저 (포트 3000)        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      Flask 통합 서버                │
│  ┌─────────────┐ ┌─────────────────┐│
│  │ 정적 파일   │ │ API 라우터      ││
│  │ 서빙        │ │ & 프록시        ││
│  └─────────────┘ └─────────────────┘│
└─────────┬───────────────┬───────────┘
          │               │
┌─────────▼──────┐ ┌──────▼──────────┐
│ CrewAI 서버    │ │ MetaGPT 로컬    │
│ (포트 5000)    │ │ 스크립트 실행   │
│ [선택사항]     │ │                 │
└────────────────┘ └─────────────────┘
```

### UI 컴포넌트 아키텍처

#### 프레임워크별 인터페이스
- **CrewAI 인터페이스**: 3개 협업 역할 (연구원, 작성자, 기획자)
- **MetaGPT 인터페이스**: 5단계 소프트웨어 개발 프로세스 (PM → 설계자 → PM → 엔지니어 → QA)
- **통합 대시보드**: 시스템 개요 및 프레임워크 선택

#### React.js 프론트엔드 컴포넌트
```javascript
// 각 프레임워크의 핵심 UI 패턴
const FrameworkInterface = () => {
    const [selectedRole, setSelectedRole] = useState();
    const [roleLLMMapping, setRoleLLMMapping] = useState({});
    const [messages, setMessages] = useState([]);
    const [activeProject, setActiveProject] = useState(null);
    // 프레임워크별 로직...
};
```

### LLM 모델 관리 시스템

#### 프레임워크별 지원 모델
```javascript
// 두 프레임워크에서 지원하는 12개 LLM 모델
const llmOptions = [
    { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
    { id: 'claude-3', name: 'Claude-3 Sonnet', provider: 'Anthropic' },
    { id: 'deepseek-coder', name: 'DeepSeek Coder', provider: 'DeepSeek' },
    // ... 9개 추가 모델
];
```

#### 역할-LLM 매핑 전략
- **CrewAI**: 역할별 독립적인 LLM 선택 (연구원, 작성자, 기획자)
- **MetaGPT**: 단계별 LLM 최적화 (PM: GPT-4, 엔지니어: DeepSeek Coder 등)
- **동적 전환**: 대화별 실시간 모델 변경

## API 엔드포인트

### 상태 및 헬스체크
```
GET /api/health                    # 시스템 상태 확인
GET /api/services/status           # 서비스 가용성 확인
```

### CrewAI 통합
```
POST /api/crewai                   # CrewAI 요청 처리
GET /api/crewai/projects          # 프로젝트 목록
POST /api/services/crewai/start    # CrewAI 서비스 시작
```

### MetaGPT 통합
```
POST /api/metagpt                  # MetaGPT 요청 처리
GET /api/execution/<id>/status     # 실행 상태 추적
```

### 정적 리소스
```
GET /<filename>                    # 정적 파일 제공 (HTML, CSS, JS)
GET /crewai                       # CrewAI 인터페이스
GET /metagpt                      # MetaGPT 인터페이스
```

## 주요 파일 및 구조

### 핵심 통합 파일
- **`ai-chat-interface/app.py`**: 모든 프레임워크를 조율하는 메인 Flask 서버
- **`ai-chat-interface/start.py`**: 서비스 초기화가 포함된 서버 시작 스크립트
- **`requirements.txt`**: 통합 서버를 위한 Python 종속성

### 프레임워크별 UI
- **`dashboard.{html,js,css}`**: 통합 시스템 대시보드
- **`crewai.{html,js,css}`**: CrewAI 전용 인터페이스 (보라색 테마)
- **`metagpt.{html,js,css}`**: MetaGPT 전용 인터페이스 (녹색 테마)

### 브리지 컴포넌트
- **`metagpt_bridge.py`**: MetaGPT 로컬 실행 래퍼
- **`metagpt_simple.py`**: 단순화된 MetaGPT 상호작용 레이어

### 레거시 컴포넌트
- **`app_simple.js`**: 원본 통합 인터페이스 (프레임워크별 UI로 대체됨)
- **`app_*.js`**: 메인 인터페이스의 개발 반복판

## 개발 가이드라인

### 새로운 프레임워크 통합 추가
1. 기존 패턴을 따라 전용 `{framework}.{html,js,css}` 파일 생성
2. 새 프레임워크 엔드포인트용 `app.py`에 라우팅 추가
3. 헬스 엔드포인트에서 서비스 상태 확인 구현
4. 프레임워크별 API 프록시 로직 추가

### UI 개발 패턴
- 각 프레임워크는 일관된 상태 관리 패턴을 가진 React.js 사용
- 색상 테마: CrewAI (보라색: #4F46E5), MetaGPT (녹색: #059669)
- 모바일/데스크톱 호환성을 가진 반응형 디자인
- 실시간 연결 상태 모니터링

### 서비스 통합
- 프레임워크 서비스는 독립적으로 실행 (CrewAI: 포트 5000, MetaGPT: 포트 8000)
- Flask 서버는 통합 접근점 제공 및 서비스 검색 처리
- 개별 프레임워크를 사용할 수 없을 때 우아한 성능 저하
- 장시간 실행되는 MetaGPT 프로세스의 백그라운드 실행 추적

## 구성 관리

### 환경 설정
- 모든 컴포넌트에 Python 3.9+ 필요
- Node.js 선택사항 (Playwright 브라우저 자동화만 해당)
- 크로스 플랫폼 지원 (Windows/Linux 경로 자동 처리)

### 서비스 종속성
- **CrewAI**: 전체 기능을 위해 별도 서버 시작 필요
- **MetaGPT**: 로컬 Python 스크립트로 실행, 별도 서버 불필요
- **LLM API**: 프레임워크 요구사항별 API 키 구성

### 경로 구성
시스템이 자동으로 경로를 감지하고 구성합니다:
```python
# app.py에서 자동 경로 해석
crewai_path = os.path.join(os.path.dirname(current_dir), 'CrewAi')
metagpt_path = os.path.join(os.path.dirname(current_dir), 'MetaGPT')
```

## 테스트 및 디버깅

### 로컬 개발
- 전체 통합 테스트를 위해 `python start.py` 사용
- 각각의 서버를 통한 개별 프레임워크 테스트
- 프론트엔드 디버깅을 위한 브라우저 개발자 도구

### 서비스 상태 확인
```bash
# 모든 서비스가 응답하는지 확인
curl http://localhost:3000/api/health

# 개별 서비스 테스트
curl http://localhost:5000/api/projects  # CrewAI
python MetaGPT/run_metagpt.py           # MetaGPT
```

### 일반적인 문제
- **포트 충돌**: 포트 3000, 5000, 8000이 사용 가능한지 확인
- **경로 해석**: 프레임워크 디렉터리는 ai-chat-interface와 형제여야 함
- **LLM API 키**: 프레임워크 문서별 구성

## 통합 지점

### 데이터 플로우
1. 사용자가 포트 3000의 통합 대시보드에 접근
2. 특정 프레임워크 인터페이스 선택 (CrewAI 또는 MetaGPT)
3. 역할별 LLM 모델 구성
4. 프레임워크별 API를 통해 요청 제출
5. Flask 서버가 적절한 백엔드 서비스로 라우팅
6. 프레임워크 테마 인터페이스에서 결과 표시

### 공유 컴포넌트
- **LLM 모델 선택**: 두 프레임워크에서 일관성 유지
- **프로젝트 관리**: 통합 프로젝트 추적 및 상태
- **실시간 업데이트**: 장시간 작업을 위한 WebSocket 스타일 통신
- **테마 시스템**: 프레임워크별 시각적 브랜딩

시스템은 확장성을 위해 설계되었습니다 - 전용 UI 컴포넌트, Flask 라우팅, 서비스 상태 관리의 기존 패턴을 따라 새로운 AI 프레임워크를 통합할 수 있습니다.