const { useState, useEffect, useRef, createElement: e } = React;

const CrewAIInterface = () => {
    const [selectedRole, setSelectedRole] = useState('researcher');
    const [roleLLMMapping, setRoleLLMMapping] = useState({
        researcher: 'gpt-4',
        writer: 'claude-3',
        planner: 'gpt-4o'
    });
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState('connecting');

    const roles = [
        { id: 'researcher', name: 'Researcher', description: '정보 수집 및 분석 전문가', icon: '🔍' },
        { id: 'writer', name: 'Writer', description: '콘텐츠 생성 및 문서화 전문가', icon: '✍️' },
        { id: 'planner', name: 'Planner', description: '전략 수립 및 계획 전문가', icon: '📋' }
    ];

    // LLM 모델 목록 (동적으로 로드됨)
    let llmOptions = [];

    // LLM 모델 동적 로드
    const loadLLMModels = async () => {
        try {
            const response = await fetch('/api/llm/models');
            const data = await response.json();

            if (data.success) {
                llmOptions = data.models.map(model => ({
                    id: model.id,
                    name: model.name,
                    description: model.description || '',
                    provider: model.provider,
                    type: model.type || 'cloud',
                    parameter_size: model.parameter_size
                }));
                console.log('LLM 모델 로드 완료:', llmOptions.length, '개');
            } else {
                console.error('LLM 모델 로드 실패:', data.error);
                // 기본 모델 설정
                llmOptions = [
                    { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                    { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
                ];
            }
        } catch (error) {
            console.error('LLM 모델 로드 오류:', error);
            // 기본 모델 설정
            llmOptions = [
                { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
            ];
        }
    };

    // 연결 상태 체크
    const checkConnection = async () => {
        try {
            const response = await fetch('/api/health');
            setConnectionStatus(response.ok ? 'connected' : 'disconnected');
        } catch (error) {
            setConnectionStatus('disconnected');
        }
    };

    // 메시지 전송
    const sendMessage = async () => {
        if (!inputText.trim()) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputText,
            role: selectedRole,
            llm: roleLLMMapping[selectedRole],
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const response = await fetch('/api/crewai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: inputText,
                    role: selectedRole,
                    llm_model: roleLLMMapping[selectedRole]
                })
            });

            const data = await response.json();

            const aiMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: data.response || '응답을 받을 수 없습니다.',
                role: selectedRole,
                llm: roleLLMMapping[selectedRole],
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('메시지 전송 실패:', error);
            const errorMessage = {
                id: Date.now() + 1,
                type: 'error',
                content: '메시지 전송 중 오류가 발생했습니다.',
                timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    // 대시보드로 이동
    const goToDashboard = () => {
        window.location.href = '/';
    };

    // 역할 변경
    const handleRoleChange = (roleId) => {
        setSelectedRole(roleId);
    };

    // LLM 변경
    const handleLLMChange = (roleId, llmId) => {
        setRoleLLMMapping(prev => ({
            ...prev,
            [roleId]: llmId
        }));
    };

    // 엔터 키 처리
    const handleKeyPress = (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    };

    useEffect(() => {
        const initializeInterface = async () => {
            await loadLLMModels();
            checkConnection();
        };

        initializeInterface();
        const interval = setInterval(checkConnection, 30000);
        return () => clearInterval(interval);
    }, []);

    return e('div', { className: 'crewai-container' },
        // Header
        e('header', { className: 'crewai-header' },
            e('div', { className: 'header-left' },
                e('button', {
                    className: 'dashboard-btn',
                    onClick: goToDashboard
                }, '← 대시보드'),
                e('div', { className: 'header-title' },
                    e('h1', null, '🤝 CrewAI Platform'),
                    e('div', { className: 'header-status' },
                        e('span', { className: 'project-indicator' }, '새 프로젝트'),
                        e('span', {
                            className: `connection-status ${connectionStatus}`
                        }, connectionStatus === 'connected' ? '🟢 연결됨' : '🔴 연결 안됨')
                    )
                )
            )
        ),

        // Main Content
        e('main', { className: 'crewai-main' },
            // Left Sidebar - Role & LLM Selection
            e('aside', { className: 'crewai-sidebar' },
                e('div', { className: 'section' },
                    e('h3', null, '🎭 역할 선택'),
                    e('div', { className: 'roles-grid' },
                        ...roles.map(role =>
                            e('div', {
                                key: role.id,
                                className: `role-card ${selectedRole === role.id ? 'selected' : ''}`,
                                onClick: () => handleRoleChange(role.id)
                            },
                                e('div', { className: 'role-icon' }, role.icon),
                                e('div', { className: 'role-info' },
                                    e('h4', null, role.name),
                                    e('p', null, role.description)
                                )
                            )
                        )
                    )
                ),

                e('div', { className: 'section' },
                    e('h3', null, '🧠 LLM 모델 설정'),
                    ...roles.map(role =>
                        e('div', {
                            key: role.id,
                            className: 'llm-mapping'
                        },
                            e('label', null, `${role.icon} ${role.name}`),
                            e('select', {
                                value: roleLLMMapping[role.id],
                                onChange: (ev) => handleLLMChange(role.id, ev.target.value)
                            },
                                ...llmOptions.map(llm =>
                                    e('option', {
                                        key: llm.id,
                                        value: llm.id
                                    }, `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name} (${llm.provider})${llm.parameter_size ? ` [${llm.parameter_size}]` : ''}`)
                                )
                            )
                        )
                    )
                )
            ),

            // Chat Area
            e('div', { className: 'chat-container' },
                e('div', { className: 'chat-header' },
                    e('h2', null, `${roles.find(r => r.id === selectedRole)?.icon} ${roles.find(r => r.id === selectedRole)?.name} 채팅`),
                    e('span', { className: 'current-llm' },
                        (() => {
                            const llm = llmOptions.find(l => l.id === roleLLMMapping[selectedRole]);
                            return `모델: ${llm ? `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name}` : 'Unknown'}`;
                        })()
                    )
                ),

                e('div', { className: 'messages-area' },
                    messages.length === 0 ?
                        e('div', { className: 'welcome-message' },
                            e('h3', null, '🤝 CrewAI와 함께 작업을 시작하세요!'),
                            e('p', null, '선택한 역할과 LLM 모델로 대화를 시작할 수 있습니다.'),
                            e('ul', null,
                                e('li', null, '🔍 Researcher: 정보 수집 및 분석'),
                                e('li', null, '✍️ Writer: 콘텐츠 생성 및 문서화'),
                                e('li', null, '📋 Planner: 전략 수립 및 계획')
                            )
                        ) :
                        messages.map(message =>
                            e('div', {
                                key: message.id,
                                className: `message ${message.type}`
                            },
                                e('div', { className: 'message-header' },
                                    e('span', { className: 'message-role' },
                                        message.type === 'user' ? '👤 사용자' :
                                        message.type === 'ai' ? `🤖 ${roles.find(r => r.id === message.role)?.name}` :
                                        '⚠️ 오류'
                                    ),
                                    message.llm && e('span', { className: 'message-llm' },
                                        (() => {
                                            const llm = llmOptions.find(l => l.id === message.llm);
                                            return llm ? `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name}` : 'Unknown';
                                        })()
                                    )
                                ),
                                e('div', { className: 'message-content' }, message.content)
                            )
                        )
                ),

                e('div', { className: 'input-area' },
                    e('div', { className: 'input-container' },
                        e('textarea', {
                            value: inputText,
                            onChange: (ev) => setInputText(ev.target.value),
                            onKeyPress: handleKeyPress,
                            placeholder: `${roles.find(r => r.id === selectedRole)?.name}에게 메시지를 보내세요...`,
                            rows: 3,
                            disabled: isLoading
                        }),
                        e('button', {
                            onClick: sendMessage,
                            disabled: isLoading || !inputText.trim(),
                            className: 'send-button'
                        }, isLoading ? '⏳ 전송 중...' : '📤 전송')
                    )
                )
            )
        )
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(CrewAIInterface));