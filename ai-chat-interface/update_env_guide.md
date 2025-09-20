# Supabase 환경 변수 설정 가이드

## 🔑 필요한 정보 수집

1. Supabase 대시보드 (https://supabase.com/dashboard) 접속
2. "GenProjects" 프로젝트 선택
3. 좌측 메뉴에서 **Settings** → **API** 클릭
4. 다음 정보 복사:

### Project URL
```
Project URL: https://[your-project-id].supabase.co
```

### API Keys
```
anon public: eyJ...
service_role: eyJ...
```

## 📝 .env 파일 업데이트

아래 형식으로 `.env` 파일을 수정하세요:

```bash
# Supabase Configuration - GenProjects
SUPABASE_URL=https://[your-project-id].supabase.co
SUPABASE_ANON_KEY=eyJ[your-anon-key]
SUPABASE_SERVICE_ROLE_KEY=eyJ[your-service-role-key]

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-for-ai-chat-interface-2024
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24

# Flask Configuration
FLASK_ENV=development
DEBUG=True

# Server Configuration
PORT=3000
```

## ⚠️ 보안 주의사항

- `service_role` 키는 매우 강력합니다. 절대 프론트엔드에 노출하지 마세요
- `.env` 파일은 `.gitignore`에 포함되어 있습니다
- 실제 운영환경에서는 환경 변수로 관리하세요

## 📋 다음 단계

환경 변수를 업데이트한 후:
1. 서버 재시작
2. 데이터베이스 스키마 실행
3. 연결 테스트