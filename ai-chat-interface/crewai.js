const { useState, useEffect, useRef } = React;

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
    const [showProjects, setShowProjects] = useState(false);
    const [projects, setProjects] = useState([]);
    const [activeProject, setActiveProject] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('connecting');
    const [showNewProjectModal, setShowNewProjectModal] = useState(false);
    const [newProjectData, setNewProjectData] = useState({
        name: '',
        description: '',
        project_type: 'web_app'
    });

    const roles = [
        { id: 'researcher', name: 'Researcher', description: '정보 수집 및 분석 전문가', icon: '🔍' },
        { id: 'writer', name: 'Writer', description: '콘텐츠 생성 및 문서화 전문가', icon: '✍️' },
        { id: 'planner', name: 'Planner', description: '전략 수립 및 계획 전문가', icon: '📋' }
    ];

    // LLM 모델 목록 (React 상태로 관리)
    const [llmOptions, setLlmOptions] = useState([]);

    // LLM 모델 동적 로드
    const loadLLMModels = async () => {
        try {
            const response = await fetch('/api/llm/models');
            const data = await response.json();

            if (data.success) {
                const models = data.models.map(model => ({
                    id: model.id,
                    name: model.name,
                    description: model.description || '',
                    provider: model.provider,
                    type: model.type || 'cloud',
                    parameter_size: model.parameter_size
                }));
                setLlmOptions(models);
                console.log('LLM 모델 로드 완료:', models.length, '개');
            } else {
                console.error('LLM 모델 로드 실패:', data.error);
                // 기본 모델 설정
                const defaultModels = [
                    { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                    { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
                ];
                setLlmOptions(defaultModels);
            }
        } catch (error) {
            console.error('LLM 모델 로드 오류:', error);
            // 기본 모델 설정
            const defaultModels = [
                { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
            ];
            setLlmOptions(defaultModels);
        }
    };

    // 연결 상태 체크
    const checkConnection = async () => {
        try {
            const response = await fetch('/api/crewai/projects');
            setConnectionStatus(response.ok ? 'connected' : 'disconnected');
        } catch (error) {
            setConnectionStatus('disconnected');
        }
    };

    // 새 프로젝트 생성
    const createProject = async () => {
        if (!newProjectData.name.trim()) {
            window.UIHelpers.showNotification('프로젝트 이름을 입력하세요', 'warning');
            return;
        }

        try {
            setIsLoading(true);

            // 프로젝트 생성
            const projectData = {
                ...newProjectData,
                selected_ai: 'crew-ai'
            };

            const result = await window.apiClient.createProject(projectData);

            if (result.success) {
                // 역할-LLM 매핑 저장
                const mappings = [
                    { role_name: 'Researcher', llm_model: roleLLMMapping.researcher },
                    { role_name: 'Writer', llm_model: roleLLMMapping.writer },
                    { role_name: 'Planner', llm_model: roleLLMMapping.planner }
                ];

                await window.apiClient.setRoleLLMMapping(result.project.id, mappings);

                setActiveProject(result.project);
                setShowNewProjectModal(false);
                setNewProjectData({ name: '', description: '', project_type: 'web_app' });
                loadProjects();

                window.UIHelpers.showNotification('프로젝트가 성공적으로 생성되었습니다', 'success');
            } else {
                window.UIHelpers.showNotification(result.error || '프로젝트 생성에 실패했습니다', 'error');
            }
        } catch (error) {
            console.error('프로젝트 생성 실패:', error);
            window.UIHelpers.showNotification('프로젝트 생성 중 오류가 발생했습니다', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    // LLM 매핑 저장
    const saveLLMMapping = async () => {
        if (!activeProject) {
            window.UIHelpers.showNotification('프로젝트를 먼저 선택하세요', 'warning');
            return;
        }

        try {
            const mappings = [
                { role_name: 'Researcher', llm_model: roleLLMMapping.researcher },
                { role_name: 'Writer', llm_model: roleLLMMapping.writer },
                { role_name: 'Planner', llm_model: roleLLMMapping.planner }
            ];

            const result = await window.apiClient.setRoleLLMMapping(activeProject.id, mappings);

            if (result.success) {
                window.UIHelpers.showNotification('LLM 매핑이 저장되었습니다', 'success');
                // 로컬 스토리지에도 저장
                window.StorageHelpers.setItem(`crewai_llm_mapping_${activeProject.id}`, roleLLMMapping);
            } else {
                window.UIHelpers.showNotification(result.error || 'LLM 매핑 저장에 실패했습니다', 'error');
            }
        } catch (error) {
            console.error('LLM 매핑 저장 실패:', error);
            window.UIHelpers.showNotification('LLM 매핑 저장 중 오류가 발생했습니다', 'error');
        }
    };

    // 프로젝트 LLM 매핑 로드
    const loadProjectLLMMapping = async (projectId) => {
        try {
            const result = await window.apiClient.getRoleLLMMapping(projectId);

            if (result.success && result.mappings.length > 0) {
                const mapping = {};
                result.mappings.forEach(item => {
                    const roleKey = item.role_name.toLowerCase();
                    mapping[roleKey] = item.llm_model;
                });

                setRoleLLMMapping(mapping);
            } else {
                // 로컬 스토리지에서 로드
                const localMapping = window.StorageHelpers.getItem(`crewai_llm_mapping_${projectId}`);
                if (localMapping) {
                    setRoleLLMMapping(localMapping);
                }
            }
        } catch (error) {
            console.error('LLM 매핑 로드 실패:', error);
        }
    };

    // 프로젝트 목록 로드
    const loadProjects = async () => {
        try {
            const result = await window.apiClient.getProjects();

            if (result.success) {
                // CrewAI 프로젝트만 필터링
                const crewaiProjects = result.projects.filter(p => p.selected_ai === 'crew-ai');
                setProjects(crewaiProjects);
            } else {
                // 레거시 API 시도
                const response = await fetch('/api/crewai/projects');
                const data = await response.json();

            if (data.success) {
                const formattedProjects = (data.data || []).map(project => ({
                    id: project.id,
                    name: project.name,
                    description: project.description,
                    created_at: project.created_at,
                    status: project.status || '대기 중',
                    progress: project.progress_percentage || 0,
                    selected_ai: 'crewai',
                    role_llm_mapping: project.role_llm_mapping || roleLLMMapping
                }));
                setProjects(formattedProjects);
            }
            }
        } catch (error) {
            console.error('프로젝트 로드 실패:', error);
            setProjects([]);
        }
    };

    // 역할별 LLM 변경
    const handleRoleLLMChange = (roleId, llmId) => {
        const newMapping = {
            ...roleLLMMapping,
            [roleId]: llmId
        };
        setRoleLLMMapping(newMapping);

        // 활성 프로젝트가 있다면 데이터베이스에 즉시 저장
        if (activeProject) {
            updateProjectLLMMapping(activeProject.id, newMapping);
        }
    };

    // 프로젝트 LLM 매핑 업데이트 (데이터베이스 저장)
    const updateProjectLLMMapping = async (projectId, mapping) => {
        try {
            const mappings = [
                { role_name: 'Researcher', llm_model: mapping.researcher },
                { role_name: 'Writer', llm_model: mapping.writer },
                { role_name: 'Planner', llm_model: mapping.planner }
            ];

            const result = await window.apiClient.saveRoleLLMMapping(projectId, mappings);
            if (result.success) {
                console.log('LLM 매핑 저장 완료');
            } else {
                console.error('LLM 매핑 저장 실패:', result.error);
            }
        } catch (error) {
            console.error('LLM 매핑 업데이트 실패:', error);
        }
    };

    // 메시지 전송
    const handleSendMessage = async () => {
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

        try {
            const response = await fetch('/api/crewai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement: inputText,
                    selectedModels: roleLLMMapping,
                    selectedRole: selectedRole,
                    projectId: activeProject?.id
                })
            });

            const data = await response.json();

            const aiMessage = {
                id: Date.now() + 1,
                text: data.result || data.message || '처리가 완료되었습니다.',
                sender: 'ai',
                role: selectedRole,
                timestamp: new Date(),
                data: data
            };

            setMessages(prev => [...prev, aiMessage]);

            // 프로젝트 목록 새로고침
            loadProjects();
        } catch (error) {
            const errorMessage = {
                id: Date.now() + 1,
                text: `오류가 발생했습니다: ${error.message}`,
                sender: 'ai',
                role: selectedRole,
                timestamp: new Date(),
                error: true
            };
            setMessages(prev => [...prev, errorMessage]);
        }

        setIsLoading(false);
    };

    // 키보드 이벤트
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // 프로젝트 선택
    const selectProject = async (project) => {
        setActiveProject(project);
        setShowProjects(false);

        // 프로젝트별 LLM 매핑 로드
        await loadProjectLLMMapping(project.id);

        // 프로젝트 정보를 채팅에 추가
        const projectMessage = {
            id: Date.now(),
            text: `프로젝트 "${project.name}"를 선택했습니다.\n\n**설명**: ${project.description}\n**상태**: ${project.status}\n**진행률**: ${project.progress}%\n\n계속 작업하시겠습니까?`,
            sender: 'system',
            timestamp: new Date(),
            project: project
        };

        setMessages([projectMessage]);
    };

    // 새 프로젝트 시작
    const startNewProject = () => {
        setActiveProject(null);
        setMessages([]);
        setShowProjects(false);
    };

    // 대시보드로 돌아가기
    const goToDashboard = () => {
        window.location.href = '/';
    };

    useEffect(() => {
        const initializeInterface = async () => {
            await loadLLMModels();
            checkConnection();
            loadProjects();

            // 기본 LLM 매핑 로드 (프로젝트 선택 전)
            const savedMapping = window.StorageHelpers.getItem('crewai_default_llm_mapping');
            if (savedMapping) {
                setRoleLLMMapping(savedMapping);
            }
        };

        initializeInterface();

        const interval = setInterval(() => {
            checkConnection();
        }, 30000);

        return () => clearInterval(interval);
    }, []);

    const renderMessage = (message) => {
        const roleInfo = roles.find(r => r.id === message.role);
        const roleName = roleInfo ? `${roleInfo.icon} ${roleInfo.name}` : 'CrewAI';

        return (
            <div key={message.id} className={`message ${message.sender}`}>
                {message.sender === 'ai' && (
                    <div className="message-header">
                        <span className="role-badge">{roleName}</span>
                        {message.data?.models_used && (
                            <span className="model-badge">
                                {llmOptions.find(llm => llm.id === roleLLMMapping[message.role])?.name}
                            </span>
                        )}
                    </div>
                )}
                {message.sender === 'system' && (
                    <div className="message-header">
                        <span className="system-badge">🤖 시스템</span>
                    </div>
                )}
                <div className={`message-bubble ${message.error ? 'error' : ''}`}>
                    <div className="message-content">
                        {message.text.split('\n').map((line, i) => (
                            <div key={i}>{line}</div>
                        ))}
                    </div>
                    <div className="message-timestamp">
                        {message.timestamp.toLocaleTimeString()}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="crewai-container">
            <header className="crewai-header">
                <div className="header-left">
                    <button className="dashboard-btn" onClick={goToDashboard}>
                        ← 대시보드
                    </button>
                    <div className="header-title">
                        <h1>🤝 CrewAI Platform</h1>
                        <div className="header-status">
                            <span className="project-indicator">
                                {activeProject ? activeProject.name : '새 프로젝트'}
                            </span>
                            <span className={`connection-status ${connectionStatus}`}>
                                {connectionStatus === 'connected' ? '🟢 연결됨' :
                                 connectionStatus === 'connecting' ? '🟡 연결중' : '🔴 연결 끊김'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="header-controls">
                    <button
                        className={`projects-btn ${showProjects ? 'active' : ''}`}
                        onClick={() => {
                            setShowProjects(!showProjects);
                            if (!showProjects) loadProjects();
                        }}
                    >
                        📂 프로젝트 ({projects.length})
                    </button>
                    <button
                        className="new-project-btn"
                        onClick={() => setShowNewProjectModal(true)}
                    >
                        ➕ 새 프로젝트
                    </button>
                    {activeProject && (
                        <button
                            className="save-mapping-btn"
                            onClick={saveLLMMapping}
                            disabled={isLoading}
                        >
                            💾 LLM 매핑 저장
                        </button>
                    )}
                </div>
            </header>

            <div className="crewai-main">
                {showProjects && (
                    <div className="projects-panel">
                        <div className="panel-header">
                            <h3>📂 CrewAI 프로젝트 목록</h3>
                            <button
                                className="close-panel"
                                onClick={() => setShowProjects(false)}
                            >
                                ✕
                            </button>
                        </div>
                        <div className="projects-list">
                            {projects.length === 0 ? (
                                <div className="no-projects">
                                    <p>아직 생성된 프로젝트가 없습니다.</p>
                                    <p>새 프로젝트를 시작해보세요!</p>
                                </div>
                            ) : (
                                projects.map(project => (
                                    <div
                                        key={project.id}
                                        className={`project-item ${activeProject?.id === project.id ? 'active' : ''}`}
                                        onClick={() => selectProject(project)}
                                    >
                                        <div className="project-info">
                                            <h4>{project.name}</h4>
                                            <p>{project.description}</p>
                                        </div>
                                        <div className="project-meta">
                                            <div className="project-progress">
                                                <div className="progress-bar">
                                                    <div
                                                        className="progress-fill"
                                                        style={{ width: `${project.progress}%` }}
                                                    />
                                                </div>
                                                <span>{project.progress}%</span>
                                            </div>
                                            <span className="project-status">{project.status}</span>
                                            <span className="project-date">
                                                {new Date(project.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                <div className="chat-area">
                    <div className="sidebar">
                        <div className="role-selector">
                            <h3>🎭 역할 선택</h3>
                            <div className="roles-grid">
                                {roles.map(role => (
                                    <button
                                        key={role.id}
                                        className={`role-btn ${selectedRole === role.id ? 'active' : ''}`}
                                        onClick={() => setSelectedRole(role.id)}
                                    >
                                        <div className="role-icon" style={{ fontSize: '14px' }}>{role.icon}</div>
                                        <div className="role-info">
                                            <div className="role-name">{role.name}</div>
                                            <div className="role-desc">{role.description}</div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="llm-mapping">
                            <h3>⚙️ 역할별 LLM 설정</h3>
                            <div className="llm-status" style={{ fontSize: '12px', marginBottom: '10px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '6px' }}>
                                {llmOptions.length > 0 ? (
                                    <span style={{ color: 'green' }}>✅ {llmOptions.length}개 모델 로드됨</span>
                                ) : (
                                    <span style={{ color: 'orange' }}>⏳ LLM 모델 로딩 중...</span>
                                )}
                            </div>
                            <div className="mapping-list">
                                {roles.map(role => (
                                    <div key={role.id} className="mapping-item" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <div className="mapping-role">
                                            <span className="role-icon" style={{ fontSize: '14px' }}>{role.icon}</span>
                                            <span className={`role-name ${selectedRole === role.id ? 'current' : ''}`}>
                                                {role.name}
                                            </span>
                                        </div>
                                        <select
                                            className="llm-select"
                                            style={{ fontSize: '12px', padding: '6px 8px', minWidth: '160px' }}
                                            value={roleLLMMapping[role.id] || 'gpt-4'}
                                            onChange={(e) => handleRoleLLMChange(role.id, e.target.value)}
                                            disabled={llmOptions.length === 0}
                                        >
                                            {llmOptions.length === 0 ? (
                                                <option value="">모델 로딩 중...</option>
                                            ) : (
                                                llmOptions.map(llm => (
                                                    <option key={llm.id} value={llm.id}>
                                                        {llm.type === 'local' ? '🏠' : '☁️'} {llm.name} ({llm.provider})
                                                        {llm.parameter_size ? ` [${llm.parameter_size}]` : ''}
                                                    </option>
                                                ))
                                            )}
                                        </select>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {activeProject && (
                            <div className="active-project-info">
                                <h3>📋 현재 프로젝트</h3>
                                <div className="project-summary">
                                    <div className="project-name">{activeProject.name}</div>
                                    <div className="project-progress">
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{ width: `${activeProject.progress}%` }}
                                            />
                                        </div>
                                        <span>{activeProject.progress}%</span>
                                    </div>
                                    <div className="project-status">{activeProject.status}</div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="chat-main">
                        <div className="chat-messages">
                            {messages.length === 0 ? (
                                <div className="welcome-message">
                                    <h3>CrewAI 팀과 함께 시작하세요!</h3>
                                    <p>3명의 전문 AI 에이전트가 협력하여 작업을 수행합니다.</p>
                                    <div className="team-preview">
                                        {roles.map(role => (
                                            <div key={role.id} className="team-member">
                                                <div className="member-icon">{role.icon}</div>
                                                <div className="member-name">{role.name}</div>
                                                <div className="member-llm">
                                                    {llmOptions.find(llm => llm.id === roleLLMMapping[role.id])?.name}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <p>역할을 선택하고 작업을 시작해보세요.</p>
                                </div>
                            ) : (
                                messages.map(renderMessage)
                            )}

                            {isLoading && (
                                <div className="message ai">
                                    <div className="message-header">
                                        <span className="role-badge">
                                            {roles.find(r => r.id === selectedRole)?.icon} {roles.find(r => r.id === selectedRole)?.name}
                                        </span>
                                    </div>
                                    <div className="message-bubble loading">
                                        <div className="loading-dots">
                                            <span></span><span></span><span></span>
                                        </div>
                                        작업 처리 중...
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="chat-input">
                            <div className="input-header">
                                <div className="current-role">
                                    <span className="role-icon">{roles.find(r => r.id === selectedRole)?.icon}</span>
                                    <span className="role-name">{roles.find(r => r.id === selectedRole)?.name}</span>
                                    <span className="role-llm">
                                        ({llmOptions.find(llm => llm.id === roleLLMMapping[selectedRole])?.name})
                                    </span>
                                </div>
                            </div>
                            <div className="input-container">
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder={`${roles.find(r => r.id === selectedRole)?.name}에게 작업을 요청하세요...`}
                                    disabled={isLoading || connectionStatus !== 'connected'}
                                    rows="3"
                                />
                                <button
                                    onClick={handleSendMessage}
                                    disabled={!inputText.trim() || isLoading || connectionStatus !== 'connected'}
                                    className="send-button"
                                >
                                    {isLoading ? '처리중...' : '전송'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 새 프로젝트 생성 모달 */}
            {showNewProjectModal && (
                <div className="modal-overlay" onClick={() => setShowNewProjectModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>새 CrewAI 프로젝트 생성</h2>
                            <button
                                className="modal-close"
                                onClick={() => setShowNewProjectModal(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="modal-body">
                            <div className="form-group">
                                <label>프로젝트 이름</label>
                                <input
                                    type="text"
                                    value={newProjectData.name}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        name: e.target.value
                                    })}
                                    placeholder="프로젝트 이름을 입력하세요"
                                    className="form-input"
                                />
                            </div>

                            <div className="form-group">
                                <label>프로젝트 설명</label>
                                <textarea
                                    value={newProjectData.description}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        description: e.target.value
                                    })}
                                    placeholder="프로젝트 설명을 입력하세요"
                                    className="form-textarea"
                                    rows="3"
                                />
                            </div>

                            <div className="form-group">
                                <label>프로젝트 타입</label>
                                <select
                                    value={newProjectData.project_type}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        project_type: e.target.value
                                    })}
                                    className="form-select"
                                >
                                    <option value="web_app">웹 애플리케이션</option>
                                    <option value="mobile_app">모바일 앱</option>
                                    <option value="api">API 서버</option>
                                    <option value="desktop">데스크톱 앱</option>
                                    <option value="data_analysis">데이터 분석</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>현재 역할-LLM 매핑</label>
                                <div className="llm-mapping-preview">
                                    {roles.map(role => (
                                        <div key={role.id} className="mapping-item">
                                            <span className="role-name">{role.name}</span>
                                            <span className="llm-name">
                                                {llmOptions.find(llm => llm.id === roleLLMMapping[role.id])?.name || 'Unknown'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                                <p className="helper-text">
                                    프로젝트 생성 후 좌측 패널에서 LLM 매핑을 수정할 수 있습니다.
                                </p>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button
                                className="modal-button secondary"
                                onClick={() => setShowNewProjectModal(false)}
                            >
                                취소
                            </button>
                            <button
                                className="modal-button primary"
                                onClick={createProject}
                                disabled={isLoading || !newProjectData.name.trim()}
                            >
                                {isLoading ? '생성 중...' : '프로젝트 생성'}
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
root.render(<CrewAIInterface />);