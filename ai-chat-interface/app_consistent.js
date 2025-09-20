const { useState, useEffect, useRef } = React;

const AIChatInterface = () => {
    const [selectedAI, setSelectedAI] = useState('crew-ai');
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [currentWorkflow, setCurrentWorkflow] = useState(null); // MetaGPT 워크플로우 상태
    const [showProjects, setShowProjects] = useState(false); // 프로젝트 목록 표시 상태
    const [projects, setProjects] = useState([]); // 프로젝트 목록
    const [selectedProject, setSelectedProject] = useState(null); // 선택된 프로젝트
    const messagesEndRef = useRef(null);

    const aiOptions = [
        { id: 'crew-ai', name: 'CREW AI', description: '협업 기반 AI 에이전트' },
        { id: 'meta-gpt', name: 'MetaGPT', description: '단계별 승인 기반 전문 개발팀' }
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const formatStepByStepResponse = (data) => {
        if (!data.success) {
            return `❌ **오류 발생**: ${data.error}\n\n${data.details || ''}`;
        }

        const { step, step_name, result, need_approval, next_step } = data;

        let response = `## 📋 **${step}단계: ${step_name}**\n\n`;

        // 수정 요청 결과 처리
        if (result.modification_note) {
            response += `### 🔄 **수정 반영**
- **피드백**: ${result.original_feedback || '수정 요청'}
- **수정 내용**: ${result.message}
- **상태**: ${result.modification_note}

---
`;
            // 승인 요청 추가
            if (need_approval) {
                response += `\n\n✅ **수정된 내용을 승인하시겠습니까?**\n\n`;
                response += `승인하시면 다음 단계(${next_step}단계)로 진행됩니다.`;
            }
            return response;
        }

        // 단계별 결과 포맷팅
        if (step === 1) {
            // 요구사항 정리 단계
            response += `### 🎯 **프로젝트 개요**
- **프로젝트명**: ${result.project_name}
- **기술 스택**: ${JSON.stringify(result.technology_stack)}
- **대상 사용자**: ${result.target_users.join(', ')}

### 🔧 **주요 기능**
${result.main_features.map(feature => `- ${feature}`).join('\n')}

### ✅ **성공 기준**
${result.success_criteria.map(criteria => `- ${criteria}`).join('\n')}

### 📝 **상세 요구사항**
**기능 요구사항:**
${result.detailed_requirements.functional_requirements.map(req => `- ${req}`).join('\n')}

**비기능 요구사항:**
${result.detailed_requirements.non_functional_requirements.map(req => `- ${req}`).join('\n')}

**제약사항:**
${result.detailed_requirements.constraints.map(constraint => `- ${constraint}`).join('\n')}`;

        } else if (step === 2) {
            // 프로젝트 분석 단계 - 새 프로젝트와 기존 프로젝트 동일한 포맷
            response += `### 🏗️ **아키텍처 패턴**
- ${result.architecture_pattern}

### 🧩 **핵심 모듈**
${result.core_modules.map(module => `- **${module.name}**: ${module.description}`).join('\n')}

### 📊 **데이터 흐름**
- **입력**: ${result.data_flow.input_flow}
- **처리**: ${result.data_flow.processing_flow}
- **출력**: ${result.data_flow.output_flow}

### 📦 **외부 의존성**
${result.external_dependencies.map(dep => `- ${dep}`).join('\n')}

### ⚠️ **위험 요소**
${result.risk_assessment.map(risk => `- **${risk.risk}**: ${risk.mitigation}`).join('\n')}

### 🛠️ **구현 방식**
- **개발 방법론**: ${result.implementation_approach.development_methodology}
- **구현 순서**: ${result.implementation_approach.implementation_order}
- **테스트 전략**: ${result.implementation_approach.testing_strategy}`;

        } else if (step === 3) {
            // 시스템 설계 단계
            response += `### 🏛️ **시스템 아키텍처**
${JSON.stringify(result.system_architecture, null, 2)}

### 📋 **클래스 구조**
${Object.entries(result.class_structure).map(([className, classInfo]) =>
    `**${className}**:
- 메서드: ${classInfo.methods.join(', ')}
- 속성: ${classInfo.attributes.join(', ')}`
).join('\n\n')}

### 📁 **파일 구조**
${JSON.stringify(result.file_structure, null, 2)}`;

        } else if (step === 4) {
            // 코드 개발 단계
            response += `### 💻 **생성된 파일들**
${Object.keys(result.generated_files).map(filename => `- ${filename}`).join('\n')}

### 📝 **구현 노트**
${result.implementation_notes.map(note => `- ${note}`).join('\n')}

### 🚀 **설치 지침**
${result.setup_instructions.map((instruction, index) => `${index + 1}. ${instruction}`).join('\n')}

### 📚 **사용 예제**
${result.usage_examples.map(example => `- ${example}`).join('\n')}`;

        } else if (step === 5) {
            // 단위 테스트 단계
            response += `### 🧪 **테스트 파일들**
${Object.keys(result.test_files).map(filename => `- ${filename}`).join('\n')}

### 📊 **테스트 커버리지**
${Object.entries(result.test_coverage).map(([component, coverage]) => `- **${component}**: ${coverage}`).join('\n')}

### 📋 **테스트 지침**
${result.test_instructions.map((instruction, index) => `${index + 1}. ${instruction}`).join('\n')}

### 📈 **품질 보고서**
${JSON.stringify(result.quality_report, null, 2)}`;
        }

        // 승인 요청 추가
        if (need_approval) {
            response += `\n\n---\n\n✅ **이 단계를 승인하시겠습니까?**\n\n`;
            response += `승인하시면 다음 단계(${next_step}단계)로 진행됩니다.`;
        } else {
            response += `\n\n---\n\n🎉 **모든 단계가 완료되었습니다!**`;
        }

        return response;
    };

    // 기존 프로젝트 단계 결과 포맷팅 - 새 프로젝트와 동일한 형식 사용
    const formatStepResult = (stepNumber, stepResult) => {
        const stepNames = {
            1: "요구사항 정리",
            2: "프로젝트 분석",
            3: "시스템 설계",
            4: "코드 개발",
            5: "단위 테스트"
        };

        let content = `## 📋 **${stepNumber}단계: ${stepNames[stepNumber]} 결과**\n\n`;

        // 2단계는 새 프로젝트와 동일한 포맷 사용
        if (stepNumber === 2 && stepResult.architecture_pattern) {
            content += `### 🏗️ **아키텍처 패턴**
- ${stepResult.architecture_pattern}

### 🧩 **핵심 모듈**
${stepResult.core_modules.map(module => `- **${module.name}**: ${module.description}`).join('\n')}

### 📊 **데이터 흐름**
- **입력**: ${stepResult.data_flow.input_flow}
- **처리**: ${stepResult.data_flow.processing_flow}
- **출력**: ${stepResult.data_flow.output_flow}

### 📦 **외부 의존성**
${stepResult.external_dependencies.map(dep => `- ${dep}`).join('\n')}

### ⚠️ **위험 요소**
${stepResult.risk_assessment.map(risk => `- **${risk.risk}**: ${risk.mitigation}`).join('\n')}

### 🛠️ **구현 방식**
- **개발 방법론**: ${stepResult.implementation_approach.development_methodology}
- **구현 순서**: ${stepResult.implementation_approach.implementation_order}
- **테스트 전략**: ${stepResult.implementation_approach.testing_strategy}`;
        }
        // 다른 단계들의 일반적인 처리
        else {
            if (stepResult.analysis) {
                content += `### 📊 **분석 결과**\n${stepResult.analysis}\n\n`;
            }

            if (stepResult.design) {
                content += `### 🏗️ **설계 내용**\n${stepResult.design}\n\n`;
            }

            if (stepResult.code) {
                content += `### 💻 **생성된 코드**\n\
\
${stepResult.code}\n\
\
`;
            }

            if (stepResult.tests) {
                content += `### 🧪 **테스트 코드**\n\
\
${stepResult.tests}\n\
\
`;
            }

            if (stepResult.summary) {
                content += `### 📝 **요약**\n${stepResult.summary}\n\n`;
            }

            // 일반적인 content 필드 처리
            if (stepResult.content && typeof stepResult.content === 'string') {
                content += `### 📄 **상세 내용**\n${stepResult.content}\n\n`;
            }

            // JSON 객체의 다른 필드들 처리 (2단계가 아닌 경우에만)
            Object.keys(stepResult).forEach(key => {
                if (!['analysis', 'design', 'code', 'tests', 'summary', 'content', 'architecture_pattern', 'core_modules', 'data_flow', 'external_dependencies', 'risk_assessment', 'implementation_approach'].includes(key)) {
                    if (typeof stepResult[key] === 'string' && stepResult[key].length > 0) {
                        content += `### 📌 **${key}**\n${stepResult[key]}\n\n`;
                    }
                }
            });
        }

        content += `\n✅ **${stepNumber}단계가 완료되었습니다.**\n`;
        content += `🔄 이 결과를 검토하고 **승인** 또는 **수정 요청**을 해주세요.`;

        return content;
    };

    const formatAdvancedResponse = (data) => {
        const analysis = data.project_analysis;
        const teamPlan = data.team_plan;
        const executionPlan = data.execution_plan;

        let response = `## 🔍 **MetaGPT 프로젝트 분석 완료**

### 📊 **프로젝트 정보**
- **타입**: ${analysis.project_type} (${analysis.domain})
- **기술 스택**: ${analysis.technology}
- **복잡도**: ${analysis.complexity}
- **예상 소요시간**: ${analysis.estimated_time}

### 🎯 **핵심 기능**
${analysis.key_features.map(feature => `- ${feature}`).join('\n')}

### 📋 **요구사항**
${analysis.requirements.map(req => `- ${req}`).join('\n')}

### 👥 **팀 구성** (${teamPlan.team_size}명)
${teamPlan.team_members.map(member =>
    `**${member.name}** (${member.estimated_time})
- 담당업무: ${member.responsibility}
- 결과물: ${member.deliverables.join(', ')}`
).join('\n\n')}

### 🚀 **실행 계획** (${executionPlan.total_phases}단계)
${executionPlan.phases.map(phase =>
    `**${phase.phase}단계**: ${phase.title}
- 설명: ${phase.description}
- 소요시간: ${phase.estimated_time}
- 결과물: ${phase.deliverables.join(', ')}`
).join('\n\n')}

### 💰 **예상 비용**: ${executionPlan.estimated_budget}

---

✅ **다음 단계**: 위 계획을 승인하시면 단계별로 팀원들이 순차적으로 작업을 진행합니다.

❓ **승인하시겠습니까?** (예/아니오)`;

        return response;
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleAISelect = (aiId) => {
        setSelectedAI(aiId);

        const aiName = aiOptions.find(ai => ai.id === aiId)?.name;
        const switchMessage = {
            id: Date.now(),
            text: `${aiName}로 전환되었습니다. 어떤 프로그램을 만들어드릴까요?`,
            sender: 'ai',
            aiType: aiId,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, switchMessage]);
    };

    const callRealAPI = async (userMessage, aiType) => {
        const apiEndpoint = aiType === 'crew-ai' ? '/api/crewai' : '/api/metagpt';

        try {
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    requirement: userMessage,
                    selectedModels: {
                        primary: aiType,
                        temperature: 0.7
                    },
                    aiType: aiType
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                // CrewAI 응답 처리
                if (aiType === 'crew-ai') {
                    return data.result || data.message || '요청이 처리되었습니다.';
                }
                // MetaGPT 응답 처리
                else {
                    // 단계별 워크플로우 응답 처리
                    if (data.step && data.step_name) {
                        return {
                            text: formatStepByStepResponse(data),
                            workflowData: data.need_approval ? {
                                step: data.step,
                                next_step: data.next_step,
                                need_approval: data.need_approval
                            } : null
                        };
                    }

                    // MetaGPT (Advanced) 응답 처리
                    if (data.type === 'advanced') {
                        return formatAdvancedResponse(data);
                    }

                    let responseText = '';

                    if (data.execution_id) {
                        responseText = `MetaGPT 실행이 시작되었습니다. (실행 ID: ${data.execution_id})

${data.message}

실행 상태는 실시간으로 확인할 수 있습니다.`;
                    } else {
                        responseText = data.message || data.result || '요청이 처리되었습니다.';

                        if (data.project_path) {
                            responseText += `

📂 프로젝트 경로: ${data.project_path}`;
                        }
                    }

                    return responseText;
                }
            } else {
                return `⚠️ 오류가 발생했습니다: ${data.error}` + `

${data.note || ''}`;
            }
        } catch (error) {
            console.error('API 호출 실패:', error);
            // 실패 시 시뮬레이션 응답으로 폴백
            return getSimulatedResponse(userMessage, aiType, error);
        }
    };

    const getSimulatedResponse = (userMessage, aiType, error) => {
        if (aiType === 'crew-ai') {
            return `[🔌 연결 실패 - 시뮬레이션 모드]

CREW AI 팀이 "${userMessage}" 프로젝트를 분석했습니다.

협업 기반 개발 프로세스:

1️⃣ **요구사항 분석** (Project Manager)
   - 사용자 니즈 파악
   - 기능 우선순위 설정

2️⃣ **아키텍처 설계** (System Architect)
   - 전체 시스템 구조
   - 기술 스택 선정

3️⃣ **개발 실행** (Development Team)
   - 애자일 방식 적용
   - 지속적 통합/배포

4️⃣ **품질 관리** (QA Team)
   - 자동화 테스트
   - 성능 최적화

⚠️ **실제 CrewAI 서버와 연결하려면:**
- CrewAI 서버를 포트 3001에서 시작해주세요
- 또는 Flask 서버의 CrewAI 통합 기능을 확인해주세요

오류 정보: ${error?.message || '서버 연결 실패'}`;
        } else {
            return `[🔌 연결 실패 - 시뮬레이션 모드]

MetaGPT가 "${userMessage}" 요청을 분석했습니다.

고성능 솔루션 제공 준비:

🚀 최적화된 알고리즘 사용
⚡ 빠른 실행 속도 보장
💾 메모리 효율적 구현
🔧 즉시 사용 가능한 코드

구체적인 기능이나 프로그래밍 언어를 지정해주시면 맞춤형 코드를 생성하겠습니다.

예시 요청:
- "Python으로 데이터 분석 도구 만들어줘"
- "JavaScript로 계산기 웹앱 만들어줘"
- "React 컴포넌트 생성해줘"

⚠️ **실제 MetaGPT와 연결하려면:**
- MetaGPT 환경 설정을 완료해주세요
- 또는 Flask 서버의 MetaGPT 통합 기능을 확인해주세요

오류 정보: ${error?.message || '서버 연결 실패'}`;
        }
    };

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
            const response = await callRealAPI(inputText, selectedAI);

            const aiMessage = {
                id: Date.now() + 1,
                text: response.text || response,
                sender: 'ai',
                aiType: selectedAI,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, aiMessage]);

            // MetaGPT 워크플로우 상태 설정
            if (selectedAI === 'meta-gpt' && response.workflowData) {
                setCurrentWorkflow({
                    requirement: inputText,
                    currentStep: response.workflowData.step,
                    nextStep: response.workflowData.next_step,
                    needApproval: response.workflowData.need_approval
                });
            }
        } catch (error) {
            console.error('Error generating AI response:', error);
            const errorMessage = {
                id: Date.now() + 1,
                text: '죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요.',
                sender: 'ai',
                aiType: selectedAI,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const loadProjects = async () => {
        try {
            const response = await fetch('/api/projects');
            const data = await response.json();

            if (data.success) {
                setProjects(data.projects);
            } else {
                console.error('프로젝트 목록 로드 실패:', data.error);
            }
        } catch (error) {
            console.error('프로젝트 목록 로드 오류:', error);
        }
    };

    const handleProjectSelect = async (projectName) => {
        try {
            const response = await fetch(`/api/projects/${projectName}`);
            const data = await response.json();

            if (data.success) {
                setSelectedProject(data.project);
                setShowProjects(false);

                const project = data.project;
                const currentStep = project.metadata.current_step;
                const completedSteps = Object.keys(project.step_results).length;

                // 프로젝트 정보와 현재 단계 결과를 메시지로 표시
                const messages = [];

                // 1. 프로젝트 기본 정보
                messages.push({
                    id: Date.now(),
                    text: formatProjectInfo(project),
                    sender: 'ai',
                    aiType: 'meta-gpt',
                    timestamp: new Date()
                });

                // 2. 현재 진행 중인 단계의 결과 표시 (완료된 가장 최근 단계)
                if (completedSteps > 0) {
                    const lastCompletedStep = Math.max(...Object.keys(project.step_results).map(Number));
                    const stepResult = project.step_results[lastCompletedStep];

                    if (stepResult) {
                        messages.push({
                            id: Date.now() + 1,
                            text: formatStepResult(lastCompletedStep, stepResult),
                            sender: 'ai',
                            aiType: 'meta-gpt',
                            timestamp: new Date(),
                            workflowData: currentStep <= 5 ? {
                                step: currentStep,
                                next_step: currentStep + 1,
                                need_approval: true
                            } : null
                        });
                    }
                }

                setMessages(messages);

                // 완료된 단계가 있고 아직 모든 단계가 완료되지 않았다면 승인 필요 상태로 설정
                if (completedSteps > 0 && currentStep <= 5) {
                    setCurrentWorkflow({
                        requirement: project.metadata.requirement,
                        currentStep: currentStep,
                        nextStep: currentStep + 1,
                        needApproval: true,
                        projectName: projectName
                    });
                }
            } else {
                console.error('프로젝트 로드 실패:', data.error);
            }
        } catch (error) {
            console.error('프로젝트 로드 오류:', error);
        }
    };

    const formatProjectInfo = (project) => {
        const { metadata, step_results, next_step } = project;
        const completedSteps = Object.keys(step_results).length;

        let info = `## 📂 **프로젝트: ${metadata.project_name}**

### 📋 **프로젝트 정보**
- **요구사항**: ${metadata.requirement}
- **생성일**: ${new Date(metadata.created_at).toLocaleString()}
- **진행상황**: ${completedSteps}/5 단계 완료 (${(completedSteps/5*100).toFixed(1)}%)

### 📊 **완료된 단계**`;

        const stepNames = {
            1: "요구사항 정리",
            2: "프로젝트 분석",
            3: "시스템 설계",
            4: "코드 개발",
            5: "단위 테스트"
        };

        for (let i = 1; i <= 5; i++) {
            if (step_results[i]) {
                info += `\n✅ **${i}단계**: ${stepNames[i]}`;
            } else {
                info += `\n⏳ **${i}단계**: ${stepNames[i]} (대기 중)`;
                if (i === next_step) {
                    info += ` ← **다음 단계**`;
                }
            }
        }

        if (next_step && next_step <= 5) {
            info += `\n\n🚀 **다음 단계**: ${next_step}단계 (${stepNames[next_step]})를 계속 진행할 수 있습니다.`;
        } else if (completedSteps >= 5) {
            info += `\n\n🎉 **프로젝트 완료**: 모든 단계가 완료되었습니다!`;
        }

        return info;
    };

    const handleStepApproval = async (approve, modifications = '') => {
        if (!currentWorkflow) return;

        setIsLoading(true);

        try {
            const response = await fetch('/api/metagpt/step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    requirement: currentWorkflow.requirement,
                    step: approve ? currentWorkflow.nextStep : (currentWorkflow.currentStep - 1),
                    user_response: approve ? 'reject' : 'reject',
                    modifications: modifications
                })
            });

            const data = await response.json();

            if (data.success) {
                const stepResponseText = formatStepByStepResponse(data);

                const aiMessage = {
                    id: Date.now(),
                    text: stepResponseText,
                    sender: 'ai',
                    aiType: 'meta-gpt',
                    timestamp: new Date()
                };

                setMessages(prev => [...prev, aiMessage]);

                // 워크플로우 상태 업데이트
                if (data.need_approval) {
                    setCurrentWorkflow({
                        requirement: currentWorkflow.requirement,
                        currentStep: data.step,
                        nextStep: data.next_step,
                        needApproval: true
                    });
                } else {
                    setCurrentWorkflow(null); // 워크플로우 완료
                }
            } else {
                const errorMessage = {
                    id: Date.now(),
                    text: `❌ 단계 진행 중 오류가 발생했습니다: ${data.error}`,
                    sender: 'ai',
                    aiType: 'meta-gpt',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, errorMessage]);
            }
        } catch (error) {
            console.error('Step approval error:', error);
            const errorMessage = {
                id: Date.now(),
                text: '단계 승인 처리 중 오류가 발생했습니다. 다시 시도해주세요.',
                sender: 'ai',
                aiType: 'meta-gpt',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
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
                    {message.text.includes('```') ? (
                        message.text.split('```').map((part, index) => {
                            if (index % 2 === 1) {
                                return <div key={index} className="code-block">{part}</div>;
                            }
                            return <div key={index}>{part}</div>;
                        })
                    ) : (
                        message.text.split('\n').map((line, index) => (
                            <div key={index}>{line}</div>
                        ))
                    )}
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
                            {aiOptions.map(ai => (
                                <button
                                    key={ai.id}
                                    className={`ai-option ${selectedAI === ai.id ? 'active' : ''}`}
                                    onClick={() => handleAISelect(ai.id)}
                                    title={ai.description}
                                >
                                    {ai.name}
                                </button>
                            ))}
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
                                        setSelectedProject(null);
                                        setCurrentWorkflow(null);
                                        setMessages([]);
                                        setShowProjects(false);
                                    }}
                                >
                                    ➕ 새 프로젝트
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* 프로젝트 목록 표시 (Sidebar) */}
                {showProjects && (
                    <div className="projects-list">
                        <h3>📂 기존 프로젝트 목록</h3>
                        {projects.length === 0 ? (
                            <div className="no-projects">
                                <p>아직 생성된 프로젝트가 없습니다.</p>
                                <p>새 프로젝트를 시작해보세요!</p>
                            </div>
                        ) : (
                            <div className="projects-grid">
                                {projects.map(project => (
                                    <div
                                        key={project.project_name}
                                        className="project-card"
                                        onClick={() => handleProjectSelect(project.project_name)}
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
                    {/* 프로젝트 목록은 사이드바로 이동 */}
                    {messages.length === 0 && !showProjects ? (
                        <div className="welcome-message">
                            <h3>환영합니다! 👋</h3>
                            <p>AI를 선택하고 만들고 싶은 프로그램에 대해 설명해주세요.</p>
                            <p>CREW AI는 팀워크 기반으로, MetaGPT는 고성능 코드 생성에 특화되어 있습니다.</p>
                            <div className="status-info">
                                <h4>🔧 시스템 상태</h4>
                                <p>• Flask 통합 서버가 실행 중입니다</p>
                                <p>• CrewAI 및 MetaGPT 연결을 자동으로 시도합니다</p>
                                <p>• 연결 실패 시 시뮬레이션 모드로 동작합니다</p>
                            </div>
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
                                응답 생성 중
                                <div className="loading-dots">
                                    <div className="loading-dot"></div>
                                    <div className="loading-dot"></div>
                                    <div className="loading-dot"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                <div className="chat-input">
                    {/* MetaGPT 워크플로우 승인 버튼 */}
                    {currentWorkflow && currentWorkflow.needApproval && !isLoading && (
                        <div className="approval-section">
                            <div className="approval-message">
                                ✅ <strong>{currentWorkflow.currentStep}단계</strong>를 승인하시겠습니까?
                            </div>
                            <div className="approval-buttons">
                                <button
                                    onClick={() => handleStepApproval(true)}
                                    className="approve-button"
                                    disabled={isLoading}
                                >
                                    ✓ 승인하고 다음 단계로
                                </button>
                                <button
                                    onClick={() => handleStepApproval(false)}
                                    className="reject-button"
                                    disabled={isLoading}
                                >
                                    ✗ 수정 요청
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="input-container">
                        <textarea
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={currentWorkflow && currentWorkflow.needApproval ?
                                "위 단계를 먼저 승인해주세요..." :
                                `${aiOptions.find(ai => ai.id === selectedAI)?.name}에게 프로그램 요청을 입력하세요...`}
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
                    <div className="input-hint">
                        {currentWorkflow && currentWorkflow.needApproval ?
                            "단계별 승인이 필요합니다" :
                            "Enter를 눌러 전송 • Shift+Enter로 줄바꿈"}
                    </div>
                </div>
            </div>
        </div>
    );
};

// React 앱 렌더링
const root = ReactDOM.createRoot ? ReactDOM.createRoot(document.getElementById('root')) : null;
if (root) {
    root.render(<AIChatInterface />);
} else {
    ReactDOM.render(<AIChatInterface />, document.getElementById('root'));
}