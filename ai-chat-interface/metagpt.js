const { useState, useEffect, useRef } = React;

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
    const [showProjects, setShowProjects] = useState(false);
    const [projects, setProjects] = useState([]);
    const [activeProject, setActiveProject] = useState(null);
    const [pendingApproval, setPendingApproval] = useState(null);
    const [stepResults, setStepResults] = useState({});

    // Modal states
    const [showNewProjectModal, setShowNewProjectModal] = useState(false);
    const [newProjectData, setNewProjectData] = useState({
        name: '',
        description: '',
        type: 'web_app'
    });

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
            deliverables: ['Source Code', 'Implementation', 'Documentation']
        },
        {
            id: 5,
            name: '품질 보증',
            role: 'qa-engineer',
            icon: '🧪',
            description: '테스트 및 품질 검증',
            deliverables: ['Test Cases', 'Quality Report', 'Bug Reports']
        }
    ];

    const roles = [
        { id: 'product-manager', name: 'Product Manager', description: '요구사항 정리 및 PRD 작성', icon: '📋', color: '#EF4444' },
        { id: 'architect', name: 'Architect', description: '시스템 설계 및 구조 계획', icon: '🏗️', color: '#F59E0B' },
        { id: 'project-manager', name: 'Project Manager', description: '작업 분석 및 계획 수립', icon: '📊', color: '#10B981' },
        { id: 'engineer', name: 'Engineer', description: '코드 개발 및 구현', icon: '💻', color: '#3B82F6' },
        { id: 'qa-engineer', name: 'QA Engineer', description: '테스트 및 품질 보증', icon: '🧪', color: '#8B5CF6' }
    ];

    // LLM 모델 목록 (React 상태로 관리)
    const [llmOptions, setLlmOptions] = useState([]);

    // LLM 모델 목록 로드
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
                    parameter_size: model.parameter_size || '',
                    family: model.family || '',
                    quantization: model.quantization || ''
                }));
                setLlmOptions(models);

                console.log(`LLM 모델 로드 완료: ${models.length}개 (클라우드: ${data.cloud_count}, 로컬: ${data.local_count})`);
                return true;
            } else {
                console.error('LLM 모델 로드 실패:', data.error);
                // 기본 모델 사용
                const defaultModels = [
                    { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                    { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
                ];
                setLlmOptions(defaultModels);
                return false;
            }
        } catch (error) {
            console.error('LLM 모델 로드 오류:', error);
            // 기본 모델 사용
            const defaultModels = [
                { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
            ];
            setLlmOptions(defaultModels);
            return false;
        }
    };

    // 프로젝트 목록 로드
    const loadProjects = async () => {
        try {
            const response = await fetch('/api/metagpt/projects');
            const data = await response.json();

            if (data.success) {
                const formattedProjects = (data.projects || []).map(project => ({
                    id: project.project_id || project.project_name,
                    name: project.project_name,
                    requirement: project.requirement,
                    created_at: project.created_at,
                    current_step: project.current_step || 1,
                    completed_steps: project.completed_steps || 0,
                    progress_percentage: project.progress_percentage || 0,
                    workspace_path: project.workspace_path,
                    status: project.status || '대기 중'
                }));
                setProjects(formattedProjects);
            }
        } catch (error) {
            console.error('프로젝트 로드 실패:', error);
            setProjects([]);
        }
    };

    // 역할별 LLM 변경
    const handleRoleLLMChange = (roleId, llmId) => {
        setRoleLLMMapping(prev => ({
            ...prev,
            [roleId]: llmId
        }));
    };

    // 단계 시작
    const startStep = async (stepNumber = currentStep) => {
        if (!inputText.trim() && stepNumber === 1) return;

        setIsLoading(true);

        // inputText 값을 먼저 보존
        const currentInputText = inputText;

        const stepInfo = steps.find(s => s.id === stepNumber);
        const userMessage = {
            id: Date.now(),
            text: stepNumber === 1 ? currentInputText : `${stepNumber}단계 (${stepInfo.name}) 진행 요청`,
            sender: 'user',
            step: stepNumber,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        if (stepNumber === 1) setInputText('');

        try {
            const response = await fetch('/api/metagpt/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement: stepNumber === 1 ? currentInputText : activeProject?.requirement,
                    step: stepNumber,
                    selectedModels: roleLLMMapping,
                    projectId: activeProject?.id
                })
            });

            const data = await response.json();

            if (data.success) {
                // Format the response text properly
                let responseText = data.message;
                if (!responseText && data.result) {
                    if (typeof data.result === 'string') {
                        responseText = data.result;
                    } else {
                        // Format object result into readable text
                        responseText = `${data.step_name || `${stepNumber}단계`} 완료\n\n`;
                        if (data.result.project_name) {
                            responseText += `프로젝트: ${data.result.project_name}\n\n`;
                        }
                        if (data.result.main_features) {
                            responseText += `주요 기능:\n${data.result.main_features.map(f => `• ${f}`).join('\n')}\n\n`;
                        }
                        if (data.result.technology_stack) {
                            responseText += `기술 스택:\n• 언어: ${data.result.technology_stack.language}\n• GUI: ${data.result.technology_stack.gui}\n`;
                        }
                    }
                }
                if (!responseText) {
                    responseText = `${stepNumber}단계가 완료되었습니다.`;
                }

                const aiMessage = {
                    id: Date.now() + 1,
                    text: responseText,
                    sender: 'ai',
                    step: stepNumber,
                    role: stepInfo.role,
                    deliverables: data.deliverables || stepInfo.deliverables,
                    timestamp: new Date(),
                    data: data
                };

                setMessages(prev => [...prev, aiMessage]);

                // 단계 결과 저장
                setStepResults(prev => ({
                    ...prev,
                    [stepNumber]: data
                }));

                // 승인 대기 상태로 설정
                if (stepNumber < 5) {
                    setPendingApproval({
                        step: stepNumber,
                        result: data,
                        nextStep: stepNumber + 1
                    });
                } else {
                    // 마지막 단계 완료
                    setCurrentStep(5);
                    setPendingApproval(null);
                }

                // 프로젝트 목록 새로고침
                loadProjects();
            } else {
                throw new Error(data.error || '단계 처리 실패');
            }
        } catch (error) {
            const errorMessage = {
                id: Date.now() + 1,
                text: `오류가 발생했습니다: ${error.message}`,
                sender: 'ai',
                step: stepNumber,
                error: true,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        }

        setIsLoading(false);
    };

    // 승인/거부 처리
    const handleApproval = async (approved, feedback = '') => {
        if (!pendingApproval) return;

        const { step, nextStep } = pendingApproval;

        const approvalMessage = {
            id: Date.now(),
            text: approved
                ? `${step}단계 승인 - 다음 단계로 진행합니다.${feedback ? `\n피드백: ${feedback}` : ''}`
                : `${step}단계 거부 - 수정이 필요합니다.${feedback ? `\n피드백: ${feedback}` : ''}`,
            sender: 'user',
            approval: approved,
            step: step,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, approvalMessage]);
        setPendingApproval(null);

        if (approved && nextStep <= 5) {
            // 다음 단계로 진행
            setCurrentStep(nextStep);
            setSelectedRole(steps.find(s => s.id === nextStep)?.role || 'product-manager');

            // 자동으로 다음 단계 시작
            setTimeout(() => {
                startStep(nextStep);
            }, 1000);
        } else if (!approved) {
            // 현재 단계 재시작
            setTimeout(() => {
                startStep(step);
            }, 1000);
        }
    };

    // 키보드 이벤트
    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (currentStep === 1) {
                startStep(1);
            }
        }
    };

    // 프로젝트 선택
    const selectProject = (project) => {
        setActiveProject(project);
        setCurrentStep(project.current_step);
        setShowProjects(false);

        const projectMessage = {
            id: Date.now(),
            text: `프로젝트 "${project.name}"를 선택했습니다.\n\n**요구사항**: ${project.requirement}\n**현재 단계**: ${project.current_step}/5\n**진행률**: ${project.progress_percentage}%\n**상태**: ${project.status}\n\n${project.current_step <= 5 ? '계속 진행하시겠습니까?' : '프로젝트가 완료되었습니다.'}`,
            sender: 'system',
            timestamp: new Date(),
            project: project
        };

        setMessages([projectMessage]);
    };

    // 새 프로젝트 모달 열기
    const openNewProjectModal = () => {
        setNewProjectData({
            name: '',
            description: '',
            type: 'web_app'
        });
        setShowNewProjectModal(true);
    };

    // 새 프로젝트 생성
    const createNewProject = () => {
        if (!newProjectData.name.trim()) {
            alert('프로젝트 이름을 입력해주세요.');
            return;
        }

        // 새 프로젝트 객체 생성
        const newProject = {
            id: Date.now(),
            name: newProjectData.name,
            description: newProjectData.description,
            type: newProjectData.type,
            status: '진행중',
            current_step: 1,
            progress_percentage: 0,
            created_at: new Date().toISOString()
        };

        // 프로젝트 상태 초기화
        setActiveProject(newProject);
        setCurrentStep(1);
        setSelectedRole('product-manager');
        setMessages([]);
        setShowProjects(false);
        setPendingApproval(null);
        setStepResults({});
        setShowNewProjectModal(false);

        // 초기 메시지 설정 (올바른 구조로 수정)
        const initialMessage = {
            id: Date.now(),
            text: `새 ${newProjectData.type === 'web_app' ? '웹 애플리케이션' :
                     newProjectData.type === 'mobile_app' ? '모바일 앱' :
                     newProjectData.type === 'api' ? 'API 서버' :
                     newProjectData.type === 'desktop' ? '데스크톱 앱' : '데이터 분석'} 프로젝트 "${newProjectData.name}"이 시작되었습니다.\n\n${newProjectData.description}`,
            sender: 'system',
            timestamp: new Date()
        };
        setMessages([initialMessage]);
    };

    // 대시보드로 돌아가기
    const goToDashboard = () => {
        window.location.href = '/';
    };

    useEffect(() => {
        loadLLMModels().then(() => {
            loadProjects();
        });
    }, []);

    const renderMessage = (message) => {
        const roleInfo = roles.find(r => r.id === message.role);
        const stepInfo = steps.find(s => s.id === message.step);

        return (
            <div key={message.id} className={`message ${message.sender}`}>
                {message.sender === 'ai' && (
                    <div className="message-header">
                        <span className="step-badge" style={{ backgroundColor: roleInfo?.color }}>
                            {stepInfo?.icon} {stepInfo?.name}
                        </span>
                        <span className="role-badge">
                            {roleInfo?.icon} {roleInfo?.name}
                        </span>
                        <span className="model-badge">
                            {llmOptions.find(llm => llm.id === roleLLMMapping[message.role])?.name}
                        </span>
                    </div>
                )}
                {message.sender === 'system' && (
                    <div className="message-header">
                        <span className="system-badge">🤖 시스템</span>
                    </div>
                )}
                <div className={`message-bubble ${message.error ? 'error' : ''} ${message.approval !== undefined ? 'approval' : ''}`}>
                    <div className="message-content">
                        {(message.text || '').toString().split('\n').map((line, i) => (
                            <div key={i}>{line}</div>
                        ))}
                        {message.deliverables && (
                            <div className="deliverables">
                                <h4>📋 산출물:</h4>
                                <ul>
                                    {message.deliverables.map((item, i) => (
                                        <li key={i}>{item}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                    <div className="message-timestamp">
                        {message.timestamp.toLocaleTimeString()}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="metagpt-container">
            <header className="metagpt-header">
                <div className="header-left">
                    <button className="dashboard-btn" onClick={goToDashboard}>
                        ← 대시보드
                    </button>
                    <div className="header-title">
                        <h1>🏗️ MetaGPT Platform</h1>
                        <div className="header-status">
                            {activeProject ? (
                                <div className="current-project-header">
                                    🏗️ {activeProject.name} | {currentStep}/5 단계 | {activeProject.status}
                                </div>
                            ) : (
                                <span className="step-indicator">새 프로젝트</span>
                            )}
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
                        onClick={openNewProjectModal}
                    >
                        ➕ 새 프로젝트
                    </button>
                </div>
            </header>

            <div className="metagpt-main">
                {showProjects && (
                    <div className="projects-panel">
                        <div className="panel-header">
                            <h3>📂 MetaGPT 프로젝트 목록</h3>
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
                                            <p>{project.requirement}</p>
                                        </div>
                                        <div className="project-meta">
                                            <div className="step-progress">
                                                <div className="steps-indicator">
                                                    {steps.map(step => (
                                                        <div
                                                            key={step.id}
                                                            className={`step-dot ${step.id <= project.completed_steps ? 'completed' : step.id === project.current_step ? 'current' : 'pending'}`}
                                                        >
                                                            {step.icon}
                                                        </div>
                                                    ))}
                                                </div>
                                                <span>{project.current_step}/5 단계</span>
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

                <div className="workflow-area">
                    <div className="sidebar">
                        <div className="workflow-progress">
                            <h3>🏗️ 개발 워크플로</h3>
                            <div className="steps-list">
                                {steps.map(step => (
                                    <div
                                        key={step.id}
                                        className={`step-item ${
                                            step.id < currentStep ? 'completed' :
                                            step.id === currentStep ? 'current' : 'pending'
                                        } ${selectedRole === step.role ? 'selected' : ''}`}
                                        onClick={() => setSelectedRole(step.role)}
                                    >
                                        <div className="step-icon" style={{ backgroundColor: roles.find(r => r.id === step.role)?.color }}>
                                            {step.icon}
                                        </div>
                                        <div className="step-info">
                                            <div className="step-name">
                                                {step.name} (<span className="step-desc-inline">{step.description}</span>)
                                            </div>
                                            <div className="step-role">
                                                {roles.find(r => r.id === step.role)?.name}
                                            </div>
                                        </div>
                                        <div className="step-status">
                                            {step.id < currentStep ? '✅' :
                                             step.id === currentStep ? '🔄' : '⏳'}
                                        </div>
                                    </div>
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
                                    <div key={role.id} className="mapping-item">
                                        <div className="mapping-role">
                                            <span className="role-icon" style={{ backgroundColor: role.color }}>
                                                {role.icon}
                                            </span>
                                            <span className={`role-name ${selectedRole === role.id ? 'current' : ''}`}>
                                                {role.name}
                                            </span>
                                        </div>
                                        <select
                                            className="llm-select"
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

                    </div>

                    <div className="chat-main">
                        <div className="chat-messages">
                            {messages.length === 0 ? (
                                <div className="welcome-message">
                                    <h3>MetaGPT 개발팀과 함께 시작하세요!</h3>
                                    <p>5단계 승인 프로세스로 체계적인 개발을 진행합니다.</p>
                                    <div className="workflow-preview">
                                        {steps.map((step, index) => (
                                            <div key={step.id} className="workflow-step">
                                                <div className="step-number">{step.id}</div>
                                                <div className="step-icon">{step.icon}</div>
                                                <div className="step-title">{step.name}</div>
                                                {index < steps.length - 1 && <div className="step-arrow">→</div>}
                                            </div>
                                        ))}
                                    </div>
                                    <p>프로젝트 요구사항을 입력하여 시작해보세요.</p>
                                </div>
                            ) : (
                                messages.map(renderMessage)
                            )}

                            {isLoading && (
                                <div className="message ai">
                                    <div className="message-header">
                                        <span className="step-badge">
                                            {steps.find(s => s.id === currentStep)?.icon} {steps.find(s => s.id === currentStep)?.name}
                                        </span>
                                    </div>
                                    <div className="message-bubble loading">
                                        <div className="loading-dots">
                                            <span></span><span></span><span></span>
                                        </div>
                                        단계 처리 중...
                                    </div>
                                </div>
                            )}

                            {pendingApproval && (
                                <div className="approval-section">
                                    <div className="approval-header">
                                        <h4>🔍 {pendingApproval.step}단계 승인 대기</h4>
                                        <p>결과를 검토하고 다음 단계로 진행할지 결정해주세요.</p>
                                    </div>
                                    <div className="approval-actions">
                                        <button
                                            className="approve-btn"
                                            onClick={() => handleApproval(true)}
                                        >
                                            ✅ 승인 후 다음 단계
                                        </button>
                                        <button
                                            className="reject-btn"
                                            onClick={() => handleApproval(false)}
                                        >
                                            ❌ 거부 후 재작업
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="chat-input">
                            {currentStep === 1 ? (
                                <div className="input-container">
                                    <div className="input-header">
                                        <div className="current-step">
                                            <div className="step-line-1">
                                                <span className="step-icon">📋</span>
                                                <span className="step-name">1단계: 요구사항 분석</span>
                                            </div>
                                            <div className="step-line-2">
                                                <span className="step-role">(Product Manager)</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="input-right">
                                        <textarea
                                            value={inputText}
                                            onChange={(e) => setInputText(e.target.value)}
                                            onKeyPress={handleKeyPress}
                                            placeholder="개발하고 싶은 프로그램의 요구사항을 상세히 입력해주세요..."
                                            disabled={isLoading}
                                            rows="4"
                                        />
                                        <button
                                            onClick={() => startStep(1)}
                                            disabled={!inputText.trim() || isLoading}
                                            className="start-button"
                                        >
                                            {isLoading ? '프로젝트 시작 중...' : '🚀 프로젝트 시작'}
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="workflow-controls">
                                    <div className="current-step-info">
                                        <span className="step-icon">
                                            {steps.find(s => s.id === currentStep)?.icon}
                                        </span>
                                        <span className="step-name">
                                            {currentStep}단계: {steps.find(s => s.id === currentStep)?.name}
                                        </span>
                                        <span className="step-role">
                                            ({roles.find(r => r.id === steps.find(s => s.id === currentStep)?.role)?.name})
                                        </span>
                                    </div>
                                    {!isLoading && !pendingApproval && currentStep <= 5 && (
                                        <button
                                            onClick={() => startStep(currentStep)}
                                            className="continue-button"
                                        >
                                            {currentStep === 1 ? '🚀 시작하기' : `▶️ ${currentStep}단계 계속`}
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* New Project Modal */}
            {showNewProjectModal && (
                <div className="modal-overlay" onClick={() => setShowNewProjectModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>🏗️ 새 MetaGPT 프로젝트 생성</h2>
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
                                    className="form-input"
                                    value={newProjectData.name}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        name: e.target.value
                                    })}
                                    placeholder="프로젝트 이름을 입력하세요"
                                />
                            </div>

                            <div className="form-group">
                                <label>프로젝트 설명</label>
                                <textarea
                                    className="form-textarea"
                                    value={newProjectData.description}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        description: e.target.value
                                    })}
                                    placeholder="프로젝트 설명을 입력하세요"
                                />
                            </div>

                            <div className="form-group">
                                <label>프로젝트 타입</label>
                                <select
                                    className="form-select"
                                    value={newProjectData.type}
                                    onChange={(e) => setNewProjectData({
                                        ...newProjectData,
                                        type: e.target.value
                                    })}
                                >
                                    <option value="web_app">웹 애플리케이션</option>
                                    <option value="mobile_app">모바일 앱</option>
                                    <option value="api">API 서버</option>
                                    <option value="desktop">데스크톱 앱</option>
                                    <option value="data_analysis">데이터 분석</option>
                                </select>
                            </div>

                            <div className="llm-mapping-wrapper">
                                <label className="mapping-label">역할-LLM</label>
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
                                onClick={createNewProject}
                            >
                                프로젝트 생성
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
root.render(<MetaGPTInterface />);