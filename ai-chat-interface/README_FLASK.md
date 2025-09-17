# AI Chat Interface - Flask 통합 서버

Python Flask 기반으로 통일된 AI Chat Interface 서버입니다.

## 주요 변경사항

### 🔄 환경 통일
- **이전**: Node.js Express (포트 3000) + Python Flask (포트 5000)
- **현재**: Python Flask 단일 서버 (포트 3000)

### 📁 파일 구조
```
ai-chat-interface/
├── app.py              # Flask 메인 서버
├── start.py            # 서버 시작 스크립트
├── requirements.txt    # Python 종속성
├── README_FLASK.md     # 이 파일
├── index.html          # 프론트엔드 메인 페이지
├── app.js              # React 프론트엔드 로직
├── styles.css          # 스타일
└── metagpt_simple.py   # MetaGPT 연결 스크립트
```

## 🚀 실행 방법

### 1. Python 환경 준비
```bash
# Python 3.9+ 필요
python --version

# 종속성 설치
pip install -r requirements.txt
```

### 2. 서버 시작
```bash
# 방법 1: 시작 스크립트 사용 (권장)
python start.py

# 방법 2: 직접 실행
python app.py
```

### 3. 브라우저에서 접속
```
http://localhost:3000
```

## 🔗 API 엔드포인트

### 기본 엔드포인트
- `GET /` - 메인 페이지
- `GET /api/health` - 헬스 체크
- `GET /api/services/status` - 서비스 상태 확인

### AI 처리 엔드포인트
- `POST /api/crewai` - CrewAI 요청 처리
- `POST /api/metagpt` - MetaGPT 요청 처리
- `GET /api/execution/<id>/status` - 실행 상태 조회

### 서비스 관리 엔드포인트
- `POST /api/services/crewai/start` - CrewAI 서비스 시작

## 🔧 통합 기능

### CrewAI 연결
- CrewAI 서버가 실행 중이면 직접 연결 (포트 5000)
- 실행되지 않은 경우 시뮬레이션 모드로 응답
- 자동 서비스 상태 감지

### MetaGPT 연결
- 로컬 MetaGPT 스크립트 실행
- 백그라운드 실행 및 상태 추적
- 실행 결과 실시간 조회

## 🏗️ 아키텍처

```
┌─────────────────────────────────────┐
│        웹 브라우저 (포트 3000)        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│       Flask 통합 서버 (포트 3000)    │
│  ┌─────────────┐ ┌─────────────────┐│
│  │ 정적 파일   │ │ API 라우터      ││
│  │ 서빙        │ │ 및 프록시       ││
│  └─────────────┘ └─────────────────┘│
└─────────┬───────────────┬───────────┘
          │               │
┌─────────▼──────┐ ┌──────▼──────────┐
│ CrewAI 서버    │ │ MetaGPT 로컬    │
│ (포트 5000)    │ │ 스크립트 실행   │
│ [선택적 실행]  │ │                 │
└────────────────┘ └─────────────────┘
```

## 🎯 장점

### 환경 통일
- ✅ 단일 Python 환경
- ✅ 동일한 종속성 관리
- ✅ 통합된 로깅 및 모니터링

### 운영 편의성
- ✅ 단일 포트 (3000)
- ✅ 자동 서비스 감지
- ✅ 통합 헬스 체크

### 개발 효율성
- ✅ 코드 재사용성 증가
- ✅ 디버깅 용이성
- ✅ 배포 단순화

## 🔄 마이그레이션 가이드

### 기존 Node.js 서버에서 변경된 점
1. **서버 런타임**: Node.js → Python Flask
2. **종속성 관리**: package.json → requirements.txt
3. **실행 명령**: `npm start` → `python start.py`
4. **API 응답**: 동일한 JSON 구조 유지

### 호환성
- 프론트엔드 코드는 변경 없음
- API 엔드포인트 경로 동일
- 응답 형식 호환성 유지

## 🚨 문제 해결

### 포트 충돌
```bash
# 포트 3000이 사용 중인 경우
netstat -ano | findstr :3000
taskkill /PID <PID번호> /F
```

### 종속성 문제
```bash
# 가상환경 생성 (권장)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 종속성 재설치
pip install -r requirements.txt
```

### CrewAI 연결 실패
```bash
# CrewAI 서버 수동 시작
cd ../CrewAi/crewai_platform
python server.py
```

## 📝 로그 확인

서버 실행 시 다음과 같은 정보가 출력됩니다:
- 서비스 상태 (CrewAI, MetaGPT)
- API 요청 로그
- 에러 메시지 및 스택 트레이스