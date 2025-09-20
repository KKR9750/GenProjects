const { useState, useEffect, createElement: e } = React;

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
        user_id: 'demo-user',
        email: 'demo@example.com',
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

    // React.createElement로 JSX 대체
    return e('div', { className: 'dashboard-container' },
        // Header
        e('header', { className: 'dashboard-header' },
            e('div', { className: 'header-content' },
                e('div', { className: 'header-left' },
                    e('h1', null, '🚀 AI 개발 플랫폼 통합 대시보드'),
                    e('p', null, 'CrewAI와 MetaGPT를 통합 관리하는 중앙 제어 센터')
                ),
                e('div', { className: 'header-right' },
                    e('div', { className: 'system-overview' },
                        e('div', { className: 'status-item' },
                            e('span', { className: 'status-icon' }, getStatusIcon(systemStatus.dashboard)),
                            e('span', { className: 'status-text' }, '대시보드')
                        ),
                        e('div', { className: 'status-item' },
                            e('span', { className: 'status-icon' }, getStatusIcon(systemStatus.database)),
                            e('span', { className: 'status-text' }, '데이터베이스')
                        ),
                        e('div', { className: 'status-item' },
                            e('span', { className: 'status-icon' }, getStatusIcon(systemStatus.crewai)),
                            e('span', { className: 'status-text' }, 'CrewAI')
                        ),
                        e('div', { className: 'status-item' },
                            e('span', { className: 'status-icon' }, getStatusIcon(systemStatus.metagpt)),
                            e('span', { className: 'status-text' }, 'MetaGPT')
                        ),
                        e('div', { className: 'auth-section' },
                            authToken ?
                                e('div', { className: 'auth-info' },
                                    e('span', { className: 'auth-status' }, '🔐 인증됨'),
                                    e('button', {
                                        className: 'auth-button logout',
                                        onClick: logout
                                    }, '로그아웃')
                                ) :
                                e('button', {
                                    className: 'auth-button login',
                                    onClick: () => setShowAuthModal(true)
                                }, '🔑 로그인')
                        ),
                        e('button', {
                            className: 'refresh-button',
                            onClick: () => checkSystemStatus(),
                            disabled: isLoading
                        }, `${isLoading ? '🔄' : '🔄'} 새로고침`)
                    )
                )
            )
        ),
        // Main content
        e('main', { className: 'dashboard-main' },
            e('section', { className: 'systems-grid' },
                ...systems.map(system =>
                    e('div', { key: system.id, className: 'system-row' },
                        e('div', {
                            className: `system-card ${systemStatus[system.id]}`,
                            onClick: () => handleSystemAccess(system)
                        },
                            e('div', { className: 'system-header' },
                                e('div', {
                                    className: 'system-icon',
                                    style: { color: system.color }
                                }, system.icon),
                                e('div', { className: 'system-info' },
                                    e('h3', null, system.name),
                                    e('p', null, system.description)
                                ),
                                e('div', { className: 'system-status' },
                                    e('span', { className: 'status-indicator' },
                                        getStatusIcon(systemStatus[system.id])
                                    ),
                                    e('span', { className: 'status-text' },
                                        getStatusText(systemStatus[system.id])
                                    )
                                )
                            ),
                            e('div', { className: 'system-details' },
                                e('div', { className: 'port-info' },
                                    e('span', { className: 'label' }, '경로:'),
                                    e('span', { className: 'value' }, system.path)
                                ),
                                e('div', { className: 'roles-info' },
                                    e('span', { className: 'label' }, '역할:'),
                                    e('div', { className: 'roles-list' },
                                        ...system.roles.map((role, index) =>
                                            e('span', {
                                                key: index,
                                                className: 'role-tag'
                                            }, role)
                                        )
                                    )
                                ),
                                e('div', { className: 'features-info' },
                                    e('span', { className: 'label' }, '주요 기능:'),
                                    e('ul', { className: 'features-list' },
                                        ...system.features.map((feature, index) =>
                                            e('li', { key: index }, feature)
                                        )
                                    )
                                )
                            ),
                            e('div', { className: 'system-actions' },
                                e('button', {
                                    className: 'access-button online',
                                    onClick: (ev) => {
                                        ev.stopPropagation();
                                        handleSystemAccess(system);
                                    }
                                }, '접속하기')
                            )
                        )
                    )
                )
            )
        ),
        // Footer
        e('footer', { className: 'dashboard-footer' },
            e('div', { className: 'footer-content' },
                e('span', null, 'AI Development Platform Integration Dashboard'),
                e('span', null, '통합 포트: 3000'),
                e('span', null, '경로: /crewai, /metagpt')
            )
        ),
        // Auth Modal
        showAuthModal && e('div', {
            className: 'modal-overlay',
            onClick: () => setShowAuthModal(false)
        },
            e('div', {
                className: 'modal-content',
                onClick: (ev) => ev.stopPropagation()
            },
                e('div', { className: 'modal-header' },
                    e('h2', null, '🔑 JWT 인증 토큰 생성'),
                    e('button', {
                        className: 'modal-close',
                        onClick: () => setShowAuthModal(false)
                    }, '✕')
                ),
                e('div', { className: 'modal-body' },
                    e('p', { className: 'modal-description' },
                        '데이터베이스에 안전하게 접근하기 위한 JWT 토큰을 생성합니다. 개발 환경에서는 아래 정보로 데모 토큰을 생성할 수 있습니다.'
                    ),
                    e('div', { className: 'form-group' },
                        e('label', null, '사용자 ID'),
                        e('input', {
                            type: 'text',
                            value: authData.user_id,
                            onChange: (ev) => setAuthData({
                                ...authData,
                                user_id: ev.target.value
                            }),
                            placeholder: '사용자 ID를 입력하세요',
                            className: 'form-input'
                        })
                    ),
                    e('div', { className: 'form-group' },
                        e('label', null, '이메일'),
                        e('input', {
                            type: 'email',
                            value: authData.email,
                            onChange: (ev) => setAuthData({
                                ...authData,
                                email: ev.target.value
                            }),
                            placeholder: '이메일을 입력하세요',
                            className: 'form-input'
                        })
                    ),
                    e('div', { className: 'form-group' },
                        e('label', null, '역할'),
                        e('select', {
                            value: authData.role,
                            onChange: (ev) => setAuthData({
                                ...authData,
                                role: ev.target.value
                            }),
                            className: 'form-select'
                        },
                            e('option', { value: 'user' }, '사용자'),
                            e('option', { value: 'admin' }, '관리자'),
                            e('option', { value: 'developer' }, '개발자')
                        )
                    ),
                    e('div', { className: 'info-box' },
                        e('div', { className: 'info-icon' }, 'ℹ️'),
                        e('div', { className: 'info-content' },
                            e('h4', null, 'JWT 토큰 정보'),
                            e('ul', null,
                                e('li', null, '토큰은 24시간 동안 유효합니다'),
                                e('li', null, '브라우저의 로컬 스토리지에 안전하게 저장됩니다'),
                                e('li', null, 'API 요청 시 자동으로 헤더에 포함됩니다'),
                                e('li', null, '만료 시 자동으로 로그아웃됩니다')
                            )
                        )
                    )
                ),
                e('div', { className: 'modal-footer' },
                    e('button', {
                        className: 'modal-button secondary',
                        onClick: () => setShowAuthModal(false)
                    }, '취소'),
                    e('button', {
                        className: 'modal-button primary',
                        onClick: generateAuthToken
                    }, '토큰 생성')
                )
            )
        )
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(Dashboard));