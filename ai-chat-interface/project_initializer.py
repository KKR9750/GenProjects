# -*- coding: utf-8 -*-
"""
Project Initializer & DB Entry Management
프로젝트 초기화 및 데이터베이스 항목 관리
"""

import os
import uuid
from typing import Optional

from supabase import create_client, Client

def get_supabase_client() -> Optional[Client]:
    """Supabase 클라이언트를 반환합니다."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    if supabase_url and supabase_key:
        return create_client(supabase_url, supabase_key)
    return None

def get_next_project_id(framework: str) -> str:
    """프레임워크에 따라 다음 프로젝트 ID를 생성합니다 (예: CREW0000001, META0000001)."""
    supabase = get_supabase_client()
    if not supabase:
        return f"local-{str(uuid.uuid4())[:8]}"
    
    prefix = 'CREW' if framework.lower() == 'crewai' else 'META'
    response = supabase.table('projects').select('project_id').like('project_id', f'{prefix}%').order('project_id', desc=True).limit(1).execute()

    last_id_num = 0
    if response.data:
        last_id = response.data[0]['project_id']
        try: last_id_num = int(last_id.replace(prefix, ''))
        except (ValueError, TypeError): last_id_num = 0
    new_id_num = last_id_num + 1
    return f"{prefix}{new_id_num:07d}"