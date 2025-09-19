# -*- coding: utf-8 -*-
"""
Hybrid Database Handler
Supabase 우선, 연결 실패 시 로컬 SQLite 백업 사용
"""

import os
from typing import Dict, Any
from database import Database
from local_database import LocalDatabase

class HybridDatabase:
    """Hybrid 데이터베이스 처리 클래스 (Supabase + SQLite 백업)"""

    def __init__(self):
        self.supabase_db = Database()
        self.local_db = LocalDatabase()
        self.using_local = False

    def _get_active_db(self):
        """현재 사용할 데이터베이스 반환"""
        if self.supabase_db.is_connected() and not self.using_local:
            try:
                # Supabase 연결 테스트
                test_result = self.supabase_db.test_connection()
                if test_result.get("connected", False):
                    return self.supabase_db
            except Exception as e:
                print(f"Supabase 연결 실패, 로컬 데이터베이스로 전환: {e}")
                self.using_local = True

        # 로컬 데이터베이스 사용
        return self.local_db

    def get_database_status(self) -> Dict[str, Any]:
        """데이터베이스 상태 정보 반환"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return {
                "primary": "local_sqlite",
                "message": "로컬 SQLite 데이터베이스 사용 중",
                "supabase_available": False,
                "local_available": True
            }
        else:
            return {
                "primary": "supabase",
                "message": "Supabase 데이터베이스 사용 중",
                "supabase_available": True,
                "local_available": True
            }

    def test_connection(self) -> Dict[str, Any]:
        """데이터베이스 연결 테스트"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            result = active_db.test_connection()
            result["database_type"] = "local_sqlite"
            result["fallback_mode"] = True
        else:
            result = active_db.test_connection()
            result["database_type"] = "supabase"
            result["fallback_mode"] = False

        return result

    # ==================== PROJECT MANAGEMENT ====================

    def get_projects(self) -> Dict[str, Any]:
        """프로젝트 목록 조회"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.get_projects()
        else:
            try:
                return active_db.get_projects()
            except Exception as e:
                print(f"Supabase 프로젝트 조회 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.get_projects()

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 프로젝트 생성"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.create_project(project_data)
        else:
            try:
                return active_db.create_project(project_data)
            except Exception as e:
                print(f"Supabase 프로젝트 생성 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.create_project(project_data)

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """특정 프로젝트 조회"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.get_project(project_id)
        else:
            try:
                return active_db.get_project(project_id)
            except Exception as e:
                print(f"Supabase 프로젝트 조회 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.get_project(project_id)

    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 업데이트"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.update_project(project_id, update_data)
        else:
            try:
                return active_db.update_project(project_id, update_data)
            except Exception as e:
                print(f"Supabase 프로젝트 업데이트 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.update_project(project_id, update_data)

    # ==================== ROLE-LLM MAPPING ====================

    def get_role_llm_mapping(self, project_id: str) -> Dict[str, Any]:
        """프로젝트의 Role-LLM 매핑 조회"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.get_role_llm_mapping(project_id)
        else:
            try:
                return active_db.get_role_llm_mapping(project_id)
            except Exception as e:
                print(f"Supabase Role-LLM 매핑 조회 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.get_role_llm_mapping(project_id)

    def set_role_llm_mapping(self, project_id: str, mappings: Dict[str, str]) -> Dict[str, Any]:
        """프로젝트의 Role-LLM 매핑 설정"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.set_role_llm_mapping(project_id, mappings)
        else:
            try:
                return active_db.set_role_llm_mapping(project_id, mappings)
            except Exception as e:
                print(f"Supabase Role-LLM 매핑 설정 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.set_role_llm_mapping(project_id, mappings)

    # ==================== METAGPT WORKFLOW ====================

    def get_metagpt_workflow_stages(self, project_id: str) -> Dict[str, Any]:
        """MetaGPT 워크플로우 단계 조회"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.get_metagpt_workflow_stages(project_id)
        else:
            try:
                return active_db.get_metagpt_workflow_stages(project_id)
            except Exception as e:
                print(f"Supabase 워크플로우 조회 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.get_metagpt_workflow_stages(project_id)

    def update_workflow_stage(self, project_id: str, stage_number: int, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 단계 업데이트"""
        active_db = self._get_active_db()

        if isinstance(active_db, LocalDatabase):
            return active_db.update_workflow_stage(project_id, stage_number, stage_data)
        else:
            try:
                return active_db.update_workflow_stage(project_id, stage_number, stage_data)
            except Exception as e:
                print(f"Supabase 워크플로우 업데이트 실패, 로컬 DB로 전환: {e}")
                self.using_local = True
                return self.local_db.update_workflow_stage(project_id, stage_number, stage_data)


# 전역 hybrid 데이터베이스 인스턴스
hybrid_db = HybridDatabase()