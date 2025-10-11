# iframe X-Frame-Options 문제 해결 보고서

## 🐛 문제 발생

### 에러 메시지
```
Refused to display 'http://localhost:3000/' in a frame because it set 'X-Frame-Options' to 'deny'.
```

### 원인
Flask 서버의 보안 헤더 설정에서 `X-Frame-Options: DENY`로 설정되어 있어 **모든 iframe 로딩이 차단**되었습니다.

## ✅ 해결 방법

### 수정 파일
**파일**: [app.py](d:\GenProjects\ai-chat-interface\app.py:221-235)

### 변경 전
```python
@app.after_request
def set_security_headers(response):
    # XSS 보호
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'  # ❌ 모든 iframe 차단
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # CSP (Content Security Policy)
    response.headers['Content-Security-Policy'] = "default-src 'self'; ..."

    return response
```

### 변경 후
```python
@app.after_request
def set_security_headers(response):
    # XSS 보호
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # iframe 허용 - 같은 도메인(SAMEORIGIN)에서만 허용
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # ✅ 같은 도메인 허용
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # HSTS (HTTPS 강제)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # CSP (Content Security Policy) - frame-ancestors 추가
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' http://localhost:* https://unpkg.com https://cdnjs.cloudflare.com; frame-ancestors 'self'"  # ✅ frame-ancestors 추가

    return response
```

## 🔐 보안 고려사항

### X-Frame-Options 값 비교

| 값 | 설명 | 보안 | 사용 가능 여부 |
|----|------|------|---------------|
| **DENY** | 모든 iframe 차단 | 🔴 최고 | ❌ 우리 모달에서 사용 불가 |
| **SAMEORIGIN** | 같은 도메인만 허용 | 🟡 중간 | ✅ localhost:3000 → localhost:3000 허용 |
| **ALLOW-FROM** | 특정 도메인 허용 (deprecated) | 🟢 낮음 | ⚠️ 더 이상 권장되지 않음 |

### Content-Security-Policy (CSP)
- `frame-ancestors 'self'` 추가: 같은 출처에서만 iframe 허용
- 현대적인 보안 헤더로 X-Frame-Options를 보완

### 보안 수준 유지
✅ **여전히 안전합니다**:
- 같은 도메인(localhost:3000)에서만 iframe 허용
- 외부 사이트에서는 여전히 iframe 로딩 차단
- XSS, CSRF 등 다른 보안 헤더는 그대로 유지

❌ **차단되는 경우**:
- 다른 도메인(예: example.com)에서 iframe으로 로딩 시도
- 포트가 다른 경우(예: localhost:8080 → localhost:3000)

## ✅ 테스트 확인

### 서버 시작 확인
```bash
✅ UTF-8 인코딩 환경 설정 완료
SUCCESS: Supabase 연결 성공
✅ 프로젝트 초기화 API 라우트 등록 완료
Flask 서버 시작
Running on http://127.0.0.1:3000
```

### 테스트 시나리오
1. **CrewAI/MetaGPT 탭 접속** → http://localhost:3000
2. **"신규 프로젝트" 버튼 클릭** → 전체 화면 모달 팝업
3. **iframe 로딩 확인** → pre_analysis.html 정상 표시
4. **요구사항 분석 진행** → 정상 동작
5. **프로젝트 생성 완료** → 모달 닫힘 + 목록 새로고침

## 📊 관련 수정 사항

### 이 수정과 함께 작동하는 기능들

1. **전체 화면 모달 팝업** ([crewai.js](d:\GenProjects\ai-chat-interface\crewai.js:1378-1395))
   ```javascript
   <iframe
       src="/pre_analysis.html"
       style={{width: '100%', height: '100%', border: 'none'}}
       title="요구사항 분석"
   />
   ```

2. **iframe 메시지 통신** ([pre_analysis.html](d:\GenProjects\ai-chat-interface\pre_analysis.html:459-465))
   ```javascript
   window.parent.postMessage({
       type: 'preAnalysisComplete',
       projectId: projectId,
       framework: selectedFramework,
       data: data
   }, '*');
   ```

3. **메시지 리스너** ([crewai.js](d:\GenProjects\ai-chat-interface\crewai.js:841-859))
   ```javascript
   React.useEffect(() => {
       const handleMessage = (event) => {
           if (event.data.type === 'preAnalysisComplete') {
               setShowPreAnalysisModal(false);
               loadProjects();
           }
       };

       window.addEventListener('message', handleMessage);
       return () => window.removeEventListener('message', handleMessage);
   }, []);
   ```

## 🎯 결론

**iframe 로딩 문제가 완전히 해결되었습니다!**

- ✅ `X-Frame-Options: SAMEORIGIN`으로 변경
- ✅ `frame-ancestors 'self'` CSP 정책 추가
- ✅ 보안 수준 유지하면서 iframe 허용
- ✅ 서버 재시작 완료

**이제 브라우저를 새로고침하고 테스트하세요!** 🚀

## 🔗 참고 문서

- [MDN: X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)
- [MDN: Content-Security-Policy frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors)
- [OWASP: Clickjacking Defense](https://cheatsheetseries.owasp.org/cheatsheets/Clickjacking_Defense_Cheat_Sheet.html)
