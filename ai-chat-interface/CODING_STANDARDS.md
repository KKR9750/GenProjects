# 코딩 표준 및 정책 문서

## 🚫 임시코드 및 더미데이터 금지 정책

### 🔴 절대 금지 사항 (Zero Tolerance)

#### 1. **임시 로직 (Temporary Logic)**
❌ **금지**: 임시/임시적/temporary 등의 주석이나 변수명
```python
# 임시로 모든 사용자에게 관리자 권한 부여
if user_authenticated:
    user.role = "admin"  # 임시
```

✅ **올바른 방법**: 명확한 비즈니스 로직 구현
```python
# 사용자 역할 기반 권한 부여
user_role = auth_service.get_user_role(user_id)
if auth_service.has_admin_permission(user_role):
    user.role = user_role
```

#### 2. **더미 데이터 (Dummy Data)**
❌ **금지**: 하드코딩된 테스트/더미 데이터
```python
def _create_dummy_analysis(self, request):
    return {
        "status": "success",
        "data": "더미 분석 결과"
    }
```

✅ **올바른 방법**: 실제 데이터 처리 또는 명확한 에러 처리
```python
def analyze_request(self, request):
    if not self.api_service.is_available():
        raise ServiceUnavailableError("분석 서비스를 사용할 수 없습니다")

    return self.api_service.process_analysis(request)
```

#### 3. **시뮬레이션 로직 (Simulation Logic)**
❌ **금지**: 실제 기능 대신 가짜 응답
```python
def call_llm_api(self, prompt):
    # 시뮬레이션: 실제 API 대신 가짜 응답
    return "시뮬레이션된 LLM 응답"
```

✅ **올바른 방법**: 실제 API 호출 또는 적절한 에러 처리
```python
def call_llm_api(self, prompt):
    if not self.api_key:
        raise ConfigurationError("LLM API 키가 설정되지 않았습니다")

    response = requests.post(self.endpoint,
                           headers={"Authorization": f"Bearer {self.api_key}"},
                           json={"prompt": prompt})

    if response.status_code != 200:
        raise APIError(f"LLM API 호출 실패: {response.status_code}")

    return response.json()
```

#### 4. **모든 상황에서 임시/더미/시뮬레이션 절대 금지 (ZERO TOLERANCE)**
❌ **절대 금지**: 어떤 이유든 임시/더미/시뮬레이션 데이터 사용
**금지 예시들:**
```python
# 에러 숨기기 - 절대 금지!
try:
    result = api.call()
except Exception:
    return {"status": "success", "data": "임시 응답"}

# 데이터 없을 때 가짜 데이터 - 절대 금지!
def get_stats():
    if not has_data():
        return {"users": 100, "projects": 50}  # 가짜 데이터

# 기능 미구현 시 시뮬레이션 - 절대 금지!
def complex_calculation():
    return 42  # 실제 계산 대신 임의 값

# 테스트용 더미 응답 - 절대 금지!
def process_payment():
    return {"transaction_id": "DUMMY_12345", "status": "success"}

# API 실패 시 가짜 성공 - 절대 금지!
def send_email():
    try:
        email_service.send()
    except:
        return True  # 실패를 성공으로 위장
```

✅ **올바른 방법들:**
```python
# 에러는 명확하게 전파
try:
    result = api.call()
except APIError as e:
    logger.error(f"API 호출 실패: {e}")
    raise ServiceUnavailableError("서비스를 사용할 수 없습니다")

# 데이터 없음은 명시적으로 표현
def get_stats():
    stats = database.get_user_stats()
    if not stats:
        return {"users": 0, "projects": 0, "last_updated": None}
    return stats

# 미구현 기능은 예외 발생
def complex_calculation():
    raise NotImplementedError("복잡한 계산 기능이 아직 구현되지 않았습니다")

# 실제 기능 구현 또는 명확한 실패
def process_payment(amount, card_info):
    if not payment_service.is_available():
        raise PaymentServiceError("결제 서비스에 연결할 수 없습니다")

    return payment_service.charge(amount, card_info)

# 이메일 실패는 실패로 처리
def send_email(to, subject, body):
    try:
        result = email_service.send(to, subject, body)
        return result.success
    except EmailServiceError as e:
        logger.error(f"이메일 전송 실패: {e}")
        raise EmailDeliveryError(f"이메일을 전송할 수 없습니다: {to}")
```

### 허용되는 예외 상황

#### 1. **개발/테스트 환경 분리**
✅ **허용**: 환경별 설정 분리
```python
if os.getenv('ENVIRONMENT') == 'development':
    # 개발 환경에서만 사용되는 설정
    db_config = DEV_DATABASE_CONFIG
else:
    db_config = PROD_DATABASE_CONFIG
```

#### 2. **기본값 설정**
✅ **허용**: 합리적인 기본값
```python
def get_llm_model(self, model_name=None):
    return model_name or "gemini-flash"  # 기본 모델
```

#### 3. **에러 처리에서의 대체 값**
✅ **허용**: 실패 시 안전한 대체 값
```python
def get_system_status(self):
    try:
        return self.health_checker.get_status()
    except Exception as e:
        logger.error(f"상태 확인 실패: {e}")
        return {"status": "unknown", "error": str(e)}
```

## 🎯 대체 패턴 가이드

### 1. **API 키 누락 처리**
❌ **잘못된 방법**: 더미 응답 반환
```python
if not api_key:
    return dummy_response()
```

✅ **올바른 방법**: 명확한 에러 및 설정 가이드
```python
if not api_key:
    raise ConfigurationError(
        "API 키가 설정되지 않았습니다. "
        "환경변수에 GOOGLE_API_KEY를 설정하세요."
    )
```

### 2. **외부 서비스 연결 실패**
❌ **잘못된 방법**: 시뮬레이션 응답
```python
try:
    result = external_service.call()
except:
    result = simulate_response()
```

✅ **올바른 방법**: 재시도 로직 또는 명확한 실패 처리
```python
try:
    result = external_service.call()
except ServiceException as e:
    logger.error(f"외부 서비스 호출 실패: {e}")
    raise ServiceUnavailableError("서비스가 일시적으로 사용할 수 없습니다")
```

### 3. **데이터 부재 상황**
❌ **잘못된 방법**: 가짜 데이터 생성
```python
if not user_data:
    user_data = create_fake_user_data()
```

✅ **올바른 방법**: 빈 상태 처리 또는 데이터 요구
```python
if not user_data:
    raise DataNotFoundError("사용자 데이터를 찾을 수 없습니다")
```

## 🔍 코드 검증 체크리스트

커밋 전에 다음 사항을 확인하세요:

### 금지 키워드 검사
- [ ] `임시`, `더미`, `테스트`, `시뮬`, `fake_`, `mock_`, `dummy_`
- [ ] `TODO`, `FIXME`, `HACK` (임시 해결책 표시)
- [ ] `sample_data`, `test_data` (하드코딩된 테스트 데이터)

### 로직 검증
- [ ] 모든 함수가 실제 비즈니스 로직을 수행하는가?
- [ ] 에러 상황에서 적절한 예외를 발생시키는가?
- [ ] 환경변수/설정이 누락되었을 때 명확한 안내를 제공하는가?

### 데이터 검증
- [ ] 하드코딩된 데이터가 없는가?
- [ ] 모든 데이터가 실제 소스에서 오는가?
- [ ] 기본값이 설정되어 있다면 합리적인가?

## 🚨 위반 시 조치 (ZERO TOLERANCE)

### 🔴 즉시 조치 (임시/더미/시뮬레이션 발견 시)
1. **커밋 전 발견**: 즉시 수정 후 재검토
2. **코드 리뷰에서 발견**: **무조건 반려** - 수정 없이 승인 금지
3. **운영 환경 발견**: **즉시 시스템 중단** → 핫픽스 배포
4. **반복 위반**: 개발 권한 제한

### 🔍 자동 검증 규칙
다음 키워드가 코드에서 발견되면 **자동 빌드 실패**:
- `임시`, `더미`, `테스트데이터`, `시뮬`, `fake_`, `mock_`, `dummy_`
- `sample_data`, `test_response`, `fallback_data`
- 주석: `# 임시`, `// TODO: 더미`, `# 시뮬레이션`

### ⚠️ 검증 예외
**유일한 허용 예외**: 실제 테스트 파일 (`*test*.py`, `*spec*.js`)에서만 허용

## 📋 예외 승인 프로세스

불가피하게 임시 로직이 필요한 경우:

1. **명확한 사유 문서화**
2. **제거 일정 명시**
3. **팀 리드 승인**
4. **이슈 트래커에 등록**

```python
# 예외 승인 예시
# TODO-APPROVED: 2025-10-15까지 임시 구현 (이슈 #123)
# 사유: 외부 API 서비스 출시 지연으로 인한 임시 처리
# 담당자: 개발팀장
if external_api_available:
    return external_api.process(data)
else:
    # 임시: 기본 처리 로직
    logger.warning("외부 API 미사용 - 기본 처리 사용")
    return basic_process(data)
```

---

**핵심 원칙**: 코드는 항상 운영 환경에서 실제 사용될 수 있는 상태여야 합니다.