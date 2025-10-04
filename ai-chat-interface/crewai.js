const { useState, useEffect, useRef } = React;

const CrewAIInterface = () => {
    // SocketIO 연결 상태
    const [socket, setSocket] = useState(null);
    const [selectedRole, setSelectedRole] = useState('planner');
    const [roleLLMMapping, setRoleLLMMapping] = useState({
        planner: 'gemini-2.5-flash',
        researcher: 'gemini-2.5-flash',
        writer: 'gemini-2.5-flash'
    });
    const [preAnalysisModel, setPreAnalysisModel] = useState('gemini-2.5-flash');
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showProjects, setShowProjects] = useState(false);
    const [projects, setProjects] = useState([]);
    const [activeProject, setActiveProject] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('connected');
    const [showNewProjectModal, setShowNewProjectModal] = useState(false);
    const [newProjectData, setNewProjectData] = useState({
        name: '',
        description: '',
        project_type: 'web_app'
    });

    // 새로운 모델 선택 모드 상태
    const [modelSelectionMode, setModelSelectionMode] = useState('manual'); // 'auto' 또는 'manual'
    const [autoRecommendations, setAutoRecommendations] = useState(null);
    const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
    const [recommendationStrategy, setRecommendationStrategy] = useState('balanced');

    // 승인 시스템 상태
    const [showApprovalModal, setShowApprovalModal] = useState(false);
    const [pendingApproval, setPendingApproval] = useState(null);
    const [approvalFeedback, setApprovalFeedback] = useState('');

    // 검토-재작성 반복 횟수 상태 (0~3회)
    const [reviewIterations, setReviewIterations] = useState(3);

    // MCP/도구 선택 상태
    const [availableMCPs, setAvailableMCPs] = useState([]);
    const [selectedTools, setSelectedTools] = useState([]);
    const [apiKeys, setApiKeys] = useState({});
    const [showMCPModal, setShowMCPModal] = useState(false);
    const [mcpCategory, setMcpCategory] = useState('all');

    // Real-time monitoring states removed

    const roles = [
        { id: 'planner', name: 'Planner', description: '전략 수립 및 계획 전문가', icon: '📋' },
        { id: 'researcher', name: 'Researcher', description: '정보 수집 및 분석 전문가', icon: '🔍' },
        { id: 'writer', name: 'Writer', description: '콘텐츠 생성 및 문서화 전문가', icon: '✍️' }
    ];

    // LLM 모델 목록 (React 상태로 관리)
    const [llmOptions, setLlmOptions] = useState([]);

    // SocketIO 연결 초기화
    const initializeSocketConnection = () => {
        try {
            if (typeof io === 'undefined') {
                console.warn('Socket.IO 라이브러리가 로드되지 않음');
                return;
            }

            const newSocket = io();

            // 연결 성공
            newSocket.on('connect', () => {
                console.log('✅ WebSocket 연결 성공');
                setConnectionStatus('connected');
            });

            // 연결 실패
            newSocket.on('disconnect', () => {
                console.log('🔌 WebSocket 연결 해제');
                setConnectionStatus('disconnected');
            });

            // 프로젝트 완성 알림 수신
            newSocket.on('project_notification', (data) => {
                console.log('🎉 프로젝트 완성 알림 수신:', data);

                if (data.type === 'project_completion') {
                    // 대화창에 완성 알림 메시지 추가
                    const completionMessage = {
                        id: Date.now(),
                        text: `## 🎉 프로젝트 완성!

**${data.project_name}**가 성공적으로 완성되었습니다!

📂 **결과 위치**: \`${data.result_path}\`
⏰ **완성 시간**: ${data.details.completion_time}

생성된 파일들을 확인해보세요!`,
                        sender: 'system',
                        timestamp: new Date().toLocaleTimeString(),
                        isNotification: true
                    };

                    setMessages(prev => [...prev, completionMessage]);

                    // 브라우저 알림도 표시
                    if (window.UIHelpers && window.UIHelpers.showNotification) {
                        window.UIHelpers.showNotification(
                            `프로젝트 '${data.project_name}' 완성!`,
                            'success'
                        );
                    }

                    // 프로젝트 목록 새로고침
                    loadProjects();
                }
            });

            // 로그 메시지 수신
            newSocket.on('log_message', (data) => {
                if (data.level === 'success') {
                    console.log('📝 로그 메시지:', data.message);
                }
            });

            setSocket(newSocket);

        } catch (error) {
            console.error('❌ WebSocket 연결 실패:', error);
            setConnectionStatus('error');
        }
    };

    // MCP/도구 목록 로드
    const loadAvailableMCPs = async () => {
        try {
            const response = await fetch('/api/mcps/available');
            const data = await response.json();

            if (data.status === 'success') {
                setAvailableMCPs(data.mcps);
                console.log('✅ MCP/도구 로드 완료:', data.count, '개');
            } else {
                console.error('❌ MCP 로드 실패:', data.error);
            }
        } catch (error) {
            console.error('❌ MCP 로드 중 오류:', error);
        }
    };

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
                    { id: 'gemini-flash', name: 'Gemini Flash', description: '빠른 응답 특화 모델', provider: 'Google', type: 'cloud' },
                    { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                    { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
                ];
                setLlmOptions(defaultModels);
            }
        } catch (error) {
            console.error('LLM 모델 로드 오류:', error);
            // 기본 모델 설정
            const defaultModels = [
                { id: 'gemini-flash', name: 'Gemini Flash', description: '빠른 응답 특화 모델', provider: 'Google', type: 'cloud' },
                { id: 'gpt-4', name: 'GPT-4', description: '범용 고성능 모델', provider: 'OpenAI', type: 'cloud' },
                { id: 'claude-3', name: 'Claude-3 Sonnet', description: '추론 특화 모델', provider: 'Anthropic', type: 'cloud' }
            ];
            setLlmOptions(defaultModels);
        }
    };

    // WebSocket functionality removed

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
                    { role_name: 'Planner', llm_model: roleLLMMapping.planner },
                    { role_name: 'Researcher', llm_model: roleLLMMapping.researcher },
                    { role_name: 'Writer', llm_model: roleLLMMapping.writer }
                ];

                await window.apiClient.setRoleLLMMapping(result.project.project_id, mappings);

                setActiveProject(result.project);
                setShowNewProjectModal(false);
                setNewProjectData({ name: '', description: '', project_type: 'web_app' });
                setConnectionStatus('connected'); // 연결 상태 활성화
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
                { role_name: 'Planner', llm_model: roleLLMMapping.planner },
                { role_name: 'Researcher', llm_model: roleLLMMapping.researcher },
                { role_name: 'Writer', llm_model: roleLLMMapping.writer }
            ];

            const result = await window.apiClient.setRoleLLMMapping(activeProject.project_id, mappings);

            if (result.success) {
                window.UIHelpers.showNotification('LLM 매핑이 저장되었습니다', 'success');
                // 로컬 스토리지에도 저장
                window.StorageHelpers.setItem(`crewai_llm_mapping_${activeProject.project_id}`, roleLLMMapping);
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
                    project_id: project.project_id || project.id,
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

        // localStorage에 기본값으로 저장
        window.StorageHelpers.setItem('crewai_default_llm_mapping', newMapping);

        // 활성 프로젝트가 있다면 데이터베이스에 즉시 저장
        if (activeProject) {
            updateProjectLLMMapping(activeProject.project_id, newMapping);
        }
    };

    // 사전 분석 LLM 변경
    const handlePreAnalysisModelChange = (llmId) => {
        setPreAnalysisModel(llmId);

        // localStorage에 즉시 저장
        window.StorageHelpers.setItem('crewai_pre_analysis_model', llmId);

        // 사전 분석 모델은 프로젝트별로 저장하지 않음 (글로벌 설정)
        // 역할별 LLM 매핑과는 별개로 처리
    };

    // 자동 모델 추천 요청
    const getAutoRecommendations = async (requirement) => {
        if (!requirement || requirement.trim().length < 10) {
            setAutoRecommendations(null);
            return;
        }

        setIsLoadingRecommendations(true);
        try {
            const response = await fetch('/api/llm/models/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement: requirement,
                    budget: 'medium',
                    strategy: recommendationStrategy
                })
            });

            const data = await response.json();
            if (data.success) {
                setAutoRecommendations(data);

                // 자동 모드일 때 추천된 모델을 현재 매핑에 적용
                if (modelSelectionMode === 'auto' && data.simple_models) {
                    const newMapping = { ...roleLLMMapping };

                    // 에이전트 이름을 역할 이름으로 매핑
                    const roleMapping = {
                        'planner': ['content_strategist', 'requirements_analyst', 'solution_architect'],
                        'researcher': ['technology_researcher', 'information_extractor', 'data_scientist'],
                        'writer': ['content_creator', 'document_parser', 'quality_assurance']
                    };

                    // 추천된 모델을 역할별로 적용
                    Object.entries(data.simple_models).forEach(([agentName, modelName]) => {
                        for (const [role, agents] of Object.entries(roleMapping)) {
                            if (agents.includes(agentName)) {
                                newMapping[role] = modelName;
                                break;
                            }
                        }
                    });

                    setRoleLLMMapping(newMapping);
                }
            } else {
                console.error('자동 추천 실패:', data.error);
                setAutoRecommendations(null);
            }
        } catch (error) {
            console.error('자동 추천 오류:', error);
            setAutoRecommendations(null);
        } finally {
            setIsLoadingRecommendations(false);
        }
    };

    // 모델 선택 모드 변경
    const handleModeChange = (mode) => {
        setModelSelectionMode(mode);
        window.StorageHelpers.setItem('crewai_model_selection_mode', mode);

        if (mode === 'auto' && inputText.trim()) {
            // 자동 모드로 전환하면서 현재 입력된 텍스트가 있으면 추천 요청
            getAutoRecommendations(inputText);
        } else if (mode === 'manual') {
            // 수동 모드로 전환시 추천 초기화
            setAutoRecommendations(null);
        }
    };

    // 추천 전략 변경
    const handleStrategyChange = (strategy) => {
        setRecommendationStrategy(strategy);
        window.StorageHelpers.setItem('crewai_recommendation_strategy', strategy);

        // 자동 모드이고 입력이 있으면 새로운 전략으로 재추천
        if (modelSelectionMode === 'auto' && inputText.trim()) {
            getAutoRecommendations(inputText);
        }
    };

    // 프로젝트 LLM 매핑 업데이트 (데이터베이스 저장)
    const updateProjectLLMMapping = async (projectId, mapping) => {
        try {
            const mappings = [
                { role_name: 'Planner', llm_model: mapping.planner },
                { role_name: 'Researcher', llm_model: mapping.researcher },
                { role_name: 'Writer', llm_model: mapping.writer }
            ];

            const result = await window.apiClient.setRoleLLMMapping(projectId, mappings);
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
        const currentInput = inputText; // 자동 추천에 사용할 원본 텍스트 보존
        setInputText('');
        setIsLoading(true);

        // 자동 모드일 때 실시간 추천 업데이트
        if (modelSelectionMode === 'auto') {
            getAutoRecommendations(currentInput);
        }

        try {
            // Simplified - no log panel

            const response = await fetch('/api/crewai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    requirement: currentInput,
                    selectedModels: roleLLMMapping,
                    preAnalysisModel: preAnalysisModel,
                    selectedRole: selectedRole,
                    projectId: activeProject?.project_id,
                    modelSelectionMode: modelSelectionMode,
                    recommendationStrategy: recommendationStrategy,
                    reviewIterations: reviewIterations,
                    selectedTools: selectedTools,
                    apiKeys: apiKeys
                })
            });

            const data = await response.json();

            // Real-time monitoring removed

            // 응답 메시지 개선
            let responseText;
            if (data.status === 'pending_approval') {
                responseText = `🔍 AI 계획이 분석되었습니다.\n\n승인 ID: ${data.approval_id}\n상태: 승인 대기 중\n\n승인 팝업을 확인하고 계획을 검토해주세요.`;
            } else if (data.requires_approval) {
                responseText = `📋 프로젝트 계획이 준비되었습니다. 승인이 필요합니다.`;
            } else if (data.error) {
                responseText = `❌ 오류 발생: ${data.error}`;
            } else {
                responseText = data.result || data.message || '요청이 처리되었습니다.';
            }

            const aiMessage = {
                id: Date.now() + 1,
                text: responseText,
                sender: 'ai',
                role: selectedRole,
                timestamp: new Date(),
                data: data,
                status: data.status || 'completed'
            };

            setMessages(prev => [...prev, aiMessage]);

            // 승인이 필요한 경우 즉시 승인 팝업 확인
            if (data.status === 'pending_approval' || data.requires_approval) {
                // 약간의 지연 후 승인 확인 (서버에서 데이터 저장 완료 대기)
                setTimeout(() => {
                    checkPendingApprovals();
                }, 1000);
            }

            // 프로젝트 목록 새로고침
            loadProjects();
        } catch (error) {
            console.error('🚨 CrewAI 요청 실패:', error);

            const errorMessage = {
                id: Date.now() + 1,
                text: `❌ 요청 처리 중 오류가 발생했습니다.\n\n오류 내용: ${error.message}\n\n다시 시도하거나, 다른 방식으로 요청해 주세요.`,
                sender: 'ai',
                role: selectedRole,
                timestamp: new Date(),
                error: true,
                status: 'error'
            };

            setMessages(prev => [...prev, errorMessage]);

            // Error logging removed
        }

        setIsLoading(false);
    };

    // 승인 관련 함수들
    const checkPendingApprovals = async () => {
        try {
            const response = await fetch('/api/approval/pending');
            if (response.ok) {
                const approvals = await response.json();
                if (approvals.length > 0) {
                    const latestApproval = approvals[0];
                    console.log('승인 팝업 표시:', latestApproval);
                    setPendingApproval(latestApproval);
                    setShowApprovalModal(true);
                    console.log('showApprovalModal 상태 변경됨:', true);
                }
            }
        } catch (error) {
            console.error('승인 확인 실패:', error);
        }
    };

    const handleApprovalAction = async (action) => {
        console.log('handleApprovalAction 호출됨:', action);
        console.log('pendingApproval:', pendingApproval);

        if (!pendingApproval) {
            console.error('pendingApproval이 없습니다');
            return;
        }

        try {
            const response = await fetch(`/api/approval/${pendingApproval.approval_id}/respond`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: action,
                    feedback: approvalFeedback,
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                const result = await response.json();

                console.log('승인 처리 성공:', result);

                // 승인 결과 메시지 추가
                const resultMessage = {
                    id: Date.now(),
                    text: `승인 요청이 ${action === 'approve' ? '승인' : action === 'reject' ? '거부' : '수정 요청'}되었습니다.\n${result.message || ''}`,
                    sender: 'system',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, resultMessage]);

                // 모달 닫기
                setShowApprovalModal(false);
                setPendingApproval(null);
                setApprovalFeedback('');

                console.log('승인 처리 완료 - 모달 닫힘');

                // 승인된 경우 실행 계속
                if (action === 'approve') {
                    window.UIHelpers.showNotification('승인되었습니다. AI 실행을 계속합니다.', 'success');
                }
            }
        } catch (error) {
            console.error('승인 처리 실패:', error);
            window.UIHelpers.showNotification('승인 처리 중 오류가 발생했습니다.', 'error');
        }
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
        setConnectionStatus('connected'); // 연결 상태 활성화

        // 프로젝트별 LLM 매핑 로드
        await loadProjectLLMMapping(project.project_id);

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

    // 프로젝트 삭제
    const deleteProject = async (projectId, projectName) => {
        if (!confirm(`정말로 프로젝트 "${projectName}" (${projectId})를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) {
            return;
        }

        try {
            const result = await window.apiClient.deleteProject(projectId);
            if (result.success) {
                // 삭제 성공 시 프로젝트 목록에서 제거
                setProjects(projects.filter(p => p.project_id !== projectId));

                // 삭제한 프로젝트가 현재 활성 프로젝트였다면 초기화
                if (activeProject?.project_id === projectId) {
                    setActiveProject(null);
                    setMessages([]);
                }

                // 성공 메시지
                const successMessage = {
                    id: Date.now(),
                    text: `프로젝트 "${projectName}" (${projectId})가 성공적으로 삭제되었습니다.`,
                    sender: 'system',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, successMessage]);

                console.log('프로젝트 삭제 완료:', result.message);
            } else {
                alert(`프로젝트 삭제 실패: ${result.error}`);
                console.error('프로젝트 삭제 실패:', result.error);
            }
        } catch (error) {
            alert(`프로젝트 삭제 중 오류가 발생했습니다: ${error.message}`);
            console.error('프로젝트 삭제 오류:', error);
        }
    };

    // 새 프로젝트 시작
    const startNewProject = () => {
        setActiveProject(null);
        setMessages([]);
        setShowProjects(false);
    };


    // 입력 텍스트 변경 핸들러 (자동 추천용)
    const handleInputChange = (e) => {
        const newText = e.target.value;
        setInputText(newText);

        // 자동 모드일 때 일정 길이 이상이면 실시간 추천
        if (modelSelectionMode === 'auto' && newText.trim().length >= 15) {
            // 디바운싱을 위해 타이머 사용
            clearTimeout(window.recommendationTimer);
            window.recommendationTimer = setTimeout(() => {
                getAutoRecommendations(newText);
            }, 1000); // 1초 지연
        }
    };

    useEffect(() => {
        const initializeInterface = async () => {
            await loadLLMModels();
            await loadAvailableMCPs();
            // SocketIO 연결 초기화
            initializeSocketConnection();
            loadProjects();

            // 기본 LLM 매핑을 Gemini 2.5 Flash로 강제 초기화
            const defaultMapping = {
                planner: 'gemini-2.5-flash',
                researcher: 'gemini-2.5-flash',
                writer: 'gemini-2.5-flash'
            };

            // 기존 저장된 매핑이 있어도 새로운 기본값으로 덮어쓰기
            setRoleLLMMapping(defaultMapping);
            window.StorageHelpers.setItem('crewai_default_llm_mapping', defaultMapping);

            // 사전 분석 모델도 기본값으로 설정
            const defaultPreAnalysisModel = 'gemini-2.5-flash';
            setPreAnalysisModel(defaultPreAnalysisModel);
            window.StorageHelpers.setItem('crewai_pre_analysis_model', defaultPreAnalysisModel);

            // 모델 선택 모드를 수동으로 강제 설정
            const defaultMode = 'manual';
            setModelSelectionMode(defaultMode);
            window.StorageHelpers.setItem('crewai_model_selection_mode', defaultMode)

            // 추천 전략 로드
            const savedStrategy = window.StorageHelpers.getItem('crewai_recommendation_strategy');
            if (savedStrategy) {
                setRecommendationStrategy(savedStrategy);
            }

            // 승인 대기 확인
            checkPendingApprovals();
        };

        initializeInterface();

        // 30초마다 승인 대기 확인
        const approvalInterval = setInterval(checkPendingApprovals, 30000);

        return () => {
            clearInterval(approvalInterval);
            clearTimeout(window.recommendationTimer);

            // Socket 연결 정리
            if (socket) {
                socket.disconnect();
                console.log('🔌 WebSocket 연결 해제됨');
            }
        };

        // Initialization simplified - no WebSocket
    }, []);

    const renderMessage = (message) => {
        const roleInfo = roles.find(r => r.id === message.role);
        const roleName = roleInfo ? `${roleInfo.name}` : 'CrewAI';

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
                                        key={project.project_id}
                                        className={`project-item ${activeProject?.project_id === project.project_id ? 'active' : ''}`}
                                    >
                                        <div className="project-info" onClick={() => selectProject(project)}>
                                            <h4>{project.name}</h4>
                                            <p>{project.description}</p>
                                            <div className="project-id">
                                                <span className="project-id-label">ID:</span>
                                                <span className="project-id-value">{project.project_id}</span>
                                            </div>
                                        </div>
                                        <div className="project-meta" onClick={() => selectProject(project)}>
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
                                        <div className="project-actions">
                                            <button
                                                className="delete-project-btn"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    deleteProject(project.project_id, project.name);
                                                }}
                                                title={`프로젝트 ${project.name} 삭제`}
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                <div className="chat-area">
                    <div className="sidebar">
                        {/* 프로젝트 컨트롤 섹션 - 사이드바 상단에 고정 */}
                        <div className="project-controls">
                            <div className="current-project">
                                {activeProject ? (
                                    <div className="project-info-compact">
                                        <span className="project-id-badge">#{activeProject.project_id}</span>
                                        📋 {activeProject.name}
                                        <span className="project-status-badge">{activeProject.status}</span>
                                    </div>
                                ) : (
                                    <span className="project-indicator">새 프로젝트</span>
                                )}
                            </div>
                            <div className="control-buttons">
                                <button
                                    className={`control-btn projects-btn ${showProjects ? 'active' : ''}`}
                                    onClick={() => {
                                        setShowProjects(!showProjects);
                                        if (!showProjects) loadProjects();
                                    }}
                                    title="프로젝트 목록"
                                >
                                    📂 프로젝트 ({projects.length})
                                </button>
                                <button
                                    className="control-btn new-project-btn"
                                    onClick={() => setShowNewProjectModal(true)}
                                    title="새 프로젝트 생성"
                                >
                                    ➕ 새 프로젝트
                                </button>
                                {activeProject && (
                                    <button
                                        className="control-btn save-mapping-btn"
                                        onClick={saveLLMMapping}
                                        disabled={isLoading}
                                        title="LLM 매핑 저장"
                                    >
                                        💾 저장
                                    </button>
                                )}
                            </div>
                        </div>

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

                            {/* 모델 선택 모드 토글 */}
                            <div className="mode-selector" style={{ marginBottom: '15px', padding: '10px', background: 'rgba(139, 69, 19, 0.1)', borderRadius: '8px', border: '1px solid #8B4513' }}>
                                <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '8px', color: '#8B4513' }}>🎯 모델 선택 모드</div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        className={`mode-btn ${modelSelectionMode === 'auto' ? 'active' : ''}`}
                                        onClick={() => handleModeChange('auto')}
                                        style={{
                                            flex: 1,
                                            padding: '8px 12px',
                                            fontSize: '12px',
                                            border: modelSelectionMode === 'auto' ? '2px solid #8B4513' : '1px solid #ccc',
                                            borderRadius: '6px',
                                            background: modelSelectionMode === 'auto' ? '#8B4513' : '#fff',
                                            color: modelSelectionMode === 'auto' ? '#fff' : '#333',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        🤖 자동 추천
                                    </button>
                                    <button
                                        className={`mode-btn ${modelSelectionMode === 'manual' ? 'active' : ''}`}
                                        onClick={() => handleModeChange('manual')}
                                        style={{
                                            flex: 1,
                                            padding: '8px 12px',
                                            fontSize: '12px',
                                            border: modelSelectionMode === 'manual' ? '2px solid #8B4513' : '1px solid #ccc',
                                            borderRadius: '6px',
                                            background: modelSelectionMode === 'manual' ? '#8B4513' : '#fff',
                                            color: modelSelectionMode === 'manual' ? '#fff' : '#333',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        👤 수동 선택
                                    </button>
                                </div>

                                {/* 자동 모드일 때 전략 선택 */}
                                {modelSelectionMode === 'auto' && (
                                    <div style={{ marginTop: '8px' }}>
                                        <label style={{ fontSize: '11px', color: '#8B4513', marginBottom: '4px', display: 'block' }}>추천 전략:</label>
                                        <select
                                            value={recommendationStrategy}
                                            onChange={(e) => handleStrategyChange(e.target.value)}
                                            style={{ width: '100%', padding: '4px', fontSize: '11px', borderRadius: '4px' }}
                                        >
                                            <option value="balanced">균형 (비용/성능)</option>
                                            <option value="cost_optimized">비용 최적화</option>
                                            <option value="performance_optimized">성능 최적화</option>
                                            <option value="single_model">단일 모델</option>
                                        </select>
                                    </div>
                                )}
                            </div>

                            {/* 자동 추천 결과 표시 */}
                            {modelSelectionMode === 'auto' && autoRecommendations && (
                                <div className="auto-recommendations" style={{ marginBottom: '15px', padding: '10px', background: 'rgba(34, 197, 94, 0.1)', borderRadius: '8px', border: '1px solid #22C55E' }}>
                                    <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '8px', color: '#16A34A' }}>
                                        🎯 AI 추천 결과 (신뢰도: {(autoRecommendations.confidence * 100).toFixed(0)}%)
                                    </div>
                                    <div style={{ fontSize: '11px', color: '#16A34A', marginBottom: '8px' }}>
                                        {autoRecommendations.reasoning}
                                    </div>
                                    <div style={{ fontSize: '10px', color: '#666' }}>
                                        예상 비용: {autoRecommendations.total_cost} |
                                        에이전트: {autoRecommendations.analysis?.agent_count}개 |
                                        복잡도: {autoRecommendations.analysis?.complexity}
                                    </div>
                                </div>
                            )}

                            {/* 자동 추천 로딩 표시 */}
                            {modelSelectionMode === 'auto' && isLoadingRecommendations && (
                                <div className="loading-recommendations" style={{ marginBottom: '15px', padding: '10px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', border: '1px solid #3B82F6' }}>
                                    <div style={{ fontSize: '12px', color: '#2563EB', textAlign: 'center' }}>
                                        🔄 최적 모델 분석 중...
                                    </div>
                                </div>
                            )}

                            <div className="llm-status" style={{ fontSize: '12px', marginBottom: '10px', padding: '8px', background: 'rgba(0,0,0,0.05)', borderRadius: '6px' }}>
                                {llmOptions.length > 0 ? (
                                    <span style={{ color: 'green' }}>✅ {llmOptions.length}개 모델 로드됨</span>
                                ) : (
                                    <span style={{ color: 'orange' }}>⏳ LLM 모델 로딩 중...</span>
                                )}
                                {modelSelectionMode === 'auto' && (
                                    <span style={{ color: '#8B4513', fontSize: '11px', marginLeft: '8px' }}>
                                        (자동 추천 모드)
                                    </span>
                                )}
                            </div>
                            <div className="mapping-list">
                                {/* 사전 분석 모델 선택 */}
                                <div className="mapping-item" style={{ display: 'flex', alignItems: 'center', gap: '0', borderBottom: '1px solid #eee', paddingBottom: '8px', marginBottom: '8px' }}>
                                    <div className="mapping-role" style={{ minWidth: '70px', width: '70px' }}>
                                        <span className="role-name" style={{ fontWeight: 'bold', color: '#6B46C1' }}>
                                            사전 분석
                                        </span>
                                    </div>
                                    <select
                                        className="llm-select"
                                        style={{ fontSize: '12px', padding: '6px 8px', minWidth: '160px' }}
                                        value={preAnalysisModel || 'gemini-2.5-flash'}
                                        onChange={(e) => handlePreAnalysisModelChange(e.target.value)}
                                        disabled={llmOptions.length === 0}
                                    >
                                        {llmOptions.length === 0 ? (
                                            <option value="">모델 로딩 중...</option>
                                        ) : (
                                            llmOptions.map(llm => (
                                                <option key={llm.id} value={llm.id}>
                                                    {llm.name} ({llm.provider})
                                                    {llm.parameter_size ? ` [${llm.parameter_size}]` : ''}
                                                </option>
                                            ))
                                        )}
                                    </select>
                                </div>

                                {/* 역할별 LLM 선택 */}
                                {roles.map(role => (
                                    <div key={role.id} className="mapping-item" style={{ display: 'flex', alignItems: 'center', gap: '0', borderBottom: '1px solid #eee', paddingBottom: '8px', marginBottom: '8px' }}>
                                        <div className="mapping-role" style={{ minWidth: '70px', width: '70px' }}>
                                            <span className={`role-name ${selectedRole === role.id ? 'current' : ''}`} style={{ fontWeight: 'bold', color: '#6B46C1' }}>
                                                {role.name}
                                            </span>
                                            {modelSelectionMode === 'auto' && (
                                                <span style={{ fontSize: '10px', color: '#8B4513', marginLeft: '4px' }}>
                                                    (자동)
                                                </span>
                                            )}
                                        </div>
                                        {modelSelectionMode === 'manual' ? (
                                            <select
                                                className="llm-select"
                                                style={{ fontSize: '12px', padding: '6px 8px', minWidth: '160px' }}
                                                value={roleLLMMapping[role.id] || 'gemini-2.5-flash'}
                                                onChange={(e) => handleRoleLLMChange(role.id, e.target.value)}
                                                disabled={llmOptions.length === 0}
                                            >
                                                {llmOptions.length === 0 ? (
                                                    <option value="">모델 로딩 중...</option>
                                                ) : (
                                                    llmOptions.map(llm => (
                                                        <option key={llm.id} value={llm.id}>
                                                            {llm.name} ({llm.provider})
                                                            {llm.parameter_size ? ` [${llm.parameter_size}]` : ''}
                                                            {llm.available === false ? ' [사용불가]' : ''}
                                                        </option>
                                                    ))
                                                )}
                                            </select>
                                        ) : (
                                            <div style={{
                                                fontSize: '12px',
                                                padding: '6px 8px',
                                                minWidth: '160px',
                                                background: '#f5f5f5',
                                                borderRadius: '4px',
                                                border: '1px solid #ddd',
                                                color: '#666'
                                            }}>
                                                {llmOptions.find(llm => llm.id === roleLLMMapping[role.id])?.name || roleLLMMapping[role.id]}
                                                {autoRecommendations && (
                                                    <span style={{ fontSize: '10px', color: '#16A34A', marginLeft: '4px' }}>
                                                        (AI 추천)
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* 검토-재작성 반복 횟수 설정 */}
                        <div className="review-iterations">
                            <h3>🔄 검토-재작성 반복 횟수</h3>
                            <div className="iterations-selector" style={{ padding: '15px', background: 'rgba(147, 51, 234, 0.1)', borderRadius: '8px', border: '1px solid #9333EA' }}>
                                <div style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '10px', color: '#9333EA' }}>
                                    품질 검토 반복 설정
                                </div>

                                {/* 버튼 그리드 */}
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '12px' }}>
                                    {[0, 1, 2, 3].map(count => (
                                        <button
                                            key={count}
                                            onClick={() => setReviewIterations(count)}
                                            style={{
                                                padding: '12px 8px',
                                                fontSize: '14px',
                                                fontWeight: 'bold',
                                                border: reviewIterations === count ? '2px solid #9333EA' : '1px solid #ccc',
                                                borderRadius: '6px',
                                                background: reviewIterations === count ? '#9333EA' : '#fff',
                                                color: reviewIterations === count ? '#fff' : '#333',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            {count}회
                                        </button>
                                    ))}
                                </div>

                                {/* 정보 표시 */}
                                <div style={{ padding: '10px', background: 'rgba(255,255,255,0.8)', borderRadius: '6px', fontSize: '12px' }}>
                                    <div style={{ marginBottom: '6px', color: '#666' }}>
                                        <strong style={{ color: '#9333EA' }}>💡 {reviewIterations}회 선택됨</strong>
                                    </div>
                                    <div style={{ color: '#666' }}>
                                        총 <strong style={{ color: '#E11D48' }}>{4 + (reviewIterations * 2)}개</strong> 태스크 생성
                                        <span style={{ fontSize: '11px', color: '#999', marginLeft: '4px' }}>
                                            (사전분석 + 계획 + 조사 + 초기작성 {reviewIterations > 0 ? `+ 검토/재작성 ${reviewIterations}회` : ''})
                                        </span>
                                    </div>

                                    {/* 반복 횟수별 설명 */}
                                    <div style={{ marginTop: '8px', padding: '6px', background: 'rgba(147, 51, 234, 0.05)', borderRadius: '4px', fontSize: '11px', color: '#555' }}>
                                        {reviewIterations === 0 && '⚡ 빠른 프로토타입 (검토 없음)'}
                                        {reviewIterations === 1 && '📝 기본 품질 (1회 검토)'}
                                        {reviewIterations === 2 && '🎯 고품질 (2회 검토)'}
                                        {reviewIterations === 3 && '💎 최고 품질 (3회 검토, 프로덕션 레벨)'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* MCP/도구 선택 패널 */}
                        <div className="config-section">
                            <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#333' }}>🛠️ 도구 선택</h4>
                                    <span style={{ fontSize: '11px', color: '#999' }}>
                                        (선택사항 - Researcher에게 도구 제공)
                                    </span>
                                </div>
                                <button
                                    onClick={() => setShowMCPModal(!showMCPModal)}
                                    style={{
                                        padding: '6px 12px',
                                        background: selectedTools.length > 0 ? '#9333EA' : '#E5E7EB',
                                        color: selectedTools.length > 0 ? '#fff' : '#666',
                                        border: 'none',
                                        borderRadius: '6px',
                                        fontSize: '12px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {selectedTools.length > 0 ? `${selectedTools.length}개 선택됨` : '도구 선택'}
                                </button>
                            </div>

                            {showMCPModal && (
                                <div style={{
                                    background: '#fff',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: '8px',
                                    padding: '16px',
                                    marginTop: '8px'
                                }}>
                                    {/* 카테고리 탭 */}
                                    <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                                        {['all', 'search', 'knowledge', 'media', 'file'].map(cat => (
                                            <button
                                                key={cat}
                                                onClick={() => setMcpCategory(cat)}
                                                style={{
                                                    padding: '6px 12px',
                                                    background: mcpCategory === cat ? '#9333EA' : '#F3F4F6',
                                                    color: mcpCategory === cat ? '#fff' : '#666',
                                                    border: 'none',
                                                    borderRadius: '6px',
                                                    fontSize: '12px',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s'
                                                }}
                                            >
                                                {cat === 'all' && '전체'}
                                                {cat === 'search' && '🔍 검색'}
                                                {cat === 'knowledge' && '📚 지식베이스'}
                                                {cat === 'media' && '🎬 미디어'}
                                                {cat === 'file' && '📁 파일'}
                                            </button>
                                        ))}
                                    </div>

                                    {/* 도구 목록 */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '10px', maxHeight: '300px', overflowY: 'auto' }}>
                                        {Object.entries(availableMCPs)
                                            .filter(([key, mcp]) => mcpCategory === 'all' || mcp.category === mcpCategory)
                                            .map(([key, mcp]) => (
                                            <div
                                                key={key}
                                                onClick={() => {
                                                    if (selectedTools.includes(key)) {
                                                        setSelectedTools(selectedTools.filter(t => t !== key));
                                                        // API 키도 제거
                                                        const newKeys = { ...apiKeys };
                                                        delete newKeys[key];
                                                        setApiKeys(newKeys);
                                                    } else {
                                                        setSelectedTools([...selectedTools, key]);
                                                    }
                                                }}
                                                style={{
                                                    padding: '12px',
                                                    background: selectedTools.includes(key) ? 'rgba(147, 51, 234, 0.1)' : '#F9FAFB',
                                                    border: selectedTools.includes(key) ? '2px solid #9333EA' : '1px solid #E5E7EB',
                                                    borderRadius: '8px',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s'
                                                }}
                                            >
                                                <div style={{ display: 'flex', alignItems: 'start', gap: '8px' }}>
                                                    <span style={{ fontSize: '20px' }}>{mcp.icon}</span>
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ fontSize: '13px', fontWeight: '600', color: '#333', marginBottom: '4px' }}>
                                                            {mcp.name}
                                                        </div>
                                                        <div style={{ fontSize: '11px', color: '#666', lineHeight: '1.4' }}>
                                                            {mcp.description}
                                                        </div>
                                                        {mcp.config?.cost && (
                                                            <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                                                                {mcp.config.cost}
                                                            </div>
                                                        )}
                                                    </div>
                                                    {selectedTools.includes(key) && (
                                                        <span style={{ color: '#9333EA', fontSize: '18px' }}>✓</span>
                                                    )}
                                                </div>

                                                {/* API 키 입력 */}
                                                {selectedTools.includes(key) && mcp.config?.env_vars && mcp.config.env_vars.length > 0 && (
                                                    <div style={{ marginTop: '10px' }} onClick={(e) => e.stopPropagation()}>
                                                        {mcp.config.env_vars.map(envVar => (
                                                            <input
                                                                key={envVar}
                                                                type="password"
                                                                placeholder={`${envVar} 입력`}
                                                                value={apiKeys[key] || ''}
                                                                onChange={(e) => setApiKeys({
                                                                    ...apiKeys,
                                                                    [key]: e.target.value
                                                                })}
                                                                style={{
                                                                    width: '100%',
                                                                    padding: '6px 8px',
                                                                    border: '1px solid #E5E7EB',
                                                                    borderRadius: '4px',
                                                                    fontSize: '11px',
                                                                    marginTop: '4px'
                                                                }}
                                                            />
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>

                                    {/* 선택 요약 */}
                                    {selectedTools.length > 0 && (
                                        <div style={{
                                            marginTop: '12px',
                                            padding: '10px',
                                            background: 'rgba(147, 51, 234, 0.05)',
                                            borderRadius: '6px',
                                            fontSize: '12px',
                                            color: '#555'
                                        }}>
                                            <strong style={{ color: '#9333EA' }}>✓ {selectedTools.length}개 도구 선택됨:</strong>
                                            <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                                                {selectedTools.map(toolKey => (
                                                    <span
                                                        key={toolKey}
                                                        style={{
                                                            padding: '4px 8px',
                                                            background: '#fff',
                                                            border: '1px solid #9333EA',
                                                            borderRadius: '4px',
                                                            fontSize: '11px',
                                                            color: '#9333EA'
                                                        }}
                                                    >
                                                        {availableMCPs[toolKey]?.icon} {availableMCPs[toolKey]?.name}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>

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
                                    onChange={handleInputChange}
                                    onKeyPress={handleKeyPress}
                                    placeholder={`${roles.find(r => r.id === selectedRole)?.name}에게 작업을 요청하세요...${modelSelectionMode === 'auto' ? ' (15자 이상 입력시 자동 모델 추천)' : ''}`}
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
                                onClick={createProject}
                                disabled={isLoading || !newProjectData.name.trim()}
                            >
                                {isLoading ? '생성 중...' : '프로젝트 생성'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* 승인 팝업 모달 */}
            {showApprovalModal && pendingApproval && (
                <div className="modal-overlay approval-overlay" onClick={() => setShowApprovalModal(false)}>
                    <div className="modal-content approval-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header approval-header">
                            <h2>🔍 AI 계획 승인 요청</h2>
                            <button
                                className="modal-close"
                                onClick={() => setShowApprovalModal(false)}
                            >
                                ✕
                            </button>
                        </div>

                        <div className="modal-body approval-body">
                            <div className="approval-info">
                                <div className="info-grid compact">
                                    <div className="info-item">
                                        <div className="info-label">프레임워크</div>
                                        <div className="info-value">{pendingApproval.analysis_result?.framework?.toUpperCase() || 'N/A'}</div>
                                    </div>
                                    <div className="info-item">
                                        <div className="info-label">생성 시간</div>
                                        <div className="info-value">{new Date(pendingApproval.created_at).toLocaleString('ko-KR')}</div>
                                    </div>
                                    <div className="info-item">
                                        <div className="info-label">예상 시간</div>
                                        <div className="info-value">{pendingApproval.metadata?.estimated_completion_time || '미정'}</div>
                                    </div>
                                </div>
                            </div>

                            <div className="approval-content">
                                <div className="content-section compact">
                                    <h4>📋 원본 요청</h4>
                                    <div className="content-box compact">
                                        {pendingApproval.analysis_result?.original_request || '요청 정보 없음'}
                                    </div>
                                </div>

                                <div className="content-section compact">
                                    <h4>🎯 프로젝트 목표</h4>
                                    <div className="content-box compact">
                                        <div className="objectives-list">
                                            {pendingApproval.analysis_result?.analysis?.objectives?.map((obj, index) => (
                                                <div key={index} className="objective-item">• {obj}</div>
                                            )) || <div>목표 정보 없음</div>}
                                        </div>
                                    </div>
                                </div>

                                <div className="content-section compact">
                                    <h4>👥 AI 에이전트 ({pendingApproval.analysis_result?.analysis?.agents?.length || 0}명)</h4>
                                    <div className="content-box compact">
                                        {pendingApproval.analysis_result?.analysis?.agents?.map((agent, index) => (
                                            <div key={index} className="agent-item compact">
                                                <strong>🤖 {agent.role}</strong>
                                                <div className="agent-details">
                                                    <span className="expertise">{agent.expertise}</span>
                                                </div>
                                            </div>
                                        )) || <div>에이전트 정보 없음</div>}
                                    </div>
                                </div>
                            </div>

                            <div className="feedback-section compact">
                                <label htmlFor="approval-feedback" className="feedback-label">
                                    💬 피드백 (선택사항):
                                </label>
                                <textarea
                                    id="approval-feedback"
                                    className="feedback-textarea compact"
                                    value={approvalFeedback}
                                    onChange={(e) => setApprovalFeedback(e.target.value)}
                                    placeholder="승인/거부 사유나 수정 요청사항을 입력하세요..."
                                />
                            </div>
                        </div>

                        <div className="modal-footer approval-actions">
                            <button
                                className="modal-button approve-btn"
                                onClick={() => handleApprovalAction('approve')}
                            >
                                ✅ 승인
                            </button>
                            <button
                                className="modal-button modify-btn"
                                onClick={() => handleApprovalAction('request_revision')}
                            >
                                🔄 수정 요청
                            </button>
                            <button
                                className="modal-button reject-btn"
                                onClick={() => handleApprovalAction('reject')}
                            >
                                ❌ 거부
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Real-time log panel removed */}
        </div>
    );
};

// React 18 createRoot API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<CrewAIInterface />);