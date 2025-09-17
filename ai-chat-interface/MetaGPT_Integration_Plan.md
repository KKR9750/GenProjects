# MetaGPT 통합 계획 문서

## 📋 현재 상황 및 문제점

### 기존 문제
- Flask 화면에서 MetaGPT 로직을 직접 처리
- 단계별 승인 시스템이 없음
- 요구사항 → 분석 → 설계 → 개발 → 테스트의 순차적 워크플로우 부재
- 각 단계별 문서 공유 및 일관성 부족

## 🎯 목표 및 요구사항

### 올바른 워크플로우
1. **📋 요구사항 정리** → 사용자 확인
2. **🔍 프로젝트 분석** → 사용자 확인
3. **🏗️ 시스템 설계** → 사용자 확인
4. **💻 코드 개발** → 사용자 확인
5. **🧪 단위 테스트** → 사용자 확인
6. **📦 최종 결과** → 완료

### 핵심 원칙
- **모듈 분리**: MetaGPT 기능은 실제 MetaGPT 모듈에서 처리
- **인터페이스 역할**: Flask는 단순히 UI/API 인터페이스만 담당
- **단계별 승인**: 각 단계마다 사용자 확인 필요
- **문서 공유**: 각 단계별 결과물이 다음 단계에서 참조됨

## 🏗️ 시스템 아키텍처

### 현재 구조 (문제)
```
Flask App (app.py)
├── UI 처리
├── MetaGPT 로직 처리 ❌ (잘못됨)
├── 단계별 승인 처리 ❌ (잘못됨)
└── 결과 생성 ❌ (잘못됨)
```

### 올바른 구조 (목표)
```
Flask App (app.py)
├── UI 인터페이스 ✅
├── API 엔드포인트 ✅
└── MetaGPT 모듈 호출 ✅

MetaGPT Module (@MetaGPT/)
├── 실제 요구사항 분석 ✅
├── 단계별 처리 로직 ✅
├── 팀원별 작업 수행 ✅
├── 문서 생성 및 공유 ✅
└── 승인 워크플로우 ✅
```

## 📝 구현 계획

### Phase 1: 구조 분리
- [ ] Flask에서 MetaGPT 로직 제거
- [ ] 실제 MetaGPT 모듈 호출 구조 구현
- [ ] API 인터페이스 단순화

### Phase 2: MetaGPT 모듈 확장
- [ ] 단계별 워크플로우 구현
- [ ] 각 단계별 승인 시스템
- [ ] 문서 공유 및 일관성 유지

### Phase 3: 통합 테스트
- [ ] 전체 워크플로우 테스트
- [ ] 사용자 승인 프로세스 검증
- [ ] 문서 일관성 확인

## 🔧 기술적 구현 방안

### Flask App 역할
```python
# Flask는 단순히 인터페이스만
@app.route('/api/metagpt', methods=['POST'])
def handle_metagpt_request():
    """MetaGPT 모듈 호출만"""
    requirement = request.get_json().get('requirement')

    # 실제 MetaGPT 모듈 호출
    result = metagpt_module.start_project(requirement)

    return jsonify(result)

@app.route('/api/metagpt/step', methods=['POST'])
def handle_step_approval():
    """단계별 승인 처리"""
    step_data = request.get_json()

    # MetaGPT 모듈에서 다음 단계 처리
    result = metagpt_module.process_step(step_data)

    return jsonify(result)
```

### MetaGPT 모듈 역할
```python
# MetaGPT 모듈에서 실제 처리
def start_project(requirement):
    """프로젝트 시작 - 1단계 요구사항 정리"""
    requirements_doc = ProductManager.analyze_requirements(requirement)

    return {
        'step': 1,
        'step_name': '요구사항 정리',
        'result': requirements_doc,
        'need_approval': True
    }

def process_step(step_data):
    """단계별 처리"""
    current_step = step_data['current_step']
    user_approval = step_data['user_response']

    if user_approval == '예':
        return proceed_to_next_step(current_step, step_data)
    else:
        return handle_modification(current_step, step_data)
```

## 📊 단계별 문서 공유 방안

### 문서 흐름
```
1단계 요구사항 문서
    ↓ (전달)
2단계 분석 문서 (요구사항 참조)
    ↓ (전달)
3단계 설계 문서 (요구사항 + 분석 참조)
    ↓ (전달)
4단계 구현 코드 (요구사항 + 분석 + 설계 참조)
    ↓ (전달)
5단계 테스트 코드 (모든 이전 단계 참조)
```

### 일관성 유지 방법
- 각 단계에서 이전 단계 문서를 명시적으로 참조
- 수정 시 영향받는 다음 단계들 자동 업데이트
- 단계별 검증 체크리스트

## 🚀 실행 예시

### 사용자 요청: "공학 계산기 프로그램을 만들어줘"

#### 1단계: 요구사항 정리
```
ProductManager 분석 결과:
- 프로젝트명: 공학용 계산기
- 주요 기능: 사칙연산, 과학함수, 단위변환
- 기술스택: Python + tkinter
- 사용자: 공학도, 연구자
```
**사용자 확인**: "맞습니다" → 2단계 진행

#### 2단계: 프로젝트 분석
```
Architect 분석 결과:
- 아키텍처: MVC 패턴
- 핵심 모듈: GUI, Engine, MathFunctions
- 데이터 흐름: 사용자→GUI→Engine→결과
- (1단계 요구사항 문서 참조)
```
**사용자 확인**: "GUI를 더 직관적으로" → 수정 후 3단계 진행

#### 3단계: 시스템 설계
```
설계 결과:
- 클래스 구조: CalculatorGUI, CalculatorEngine
- 파일 구조: main.py, gui.py, engine.py
- (1,2단계 문서 참조하여 설계)
```

## 📅 진행 상황

### 완료된 작업
- [x] 문제점 분석
- [x] 목표 설정
- [x] 아키텍처 설계

### 진행 중인 작업
- [ ] Flask 로직 분리
- [ ] MetaGPT 모듈 호출 구현

### 예정된 작업
- [ ] 단계별 워크플로우 구현
- [ ] 문서 공유 시스템 구현
- [ ] 전체 통합 테스트

## 💡 참고사항

### 기존 MetaGPT 파일 참조
- `@MetaGPT\meta_gpt.py`: Chainlit 기반 고급 워크플로우 예시
- 해당 파일의 단계별 승인 로직을 Flask 환경에 적용

### 추가 고려사항
- 세션 관리: 사용자별 프로젝트 진행 상황 추적
- 오류 처리: 각 단계에서 발생할 수 있는 예외 상황
- 성능 최적화: 대용량 프로젝트 처리 시 응답 시간

---

**문서 생성일**: 2025-09-15
**최종 수정일**: 2025-09-15
**작성자**: Claude Code
**상태**: 진행 중