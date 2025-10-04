/**
 * 동적 컴포넌트 로더
 * CSS/JS 파일을 동적으로 로드하고 React 컴포넌트를 렌더링합니다.
 */

class ComponentLoader {
    constructor() {
        this.currentPage = null;
        this.loadedCSS = [];
        this.loadedJS = [];
    }

    /**
     * 컴포넌트 전환
     * @param {string} pageName - 로드할 페이지 이름 (dashboard, crewai, metagpt, admin)
     */
    async switchComponent(pageName) {
        // 동일한 페이지면 무시
        if (this.currentPage === pageName) {
            return;
        }

        try {
            // 로딩 표시
            this.showLoading();

            // 1. 이전 CSS 제거
            this.removeOldCSS();

            // 2. 새 CSS 로드
            await this.loadCSS(pageName);

            // 3. 새 JS 로드 및 컴포넌트 렌더링
            await this.loadComponent(pageName);

            // 4. 현재 페이지 업데이트
            this.currentPage = pageName;

            // 5. 페이드 인 애니메이션
            const contentArea = document.getElementById('content-area');
            contentArea.classList.add('fade-in');
            setTimeout(() => contentArea.classList.remove('fade-in'), 300);

        } catch (error) {
            console.error(`컴포넌트 로드 실패 (${pageName}):`, error);
            this.showError(pageName, error);
        }
    }

    /**
     * CSS 동적 로드
     */
    async loadCSS(pageName) {
        return new Promise((resolve, reject) => {
            const cssFile = this.getCSSFileName(pageName);
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = cssFile;
            link.id = `css-${pageName}`;

            link.onload = () => {
                this.loadedCSS.push(pageName);
                resolve();
            };

            link.onerror = () => reject(new Error(`CSS 로드 실패: ${cssFile}`));

            document.head.appendChild(link);
        });
    }

    /**
     * 이전 CSS 제거
     */
    removeOldCSS() {
        this.loadedCSS.forEach(page => {
            const link = document.getElementById(`css-${page}`);
            if (link) {
                link.remove();
            }
        });
        this.loadedCSS = [];
    }

    /**
     * 컴포넌트 로드 및 렌더링
     */
    async loadComponent(pageName) {
        // 1. 기존 컴포넌트 script 완전 제거
        document.querySelectorAll('script[data-component]').forEach(script => {
            script.remove();
        });

        // 2. React root 초기화 (innerHTML으로 이전 React root 정리)
        const root = document.getElementById('root');
        root.innerHTML = '';

        // 3. 페이지별 로드 로직
        switch(pageName) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'crewai':
                await this.loadCrewAI();
                break;
            case 'metagpt':
                await this.loadMetaGPT();
                break;
            case 'admin':
                await this.loadAdmin();
                break;
            case 'projects':
                await this.loadProjects();
                break;
            default:
                throw new Error(`알 수 없는 페이지: ${pageName}`);
        }
    }

    /**
     * Dashboard 로드
     */
    async loadDashboard() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.setAttribute('data-component', 'dashboard');
            script.src = 'dashboard-pure.js';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Dashboard 로드 실패'));
            document.body.appendChild(script);
        });
    }

    /**
     * CrewAI 로드
     */
    async loadCrewAI() {
        return this.loadBabelScript('crewai');
    }

    /**
     * MetaGPT 로드
     */
    async loadMetaGPT() {
        return this.loadBabelScript('metagpt');
    }

    /**
     * Admin 로드 (Pure JavaScript, No Babel)
     */
    async loadAdmin() {
        return new Promise((resolve, reject) => {
            // Remove existing admin scripts to prevent duplicate loading
            const existingScripts = document.querySelectorAll('script[data-component="admin"]');
            existingScripts.forEach(script => script.remove());

            const existingCss = document.querySelectorAll('link[data-component="admin-css"]');
            existingCss.forEach(css => css.remove());

            // Load admin.css first
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'admin.css?v=11';
            css.setAttribute('data-component', 'admin-css');
            document.head.appendChild(css);

            // Then load admin.js
            const script = document.createElement('script');
            script.setAttribute('data-component', 'admin');
            script.src = 'admin.js?v=16';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Admin 로드 실패'));
            document.body.appendChild(script);
        });
    }

    /**
     * Projects 로드 (Pure JavaScript, No Babel)
     */
    async loadProjects() {
        return new Promise((resolve, reject) => {
            // Remove existing projects scripts to prevent duplicate loading
            const existingScripts = document.querySelectorAll('script[data-component="projects"]');
            existingScripts.forEach(script => script.remove());

            const existingCss = document.querySelectorAll('link[data-component="projects-css"]');
            existingCss.forEach(css => css.remove());

            // Load projects.css first
            const css = document.createElement('link');
            css.rel = 'stylesheet';
            css.href = 'projects.css?v=11';
            css.setAttribute('data-component', 'projects-css');
            document.head.appendChild(css);

            // Then load projects.js
            const script = document.createElement('script');
            script.setAttribute('data-component', 'projects');
            script.src = 'projects.js?v=11';
            script.onload = resolve;
            script.onerror = () => reject(new Error('Projects 로드 실패'));
            document.body.appendChild(script);
        });
    }

    /**
     * Babel 스크립트 동적 로드 (인라인 방식)
     */
    async loadBabelScript(pageName) {
        try {
            const jsFile = this.getJSFileName(pageName);
            const response = await fetch(jsFile);
            const code = await response.text();

            // IIFE로 감싸서 스코프 격리
            const wrappedCode = `(function() {\n${code}\n})();`;

            const script = document.createElement('script');
            script.setAttribute('data-component', pageName);
            script.type = 'text/babel';
            script.textContent = wrappedCode;
            document.body.appendChild(script);

            // Babel 변환 트리거
            if (window.Babel) {
                window.Babel.transformScriptTags();
            }

            // 렌더링 대기
            await new Promise(resolve => setTimeout(resolve, 100));
        } catch (error) {
            throw new Error(`${pageName} 로드 실패: ${error.message}`);
        }
    }

    /**
     * CSS 파일명 매핑
     */
    getCSSFileName(pageName) {
        const cssMap = {
            'dashboard': 'dashboard.css',
            'crewai': 'crewai.css?v=7',
            'metagpt': 'metagpt.css?v=4',
            'admin': 'admin.css',
            'projects': 'projects.css'
        };
        return cssMap[pageName] || `${pageName}.css`;
    }

    /**
     * JS 파일명 매핑
     */
    getJSFileName(pageName) {
        const jsMap = {
            'dashboard': 'dashboard-pure.js',
            'crewai': 'crewai.js?v=7',
            'metagpt': 'metagpt.js?v=4',
            'admin': 'admin.js'
        };
        return jsMap[pageName] || `${pageName}.js`;
    }

    /**
     * 로딩 표시
     */
    showLoading() {
        const root = document.getElementById('root');
        root.innerHTML = '<div class="loading">컴포넌트 로딩 중</div>';
    }

    /**
     * 에러 표시
     */
    showError(pageName, error) {
        const root = document.getElementById('root');
        root.innerHTML = `
            <div style="padding: 2rem; text-align: center; color: #ef4444;">
                <h2 style="font-size: var(--font-lg); margin-bottom: 1rem;">⚠️ 로드 실패</h2>
                <p style="font-size: var(--font-base); color: #6b7280;">
                    ${pageName} 페이지를 불러올 수 없습니다.<br>
                    ${error.message}
                </p>
                <button onclick="location.reload()"
                    style="margin-top: 1rem; padding: 0.5rem 1rem;
                           font-size: var(--font-base); border-radius: 0.375rem;
                           background: #3b82f6; color: white; border: none; cursor: pointer;">
                    새로고침
                </button>
            </div>
        `;
    }
}

// 전역 인스턴스 생성
window.componentLoader = new ComponentLoader();
