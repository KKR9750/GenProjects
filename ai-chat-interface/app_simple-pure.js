const { useState, useEffect, useRef, createElement: e } = React;

const AIChatInterface = () => {
    const [selectedAI, setSelectedAI] = useState('crew-ai');
    const [selectedRole, setSelectedRole] = useState('');
    const [roleLLMMapping, setRoleLLMMapping] = useState({});
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showProjects, setShowProjects] = useState(false);

    const aiOptions = [
        {
            id: 'crew-ai',
            name: 'CREW AI',
            description: '협업 기반 AI 에이전트',
            roles: [
                { id: 'researcher', name: 'Researcher', description: '정보 수집 및 분석' },
                { id: 'writer', name: 'Writer', description: '콘텐츠 생성 및 문서화' },
                { id: 'planner', name: 'Planner', description: '전략 수립 및 계획' }
            ]
        },
        {
            id: 'meta-gpt',
            name: 'MetaGPT',
            description: '단계별 승인 기반 전문 개발팀',
            roles: [
                { id: 'product-manager', name: 'Product Manager', description: '요구사항 정리 및 PRD 작성' },
                { id: 'architect', name: 'Architect', description: '시스템 설계 및 구조 계획' },
                { id: 'project-manager', name: 'Project Manager', description: '작업 분석 및 계획 수립' },
                { id: 'engineer', name: 'Engineer', description: '코드 개발 및 구현' },
                { id: 'qa-engineer', name: 'QA Engineer', description: '테스트 및 품질 보증' }
            ]
        }
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

    // AI 변경 시 첫 번째 역할 자동 선택
    useEffect(() => {
        const initializeInterface = async () => {
            await loadLLMModels();

            const selectedAIData = aiOptions.find(ai => ai.id === selectedAI);
            if (selectedAIData && selectedAIData.roles.length > 0) {
                setSelectedRole(selectedAIData.roles[0].id);
            }
        };

        initializeInterface();
    }, [selectedAI]);

    // 메시지 전송
    const sendMessage = async () => {
        if (!inputText.trim() || !selectedRole) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputText,
            ai: selectedAI,
            role: selectedRole,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const endpoint = selectedAI === 'crew-ai' ? '/api/crewai' : '/api/metagpt';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: inputText,
                    role: selectedRole,
                    llm_model: roleLLMMapping[selectedRole] || 'gpt-4'
                })
            });

            const data = await response.json();

            const aiMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: data.response || '응답을 받을 수 없습니다.',
                ai: selectedAI,
                role: selectedRole,
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

    // LLM 매핑 변경
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

    // 대시보드로 이동
    const goToDashboard = () => {
        window.location.href = '/dashboard.html';
    };

    const currentAI = aiOptions.find(ai => ai.id === selectedAI);
    const currentRole = currentAI?.roles.find(role => role.id === selectedRole);

    return e('div', { className: 'ai-chat-container' },
        // Header
        e('header', { className: 'chat-header' },
            e('div', { className: 'header-left' },
                e('button', {
                    className: 'dashboard-btn',
                    onClick: goToDashboard
                }, '🏠 대시보드'),
                e('h1', null, '🤖 AI 프로그램 생성 대화창')
            ),
            e('div', { className: 'header-right' },
                e('button', {
                    className: 'projects-btn',
                    onClick: () => setShowProjects(!showProjects)
                }, '📁 프로젝트')
            )
        ),

        // Main Content
        e('div', { className: 'chat-main' },
            // Left Sidebar
            e('aside', { className: 'chat-sidebar' },
                // AI 선택
                e('section', { className: 'ai-selection' },
                    e('h3', null, '🎯 AI 프레임워크'),
                    e('div', { className: 'ai-options' },
                        ...aiOptions.map(ai =>
                            e('div', {
                                key: ai.id,
                                className: `ai-option ${selectedAI === ai.id ? 'selected' : ''}`,
                                onClick: () => setSelectedAI(ai.id)
                            },
                                e('h4', null, ai.name),
                                e('p', null, ai.description),
                                e('span', { className: 'role-count' }, `${ai.roles.length}개 역할`)
                            )
                        )
                    )
                ),

                // 역할 선택
                currentAI && e('section', { className: 'role-selection' },
                    e('h3', null, '👥 역할 선택'),
                    e('div', { className: 'role-options' },
                        ...currentAI.roles.map(role =>
                            e('div', {
                                key: role.id,
                                className: `role-option ${selectedRole === role.id ? 'selected' : ''}`,
                                onClick: () => setSelectedRole(role.id)
                            },
                                e('h4', null, role.name),
                                e('p', null, role.description)
                            )
                        )
                    )
                ),

                // LLM 모델 설정
                currentAI && e('section', { className: 'llm-mapping' },
                    e('h3', null, '🧠 LLM 모델 설정'),
                    ...currentAI.roles.map(role =>
                        e('div', {
                            key: role.id,
                            className: 'llm-option'
                        },
                            e('label', null, role.name),
                            e('select', {
                                value: roleLLMMapping[role.id] || 'gpt-4',
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
            e('div', { className: 'chat-area' },
                e('div', { className: 'chat-info' },
                    currentRole && e('div', { className: 'current-selection' },
                        e('span', { className: 'current-ai' }, currentAI.name),
                        e('span', { className: 'separator' }, '•'),
                        e('span', { className: 'current-role' }, currentRole.name),
                        e('span', { className: 'separator' }, '•'),
                        e('span', { className: 'current-llm' },
                            (() => {
                                const llm = llmOptions.find(l => l.id === (roleLLMMapping[selectedRole] || 'gpt-4'));
                                return llm ? `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name}` : 'Unknown';
                            })()
                        )
                    )
                ),

                e('div', { className: 'messages-container' },
                    messages.length === 0 ?
                        e('div', { className: 'welcome-message' },
                            e('h2', null, '🚀 AI 프로그램 생성을 시작하세요!'),
                            e('p', null, '좌측에서 AI 프레임워크와 역할을 선택한 후 대화를 시작할 수 있습니다.'),
                            e('div', { className: 'features' },
                                e('div', { className: 'feature' },
                                    e('h4', null, '🤝 CREW AI'),
                                    e('p', null, '3개 역할이 협업하여 작업을 수행합니다.')
                                ),
                                e('div', { className: 'feature' },
                                    e('h4', null, '🏗️ MetaGPT'),
                                    e('p', null, '5단계 승인 프로세스로 체계적으로 개발합니다.')
                                )
                            )
                        ) :
                        messages.map(message =>
                            e('div', {
                                key: message.id,
                                className: `message ${message.type}`
                            },
                                e('div', { className: 'message-header' },
                                    e('span', { className: 'message-info' },
                                        `${message.type === 'user' ? '👤 사용자' : '🤖 ' + aiOptions.find(ai => ai.id === message.ai)?.name} - ${message.role}`
                                    ),
                                    e('span', { className: 'message-time' },
                                        new Date(message.timestamp).toLocaleTimeString()
                                    )
                                ),
                                e('div', { className: 'message-content' }, message.content)
                            )
                        )
                ),

                e('div', { className: 'input-container' },
                    e('textarea', {
                        value: inputText,
                        onChange: (ev) => setInputText(ev.target.value),
                        onKeyPress: handleKeyPress,
                        placeholder: currentRole ? `${currentRole.name}에게 메시지를 보내세요...` : '역할을 선택하세요',
                        rows: 3,
                        disabled: isLoading || !selectedRole
                    }),
                    e('button', {
                        onClick: sendMessage,
                        disabled: isLoading || !inputText.trim() || !selectedRole,
                        className: 'send-button'
                    }, isLoading ? '⏳ 전송 중...' : '📤 전송')
                )
            )
        )
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(AIChatInterface));