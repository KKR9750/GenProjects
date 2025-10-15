// Admin Dashboard - Enhanced Version for Tab Mode
// Pure JavaScript (No React)

// 전역 변수 (중복 선언 방지)
if (typeof window.adminAuthToken === 'undefined') {
    window.adminAuthToken = localStorage.getItem('admin_token') || localStorage.getItem('auth_token');
    window.adminCurrentSection = 'users';
}

// 전역 스코프 재선언 문제 방지 - window 객체에 직접 할당
window.authToken = window.adminAuthToken;
window.currentSection = window.adminCurrentSection;

// 디버깅: 토큰 확인
console.log('[Admin.js] authToken:', window.authToken ? 'exists' : 'missing');

// 토큰 검증 함수
async function verifyTokenAndInit() {
    if (!window.authToken) {
        console.warn('[Admin.js] No token found, redirecting to login...');
        window.location.href = '/login.html';
        return;
    }

    try {
        // 토큰 검증 (간단한 API 호출)
        const response = await fetch('/api/admin/system/status', {
            headers: {
                'Authorization': `Bearer ${window.authToken}`
            }
        });

        if (response.status === 401) {
            console.warn('[Admin.js] Token expired or invalid, redirecting to login...');
            localStorage.removeItem('admin_token');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('admin_username');
            window.location.href = '/login.html';
            return;
        }

        if (response.ok) {
            // 토큰 유효 - 관리자 패널 렌더링
            console.log('[Admin.js] Token valid, rendering admin panel...');
            renderAdminDashboard();
        } else {
            throw new Error('Token verification failed');
        }
    } catch (error) {
        console.error('[Admin.js] Token verification error:', error);
        alert('인증에 실패했습니다. 다시 로그인해주세요.');
        window.location.href = '/login.html';
    }
}

// API 요청 헬퍼 함수
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(window.authToken && { 'Authorization': `Bearer ${window.authToken}` })
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
    }

    return data;
}

// 관리자 패널 렌더링
function renderAdminDashboard() {
    const root = document.getElementById('root');

    root.innerHTML = `
        <div class="admin-container-tab">
            <!-- 사이드바 -->
            <div class="admin-sidebar">
                <div class="sidebar-header">
                    <h1>🛡️ Admin Panel</h1>
                    <p>AI Chat Interface</p>
                </div>
                <div class="sidebar-menu">
                    <button class="menu-item active" data-section="users">
                        <i>👥</i> 사용자 관리
                    </button>
                    <button class="menu-item" data-section="llm">
                        <i>🤖</i> LLM 관리
                    </button>
                    <button class="menu-item" data-section="system">
                        <i>⚙️</i> 시스템 설정
                    </button>
                </div>
            </div>

            <!-- 메인 콘텐츠 -->
            <div class="admin-main">
                <div class="admin-header-tab">
                    <h1 id="headerTitle">사용자 관리</h1>
                    <p id="headerSubtitle">사용자 계정 관리 및 권한 설정</p>
                </div>
                <div class="admin-content-tab" id="contentArea">
                    <!-- 콘텐츠가 여기에 동적으로 로드됩니다 -->
                </div>
            </div>
        </div>
    `;

    // 이벤트 리스너 등록
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const section = e.currentTarget.dataset.section;
            switchSection(section);
        });
    });

    // 초기 사용자 섹션 로드
    switchSection('users');
}

// 섹션 전환 함수
function switchSection(section) {
    const allowedSections = ['users', 'llm', 'system'];
    if (!allowedSections.includes(section)) {
        section = 'users';
    }

    window.currentSection = section;

    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === section) {
            item.classList.add('active');
        }
    });

    const headerTitle = document.getElementById('headerTitle');
    const headerSubtitle = document.getElementById('headerSubtitle');

    switch (section) {
        case 'users':
            headerTitle.textContent = '사용자 관리';
            headerSubtitle.textContent = '사용자 계정 관리 및 권한 설정';
            loadUsersContent();
            break;
        case 'llm':
            headerTitle.textContent = 'LLM 관리';
            headerSubtitle.textContent = 'AI 모델 구성 및 상태 관리';
            loadLLMContent();
            break;
        case 'system':
            headerTitle.textContent = '시스템 설정';
            headerSubtitle.textContent = '보안 설정 및 환경 구성';
            loadSystemContent();
            break;
    }
}

// 사용자 관리 콘텐츠
async function loadUsersContent() {
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div style="background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 13px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 style="color: #2c3e50; margin: 0; font-size: 16px;">👥 사용자 목록</h3>
                <button onclick="showAddUserModal()" style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; border: none; padding: 8px 14px; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 12px;">+ 사용자 추가</button>
            </div>

            <!-- 사용자 목록 테이블 -->
            <div id="usersTableContainer" style="overflow-x: auto;">
                <div class="loading" style="text-align: center; padding: 20px; font-size: 12px;">사용자 목록을 불러오는 중...</div>
            </div>
        </div>

        <!-- 사용자 추가 모달 -->
        <div id="addUserModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 18px; border-radius: 8px; width: 85%; max-width: 400px; font-size: 13px;">
                <h3 style="margin-bottom: 12px; color: #2c3e50; font-size: 16px;">새 사용자 추가</h3>
                <form id="addUserForm">
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">사용자 ID</label>
                        <input type="text" id="newUsername" placeholder="사용자 ID" required style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">이메일</label>
                        <input type="email" id="newEmail" placeholder="이메일 주소" required style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">비밀번호</label>
                        <input type="password" id="newPassword" placeholder="비밀번호" required style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">표시 이름</label>
                        <input type="text" id="newDisplayName" placeholder="표시 이름" style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 14px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">역할</label>
                        <select id="newRole" style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                            <option value="user">일반 사용자</option>
                            <option value="admin">관리자</option>
                            <option value="viewer">조회 전용</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 8px; justify-content: flex-end;">
                        <button type="button" onclick="hideAddUserModal()" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 3px; cursor: pointer; font-size: 12px;">취소</button>
                        <button type="submit" style="padding: 6px 12px; background: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">추가</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- 사용자 수정 모달 -->
        <div id="editUserModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 18px; border-radius: 8px; width: 85%; max-width: 400px; font-size: 13px;">
                <h3 style="margin-bottom: 12px; color: #2c3e50; font-size: 16px;">사용자 정보 수정</h3>
                <form id="editUserForm">
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">사용자 ID</label>
                        <input type="text" id="editUsername" placeholder="사용자 ID" readonly style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; background-color: #f5f5f5; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">이메일</label>
                        <input type="email" id="editEmail" placeholder="이메일 주소" required style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">표시 이름</label>
                        <input type="text" id="editDisplayName" placeholder="표시 이름" style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">역할</label>
                        <select id="editRole" style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                            <option value="user">일반 사용자</option>
                            <option value="admin">관리자</option>
                            <option value="viewer">조회 전용</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 14px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 500; font-size: 12px;">상태</label>
                        <select id="editStatus" style="width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                            <option value="active">활성</option>
                            <option value="inactive">비활성</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 8px; justify-content: flex-end;">
                        <button type="button" onclick="hideEditUserModal()" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 3px; cursor: pointer; font-size: 12px;">취소</button>
                        <button type="submit" style="padding: 6px 12px; background: #e67e22; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 12px;">수정</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // 사용자 목록 로드
    await loadUsersList();
}

// LLM 관리 콘텐츠
async function loadLLMContent() {
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div style="background: white; padding: 8px; border-radius: 5px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); font-size: 11px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="color: #2c3e50; margin: 0; font-size: 13px;">🤖 LLM 모델 관리</h3>
                <button onclick="showAddLLMModal()" style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: 500; font-size: 10px;">+ 모델 추가</button>
            </div>

            <!-- LLM 모델 목록 -->
            <div id="llmModelsContainer" style="margin-top: 8px;">
                <div class="loading" style="text-align: center; padding: 12px; font-size: 10px;">LLM 모델 목록을 불러오는 중...</div>
            </div>
        </div>

        <!-- LLM 모델 추가 모달 -->
        <div id="addLLMModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 18px; border-radius: 8px; width: 90%; max-width: 480px; max-height: 80vh; overflow-y: auto; font-size: 11px;">
                <h3 style="margin-bottom: 12px; color: #2c3e50; font-size: 14px;">새 LLM 모델 추가</h3>
                <form id="addLLMForm">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">모델 ID</label>
                            <input type="text" id="llmModelId" placeholder="예: gpt-4-turbo" required style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">모델 이름</label>
                            <input type="text" id="llmModelName" placeholder="예: GPT-4 Turbo" required style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">제공업체</label>
                            <select id="llmProvider" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                                <option value="">제공업체 선택</option>
                                <option value="OpenAI">OpenAI</option>
                                <option value="Anthropic">Anthropic</option>
                                <option value="Google">Google</option>
                                <option value="Meta">Meta</option>
                                <option value="Mistral AI">Mistral AI</option>
                                <option value="DeepSeek">DeepSeek</option>
                                <option value="기타">기타</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">상태</label>
                            <select id="llmStatus" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                                <option value="active">활성</option>
                                <option value="inactive">비활성</option>
                                <option value="testing">테스트</option>
                            </select>
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">API 엔드포인트</label>
                        <input type="url" id="llmEndpoint" placeholder="https://api.example.com/v1/chat/completions" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">최대 토큰 수</label>
                            <input type="number" id="llmMaxTokens" value="4096" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                        </div>
                        <div style="margin-bottom: 10px;">
                            <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">1K 토큰당 비용</label>
                            <input type="number" id="llmCost" step="0.0001" placeholder="0.0030" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                        </div>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">기능 (쉼표로 구분)</label>
                        <input type="text" id="llmCapabilities" placeholder="text-generation, reasoning, code-generation" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                    </div>
                    <div style="margin-bottom: 12px;">
                        <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 10px;">추천 역할 (쉼표로 구분)</label>
                        <input type="text" id="llmRoles" placeholder="Researcher, Writer, Engineer" style="width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; font-size: 10px;">
                    </div>
                    <div style="display: flex; gap: 6px; justify-content: flex-end;">
                        <button type="button" onclick="hideAddLLMModal()" style="padding: 6px 12px; border: 1px solid #ddd; background: white; border-radius: 3px; cursor: pointer; font-size: 10px;">취소</button>
                        <button type="submit" style="padding: 6px 12px; background: #27ae60; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px;">추가</button>
                    </div>
                </form>
            </div>
        </div>
    `;

    // LLM 모델 목록 로드
    await loadLLMModelsList();
}

// 시스템 설정 콘텐츠
async function loadSystemContent() {
    const contentArea = document.getElementById('contentArea');

    contentArea.innerHTML = `
        <div style="background: white; padding: 8px; border-radius: 5px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); font-size: 11px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="color: #2c3e50; margin: 0; font-size: 13px;">⚙️ 시스템 설정</h3>
                <button onclick="saveSystemSettings()" style="background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: 500; font-size: 10px;">설정 저장</button>
            </div>

            <!-- 설정 로딩 -->
            <div id="systemSettingsContainer" style="margin-top: 8px;">
                <div class="loading" style="text-align: center; padding: 24px; font-size: 10px;">시스템 설정을 불러오는 중...</div>
            </div>
        </div>
    `;

    // 시스템 설정 로드
    await loadSystemSettings();
}

// 사용자 목록 로드 함수
async function loadUsersList() {
    try {
        const data = await apiRequest('/api/admin/users');
        const usersTableContainer = document.getElementById('usersTableContainer');

        if (data.success && data.users) {
            const usersTable = `
                <table style="width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 12px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">ID</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">이메일</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">표시명</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">역할</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">상태</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">생성일</th>
                            <th style="padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 500; font-size: 11px;">작업</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.users.map(user => `
                            <tr style="border-bottom: 1px solid #dee2e6;">
                                <td style="padding: 6px 8px; font-size: 11px;">${user.username}</td>
                                <td style="padding: 6px 8px; font-size: 11px;">${user.email}</td>
                                <td style="padding: 6px 8px; font-size: 11px;">${user.display_name || user.username}</td>
                                <td style="padding: 6px 8px;">
                                    <span style="padding: 2px 6px; border-radius: 3px; font-size: 10px;
                                        background: ${user.role === 'admin' ? '#e74c3c' : user.role === 'user' ? '#3498db' : '#f39c12'};
                                        color: white;">
                                        ${user.role === 'admin' ? '관리자' : user.role === 'user' ? '사용자' : '조회전용'}
                                    </span>
                                </td>
                                <td style="padding: 6px 8px;">
                                    <span style="padding: 2px 6px; border-radius: 3px; font-size: 10px;
                                        background: ${user.status === 'active' ? '#27ae60' : '#e74c3c'}; color: white;">
                                        ${user.status === 'active' ? '활성' : '비활성'}
                                    </span>
                                </td>
                                <td style="padding: 6px 8px; font-size: 10px; color: #7f8c8d;">
                                    ${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                                </td>
                                <td style="padding: 6px 8px;">
                                    <button onclick="editUser('${user.id}')" style="padding: 3px 8px; margin-right: 3px; background: #f39c12; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px;">수정</button>
                                    <button onclick="deleteUser('${user.id}')" ${user.id === 'admin' ? 'disabled' : ''} style="padding: 3px 8px; background: #e74c3c; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 10px; ${user.id === 'admin' ? 'opacity: 0.5; cursor: not-allowed;' : ''}">삭제</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <div style="margin-top: 8px; padding: 6px 8px; background: #f8f9fa; border-radius: 3px; font-size: 11px; color: #6c757d;">
                    총 ${data.total_count}명의 사용자가 등록되어 있습니다.
                </div>
            `;
            usersTableContainer.innerHTML = usersTable;
        } else {
            usersTableContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #7f8c8d;">
                    <div style="font-size: 32px; margin-bottom: 12px;">👤</div>
                    <h4 style="font-size: 14px; margin: 8px 0;">등록된 사용자가 없습니다</h4>
                    <p style="font-size: 12px; margin: 4px 0;">${data.message || '사용자를 추가해보세요'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('사용자 목록 로드 실패:', error);
        const usersContainer = document.getElementById('usersTableContainer');
        if (usersContainer) {
            usersContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #e74c3c;">
                    <h4 style="font-size: 14px; margin: 8px 0;">사용자 목록 로드 실패</h4>
                    <p style="font-size: 12px; margin: 4px 0;">${error.message}</p>
                </div>
            `;
        }
    }
}

// 사용자 모달 관련 함수들
function showAddUserModal() {
    document.getElementById('addUserModal').style.display = 'block';
}

function hideAddUserModal() {
    document.getElementById('addUserModal').style.display = 'none';
    document.getElementById('addUserForm').reset();
}

function showEditUserModal() {
    document.getElementById('editUserModal').style.display = 'block';
}

function hideEditUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
    document.getElementById('editUserForm').reset();
}

// 사용자 수정 함수
async function editUser(userId) {
    try {
        const userResponse = await apiRequest(`/api/admin/users/${userId}`);
        if (!userResponse.success) {
            alert('사용자 정보를 불러올 수 없습니다: ' + userResponse.error);
            return;
        }

        const user = userResponse.user;
        document.getElementById('editUsername').value = user.id || user.user_id || user.username || '';
        document.getElementById('editEmail').value = user.email || '';
        document.getElementById('editDisplayName').value = user.display_name || '';
        document.getElementById('editRole').value = user.role || 'user';

        let statusValue = 'active';
        if (user.status) {
            statusValue = user.status;
        } else if (user.is_active !== undefined) {
            statusValue = user.is_active ? 'active' : 'inactive';
        }
        document.getElementById('editStatus').value = statusValue;

        showEditUserModal();
    } catch (error) {
        alert('사용자 정보 조회 중 오류가 발생했습니다: ' + error.message);
    }
}

// 사용자 삭제 함수
async function deleteUser(userId) {
    if (userId === 'admin') {
        alert('기본 관리자 계정은 삭제할 수 없습니다.');
        return;
    }

    if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) {
        return;
    }

    try {
        const response = await apiRequest(`/api/admin/users/${userId}`, {
            method: 'DELETE'
        });

        if (response.success) {
            alert('사용자가 성공적으로 삭제되었습니다.');
            await loadUsersList();
        } else {
            alert('사용자 삭제 실패: ' + response.error);
        }
    } catch (error) {
        alert('사용자 삭제 중 오류가 발생했습니다: ' + error.message);
    }
}

// LLM 모델 목록 로드 함수
async function loadLLMModelsList() {
    try {
        const data = await apiRequest('/api/admin/llm-models/manage');
        const llmContainer = document.getElementById('llmModelsContainer');

        if (data.success && data.models) {
            const modelsGrid = `
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px;">
                    ${data.models.map(model => `
                        <div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; font-size: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 6px;">
                                <div>
                                    <h4 style="margin: 0; color: #2c3e50; font-size: 12px;">${model.name}</h4>
                                    <p style="margin: 1px 0; color: #6c757d; font-size: 9px;">${model.provider} • ${model.id}</p>
                                </div>
                                <span style="padding: 2px 6px; border-radius: 3px; font-size: 9px;
                                    background: ${model.status === 'active' ? '#27ae60' : model.status === 'testing' ? '#f39c12' : '#e74c3c'};
                                    color: white;">
                                    ${model.status === 'active' ? '활성' : model.status === 'testing' ? '테스트' : '비활성'}
                                </span>
                            </div>
                            <div style="margin: 6px 0; padding: 6px; background: white; border-radius: 3px; font-size: 9px;">
                                <div style="margin-bottom: 3px;">📊 토큰: ${model.max_tokens?.toLocaleString() || 'N/A'}</div>
                                <div style="margin-bottom: 3px;">💰 비용: $${model.cost_per_1k_tokens || 0}/1K</div>
                                ${model.capabilities && model.capabilities.length > 0 ? `
                                    <div style="margin-top: 4px;">
                                        ${model.capabilities.map(cap => `<span style="display: inline-block; padding: 1px 4px; margin: 1px; background: #e3f2fd; border-radius: 2px; font-size: 8px;">${cap}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                            <div style="display: flex; gap: 4px; margin-top: 6px;">
                                <button onclick="testLLMModel('${model.id}')" style="flex: 1; padding: 4px; background: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 9px;">테스트</button>
                                <button onclick="deleteLLMModel('${model.id}')" style="flex: 1; padding: 4px; background: #e74c3c; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 9px;">삭제</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            llmContainer.innerHTML = modelsGrid;
        } else {
            llmContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #7f8c8d;">
                    <div style="font-size: 32px; margin-bottom: 12px;">🤖</div>
                    <h4 style="font-size: 14px; margin: 8px 0;">등록된 LLM 모델이 없습니다</h4>
                    <p style="font-size: 12px; margin: 4px 0;">모델을 추가해보세요</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('LLM 모델 목록 로드 실패:', error);
        const llmContainer = document.getElementById('llmModelsContainer');
        if (llmContainer) {
            llmContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #e74c3c;">
                    <h4 style="font-size: 14px; margin: 8px 0;">LLM 모델 목록 로드 실패</h4>
                    <p style="font-size: 12px; margin: 4px 0;">${error.message}</p>
                </div>
            `;
        }
    }
}

// LLM 모달 관련 함수들
function showAddLLMModal() {
    document.getElementById('addLLMModal').style.display = 'block';
}

function hideAddLLMModal() {
    document.getElementById('addLLMModal').style.display = 'none';
    document.getElementById('addLLMForm').reset();
}

// LLM 모델 테스트 함수
async function testLLMModel(modelId) {
    alert('LLM 모델 테스트 기능은 향후 구현될 예정입니다.\n모델 ID: ' + modelId);
}

// LLM 모델 삭제 함수
async function deleteLLMModel(modelId) {
    if (!confirm('정말로 이 LLM 모델을 삭제하시겠습니까?\n' + modelId)) {
        return;
    }

    try {
        const response = await apiRequest(`/api/admin/llm-models/manage/${modelId}`, {
            method: 'DELETE'
        });

        if (response.success) {
            alert('LLM 모델이 성공적으로 삭제되었습니다.');
            await loadLLMModelsList();
        } else {
            alert('LLM 모델 삭제 실패: ' + response.error);
        }
    } catch (error) {
        alert('LLM 모델 삭제 중 오류가 발생했습니다: ' + error.message);
    }
}

// 시스템 설정 로드 함수
async function loadSystemSettings() {
    try {
        const data = await apiRequest('/api/admin/system/settings');
        const settingsContainer = document.getElementById('systemSettingsContainer');

        if (data.success && data.settings) {
            const settingsForm = `
                <form id="systemSettingsForm" style="font-size: 10px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <!-- 서버 설정 -->
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 11px;">🖥️ 서버 설정</h4>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">포트</label>
                                <input type="number" id="serverPort" value="${data.settings.server.port}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">호스트</label>
                                <input type="text" id="serverHost" value="${data.settings.server.host}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                            <div style="margin-bottom: 8px;">
                                <label style="display: flex; align-items: center; font-weight: 600; font-size: 9px;">
                                    <input type="checkbox" id="serverDebug" ${data.settings.server.debug ? 'checked' : ''} style="margin-right: 5px; transform: scale(0.8);">
                                    디버그 모드
                                </label>
                            </div>
                        </div>

                        <!-- 보안 설정 -->
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 11px;">🔒 보안 설정</h4>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">세션 타임아웃 (분)</label>
                                <input type="number" id="securityTimeout" value="${data.settings.security.session_timeout}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">최대 로그인 시도 횟수</label>
                                <input type="number" id="securityMaxAttempts" value="${data.settings.security.max_login_attempts}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">최소 비밀번호 길이</label>
                                <input type="number" id="securityPasswordLength" value="${data.settings.security.password_min_length}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                        </div>

                        <!-- 데이터베이스 설정 -->
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">
                            <h4 style="color: #2c3e50; margin-bottom: 8px; font-size: 11px;">🗃️ 데이터베이스 설정</h4>
                            <div style="margin-bottom: 8px;">
                                <label style="display: flex; align-items: center; font-weight: 600; font-size: 9px;">
                                    <input type="checkbox" id="dbBackupEnabled" ${data.settings.database.backup_enabled ? 'checked' : ''} style="margin-right: 5px; transform: scale(0.8);">
                                    자동 백업 활성화
                                </label>
                            </div>
                            <div style="margin-bottom: 8px;">
                                <label style="display: block; margin-bottom: 3px; font-weight: 600; font-size: 9px;">백업 간격 (시간)</label>
                                <input type="number" id="dbBackupInterval" value="${data.settings.database.backup_interval}" style="width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 9px;">
                            </div>
                        </div>
                    </div>
                </form>
            `;
            settingsContainer.innerHTML = settingsForm;
        } else {
            settingsContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #7f8c8d;">
                    <h4 style="font-size: 14px; margin: 8px 0;">설정을 불러올 수 없습니다</h4>
                    <p style="font-size: 12px; margin: 4px 0;">${data.message || '시스템 설정 로드 실패'}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('시스템 설정 로드 실패:', error);
        const settingsContainer = document.getElementById('systemSettingsContainer');
        if (settingsContainer) {
            settingsContainer.innerHTML = `
                <div style="text-align: center; padding: 24px; color: #e74c3c;">
                    <h4 style="font-size: 14px; margin: 8px 0;">시스템 설정 로드 실패</h4>
                    <p style="font-size: 12px; margin: 4px 0;">${error.message}</p>
                </div>
            `;
        }
    }
}

// 시스템 설정 저장 함수
async function saveSystemSettings() {
    try {
        const settings = {
            server: {
                port: parseInt(document.getElementById('serverPort').value),
                host: document.getElementById('serverHost').value,
                debug: document.getElementById('serverDebug').checked
            },
            security: {
                session_timeout: parseInt(document.getElementById('securityTimeout').value),
                max_login_attempts: parseInt(document.getElementById('securityMaxAttempts').value),
                password_min_length: parseInt(document.getElementById('securityPasswordLength').value)
            },
            database: {
                backup_enabled: document.getElementById('dbBackupEnabled').checked,
                backup_interval: parseInt(document.getElementById('dbBackupInterval').value)
            }
        };

        const response = await apiRequest('/api/admin/system/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });

        if (response.success) {
            alert('시스템 설정이 성공적으로 저장되었습니다.');
            await loadSystemSettings();
        } else {
            alert('설정 저장 실패: ' + response.error);
        }
    } catch (error) {
        alert('설정 저장 중 오류가 발생했습니다: ' + error.message);
    }
}

// 폼 이벤트 리스너 설정
document.addEventListener('submit', async (e) => {
    if (e.target.id === 'addUserForm') {
        e.preventDefault();
        const username = document.getElementById('newUsername').value;
        const email = document.getElementById('newEmail').value;
        const password = document.getElementById('newPassword').value;
        const displayName = document.getElementById('newDisplayName').value;
        const role = document.getElementById('newRole').value;

        try {
            const response = await apiRequest('/api/admin/users', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: username,
                    email,
                    password,
                    display_name: displayName || username,
                    role
                })
            });

            if (response.success) {
                alert('사용자가 성공적으로 추가되었습니다.');
                hideAddUserModal();
                await loadUsersList();
            } else {
                alert('사용자 추가 실패: ' + response.error);
            }
        } catch (error) {
            alert('사용자 추가 중 오류가 발생했습니다: ' + error.message);
        }
    }

    if (e.target.id === 'editUserForm') {
        e.preventDefault();
        const userId = document.getElementById('editUsername').value;
        const email = document.getElementById('editEmail').value;
        const displayName = document.getElementById('editDisplayName').value;
        const role = document.getElementById('editRole').value;
        const status = document.getElementById('editStatus').value;

        try {
            const response = await apiRequest(`/api/admin/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    email,
                    display_name: displayName,
                    role,
                    is_active: status === 'active'
                })
            });

            if (response.success) {
                alert('사용자 정보가 성공적으로 수정되었습니다.');
                hideEditUserModal();
                await loadUsersList();
            } else {
                alert('사용자 수정 실패: ' + response.error);
            }
        } catch (error) {
            alert('사용자 수정 중 오류가 발생했습니다: ' + error.message);
        }
    }

    if (e.target.id === 'addLLMForm') {
        e.preventDefault();
        const formData = {
            id: document.getElementById('llmModelId').value,
            name: document.getElementById('llmModelName').value,
            provider: document.getElementById('llmProvider').value,
            status: document.getElementById('llmStatus').value,
            api_endpoint: document.getElementById('llmEndpoint').value,
            max_tokens: parseInt(document.getElementById('llmMaxTokens').value),
            cost_per_1k_tokens: parseFloat(document.getElementById('llmCost').value) || 0,
            capabilities: document.getElementById('llmCapabilities').value.split(',').map(s => s.trim()).filter(s => s),
            recommended_roles: document.getElementById('llmRoles').value.split(',').map(s => s.trim()).filter(s => s)
        };

        try {
            const response = await apiRequest('/api/admin/llm-models/manage', {
                method: 'POST',
                body: JSON.stringify(formData)
            });

            if (response.success) {
                alert('LLM 모델이 성공적으로 추가되었습니다.');
                hideAddLLMModal();
                await loadLLMModelsList();
            } else {
                alert('LLM 모델 추가 실패: ' + response.error);
            }
        } catch (error) {
            alert('LLM 모델 추가 중 오류가 발생했습니다: ' + error.message);
        }
    }
});

// 초기화 - 토큰 검증 후 렌더링
verifyTokenAndInit();
