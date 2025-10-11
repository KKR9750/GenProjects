/**
 * ComponentLoader
 * SPA 탭 구조에서 페이지별 CSS/JS를 동적으로 교체하는 로더
 */

class ComponentLoader {
    constructor() {
        this.currentPage = null;
        this.loadedCSS = [];
    }

    async switchComponent(pageName) {
        if (this.currentPage === pageName) {
            return;
        }

        this.showLoading();
        this.removeOldCSS();

        try {
            await this.loadCSS(pageName);
            await this.loadComponent(pageName);
            this.currentPage = pageName;
            this.playFadeIn();
        } catch (error) {
            console.error('컴포넌트 로드 실패 (' + pageName + '):', error);
            this.showError(pageName, error);
        }
    }

    async loadCSS(pageName) {
        const cssFile = this.getCSSFileName(pageName);
        if (!cssFile) return;

        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = cssFile;
            link.id = 'css-' + pageName;
            link.setAttribute('data-component', pageName + '-css');

            link.onload = () => {
                this.loadedCSS.push(pageName);
                resolve();
            };
            link.onerror = () => reject(new Error('CSS 로드 실패: ' + cssFile));

            document.head.appendChild(link);
        });
    }

    removeOldCSS() {
        this.loadedCSS.forEach(page => {
            const link = document.getElementById('css-' + page);
            if (link) link.remove();
        });
        this.loadedCSS = [];
    }

    async loadComponent(pageName) {
        document.querySelectorAll('script[data-component]').forEach(script => script.remove());

        const root = document.getElementById('root');
        if (root) {
            root.innerHTML = '';
        }

        switch (pageName) {
            case 'dashboard':
                await this.loadScript('dashboard-pure.js', 'dashboard');
                break;
            case 'crewai':
                await this.loadBabelScript('crewai.js?v=7', 'crewai');
                break;
            case 'metagpt':
                await this.loadBabelScript('metagpt.js?v=4', 'metagpt');
                break;
            case 'admin':
                await this.loadAdmin();
                break;
            case 'projects':
                await this.loadProjects();
                break;
            case 'pre_analysis':
            case 'agent_manager':
                await this.loadHtmlComponent(pageName);
                break;
            default:
                throw new Error('알 수 없는 페이지: ' + pageName);
        }
    }

    async loadScript(src, key) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.setAttribute('data-component', key);
            script.onload = resolve;
            script.onerror = () => reject(new Error(src + ' 로드 실패'));
            document.body.appendChild(script);
        });
    }

    async loadBabelScript(src, key) {
        const response = await fetch(src);
        if (!response.ok) throw new Error(src + ' 로드 실패');
        const code = await response.text();

        const script = document.createElement('script');
        script.type = 'text/babel';
        script.textContent = '(function()\n{' + '\n' + code + '\n})();';
        script.setAttribute('data-component', key);
        document.body.appendChild(script);

        if (window.Babel) {
            window.Babel.transformScriptTags();
        }

        await new Promise(resolve => setTimeout(resolve, 100));
    }

    async loadAdmin() {
        await this.loadScriptWithCss('admin.js?v=16', 'admin', 'admin.css?v=11');
    }

    async loadProjects() {
        await this.loadScriptWithCss('projects.js?v=22', 'projects', 'projects.css?v=22');
    }

    async loadScriptWithCss(jsSrc, key, cssSrc) {
        document.querySelectorAll('script[data-component="' + key + '"]').forEach(el => el.remove());
        document.querySelectorAll('link[data-component="' + key + '-css"]').forEach(el => el.remove());

        if (cssSrc) {
            await new Promise((resolve, reject) => {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = cssSrc;
                link.setAttribute('data-component', key + '-css');
                link.onload = resolve;
                link.onerror = () => reject(new Error(cssSrc + ' 로드 실패'));
                document.head.appendChild(link);
            });
        }

        await this.loadScript(jsSrc, key);
    }

    async loadHtmlComponent(pageName) {
        const response = await fetch(pageName + '.html?v=1');
        if (!response.ok) {
            throw new Error(pageName + '.html 로드 실패: ' + response.statusText);
        }
        const html = await response.text();

        const root = document.getElementById('root');
        root.innerHTML = html;

        const scripts = Array.from(root.querySelectorAll('script'));
        for (const original of scripts) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                Array.from(original.attributes).forEach(attr => {
                    script.setAttribute(attr.name, attr.value);
                });
                if (original.src) {
                    script.onload = resolve;
                    script.onerror = reject;
                    script.src = original.src;
                } else {
                    script.text = original.text;
                    resolve();
                }
                root.appendChild(script);
            });
        }
    }

    playFadeIn() {
        const contentArea = document.getElementById('content-area');
        if (!contentArea) return;
        contentArea.classList.add('fade-in');
        setTimeout(() => contentArea.classList.remove('fade-in'), 300);
    }

    getCSSFileName(pageName) {
        const map = {
            dashboard: 'dashboard.css',
            crewai: 'crewai.css?v=7',
            metagpt: 'metagpt.css?v=4',
            admin: 'admin.css?v=11',
            projects: 'projects.css?v=22',
            pre_analysis: 'pre_analysis.css',
            agent_manager: 'agent_manager.css'
        };
        return map[pageName] || null;
    }

    showLoading() {
        const root = document.getElementById('root');
        if (root) {
            root.innerHTML = '<div class="loading">컴포넌트 로딩 중</div>';
        }
    }

    showError(pageName, error) {
        const root = document.getElementById('root');
        if (!root) return;
        const html = [
            '<div style="padding:2rem; text-align:center; color:#ef4444;">',
            '  <h2 style="font-size:1.25rem; margin-bottom:1rem;">⚠️ 로드 실패</h2>',
            '  <p style="color:#6b7280;">' + pageName + ' 페이지를 불러올 수 없습니다.<br>' + error.message + '</p>',
            '  <button onclick="location.reload()" style="margin-top:1rem; padding:0.5rem 1rem; border-radius:0.5rem; background:#3b82f6; color:#fff; border:none; cursor:pointer;">새로고침</button>',
            '</div>'
        ].join('');
        root.innerHTML = html;
    }
}

window.componentLoader = new ComponentLoader();
