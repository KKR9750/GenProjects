# -*- coding: utf-8 -*-
"""
Project Service - Centralized Logic for Project Management
프로젝트 생성, 조회, 수정, 삭제 등 중앙 집중식 로직 관리
"""

import os
import sys
from datetime import datetime

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .project_initializer import get_supabase_client, get_next_project_id

def _extract_project_name_from_idea(idea: str) -> str:
    """
    요구사항에서 프로젝트 이름을 추출하는 중앙 함수.
    MetaGPT와 CrewAI에서 공통으로 사용됩니다.
    """
    idea_lower = idea.lower()
    keywords = [
        '웹사이트', '웹앱', '블로그', '계산기', '게임', '시스템', 'api', '서버',
        'website', 'webapp', 'blog', 'calculator', 'game', 'system'
    ]
    for keyword in keywords:
        if keyword in idea_lower:
            # "간단한 계산기 프로그램" -> "calculator-program"
            name_part = idea.split(keyword)[-1].strip().split(' ')[0]
            return f"{keyword.replace(' ', '-')}-{name_part}".rstrip('-')
    # 키워드가 없으면 현재 시간 기반으로 생성
    return f"gen-project-{datetime.now().strftime('%H%M%S')}"

def create_new_project(framework: str, user_request: str) -> dict:
    """
    새로운 프로젝트를 생성하고 DB에 저장하는 중앙 함수.
    :param framework: 'crewai' 또는 'metagpt'
    :param user_request: 사용자의 원본 요청
    :return: 생성된 프로젝트 정보 또는 에러
    """
    supabase = get_supabase_client()
    if not supabase:
        return {"success": False, "error": "Database client not available."}
    
    try:
        project_id = get_next_project_id(framework)
        project_name = _extract_project_name_from_idea(user_request)

        # 프로젝트 작업 경로 설정
        # MetaGPT는 현재 작업 디렉토리에, CrewAI는 Projects/{project_name}에 생성
        if framework == 'metagpt':
            workspace_path = os.getcwd()
        else: # crewai
            # 이 경로는 crewai_platform/server.py의 output_path와 일치해야 함
            projects_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Projects'))
            workspace_path = os.path.join(projects_base_dir, project_name)

        project_data = {
            'project_id': project_id,
            'name': project_name,
            'description': user_request,
            'framework': framework,
            'workspace_path': workspace_path
        }
        supabase.table('projects').insert(project_data).execute()
        return {"success": True, "project": project_data}
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_project_files(project_id: str, workspace_path: str):
    """
    프로젝트 작업 경로의 파일 목록을 스캔하여 DB에 저장합니다.
    :param project_id: 프로젝트 ID
    :param workspace_path: 스캔할 작업 디렉토리 경로
    """
    supabase = get_supabase_client()
    if not supabase or not os.path.isdir(workspace_path):
        return {"success": False, "error": "DB client not available or invalid workspace path."}

    try:
        files_to_insert = []
        for root, _, files in os.walk(workspace_path):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, workspace_path)
                files_to_insert.append({
                    'project_id': project_id,
                    'file_path': relative_path.replace('\\', '/'), # 경로 구분자 통일
                    'file_name': file,
                    'file_size': os.path.getsize(full_path)
                })
        
        if files_to_insert:
            supabase.table('project_files').insert(files_to_insert).execute()
        
        return {"success": True, "count": len(files_to_insert)}
    except Exception as e:
        return {"success": False, "error": str(e)}