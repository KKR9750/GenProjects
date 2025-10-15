// Projects Page Component - Execution-first Layout

let projects = [];
let executions = [];
let filteredProjects = [];
let llmOptions = [];
let selectedProjectId = null;
const projectSettingsMap = {};
const executionDetailsMap = {}

function normalizeProject(raw, index = 0) {
    if (!raw || typeof raw !== 'object') return null;
    const idCandidateList = [raw.id, raw.project_id, raw.projectId, raw.uuid, raw.guid, raw.identifier, raw.project_uuid];
    const idCandidate = idCandidateList.find(value => value !== undefined && value !== null && value !== '');
    const id = idCandidate !== undefined && idCandidate !== null && idCandidate !== '' ? String(idCandidate) : 'project-' + index + '-' + Date.now();

    const name = raw.name || raw.project_name || raw.title || raw.projectTitle || '이름 없는 프로젝트';
    const description = raw.description || raw.project_description || raw.summary || raw.details || '';
    const framework = raw.framework || raw.selected_ai || raw.ai_framework || raw.platform || raw.engine || 'unknown';
    const projectType = raw.project_type || raw.type || raw.category || raw.projectType || '기타';
    const createdAt = raw.created_at || raw.createdAt || raw.created || raw.created_date || raw.created_time || null;

    return {
        ...raw,
        id,
        name,
        description,
        framework,
        project_type: projectType,
        created_at: createdAt
    };
}

function normalizeExecution(raw) {
    if (!raw || typeof raw !== 'object') return null;
    const projectIdCandidate = raw.project_id || raw.projectId || raw.project_uuid || raw.project || raw.id;
    const projectId = projectIdCandidate !== undefined && projectIdCandidate !== null && projectIdCandidate !== '' ? String(projectIdCandidate) : null;
    const status = raw.status || raw.state || raw.execution_status || 'pending';
    const deliverablesCount = raw.deliverables_count ?? raw.deliverable_count ?? raw.outputs_count ?? (Array.isArray(raw.deliverables) ? raw.deliverables.length : 0);

    return {
        ...raw,
        project_id: projectId,
        status,
        deliverables_count: deliverablesCount
    };
}


function renderProjectsPage() {
    const root = document.getElementById('root');
    if (!root) return;

    let html = '';
    html += '<div class="projects-page">';
    html += '  <header class="projects-header">';
    html += '    <h1>📁 프로젝트 관리</h1>';
    html += '  </header>';
    html += '  <div class="projects-content">';
    html += '    <aside class="projects-sidebar">';
    html += '      <section class="sidebar-card">';
    html += '        <header class="sidebar-card__header">';
    html += '          <h2>검색 필터</h2>';
    html += '        </header>';
    html += '        <div class="sidebar-card__body">';
    html += '          <div class="form-control-inline">';
    html += '            <div class="form-control-group">';
    html += '              <label for="frameworkFilter">AI 프레임워크</label>';
    html += '              <select id="frameworkFilter">';
    html += '                <option value="">전체</option>';
    html += '                <option value="crew_ai">CrewAI</option>';
    html += '                <option value="meta_gpt">MetaGPT</option>';
    html += '              </select>';
    html += '            </div>';
    html += '            <div class="form-control-group">';
    html += '              <label for="searchInput">🔍 프로젝트 검색</label>';
    html += '              <input type="text" id="searchInput" placeholder="프로젝트 이름 또는 설명">';
    html += '            </div>';
    html += '          </div>';
    html += '        </div>';
    html += '        <footer class="sidebar-card__footer">';
    html += '          <button class="btn btn-secondary" id="filterResetBtn">초기화</button>';
    html += '          <button class="btn btn-primary" id="filterApplyBtn">검색</button>';
    html += '        </footer>';
    html += '      </section>';
    html += '      <section class="sidebar-card sidebar-card--list">';
    html += '        <header class="sidebar-card__header">';
    html += '          <div>';
    html += '            <h2>프로젝트 목록</h2>';
    html += '            <p id="projectCountLabel" class="card-subtitle">0건</p>';
    html += '          </div>';
    html += '        </header>';
    html += '        <div class="sidebar-card__body sidebar-card__body--scroll" id="projectList">';
    html += '          <div class="empty-state small">프로젝트를 불러오는 중...</div>';
    html += '        </div>';
    html += '      </section>';
    html += '    </aside>';
    html += '    <section class="project-main">';
    html += '      <div id="loadingState" class="panel loading-panel">';
    html += '        <div class="spinner"></div>';
    html += '        <p>프로젝트를 불러오는 중...</p>';
    html += '      </div>';
    html += '      <div id="errorState" class="panel error-panel" style="display:none;">';
    html += '        <h3>⚠️ 데이터를 불러오지 못했습니다</h3>';
    html += '        <p id="errorMessage"></p>';
    html += '        <button class="btn btn-secondary" id="retryLoadBtn">다시 시도</button>';
    html += '      </div>';
    html += '      <div id="projectDetailContainer" class="project-detail-container" style="display:none;">';
    html += '        <section class="panel project-summary" id="projectSummary"></section>';
    html += '        <section class="panel project-settings" id="executionSettings"></section>';
    html += '        <section class="panel project-output" id="executionOutput"></section>';
    html += '      </div>';
    html += '      <div id="emptyState" class="panel empty-panel" style="display:none;">';
    html += '        <div class="empty-state">';
    html += '          <div class="empty-state-icon">📂</div>';
    html += '          <h3>생성된 프로젝트가 없습니다</h3>';
    html += '          <p>요구사항 분석과 템플릿 생성을 통해 첫 프로젝트를 만들어 보세요.</p>';
    html += '          <a href="/templates" class="btn btn-primary" target="_blank">템플릿 페이지 열기</a>';
    html += '        </div>';
    html += '      </div>';
    html += '    </section>';
    html += '  </div>';
    html += '</div>';
    root.innerHTML = html;

    setupProjectEventListeners();
    initializeData();

    if (window.projectsUpdateInterval) {
        clearInterval(window.projectsUpdateInterval);
    }
    window.projectsUpdateInterval = setInterval(updateExecutionStatuses, 5000);
}
async function initializeData() {
    await Promise.all([loadLLMModels(), loadProjectsData()]);
}

function setupProjectEventListeners() {
    const applyBtn = document.getElementById('filterApplyBtn');
    const resetBtn = document.getElementById('filterResetBtn');
    const searchInput = document.getElementById('searchInput');
    const retryBtn = document.getElementById('retryLoadBtn');

    if (applyBtn) applyBtn.addEventListener('click', applyFilters);
    if (resetBtn) resetBtn.addEventListener('click', resetFilters);
    if (searchInput) {
        searchInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                applyFilters();
            }
        });
    }
    if (retryBtn) retryBtn.addEventListener('click', loadProjectsData);
}

async function loadLLMModels() {
    try {
        const response = await fetch('/api/llm/models');
        if (!response.ok) throw new Error('LLM 모델 조회 실패 (' + response.status + ')');

        const data = await response.json();
        if (data.success || data.status === 'success') {
            const models = data.models || data.data || [];
            llmOptions = models.map(function (model) {
                return {
                    id: model.id || model.model_id || model.name,
                    name: model.name || model.display_name || model.id,
                    provider: model.provider || model.vendor || ''
                };
            });
        } else {
            throw new Error(data.error || 'LLM 모델 정보를 가져오지 못했습니다.');
        }
    } catch (error) {
        console.warn('LLM 모델 로드 실패:', error.message);
        llmOptions = [
            { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google' },
            { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
            { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', provider: 'Anthropic' }
        ];
    } finally {
        renderExecutionSettings();
    }
}
async function loadProjectsData() {
    try {
        setLoadingState(true);
        hideErrorState();

        const responses = await Promise.all([
            fetch('/api/templates/projects'),
            fetch('/api/templates/executions').catch(function () { return { ok: false }; })
        ]);

        const projectsResponse = responses[0];
        const executionsResponse = responses[1];
        if (!projectsResponse.ok) throw new Error('프로젝트 정보를 불러오지 못했습니다.');

        const projectsData = await projectsResponse.json();
        if (projectsData && Object.prototype.hasOwnProperty.call(projectsData, 'success') && projectsData.success === false) {
            throw new Error(projectsData.error || '프로젝트 데이터를 가져오지 못했습니다.');
        }

        const rawProjects = Array.isArray(projectsData)
            ? projectsData
            : projectsData.projects || projectsData.data || projectsData.items || [];

        projects = rawProjects
            .map(function (item, index) { return normalizeProject(item, index); })
            .filter(Boolean);

        if (executionsResponse.ok) {
            const executionsData = await executionsResponse.json();
            if (executionsData && Object.prototype.hasOwnProperty.call(executionsData, 'success') && executionsData.success === false) {
                executions = [];
            } else {
                const rawExecutions = Array.isArray(executionsData)
                    ? executionsData
                    : executionsData.executions || executionsData.data || executionsData.items || [];
                executions = rawExecutions
                    .map(function (item) { return normalizeExecution(item); })
                    .filter(function (exec) { return exec && exec.project_id; });
            }
        } else {
            executions = [];
        }

        projects.forEach(function (project, index) {
            if (!project.id) {
                project.id = 'project-' + index + '-' + Date.now();
            }
            const execution = executions.find(function (exec) { return exec.project_id === project.id; });
            project.execution = execution || null;
        });

        filteredProjects = projects.slice();
        updateProjectCount();
        renderProjectList();

        if (projects.length === 0) {
            showEmptyState();
        } else {
            hideEmptyState();
            const hasSelected = selectedProjectId && projects.some(function (project) { return project.id === selectedProjectId; });
            if (hasSelected) {
                selectProject(selectedProjectId, { silent: true });
            } else if (filteredProjects.length > 0) {
                selectProject(filteredProjects[0].id);
            } else {
                clearProjectDetails();
            }
        }

    } catch (error) {
        showErrorState(error.message);
        console.error('프로젝트 로드 오류:', error);
    } finally {
        setLoadingState(false);
    }
}

async function updateExecutionStatuses() {
    try {
        const response = await fetch('/api/templates/executions');
        if (!response.ok) return;

        const data = await response.json();
        if (data && Object.prototype.hasOwnProperty.call(data, 'success') && data.success === false) return;

        const rawExecutions = Array.isArray(data)
            ? data
            : data.executions || data.data || data.items || [];

        executions = rawExecutions
            .map(function (item) { return normalizeExecution(item); })
            .filter(function (exec) { return exec && exec.project_id; });

        projects.forEach(function (project, index) {
            if (!project.id) {
                project.id = 'project-' + index + '-' + Date.now();
            }
            const execution = executions.find(function (exec) { return exec.project_id === project.id; });
            project.execution = execution || null;
        });

        renderProjectList();
        renderProjectSummary();

        if (selectedProjectId) {
            await fetchExecutionDetails(selectedProjectId);
        }
    } catch (error) {
        console.warn('실행 상태 업데이트 실패:', error);
    }
}
function applyFilters() {
    const frameworkValue = (document.getElementById('frameworkFilter') || {}).value || '';
    const searchInput = document.getElementById('searchInput');
    const searchValue = searchInput ? searchInput.value.trim().toLowerCase() : '';

    filteredProjects = projects.filter(function (project) {
        const frameworkMatch = !frameworkValue || project.framework === frameworkValue;

        const name = (project.name || '').toLowerCase();
        const description = (project.description || '').toLowerCase();
        const searchMatch = !searchValue || name.indexOf(searchValue) > -1 || description.indexOf(searchValue) > -1;

        return frameworkMatch && searchMatch;
    });

    updateProjectCount();
    renderProjectList();

    if (filteredProjects.length === 0) {
        const list = document.getElementById('projectList');
        if (list) {
            list.innerHTML = '<div class="empty-state small">검색 조건에 해당하는 프로젝트가 없습니다.</div>';
        }
        clearProjectDetails();
        return;
    }

    const stillSelected = filteredProjects.some(function (project) { return project.id === selectedProjectId; });
    if (!stillSelected) {
        selectProject(filteredProjects[0].id);
    }
}

function resetFilters() {
    const frameworkFilter = document.getElementById('frameworkFilter');
    const searchInput = document.getElementById('searchInput');

    if (frameworkFilter) frameworkFilter.value = '';
    if (searchInput) searchInput.value = '';

    filteredProjects = projects.slice();
    updateProjectCount();
    renderProjectList();

    if (filteredProjects.length > 0) {
        selectProject(filteredProjects[0].id);
    } else {
        clearProjectDetails();
    }
}
function renderProjectList() {
    const list = document.getElementById('projectList');
    if (!list) return;

    if (filteredProjects.length === 0) {
        list.innerHTML = '<div class="empty-state small">프로젝트가 없습니다.</div>';
        return;
    }

    const cards = filteredProjects.map(function (project) {
        const createdAt = formatDateLabel(project.created_at);
        const deliverables = project.execution && project.execution.deliverables_count ? project.execution.deliverables_count : 0;
        const isActive = project.id === selectedProjectId;
        const description = project.description || project.requirement || '설명이 없습니다.';

        return `
            <article class="project-list-item ${isActive ? 'active' : ''}" data-project-id="${project.id}">
                <div class="project-list-item__header">
                    <h3 class="project-list-item__title">${escapeHtml(project.name || '이름 없는 프로젝트')}</h3>
                </div>
                <p class="project-list-item__id">ID: ${project.id}</p>
                <p class="project-list-item__meta">
                    <span>${createdAt}</span>
                    <span>${formatFramework(project.framework)}</span>
                </p>
                <p class="project-list-item__description">${escapeHtml(description)}</p>
                <div class="project-list-item__footer">
                    <span>산출물 ${deliverables}개</span>
                    <button class="btn btn-danger btn-xs btn-delete-individual" data-delete-id="${project.id}">삭제</button>
                </div>
            </article>
        `;
    }).join('');

    list.innerHTML = cards;

    Array.from(list.querySelectorAll('.project-list-item')).forEach(function (item) {
        item.addEventListener('click', function () {
            const projectId = item.getAttribute('data-project-id');
            selectProject(projectId);
        });
    });

    Array.from(list.querySelectorAll('.btn-delete-individual')).forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.stopPropagation();
            const projectId = button.getAttribute('data-delete-id');
            deleteProjectById(projectId);
        });
    });
}

function selectProject(projectId, options) {
    options = options || {};
    selectedProjectId = projectId;
    renderProjectList();

    // Load full project data
    loadFullProjectData(projectId).then(function() {
        renderProjectSummary();
        renderExecutionSettings();
        renderExecutionOutput();
    });

    if (!options.silent) {
        fetchExecutionDetails(projectId);
    }
}

async function loadFullProjectData(projectId) {
    try {
        // Load project details
        const projectResp = await fetch(`/api/v2/projects/${projectId}`);
        const projectData = await projectResp.json();

        // Update project in list
        const projectIndex = projects.findIndex(p => p.id === projectId);
        if (projectIndex !== -1 && projectData.project) {
            projects[projectIndex] = normalizeProject(projectData.project, projectIndex);
        }

        // Load agents
        const agentsResp = await fetch(`/api/v2/projects/${projectId}/agents?framework=crewai`);
        const agentsData = await agentsResp.json();
        if (agentsData.agents) {
            projects[projectIndex].agents = agentsData.agents;
        }

        // Load deliverables
        const deliverablesResp = await fetch(`/api/v2/projects/${projectId}/deliverables`);
        const deliverablesData = await deliverablesResp.json();
        if (deliverablesData.deliverables) {
            projects[projectIndex].deliverables = deliverablesData.deliverables;
        }

        // Re-render project summary to show agents
        renderProjectSummary();

    } catch (error) {
        console.error('Failed to load full project data:', error);
    }
}

function renderProjectSummary() {
    const container = document.getElementById('projectSummary');
    if (!container) return;

    if (!selectedProjectId) {
        container.innerHTML = '<div class="empty-state small">프로젝트를 선택하면 상세 정보가 표시됩니다.</div>';
        const detailContainer = document.getElementById('projectDetailContainer');
        if (detailContainer) detailContainer.style.display = 'none';
        return;
    }

    const project = projects.find(function (p) { return p.id === selectedProjectId; });
    if (!project) {
        container.innerHTML = '<div class="empty-state small">선택한 프로젝트를 찾을 수 없습니다.</div>';
        return;
    }

    const detailContainer = document.getElementById('projectDetailContainer');
    if (detailContainer) detailContainer.style.display = 'grid';

    const projectType = project.project_type || '-';
    const createdAt = project.created_at ? new Date(project.created_at).toLocaleString('ko-KR') : '-';
    const deliverables = project.execution && project.execution.deliverables_count ? project.execution.deliverables_count : 0;

    let summary = `
        <header class="panel-header">
            <div>
                <h2>${escapeHtml(project.name || '이름 없는 프로젝트')}</h2>
                <p class="panel-subtitle">${escapeHtml(project.description || project.requirement || '설명 없음')}</p>
            </div>
        </header>
        <div class="summary-compact">
            <span><strong>Project ID:</strong> ${project.id}</span>
            <span><strong>프레임워크:</strong> ${formatFramework(project.framework)}</span>
            <span><strong>프로젝트 유형:</strong> ${formatProjectType(projectType)}</span>
            <span><strong>생성일:</strong> ${createdAt}</span>
            <span><strong>산출물:</strong> ${deliverables}개</span>
        </div>
    `;

    // Add CrewAI Agent information if available
    if (project.framework === 'crewai' && project.agents && project.agents.length > 0) {
        summary += '<div class="agents-section">';
        summary += '<h3>정의된 Agent 정보</h3>';
        summary += '<div class="agents-list">';

        project.agents.forEach(function(agent) {
            const tools = agent.tools ? JSON.parse(agent.tools) : [];
            const toolsText = Array.isArray(tools) && tools.length > 0 ? tools.join(', ') : '없음';

            summary += `
                <div class="agent-card">
                    <div class="agent-header">
                        <h4>${escapeHtml(agent.role || 'Unknown Role')}</h4>
                        <span class="agent-order">#${agent.agent_order}</span>
                    </div>
                    <div class="agent-details">
                        <div class="agent-detail-item">
                            <strong>Goal:</strong>
                            <p>${escapeHtml(agent.goal || '-')}</p>
                        </div>
                        <div class="agent-detail-item">
                            <strong>Backstory:</strong>
                            <p>${escapeHtml(agent.backstory || '-')}</p>
                        </div>
                        <div class="agent-detail-row">
                            <div class="agent-detail-item">
                                <strong>LLM Model:</strong>
                                <span>${escapeHtml(agent.llm_model || '-')}</span>
                            </div>
                            <div class="agent-detail-item">
                                <strong>Tools:</strong>
                                <span>${escapeHtml(toolsText)}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        summary += '</div>';
        summary += '</div>';
    }

    container.innerHTML = summary;
}

function renderExecutionSettings() {
    const container = document.getElementById('executionSettings');
    if (!container) return;

    if (!selectedProjectId) {
        container.innerHTML = '<div class="empty-state small">실행 설정을 변경하려면 프로젝트를 선택하세요.</div>';
        return;
    }

    const project = projects.find(function (p) { return p.id === selectedProjectId; });
    if (!project) {
        container.innerHTML = '<div class="empty-state small">선택한 프로젝트 정보를 불러오지 못했습니다.</div>';
        return;
    }

    const settings = getProjectSettings(project);
    const llmOptionsHtml = llmOptions.map(function (model) {
        const selected = model.id === settings.llm_model ? ' selected' : '';
        const providerText = model.provider ? ' (' + model.provider + ')' : '';
        return '<option value="' + model.id + '"' + selected + '>' + model.name + providerText + '</option>';
    }).join('');

    let html = '';
    html += '<header class="panel-header">';
    html += '  <div>';
    html += '    <h2>실행 설정</h2>';
    html += '    <p class="panel-subtitle">실행 전에 필요한 옵션을 조정하세요.</p>';
    html += '  </div>';
    html += '</header>';
    html += '<div class="settings-grid">';
    html += '  <div class="form-control">';
    html += '    <label for="llmModelSelect">LLM 모델</label>';
    html += '    <select id="llmModelSelect">' + llmOptionsHtml + '</select>';
    html += '  </div>';
    html += '  <div class="form-control form-control--toggle">';
    html += '    <label class="toggle">';
    html += '      <input type="checkbox" id="verboseToggle"' + (settings.verbose ? ' checked' : '') + '>';
    html += '      <span class="toggle-slider"></span>';
    html += '      <span class="toggle-label">Verbose 모드</span>';
    html += '    </label>';
    html += '    <p class="toggle-description">세부 로그를 포함해 상세한 출력을 제공합니다.</p>';
    html += '  </div>';
    html += '  <div class="form-control form-control--toggle">';
    html += '    <label class="toggle">';
    html += '      <input type="checkbox" id="delegationToggle"' + (settings.allow_delegation ? ' checked' : '') + '>';
    html += '      <span class="toggle-slider"></span>';
    html += '      <span class="toggle-label">Allow Delegation</span>';
    html += '    </label>';
    html += '    <p class="toggle-description">필요 시 에이전트가 작업을 위임하도록 허용합니다.</p>';
    html += '  </div>';
    html += '  <div class="form-control">';
    html += '    <label for="executionNotes">실행 메모 (선택)</label>';
    html += '    <textarea id="executionNotes" rows="3" placeholder="이번 실행에서 참고해야 할 사항을 기록하세요.">' + escapeHtml(settings.notes || '') + '</textarea>';
    html += '  </div>';
    html += '</div>';
    html += '<footer class="panel-footer">';
    html += '  <div class="action-group">';
    html += '    <button class="btn btn-secondary" id="cancelExecutionBtn">⏸ 실행 중지</button>';
    html += '    <button class="btn btn-primary" id="executeProjectBtn">▶️ 실행</button>';
    html += '  </div>';
    html += '</footer>';

    container.innerHTML = html;

    const llmSelect = container.querySelector('#llmModelSelect');
    const verboseToggle = container.querySelector('#verboseToggle');
    const delegationToggle = container.querySelector('#delegationToggle');
    const notesInput = container.querySelector('#executionNotes');
    const executeBtn = container.querySelector('#executeProjectBtn');
    const cancelBtn = container.querySelector('#cancelExecutionBtn');

    if (llmSelect) {
        llmSelect.addEventListener('change', function (event) {
            updateProjectSettings(selectedProjectId, { llm_model: event.target.value });
        });
    }
    if (verboseToggle) {
        verboseToggle.addEventListener('change', function (event) {
            updateProjectSettings(selectedProjectId, { verbose: event.target.checked });
        });
    }
    if (delegationToggle) {
        delegationToggle.addEventListener('change', function (event) {
            updateProjectSettings(selectedProjectId, { allow_delegation: event.target.checked });
        });
    }
    if (notesInput) {
        notesInput.addEventListener('input', function (event) {
            updateProjectSettings(selectedProjectId, { notes: event.target.value });
        });
    }
    if (executeBtn) executeBtn.addEventListener('click', executeSelectedProject);
    if (cancelBtn) cancelBtn.addEventListener('click', cancelSelectedExecution);
}
function renderExecutionOutput() {
    const container = document.getElementById('executionOutput');
    if (!container) return;

    if (!selectedProjectId) {
        container.innerHTML = '<div class="empty-state small">실행 로그는 프로젝트를 선택하면 표시됩니다.</div>';
        return;
    }

    const execution = executionDetailsMap[selectedProjectId];
    if (!execution) {
        let emptyHtml = '';
        emptyHtml += '<header class="panel-header">';
        emptyHtml += '  <div>';
        emptyHtml += '    <h2>실행 로그</h2>';
        emptyHtml += '    <p class="panel-subtitle">최근 실행 기록이 없습니다.</p>';
        emptyHtml += '  </div>';
        emptyHtml += '</header>';
        emptyHtml += '<div class="empty-state small">아직 실행 기록이 존재하지 않습니다. 실행 설정을 완료하고 프로젝트를 실행해 보세요.</div>';
        container.innerHTML = emptyHtml;
        return;
    }

    const status = execution.status || 'pending';
    const startTime = execution.start_time ? new Date(execution.start_time).toLocaleString('ko-KR') : '-';
    const endTime = execution.end_time ? new Date(execution.end_time).toLocaleString('ko-KR') : '-';
    const logs = execution.output || [];
    const hasError = !!execution.error;
    const deliverables = execution.deliverables_count || 0;

    let html = '';
    html += '<header class="panel-header">';
    html += '  <div>';
    html += '    <h2>실행 로그</h2>';
    html += '    <p class="panel-subtitle">최근 실행 상태와 로그를 확인하세요.</p>';
    html += '  </div>';
    html += '  <span class="status-badge status-' + status + '">' + getProjectStatusText(status) + '</span>';
    html += '</header>';

    html += '<dl class="summary-grid summary-grid--compact">';
    html += '  <div><dt>시작 시간</dt><dd>' + startTime + '</dd></div>';
    html += '  <div><dt>완료 시간</dt><dd>' + endTime + '</dd></div>';
    html += '  <div><dt>산출물</dt><dd>' + deliverables + '개</dd></div>';
    if (hasError) {
        html += '  <div class="summary-grid__full"><dt>오류</dt><dd class="error-text">' + escapeHtml(execution.error) + '</dd></div>';
    }
    html += '</dl>';

    html += '<div class="log-viewer" id="logViewer">';
    if (logs.length === 0) {
        html += '<p class="empty-log">표시할 로그가 없습니다.</p>';
    } else {
        logs.forEach(function (line) {
            html += '<div class="log-line">' + escapeHtml(line) + '</div>';
        });
    }
    html += '</div>';

    html += '<footer class="panel-footer">';
    html += '  <div class="action-group">';
    html += '    <button class="btn btn-secondary" id="refreshExecutionBtn">🔄 로그 새로고침</button>';
    if (deliverables > 0) {
        html += '    <button class="btn btn-primary" id="viewResultBtn">📂 결과 열기</button>';
    }
    html += '  </div>';
    html += '</footer>';

    container.innerHTML = html;

    const refreshBtn = container.querySelector('#refreshExecutionBtn');
    const resultBtn = container.querySelector('#viewResultBtn');

    if (refreshBtn) {
        refreshBtn.addEventListener('click', function () {
            fetchExecutionDetails(selectedProjectId, { force: true });
        });
    }
    if (resultBtn) {
        resultBtn.addEventListener('click', function () {
            viewProjectResults(selectedProjectId);
        });
    }
}
async function executeSelectedProject() {
    if (!selectedProjectId) {
        alert('먼저 실행할 프로젝트를 선택하세요.');
        return;
    }

    try {
        const settings = projectSettingsMap[selectedProjectId] || {};
        const payload = {
            auto_start: true,
            llm_model: settings.llm_model || null,
            verbose: !!settings.verbose,
            allow_delegation: !!settings.allow_delegation,
            notes: settings.notes || ''
        };

        const response = await fetch('/api/templates/projects/' + selectedProjectId + '/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (data.success) {
            alert('프로젝트 실행이 시작되었습니다.');
            await loadProjectsData();
            await fetchExecutionDetails(selectedProjectId, { force: true });
        } else {
            alert('프로젝트 실행 실패: ' + (data.error || data.message || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('프로젝트 실행 중 오류가 발생했습니다: ' + error.message);
    }
}

async function cancelSelectedExecution() {
    if (!selectedProjectId) {
        alert('중지할 프로젝트를 선택하세요.');
        return;
    }

    if (!confirm('현재 실행 중인 작업을 중지하시겠습니까?')) return;

    try {
        const response = await fetch('/api/templates/projects/' + selectedProjectId + '/execution/cancel', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            alert('실행이 취소되었습니다.');
            await updateExecutionStatuses();
        } else {
            alert('실행 취소 실패: ' + (data.error || data.message || '알 수 없는 오류'));
        }
    } catch (error) {
        alert('실행 취소 중 오류가 발생했습니다: ' + error.message);
    }
}

async function fetchExecutionDetails(projectId, options) {
    options = options || {};
    try {
        const response = await fetch('/api/templates/projects/' + projectId + '/execution/status');
        if (!response.ok) {
            if (response.status === 404) {
                executionDetailsMap[projectId] = null;
                renderExecutionOutput();
                return;
            }
            throw new Error('실행 정보를 가져오지 못했습니다.');
        }

        const data = await response.json();
        if (data.success) {
            executionDetailsMap[projectId] = data.execution;
        }
    } catch (error) {
        if (options.force) {
            alert('실행 정보를 불러오지 못했습니다: ' + error.message);
        }
        console.warn('실행 상세 로드 실패:', error);
    } finally {
        if (projectId === selectedProjectId) {
            renderExecutionOutput();
        }
    }
}

async function deleteProjectById(projectId) {
    if (!projectId) return;
    if (!confirm(`정말로 이 프로젝트(ID: ${projectId})를 삭제하시겠습니까?`)) return;

    try {
        const data = await window.apiClient.delete(`/api/templates/projects/${projectId}`);

        if (data.success) {
            alert('프로젝트가 삭제되었습니다.');
            delete projectSettingsMap[projectId];
            delete executionDetailsMap[projectId];
            
            if (selectedProjectId === projectId) {
                selectedProjectId = null;
            }
            await loadProjectsData();
        } else {
            alert(`프로젝트 삭제 실패: ${data.error || data.message || '알 수 없는 오류'}`);
        }
    } catch (error) {
        alert(`프로젝트 삭제 중 오류가 발생했습니다: ${error.message}`);
    }
}


function viewProjectResults(projectId) {
    const execution = executionDetailsMap[projectId];
    if (execution && execution.deliverables_count > 0) {
        window.open('/api/templates/projects/' + projectId + '/results', '_blank');
    } else {
        alert('결과 파일이 없습니다.');
    }
}
function setLoadingState(isLoading) {
    const loadingPanel = document.getElementById('loadingState');
    if (loadingPanel) {
        loadingPanel.style.display = isLoading ? 'flex' : 'none';
    }
}

function showErrorState(message) {
    const errorPanel = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');
    if (errorPanel && errorMessage) {
        errorPanel.style.display = 'flex';
        errorMessage.textContent = message || '알 수 없는 오류가 발생했습니다.';
    }
}

function hideErrorState() {
    const errorPanel = document.getElementById('errorState');
    if (errorPanel) {
        errorPanel.style.display = 'none';
    }
}

function showEmptyState() {
    const emptyPanel = document.getElementById('emptyState');
    const detailContainer = document.getElementById('projectDetailContainer');
    if (emptyPanel) emptyPanel.style.display = 'flex';
    if (detailContainer) detailContainer.style.display = 'none';
}

function hideEmptyState() {
    const emptyPanel = document.getElementById('emptyState');
    if (emptyPanel) emptyPanel.style.display = 'none';
}

function clearProjectDetails() {
    selectedProjectId = null;
    renderProjectSummary();
    renderExecutionSettings();
    renderExecutionOutput();
}

function updateProjectSettings(projectId, updates) {
    const current = projectSettingsMap[projectId] || {};
    projectSettingsMap[projectId] = Object.assign({}, current, updates);
}

function getProjectSettings(project) {
    if (!projectSettingsMap[project.id]) {
        const defaultModel = project.default_llm_model || project.llm_model || (project.llm_mappings && project.llm_mappings[0] ? project.llm_mappings[0].llm_model : '') || (llmOptions[0] ? llmOptions[0].id : '');
        projectSettingsMap[project.id] = {
            llm_model: defaultModel,
            verbose: project.verbose || project.is_verbose || false,
            allow_delegation: project.allow_delegation || false,
            notes: ''
        };
    }
    return projectSettingsMap[project.id];
}

function updateProjectCount() {
    const countLabel = document.getElementById('projectCountLabel');
    if (countLabel) {
        countLabel.textContent = filteredProjects.length + '건';
    }
}
function getProjectStatusText(status) {
    const map = {
        pending: '대기중',
        starting: '시작중',
        running: '실행중',
        completed: '완료',
        failed: '실패',
        cancelled: '취소됨'
    };
    return map[status] || '알 수 없음';
}

function formatDateLabel(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
    return date.toLocaleDateString('ko-KR');
}

function formatFramework(framework) {
    const map = {
        crew_ai: 'CrewAI',
        meta_gpt: 'MetaGPT'
    };
    return map[framework] || framework || '-';
}

function formatProjectType(type) {
    const map = {
        web_app: '웹 앱',
        mobile_app: '모바일 앱',
        api_server: 'API 서버',
        desktop_app: '데스크톱 앱',
        data_analysis: '데이터 분석',
        ml_project: '머신러닝 프로젝트',
        blockchain: '블록체인',
        game_dev: '게임 개발',
        ecommerce: '전자상거래',
        crm_system: 'CRM 시스템'
    };
    return map[type] || type || '-';
}

function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

renderProjectsPage();