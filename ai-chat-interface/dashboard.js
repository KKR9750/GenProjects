const { useState, useEffect } = React;

const Dashboard = () => {
    const [systemStatus, setSystemStatus] = useState({
        crewai: 'unknown',
        metagpt: 'unknown',
        database: 'unknown',
        dashboard: 'active'
    });
    const [isLoading, setIsLoading] = useState(true);
    const [authToken, setAuthToken] = useState(null);
    const [showAuthModal, setShowAuthModal] = useState(false);
    const [authData, setAuthData] = useState({
        user_id: '',
        email: '',
        role: 'user'
    });

    const systems = [
        {
            id: 'crewai',
            name: 'CrewAI Platform',
            description: '협업 기반 AI 에이전트 팀 시스템',
            path: '/crewai',
            api: '/api/crewai',
            features: [
                '3개 역할 기반 협업',
                'Supabase DB 연동',
                'WebSocket 실시간 통신',
                '프로젝트 관리 시스템'
            ],
            roles: ['Researcher', 'Writer', 'Planner'],
            icon: '🤝',
            color: '#4F46E5'
        },
        {
            id: 'metagpt',
            name: 'MetaGPT Platform',
            description: '단계별 승인 기반 전문 개발팀',
            path: '/metagpt',
            api: '/api/metagpt',
            features: [
                '5단계 승인 프로세스',
                '전문 개발팀 시뮬레이션',
                'PRD → 설계 → 개발 → 테스트',
                '코드 생성 및 문서화'
            ],
            roles: ['Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'],
            icon: '🏗️',
            color: '#059669'
        }
    ];

    // 시스템 상태 체크
    const checkSystemStatus = async () => {
        setIsLoading(true);
        const newStatus = { dashboard: 'active' };

        try {
            // Health check API 호출
            const healthData = await window.apiClient.getHealthStatus();

            newStatus.crewai = healthData.services?.crewai || 'unavailable';
            newStatus.metagpt = healthData.services?.metagpt || 'unavailable';
            newStatus.database = healthData.database?.connected ? 'available' : 'unavailable';


        } catch (error) {
            console.error('시스템 상태 체크 실패:', error);
            newStatus.crewai = 'error';
            newStatus.metagpt = 'error';
            newStatus.database = 'error';
        }

        // 시스템별 상태는 health API 결과를 사용
        // 개별 시스템 API 호출 제거 (프로젝트 섹션 불필요)

        setSystemStatus(newStatus);
        setIsLoading(false);
    };


    // 인증 토큰 생성
    const generateAuthToken = async () => {
        try {
            const result = await window.apiClient.generateAuthToken(authData);

            if (result.success) {
                setAuthToken(result.token);
                setShowAuthModal(false);
                window.UIHelpers.showNotification('인증 토큰이 생성되었습니다', 'success');

            } else {
                window.UIHelpers.showNotification(result.error || '토큰 생성에 실패했습니다', 'error');
            }
        } catch (error) {
            console.error('토큰 생성 실패:', error);
            window.UIHelpers.showNotification('토큰 생성 중 오류가 발생했습니다', 'error');
        }
    };

    // 토큰 검증
    const verifyToken = async () => {
        if (!authToken) {
            setAuthToken(null);
            return false;
        }

        try {
            const result = await window.apiClient.verifyToken();

            if (!result.success) {
                setAuthToken(null);
                window.UIHelpers.showNotification('토큰이 만료되었습니다', 'warning');
                return false;
            }

            return true;
        } catch (error) {
            console.error('토큰 검증 실패:', error);
            setAuthToken(null);
            return false;
        }
    };

    // 로그아웃
    const logout = () => {
        setAuthToken(null);
        window.apiClient.removeToken();
        window.UIHelpers.showNotification('로그아웃되었습니다', 'info');
    };

    useEffect(() => {
        // 페이지 로드 시 기존 토큰 확인
        const existingToken = localStorage.getItem('auth_token');
        if (existingToken) {
            setAuthToken(existingToken);
            window.apiClient.setToken(existingToken);
        }

        checkSystemStatus();

        // 30초마다 상태 체크
        const interval = setInterval(() => {
            checkSystemStatus();
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'online': return '🟢';
            case 'offline': return '🔴';
            case 'active': return '🟢';
            default: return '🟡';
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'online': return '온라인';
            case 'offline': return '오프라인';
            case 'active': return '활성';
            default: return '확인중';
        }
    };

    const handleSystemAccess = (system) => {
        // 통합 포트에서 각 시스템 인터페이스로 이동
        window.location.href = system.path;
    };

    const startCrewAIServer = async () => {
        try {
            await fetch('/api/services/crewai/start', { method: 'POST' });
            // 5초 후 상태 재체크
            setTimeout(checkSystemStatus, 5000);
        } catch (error) {
            console.error('CrewAI 서버 시작 실패:', error);
        }
    };


    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div className="header-content">
                    <div className="header-left">
                        <h1>🚀 AI 개발 플랫폼 통합 대시보드</h1>
                    </div>
                    <div className="header-right">
                        <div className="system-overview">
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.dashboard)}</span>
                                <span className="status-text">대시보드</span>
                            </div>
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.database)}</span>
                                <span className="status-text">데이터베이스</span>
                            </div>
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.crewai)}</span>
                                <span className="status-text">CrewAI</span>
                            </div>
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.metagpt)}</span>
                                <span className="status-text">MetaGPT</span>
                            </div>
                            <div className="auth-section">
                                {authToken ? (
                                    <div className="auth-info">
                                        <span className="auth-status">🔐 인증됨</span>
                                        <button
                                            className="auth-button logout"
                                            onClick={logout}
                                        >
                                            로그아웃
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        className="auth-button login"
                                        onClick={() => setShowAuthModal(true)}
                                    >
                                        🔑 로그인
                                    </button>
                                )}
                            </div>
                            <button
                                className="refresh-button"
                                onClick={() => {
                                    checkSystemStatus();
                                }}
                                disabled={isLoading}
                            >
                                {isLoading ? '🔄' : '🔄'} 새로고침
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="dashboard-main">
                <section className="systems-grid">
                    {systems.map(system => {
                        return (
                            <div key={system.id} className="system-row">
                                <div
                                    className={`system-card ${systemStatus[system.id]}`}
                                    onClick={() => handleSystemAccess(system)}
                                >
                                    <div className="system-header">
                                        <div className="system-icon" style={{ color: system.color }}>
                                            {system.icon}
                                        </div>
                                        <div className="system-info">
                                            <h3>{system.name}</h3>
                                            <p>{system.description}</p>
                                        </div>
                                        <div className="system-status">
                                            <span className="status-indicator">
                                                {getStatusIcon(systemStatus[system.id])}
                                            </span>
                                            <span className="status-text">
                                                {getStatusText(systemStatus[system.id])}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="system-details">
                                        <div className="port-info">
                                            <span className="label">경로:</span>
                                            <span className="value">{system.path}</span>
                                        </div>

                                        <div className="roles-info">
                                            <span className="label">역할:</span>
                                            <div className="roles-list">
                                                {system.roles.map((role, index) => (
                                                    <span key={index} className="role-tag">
                                                        {role}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="features-info">
                                            <span className="label">주요 기능:</span>
                                            <ul className="features-list">
                                                {system.features.map((feature, index) => (
                                                    <li key={index}>{feature}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>

                                    <div className="system-actions">
                                        <button
                                            className="access-button online"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleSystemAccess(system);
                                            }}
                                        >
                                            접속하기
                                        </button>
                                    </div>
                                </div>

                            </div>
                        );
                    })}
                </section>


            </main>

            <footer className="dashboard-footer">
                <div className="footer-content">
                    <span>AI Development Platform Integration Dashboard</span>
                    <span>통합 포트: 3000</span>
                    <span>경로: /crewai, /metagpt</span>
                </div>
            </footer>

            {/* 인증 모달 */}
            {showAuthModal && (
                <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>🔑 JWT 인증 토큰 생성</h2>
                            <button
                                className="modal-close"
                                onClick={() => setShowAuthModal(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="modal-body">
                            <p className="modal-description">
                                데이터베이스에 안전하게 접근하기 위한 JWT 토큰을 생성합니다.
                                개발 환경에서는 아래 정보로 데모 토큰을 생성할 수 있습니다.
                            </p>

                            <div className="form-group">
                                <label>사용자 ID</label>
                                <input
                                    type="text"
                                    value={authData.user_id}
                                    onChange={(e) => setAuthData({
                                        ...authData,
                                        user_id: e.target.value
                                    })}
                                    placeholder="사용자 ID를 입력하세요"
                                    className="form-input"
                                />
                            </div>

                            <div className="form-group">
                                <label>이메일</label>
                                <input
                                    type="email"
                                    value={authData.email}
                                    onChange={(e) => setAuthData({
                                        ...authData,
                                        email: e.target.value
                                    })}
                                    placeholder="이메일을 입력하세요"
                                    className="form-input"
                                />
                            </div>

                            <div className="form-group">
                                <label>역할</label>
                                <select
                                    value={authData.role}
                                    onChange={(e) => setAuthData({
                                        ...authData,
                                        role: e.target.value
                                    })}
                                    className="form-select"
                                >
                                    <option value="user">사용자</option>
                                    <option value="admin">관리자</option>
                                    <option value="developer">개발자</option>
                                </select>
                            </div>

                            <div className="info-box">
                                <div className="info-icon">ℹ️</div>
                                <div className="info-content">
                                    <h4>JWT 토큰 정보</h4>
                                    <ul>
                                        <li>토큰은 24시간 동안 유효합니다</li>
                                        <li>브라우저의 로컬 스토리지에 안전하게 저장됩니다</li>
                                        <li>API 요청 시 자동으로 헤더에 포함됩니다</li>
                                        <li>만료 시 자동으로 로그아웃됩니다</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button
                                className="modal-button secondary"
                                onClick={() => setShowAuthModal(false)}
                            >
                                취소
                            </button>
                            <button
                                className="modal-button primary"
                                onClick={generateAuthToken}
                            >
                                토큰 생성
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Dashboard />);