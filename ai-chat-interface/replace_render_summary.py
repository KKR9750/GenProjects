#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
renderProjectSummary() 함수 교체
"""

import re

with open('projects.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace renderProjectSummary function
old_func_pattern = r'function renderProjectSummary\(\) \{[^}]*\{[^}]*\}[^}]*\}[^}]*\}[^}]*\}[^}]*container\.innerHTML = summary;[\s]*\}'

new_func = '''function renderProjectSummary() {
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

    const executionStatus = project.execution && project.execution.status ? project.execution.status : 'pending';
    const projectType = project.project_type || '-';
    const createdAt = project.created_at ? new Date(project.created_at).toLocaleString('ko-KR') : '-';

    // Get description from final_requirement
    let description = project.description || '';
    if (!description && project.final_requirement) {
        const lines = project.final_requirement.split('\\n').filter(l => l.trim());
        description = lines.slice(0, 3).join(' ').substring(0, 200) + '...';
    }
    if (!description) description = '설명 없음';

    // Deliverables count
    const deliverablesCount = project.deliverables ? project.deliverables.length : 0;

    let summary = `
        <header class="panel-header">
            <div>
                <h2>${escapeHtml(project.name || '이름 없는 프로젝트')}</h2>
                <p class="panel-subtitle">${escapeHtml(description)}</p>
            </div>
            <span class="status-badge status-${executionStatus}">${getProjectStatusText(executionStatus)}</span>
        </header>
        <dl class="summary-grid">
            <div><dt>Project ID</dt><dd>${project.id}</dd></div>
            <div><dt>프레임워크</dt><dd>${formatFramework(project.framework)}</dd></div>
            <div><dt>프로젝트 유형</dt><dd>${formatProjectType(projectType)}</dd></div>
            <div><dt>생성일</dt><dd>${createdAt}</dd></div>
            <div><dt>품질검토</dt><dd>${project.review_iterations || 1}회</dd></div>
            <div><dt>산출물</dt><dd>${deliverablesCount}개</dd></div>
        </dl>
    `;

    // Agent info section
    if (project.agents && project.agents.length > 0) {
        summary += '<div class="agents-section"><h3>🤖 구성된 Agent</h3><div class="agent-list">';
        project.agents.forEach(function(agent) {
            const tools = agent.tools && agent.tools.length > 0 ? agent.tools.join(', ') : '-';
            summary += `
                <div class="agent-card">
                    <div class="agent-role">${escapeHtml(agent.role)}</div>
                    <div class="agent-details">
                        <span class="llm-badge">${escapeHtml(agent.llm_model)}</span>
                        <span class="tools-badge">${escapeHtml(tools)}</span>
                    </div>
                </div>
            `;
        });
        summary += '</div></div>';
    }

    // Deliverables section
    if (project.deliverables && project.deliverables.length > 0) {
        summary += '<div class="deliverables-section"><h3>📦 산출물</h3><div class="deliverables-list">';
        project.deliverables.forEach(function(file) {
            const sizeKB = Math.round(file.size / 1024);
            const modDate = new Date(file.modified).toLocaleString('ko-KR', {month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'});
            summary += `
                <div class="deliverable-item">
                    <span class="file-icon">📄</span>
                    <span class="file-name">${escapeHtml(file.name)}</span>
                    <span class="file-size">${sizeKB}KB</span>
                    <span class="file-date">${modDate}</span>
                </div>
            `;
        });
        summary += '</div></div>';
    }

    container.innerHTML = summary;
}'''

# Use regex to replace the function
content = re.sub(old_func_pattern, new_func, content, flags=re.DOTALL)

with open('projects.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] renderProjectSummary() replaced successfully")
