const { useState, useEffect, useRef, createElement: e } = React;

const MetaGPTInterface = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [selectedRole, setSelectedRole] = useState('product-manager');
    const [roleLLMMapping, setRoleLLMMapping] = useState({
        'product-manager': 'gpt-4',
        'architect': 'claude-3',
        'project-manager': 'gpt-4o',
        'engineer': 'deepseek-coder',
        'qa-engineer': 'claude-3-haiku'
    });
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [stepResults, setStepResults] = useState({});

    const steps = [
        {
            id: 1,
            name: '요구사항 분석',
            role: 'product-manager',
            icon: '📋',
            description: 'PRD 작성 및 요구사항 정의',
            deliverables: ['Product Requirements Document', 'User Stories', 'Success Metrics']
        },
        {
            id: 2,
            name: '시스템 설계',
            role: 'architect',
            icon: '🏗️',
            description: '아키텍처 설계 및 API 명세',
            deliverables: ['System Architecture', 'API Specification', 'Data Models']
        },
        {
            id: 3,
            name: '프로젝트 계획',
            role: 'project-manager',
            icon: '📊',
            description: '작업 분석 및 일정 수립',
            deliverables: ['Project Plan', 'Task Breakdown', 'Timeline']
        },
        {
            id: 4,
            name: '코드 개발',
            role: 'engineer',
            icon: '💻',
            description: '실제 코드 구현',
            deliverables: ['Source Code', 'Documentation', 'Unit Tests']
        },
        {
            id: 5,
            name: '품질 보증',
            role: 'qa-engineer',
            icon: '🔍',
            description: '테스트 및 품질 검증',
            deliverables: ['Test Plans', 'Bug Reports', 'Quality Metrics']
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

    // 메시지 전송
    const sendMessage = async () => {
        if (!inputText.trim()) return;

        const currentStepData = steps.find(s => s.id === currentStep);
        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputText,
            step: currentStep,
            role: currentStepData.role,
            timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        try {
            const response = await fetch('/api/metagpt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: inputText,
                    step: currentStep,
                    role: currentStepData.role,
                    llm_model: roleLLMMapping[currentStepData.role],
                    previous_results: stepResults
                })
            });

            const data = await response.json();

            const aiMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: data.response || '응답을 받을 수 없습니다.',
                step: currentStep,
                role: currentStepData.role,
                timestamp: new Date().toISOString()
            };

            setMessages(prev => [...prev, aiMessage]);

            // 단계 결과 저장
            if (data.deliverables) {
                setStepResults(prev => ({
                    ...prev,
                    [currentStep]: data.deliverables
                }));
            }

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

    // 다음 단계로 이동
    const moveToNextStep = () => {
        if (currentStep < steps.length) {
            setCurrentStep(currentStep + 1);
            setSelectedRole(steps[currentStep].role);
        }
    };

    // 이전 단계로 이동
    const moveToPrevStep = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
            setSelectedRole(steps[currentStep - 2].role);
        }
    };

    // 대시보드로 이동
    const goToDashboard = () => {
        window.location.href = '/';
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

    // 컴포넌트 초기화
    useEffect(() => {
        loadLLMModels();
    }, []);

    const currentStepData = steps.find(s => s.id === currentStep);

    return e('div', { className: 'metagpt-container' },
        // Header
        e('header', { className: 'metagpt-header' },
            e('div', { className: 'header-left' },
                e('button', {
                    className: 'dashboard-btn',
                    onClick: goToDashboard
                }, '← 대시보드'),
                e('div', { className: 'header-title' },
                    e('h1', null, '🏗️ MetaGPT Platform'),
                    e('div', { className: 'header-subtitle' },
                        `단계 ${currentStep}/5: ${currentStepData.name}`
                    )
                )
            )
        ),

        // Progress Bar
        e('div', { className: 'progress-container' },
            e('div', { className: 'progress-bar' },
                e('div', {
                    className: 'progress-fill',
                    style: { width: `${(currentStep / steps.length) * 100}%` }
                })
            ),
            e('div', { className: 'steps-nav' },
                ...steps.map(step =>
                    e('div', {
                        key: step.id,
                        className: `step-indicator ${currentStep === step.id ? 'current' : ''} ${currentStep > step.id ? 'completed' : ''}`,
                        onClick: () => setCurrentStep(step.id)
                    },
                        e('span', { className: 'step-icon' }, step.icon),
                        e('span', { className: 'step-name' }, step.name)
                    )
                )
            )
        ),

        // Main Content
        e('main', { className: 'metagpt-main' },
            // Left Sidebar
            e('aside', { className: 'metagpt-sidebar' },
                e('div', { className: 'section' },
                    e('h3', null, '📋 현재 단계'),
                    e('div', { className: 'current-step-card' },
                        e('div', { className: 'step-header' },
                            e('span', { className: 'step-icon' }, currentStepData.icon),
                            e('h4', null, currentStepData.name)
                        ),
                        e('p', null, currentStepData.description),
                        e('div', { className: 'deliverables' },
                            e('h5', null, '산출물:'),
                            e('ul', null,
                                ...currentStepData.deliverables.map((item, index) =>
                                    e('li', { key: index }, item)
                                )
                            )
                        )
                    )
                ),

                e('div', { className: 'section' },
                    e('h3', null, '🧠 LLM 모델 설정'),
                    ...steps.map(step =>
                        e('div', {
                            key: step.role,
                            className: 'llm-mapping'
                        },
                            e('label', null, `${step.icon} ${step.name}`),
                            e('select', {
                                value: roleLLMMapping[step.role],
                                onChange: (ev) => handleLLMChange(step.role, ev.target.value)
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
                ),

                e('div', { className: 'section' },
                    e('h3', null, '🎯 단계 진행'),
                    e('div', { className: 'step-controls' },
                        e('button', {
                            onClick: moveToPrevStep,
                            disabled: currentStep === 1,
                            className: 'step-btn prev'
                        }, '← 이전 단계'),
                        e('button', {
                            onClick: moveToNextStep,
                            disabled: currentStep === steps.length,
                            className: 'step-btn next'
                        }, '다음 단계 →')
                    )
                )
            ),

            // Chat Area
            e('div', { className: 'chat-container' },
                e('div', { className: 'chat-header' },
                    e('h2', null, `${currentStepData.icon} ${currentStepData.name}`),
                    e('span', { className: 'current-llm' },
                        (() => {
                            const llm = llmOptions.find(l => l.id === roleLLMMapping[currentStepData.role]);
                            return `모델: ${llm ? `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name}` : 'Unknown'}`;
                        })()
                    )
                ),

                e('div', { className: 'messages-area' },
                    messages.length === 0 ?
                        e('div', { className: 'welcome-message' },
                            e('h3', null, '🏗️ MetaGPT 단계별 개발 프로세스'),
                            e('p', null, '5단계 승인 기반 소프트웨어 개발 워크플로우를 시작하세요.'),
                            e('div', { className: 'process-overview' },
                                ...steps.map(step =>
                                    e('div', {
                                        key: step.id,
                                        className: `process-step ${currentStep === step.id ? 'current' : ''}`
                                    },
                                        e('span', { className: 'process-icon' }, step.icon),
                                        e('span', { className: 'process-name' }, step.name)
                                    )
                                )
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
                                        message.type === 'ai' ? `${steps.find(s => s.role === message.role)?.icon} ${steps.find(s => s.role === message.role)?.name}` :
                                        '⚠️ 오류'
                                    ),
                                    message.step && e('span', { className: 'message-step' },
                                        `Step ${message.step}`
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
                            placeholder: `${currentStepData.name} 단계에 대한 메시지를 입력하세요...`,
                            rows: 3,
                            disabled: isLoading
                        }),
                        e('button', {
                            onClick: sendMessage,
                            disabled: isLoading || !inputText.trim(),
                            className: 'send-button'
                        }, isLoading ? '⏳ 처리 중...' : '📤 전송')
                    )
                )
            )
        )
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(e(MetaGPTInterface));