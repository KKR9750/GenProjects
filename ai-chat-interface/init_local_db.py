#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로컬 SQLite 데이터베이스 초기화 스크립트
Local SQLite Database Initialization Script
"""

import sqlite3
import os
from datetime import datetime

def init_local_database():
    """로컬 SQLite 데이터베이스 초기화"""
    db_path = "local_database.db"

    # 기존 데이터베이스가 있다면 백업
    if os.path.exists(db_path):
        backup_path = f"local_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.rename(db_path, backup_path)
        print(f"기존 데이터베이스를 {backup_path}로 백업했습니다.")

    # 새 데이터베이스 생성
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Projects 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        framework TEXT NOT NULL CHECK (framework IN ('crewai', 'metagpt')),
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata TEXT  -- JSON 형태로 저장
    )
    ''')

    # Role-LLM Mappings 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS role_llm_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        role_name TEXT NOT NULL,
        llm_model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        UNIQUE(project_id, role_name)
    )
    ''')

    # MetaGPT Workflow Stages 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS metagpt_workflow_stages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        stage_number INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'rejected')),
        result TEXT,  -- JSON 형태로 저장
        user_feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
        UNIQUE(project_id, stage_number)
    )
    ''')

    # 인덱스 생성
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_framework ON projects(framework)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_llm_project ON role_llm_mappings(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_stages_project ON metagpt_workflow_stages(project_id)')

    # 샘플 데이터 삽입
    sample_projects = [
        ('demo_crewai', 'CrewAI 데모 프로젝트', 'CrewAI 기능을 테스트하기 위한 데모 프로젝트', 'crewai'),
        ('demo_metagpt', 'MetaGPT 데모 프로젝트', 'MetaGPT 기능을 테스트하기 위한 데모 프로젝트', 'metagpt')
    ]

    cursor.executemany('''
    INSERT OR IGNORE INTO projects (id, name, description, framework)
    VALUES (?, ?, ?, ?)
    ''', sample_projects)

    # 샘플 Role-LLM 매핑
    sample_mappings = [
        ('demo_crewai', 'researcher', 'gpt-4'),
        ('demo_crewai', 'writer', 'claude-3'),
        ('demo_crewai', 'planner', 'gpt-4'),
        ('demo_metagpt', 'ProductManager', 'gpt-4'),
        ('demo_metagpt', 'Architect', 'claude-3'),
        ('demo_metagpt', 'Engineer', 'deepseek-coder')
    ]

    cursor.executemany('''
    INSERT OR IGNORE INTO role_llm_mappings (project_id, role_name, llm_model)
    VALUES (?, ?, ?)
    ''', sample_mappings)

    conn.commit()
    conn.close()

    print(f"로컬 SQLite 데이터베이스가 {db_path}에 생성되었습니다.")
    print("테이블: projects, role_llm_mappings, metagpt_workflow_stages")
    print("샘플 프로젝트: demo_crewai, demo_metagpt")

if __name__ == "__main__":
    init_local_database()