/**
 * API Utilities for AI Chat Interface
 * Database integration and authentication helpers
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.token = localStorage.getItem('auth_token');
    }

    // ==================== AUTHENTICATION ====================

    setToken(token) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }

    removeToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // ==================== HTTP METHODS ====================

    async request(method, url, data = null) {
        const config = {
            method,
            headers: this.getAuthHeaders()
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }

            return result;
        } catch (error) {
            console.error(`API ${method} ${url}:`, error);
            throw error;
        }
    }

    async get(url) {
        return this.request('GET', url);
    }

    async post(url, data) {
        return this.request('POST', url, data);
    }

    async put(url, data) {
        return this.request('PUT', url, data);
    }

    async delete(url) {
        return this.request('DELETE', url);
    }

    // ==================== AUTHENTICATION API ====================

    async generateAuthToken(userData = {}) {
        const data = {
            user_id: userData.user_id || 'demo-user',
            email: userData.email || 'demo@example.com',
            role: userData.role || 'user'
        };

        const result = await this.post('/api/v2/auth/token', data);

        if (result.success && result.token) {
            this.setToken(result.token);
        }

        return result;
    }

    async verifyToken() {
        if (!this.token) {
            return { success: false, error: '토큰이 없습니다' };
        }

        try {
            return await this.post('/api/v2/auth/verify');
        } catch (error) {
            this.removeToken();
            return { success: false, error: error.message };
        }
    }

    // ==================== PROJECT API ====================

    async getProjects(limit = 20) {
        return this.get(`/api/v2/projects?limit=${limit}`);
    }

    async createProject(projectData) {
        return this.post('/api/v2/projects', projectData);
    }

    async getProject(projectId) {
        return this.get(`/api/v2/projects/${projectId}`);
    }

    async updateProject(projectId, updateData) {
        return this.put(`/api/v2/projects/${projectId}`, updateData);
    }

    // ==================== ROLE-LLM MAPPING API ====================

    async setRoleLLMMapping(projectId, mappings) {
        return this.post(`/api/v2/projects/${projectId}/role-llm-mapping`, {
            mappings
        });
    }

    async getRoleLLMMapping(projectId) {
        return this.get(`/api/v2/projects/${projectId}/role-llm-mapping`);
    }

    // ==================== HEALTH CHECK API ====================

    async getHealthStatus() {
        return this.get('/api/health');
    }

    // ==================== LEGACY API METHODS ====================

    async getLegacyProjects() {
        return this.get('/api/projects');
    }

    async sendCrewAIRequest(data) {
        return this.post('/api/crewai', data);
    }

    async sendMetaGPTRequest(data) {
        return this.post('/api/metagpt', data);
    }
}

// ==================== UI HELPERS ====================

class UIHelpers {
    static showNotification(message, type = 'info') {
        // Simple notification implementation
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#10B981';
                break;
            case 'error':
                notification.style.backgroundColor = '#EF4444';
                break;
            case 'warning':
                notification.style.backgroundColor = '#F59E0B';
                break;
            default:
                notification.style.backgroundColor = '#3B82F6';
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    static formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return '날짜 없음';
        }
    }

    static truncateText(text, maxLength = 100) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    static getStatusBadgeClass(status) {
        const statusClasses = {
            'planning': 'status-planning',
            'in_progress': 'status-progress',
            'completed': 'status-completed',
            'paused': 'status-paused',
            'failed': 'status-failed'
        };

        return statusClasses[status] || 'status-unknown';
    }

    static calculateProgress(current, total) {
        if (!total || total === 0) return 0;
        return Math.round((current / total) * 100);
    }
}

// ==================== LOCAL STORAGE HELPERS ====================

class StorageHelpers {
    static setItem(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('localStorage setItem error:', error);
        }
    }

    static getItem(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('localStorage getItem error:', error);
            return defaultValue;
        }
    }

    static removeItem(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('localStorage removeItem error:', error);
        }
    }

    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('localStorage clear error:', error);
        }
    }
}

// ==================== CONSTANTS ====================

const LLM_MODELS = [
    { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI' },
    { id: 'gpt-4o', name: 'GPT-4o', description: '멀티모달 최신 모델', provider: 'OpenAI' },
    { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic' },
    { id: 'claude-3-haiku', name: 'Claude-3 Haiku', description: '빠른 응답 모델', provider: 'Anthropic' },
    { id: 'gemini-pro', name: 'Gemini Pro', description: '멀티모달 모델', provider: 'Google' },
    { id: 'gemini-ultra', name: 'Gemini Ultra', description: '최고 성능 모델', provider: 'Google' },
    { id: 'llama-3', name: 'Llama-3 70B', description: '오픈소스 모델', provider: 'Meta' },
    { id: 'llama-3-8b', name: 'Llama-3 8B', description: '경량 오픈소스 모델', provider: 'Meta' },
    { id: 'mistral-large', name: 'Mistral Large', description: '효율성 중심 모델', provider: 'Mistral' },
    { id: 'mistral-7b', name: 'Mistral 7B', description: '경량 효율 모델', provider: 'Mistral' },
    { id: 'deepseek-coder', name: 'DeepSeek Coder', description: '코딩 전문 모델', provider: 'DeepSeek' },
    { id: 'codellama', name: 'Code Llama', description: '코드 생성 특화', provider: 'Meta' }
];

const AI_FRAMEWORKS = {
    'crew-ai': {
        name: 'CrewAI',
        roles: ['Researcher', 'Writer', 'Planner'],
        description: '협업 기반 AI 에이전트 시스템'
    },
    'meta-gpt': {
        name: 'MetaGPT',
        roles: ['Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'],
        description: '단계별 승인 기반 전문 개발팀'
    }
};

const PROJECT_TYPES = [
    { id: 'web_app', name: '웹 애플리케이션', description: '웹 기반 애플리케이션 개발' },
    { id: 'mobile_app', name: '모바일 앱', description: '모바일 애플리케이션 개발' },
    { id: 'api', name: 'API 서버', description: 'RESTful API 서버 개발' },
    { id: 'desktop', name: '데스크톱 앱', description: '데스크톱 애플리케이션 개발' },
    { id: 'data_analysis', name: '데이터 분석', description: '데이터 분석 및 시각화' }
];

// ==================== EXPORT ====================

// Global API client instance
window.apiClient = new APIClient();
window.UIHelpers = UIHelpers;
window.StorageHelpers = StorageHelpers;
window.LLM_MODELS = LLM_MODELS;
window.AI_FRAMEWORKS = AI_FRAMEWORKS;
window.PROJECT_TYPES = PROJECT_TYPES;