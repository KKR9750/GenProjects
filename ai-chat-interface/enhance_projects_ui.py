#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
projects.js UI 개선 스크립트
- v2 API로 완전한 데이터 로드
- Agent 정보 표시
- 산출물 표시
"""

import re

print("[INFO] Enhancing projects.js...")

with open('projects.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. selectProject 함수에 추가 API 호출 추가
old_select = '''function selectProject(projectId, options) {
    options = options || {};
    selectedProjectId = projectId;
    renderProjectList();
    renderProjectSummary();
    renderExecutionSettings();
    renderExecutionOutput();

    if (!options.silent) {
        fetchExecutionDetails(projectId);
    }
}'''

new_select = '''function selectProject(projectId, options) {
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

    } catch (error) {
        console.error('Failed to load full project data:', error);
    }
}'''

content = content.replace(old_select, new_select)

print("[OK] Step 1: Added loadFullProjectData function")

# 파일 저장
with open('projects.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("[SUCCESS] projects.js enhanced successfully!")
