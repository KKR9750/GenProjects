/**
 * 탭 전환 로직 및 라우팅 관리
 */

class TabManager {
    constructor() {
        this.tabs = document.querySelectorAll('.tab');
        this.init();
    }

    /**
     * 초기화
     */
    async init() {
        // 로그인 체크 먼저 수행
        const isAuthenticated = await this.checkAuthentication();

        if (!isAuthenticated) {
            // 로그인 필요 - 로그인 페이지로 리디렉션
            this.redirectToLogin();
            return;
        }

        // 탭 클릭 이벤트 등록
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => this.handleTabClick(e));
        });

        // URL 해시 기반 초기 페이지 로드
        this.handleHashChange();

        // 브라우저 뒤로가기/앞으로가기 지원
        window.addEventListener('hashchange', () => this.handleHashChange());

        // 키보드 단축키 (Ctrl+1~4)
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcut(e));

        // 사용자 정보 로드
        this.loadUserInfo();

        // 로그아웃 버튼 이벤트
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // 초기 페이지 로드: crewai로 변경
        const initialPage = this.getPageFromHash() || 'pre_analysis';
        this.switchToTab(initialPage);
    }

    /**
     * 인증 체크
     */
    async checkAuthentication() {
        const token = localStorage.getItem('admin_token') || localStorage.getItem('auth_token');

        if (!token) {
            return false;
        }

        // 토큰 검증
        try {
            const response = await fetch('/api/v2/auth/verify', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                return true;
            } else {
                // 토큰 만료 또는 무효
                this.clearAuth();
                return false;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            return false;
        }
    }

    /**
     * 인증 정보 초기화
     */
    clearAuth() {
        localStorage.removeItem('admin_token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('admin_username');
        localStorage.removeItem('username');
    }

    /**
     * 로그인 페이지로 리디렉션
     */
    redirectToLogin() {
        // 로그인 페이지로 리디렉션
        window.location.href = '/login.html';
    }

    /**
     * 탭 클릭 핸들러
     */
    handleTabClick(event) {
        const tab = event.currentTarget;
        const pageName = tab.dataset.page;

        // 활성 탭 업데이트
        this.updateActiveTab(tab);

        // 배경색 클래스 업데이트
        this.updateBackgroundClass(pageName);

        // 컴포넌트 전환
        window.componentLoader.switchComponent(pageName);

        // URL 업데이트
        this.updateURL(pageName);
    }

    /**
     * URL 해시 변경 핸들러
     */
    handleHashChange() {
        const pageName = this.getPageFromHash();
        if (pageName) {
            this.switchToTab(pageName, false);
        }
    }

    /**
     * 특정 탭으로 전환
     * @param {string} pageName - 페이지 이름
     * @param {boolean} updateURL - URL 업데이트 여부
     */
    switchToTab(pageName, updateURL = true) {
        // 해당 탭 찾기
        const targetTab = Array.from(this.tabs).find(tab => tab.dataset.page === pageName);

        if (!targetTab) {
            console.warn(`탭을 찾을 수 없습니다: ${pageName}`);
            return;
        }

        // 활성 탭 업데이트
        this.updateActiveTab(targetTab);

        // 배경색 클래스 업데이트
        this.updateBackgroundClass(pageName);

        // 컴포넌트 로드
        window.componentLoader.switchComponent(pageName);

        // URL 업데이트
        if (updateURL) {
            this.updateURL(pageName);
        }
    }

    /**
     * 활성 탭 시각적 업데이트
     */
    updateActiveTab(activeTab) {
        this.tabs.forEach(tab => tab.classList.remove('active'));
        activeTab.classList.add('active');
    }

    /**
     * URL 업데이트
     */
    updateURL(pageName) {
        const newHash = `#${pageName}`;
        if (window.location.hash !== newHash) {
            history.pushState(null, '', newHash);
        }
    }

    /**
     * URL 해시에서 페이지 이름 추출
     */
    getPageFromHash() {
        const hash = window.location.hash.slice(1); // # 제거
        const validPages = ['dashboard', 'pre_analysis', 'crewai', 'metagpt', 'admin', 'agent_manager', 'projects'];
        return validPages.includes(hash) ? hash : null;
    }

    /**
     * 키보드 단축키 처리
     * Ctrl+1: 홈, Ctrl+2: CrewAI, Ctrl+3: MetaGPT, Ctrl+4: 관리자
     */
    handleKeyboardShortcut(event) {
        if (event.ctrlKey || event.metaKey) {
            const keyMap = {
                '1': 'pre_analysis',
                '2': 'crewai',
                '3': 'metagpt',
                '4': 'admin',
                '5': 'dashboard'
            };

            const pageName = keyMap[event.key];
            if (pageName) {
                event.preventDefault();
                this.switchToTab(pageName);
            }
        }
    }

    /**
     * 프로그래밍 방식으로 탭 전환
     * @param {string} pageName - 페이지 이름
     */
    navigateTo(pageName) {
        this.switchToTab(pageName);
    }

    /**
     * 사용자 정보 로드
     */
    loadUserInfo() {
        const token = localStorage.getItem('admin_token') || localStorage.getItem('auth_token');
        const userName = localStorage.getItem('admin_username') || localStorage.getItem('username') || 'Guest';

        const userNameElement = document.getElementById('user-name');
        if (userNameElement) {
            if (token) {
                userNameElement.textContent = userName;
            } else {
                userNameElement.textContent = 'Guest';
            }
        }
    }

    /**
     * 배경 클래스 업데이트 (프레임워크별 그라데이션 배경)
     * @param {string} pageName - 페이지 이름
     */
    updateBackgroundClass(pageName) {
        // 기존 배경 클래스 모두 제거
        document.body.classList.remove('pre-analysis-active', 'crewai-active', 'metagpt-active', 'dashboard-active', 'admin-active', 'projects-active', 'agent-active');

        // 페이지별 배경 클래스 추가
        if (pageName === 'pre_analysis') {
            document.body.classList.add('pre-analysis-active');
        } else if (pageName === 'crewai') {
            document.body.classList.add('crewai-active');
        } else if (pageName === 'metagpt') {
            document.body.classList.add('metagpt-active');
        } else if (pageName === 'dashboard') {
            document.body.classList.add('dashboard-active');
        } else if (pageName === 'admin') {
            document.body.classList.add('admin-active');
        } else if (pageName === 'projects') {
            document.body.classList.add('projects-active');
        } else if (pageName === 'agent_manager') {
            document.body.classList.add('agent-active');
        }
    }

    /**
     * 로그아웃 처리
     */
    handleLogout() {
        if (confirm('로그아웃 하시겠습니까?')) {
            this.clearAuth();
            alert('로그아웃되었습니다.');
            window.location.reload();
        }
    }
}

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.tabManager = new TabManager();

    // 전역 네비게이션 함수 노출
    window.navigateTo = (pageName) => {
        window.tabManager.navigateTo(pageName);
    };
});
