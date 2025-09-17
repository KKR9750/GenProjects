const { useState, useEffect } = React;

const Dashboard = () => {
    const [systemStatus, setSystemStatus] = useState({
        crewai: 'unknown',
        metagpt: 'unknown',
        dashboard: 'active'
    });
    const [isLoading, setIsLoading] = useState(true);

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

        for (const system of systems) {
            try {
                const response = await fetch(`${system.api}/projects`, {
                    method: 'GET'
                });
                newStatus[system.id] = response.ok ? 'online' : 'offline';
            } catch (error) {
                newStatus[system.id] = 'offline';
            }
        }

        setSystemStatus(newStatus);
        setIsLoading(false);
    };


    useEffect(() => {
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
                        <p>CrewAI와 MetaGPT를 통합 관리하는 중앙 제어 센터</p>
                    </div>
                    <div className="header-right">
                        <div className="system-overview">
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.dashboard)}</span>
                                <span>대시보드: {getStatusText(systemStatus.dashboard)}</span>
                            </div>
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.crewai)}</span>
                                <span>CrewAI: {getStatusText(systemStatus.crewai)}</span>
                            </div>
                            <div className="status-item">
                                <span className="status-icon">{getStatusIcon(systemStatus.metagpt)}</span>
                                <span>MetaGPT: {getStatusText(systemStatus.metagpt)}</span>
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
        </div>
    );
};

// React 앱 렌더링
ReactDOM.render(<Dashboard />, document.getElementById('root'));