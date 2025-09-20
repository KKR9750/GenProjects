const { useState, useEffect, useRef } = React;

const AIChatInterface = () => {
    const [selectedAI, setSelectedAI] = useState('crew-ai');
    const [selectedRole, setSelectedRole] = useState('');
    const [roleLLMMapping, setRoleLLMMapping] = useState({});
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showProjects, setShowProjects] = useState(false);
    const [projects, setProjects] = useState([]);

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

    // 선택된 AI의 역할 목록 가져오기
    const getCurrentRoles = () => {
        const currentAI = aiOptions.find(ai => ai.id === selectedAI);
        return currentAI ? currentAI.roles : [];
    };

    // 역할별 LLM 매핑 초기화
    const initializeRoleLLMMapping = (aiId) => {
        const currentAI = aiOptions.find(ai => ai.id === aiId);
        if (currentAI) {
            const newMapping = {};
            currentAI.roles.forEach(role => {
                newMapping[role.id] = 'gpt-4'; // 기본값
            });
            setRoleLLMMapping(newMapping);
        }
    };

    // AI 변경 시 첫 번째 역할로 자동 설정 및 매핑 초기화
    const handleAIChange = (aiId) => {
        setSelectedAI(aiId);
        const currentAI = aiOptions.find(ai => ai.id === aiId);
        if (currentAI && currentAI.roles.length > 0) {
            setSelectedRole(currentAI.roles[0].id);
            initializeRoleLLMMapping(aiId);
        }
    };

    // 특정 역할의 LLM 변경
    const handleRoleLLMChange = (roleId, llmId) => {
        setRoleLLMMapping(prev => ({
            ...prev,
            [roleId]: llmId
        }));
    };

    // 현재 선택된 역할의 LLM 가져오기
    const getCurrentRoleLLM = () => {
        return roleLLMMapping[selectedRole] || 'gpt-4';
    };

    // 컴포넌트 마운트 시 초기 설정
    useEffect(() => {
        const initializeInterface = async () => {
            await loadLLMModels();

            if (!selectedRole) {
                const currentAI = aiOptions.find(ai => ai.id === selectedAI);
                if (currentAI && currentAI.roles.length > 0) {
                    setSelectedRole(currentAI.roles[0].id);
                    initializeRoleLLMMapping(selectedAI);
                }
            }
        };

        initializeInterface();
    }, [selectedAI, selectedRole]);

    const handleSendMessage = () => {
        if (!inputText.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            text: inputText,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        setIsLoading(true);

        // 시뮬레이션 응답
        setTimeout(() => {
            const aiMessage = {
                id: Date.now() + 1,
                text: `${aiOptions.find(ai => ai.id === selectedAI)?.name}가 응답합니다: "${inputText}"에 대한 답변입니다.`,
                sender: 'ai',
                aiType: selectedAI,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, aiMessage]);
            setIsLoading(false);
        }, 1000);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const loadProjects = async () => {
        try {
            // CrewAI DB에서 프로젝트 목록 가져오기
            const response = await fetch('http://localhost:3001/api/projects');
            const data = await response.json();

            if (data.success) {
                // DB 스키마에 맞게 데이터 변환
                const formattedProjects = data.data.map(project => ({
                    project_id: project.id,
                    project_name: project.name,
                    requirement: project.description,
                    created_at: project.created_at,
                    current_step: project.current_step || 1,
                    completed_steps: project.completed_steps || 0,
                    progress_percentage: project.progress_percentage || 0,
                    workspace_path: project.workspace_path || '',
                    status: project.status || '대기 중',
                    selected_ai: project.selected_ai || 'crew-ai',
                    role_llm_mapping: project.role_llm_mapping || {}
                }));
                setProjects(formattedProjects);
            } else {
                console.error('프로젝트 목록 로드 실패:', data.error);
                setProjects([]);
            }
        } catch (error) {
            console.error('프로젝트 목록 로드 오류:', error);
            // CrewAI 서버 연결 실패시 기존 파일 시스템 API 시도
            try {
                const fallbackResponse = await fetch('/api/projects');
                const fallbackData = await fallbackResponse.json();
                if (fallbackData.success) {
                    setProjects(fallbackData.projects || []);
                } else {
                    setProjects([]);
                }
            } catch (fallbackError) {
                console.error('Fallback 프로젝트 목록 로드도 실패:', fallbackError);
                setProjects([]);
            }
        }
    };

    const renderMessage = (message) => {
        const aiName = aiOptions.find(ai => ai.id === message.aiType)?.name || 'AI';

        return (
            <div key={message.id} className={`message ${message.sender}`}>
                {message.sender === 'ai' && (
                    <div className="ai-label">{aiName}</div>
                )}
                <div className="message-bubble">
                    {message.text}
                </div>
            </div>
        );
    };

    return (
        <div className="chat-container">
            <div className="sidebar">
                <div className="header">
                    <h1>🤖 AI 프로그램 생성 도우미</h1>
                    <div className="header-controls">
                        <div className="ai-selector">
                            <select
                                id="ai-select"
                                className="ai-select"
                                value={selectedAI}
                                onChange={(e) => handleAIChange(e.target.value)}
                            >
                                {aiOptions.map(ai => (
                                    <option key={ai.id} value={ai.id} title={ai.description}>
                                        {ai.name} - {ai.description}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="role-selector">
                            <select
                                id="role-select"
                                className="ai-select"
                                value={selectedRole}
                                onChange={(e) => setSelectedRole(e.target.value)}
                            >
                                {getCurrentRoles().map(role => (
                                    <option key={role.id} value={role.id} title={role.description}>
                                        {role.name} - {role.description}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="llm-selector">
                            <select
                                id="llm-select"
                                className="ai-select"
                                value={getCurrentRoleLLM()}
                                onChange={(e) => handleRoleLLMChange(selectedRole, e.target.value)}
                            >
                                {llmOptions.map(llm => (
                                    <option key={llm.id} value={llm.id} title={llm.description}>
                                        {llm.type === 'local' ? '🏠' : '☁️'} {llm.name} ({llm.provider})
                                        {llm.parameter_size ? ` [${llm.parameter_size}]` : ''}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* 역할별 LLM 매핑 표시 */}
                        <div className="role-llm-mapping">
                            <h4>🎭 역할별 LLM 설정</h4>
                            <div className="mapping-list">
                                {getCurrentRoles().map(role => (
                                    <div key={role.id} className="mapping-item">
                                        <span className={`role-name ${selectedRole === role.id ? 'active' : ''}`}>
                                            {role.name}
                                        </span>
                                        <span className="llm-name">
                                            {(() => {
                                                const llm = llmOptions.find(llm => llm.id === (roleLLMMapping[role.id] || 'gpt-4'));
                                                return llm ? `${llm.type === 'local' ? '🏠' : '☁️'} ${llm.name}` : 'Unknown';
                                            })()}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {selectedAI === 'meta-gpt' && (
                            <div className="project-controls">
                                <button
                                    className="projects-button"
                                    onClick={() => {
                                        setShowProjects(!showProjects);
                                        if (!showProjects) loadProjects();
                                    }}
                                >
                                    📂 프로젝트
                                </button>
                                <button
                                    className="new-project-button"
                                    onClick={() => {
                                        setShowProjects(false);
                                        setMessages([]);
                                    }}
                                >
                                    ➕ 새 프로젝트
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* 프로젝트 목록 표시 (Sidebar) */}
                {showProjects && selectedAI === 'meta-gpt' && (
                    <div className="projects-list">
                        <h3>📂 기존 프로젝트 목록</h3>
                        {projects.length === 0 ? (
                            <div className="no-projects">
                                <p>아직 생성된 프로젝트가 없습니다.</p>
                                <p>새 프로젝트를 시작해보세요!</p>
                            </div>
                        ) : (
                            <div className="projects-grid">
                                {projects.map((project, index) => (
                                    <div
                                        key={index}
                                        className="project-card"
                                        onClick={() => {
                                            setShowProjects(false);
                                            const stepNames = {
                                                1: "요구사항 정리",
                                                2: "프로젝트 분석",
                                                3: "시스템 설계",
                                                4: "코드 개발",
                                                5: "단위 테스트"
                                            };

                                            const nextStepName = stepNames[project.current_step];
                                            const isCompleted = project.completed_steps >= 5;

                                            setMessages([{
                                                id: Date.now(),
                                                text: `## 📂 프로젝트: ${project.project_name}\n\n### 📋 프로젝트 정보\n- **요구사항**: ${project.requirement}\n- **생성일**: ${new Date(project.created_at).toLocaleDateString()}\n- **진행상황**: ${project.progress_percentage}% (${project.status})\n- **완료된 단계**: ${project.completed_steps}/5\n- **작업 경로**: ${project.workspace_path}\n\n${!isCompleted ? `🚀 **다음 단계**: ${project.current_step}단계 (${nextStepName})을 계속 진행할 수 있습니다.` : '🎉 **프로젝트 완료**: 모든 단계가 완료되었습니다!'}\n\n진행하려면 "단계 계속" 또는 "다음 단계"라고 입력하세요.`,
                                                sender: 'ai',
                                                aiType: 'meta-gpt',
                                                timestamp: new Date()
                                            }]);
                                        }}
                                    >
                                        <div className="project-header">
                                            <h4>{project.project_name}</h4>
                                            <span className="project-status">{project.status}</span>
                                        </div>
                                        <div className="project-info">
                                            <p className="project-requirement">{project.requirement}</p>
                                            <div className="project-progress">
                                                <div className="progress-bar">
                                                    <div
                                                        className="progress-fill"
                                                        style={{ width: `${project.progress_percentage}%` }}
                                                    ></div>
                                                </div>
                                                <span className="progress-text">
                                                    {project.status}
                                                </span>
                                            </div>
                                            <p className="project-date">
                                                {new Date(project.created_at).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            <div className="main-chat">
                <div className="chat-messages">
                    {messages.length === 0 ? (
                        <div className="welcome-message">
                            <h3>환영합니다! 👋</h3>
                            <p>AI를 선택하고 만들고 싶은 프로그램에 대해 설명해주세요.</p>
                        </div>
                    ) : (
                        messages.map(renderMessage)
                    )}

                    {isLoading && (
                        <div className="message ai">
                            <div className="ai-label">
                                {aiOptions.find(ai => ai.id === selectedAI)?.name}
                            </div>
                            <div className="message-bubble loading">
                                응답 생성 중...
                            </div>
                        </div>
                    )}
                </div>

                <div className="chat-input">
                    <div className="input-container">
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="프로그램 요청을 입력하세요..."
                            disabled={isLoading}
                            rows="3"
                        />
                        <button
                            onClick={handleSendMessage}
                            disabled={!inputText.trim() || isLoading}
                            className="send-button"
                        >
                            {isLoading ? '처리중...' : '전송'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<AIChatInterface />);