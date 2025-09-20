# -*- coding: utf-8 -*-
"""
Local SQLite Database Handler
Supabase 연결 실패 시 사용하는 로컬 SQLite 백업 데이터베이스
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

class LocalDatabase:
    """로컬 SQLite 데이터베이스 처리 클래스"""

    def __init__(self, db_path: str = "local_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """데이터베이스 초기화"""
        if not os.path.exists(self.db_path):
            # 데이터베이스가 없으면 초기화
            import subprocess
            subprocess.run(["python", "init_local_db.py"], cwd=os.path.dirname(__file__))

    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn

    def test_connection(self) -> Dict[str, Any]:
        """데이터베이스 연결 테스트"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM projects")
            result = cursor.fetchone()
            conn.close()

            return {
                "connected": True,
                "message": f"로컬 SQLite 데이터베이스 연결 성공 (프로젝트 {result['count']}개)",
                "database_type": "SQLite",
                "path": self.db_path
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "message": f"로컬 데이터베이스 연결 실패: {str(e)}"
            }

    def get_projects(self) -> Dict[str, Any]:
        """프로젝트 목록 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, framework, status,
                       created_at, updated_at, metadata
                FROM projects
                ORDER BY updated_at DESC
            """)

            rows = cursor.fetchall()
            projects = []

            for row in rows:
                project = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "framework": row["framework"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                projects.append(project)

            conn.close()
            return {"success": True, "projects": projects}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 프로젝트 생성"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            project_id = project_data.get("id", f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            cursor.execute("""
                INSERT INTO projects (id, name, description, framework, status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                project_data.get("name", ""),
                project_data.get("description", ""),
                project_data.get("framework", ""),
                project_data.get("status", "active"),
                json.dumps(project_data.get("metadata", {}))
            ))

            conn.commit()
            conn.close()

            return {"success": True, "project_id": project_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """특정 프로젝트 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, name, description, framework, status,
                       created_at, updated_at, metadata
                FROM projects
                WHERE id = ?
            """, (project_id,))

            row = cursor.fetchone()

            if row:
                project = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "framework": row["framework"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                conn.close()
                return {"success": True, "project": project}
            else:
                conn.close()
                return {"success": False, "error": "프로젝트를 찾을 수 없습니다"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 업데이트"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 업데이트할 필드들
            set_clauses = []
            values = []

            for field in ["name", "description", "status"]:
                if field in update_data:
                    set_clauses.append(f"{field} = ?")
                    values.append(update_data[field])

            if "metadata" in update_data:
                set_clauses.append("metadata = ?")
                values.append(json.dumps(update_data["metadata"]))

            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(project_id)

            query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)

            conn.commit()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_role_llm_mapping(self, project_id: str) -> Dict[str, Any]:
        """프로젝트의 Role-LLM 매핑 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT role_name, llm_model
                FROM role_llm_mappings
                WHERE project_id = ?
            """, (project_id,))

            rows = cursor.fetchall()
            mappings = {row["role_name"]: row["llm_model"] for row in rows}

            conn.close()
            return {"success": True, "mappings": mappings}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_role_llm_mapping(self, project_id: str, mappings: Dict[str, str]) -> Dict[str, Any]:
        """프로젝트의 Role-LLM 매핑 설정"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 기존 매핑 삭제
            cursor.execute("DELETE FROM role_llm_mappings WHERE project_id = ?", (project_id,))

            # 새 매핑 삽입
            for role_name, llm_model in mappings.items():
                cursor.execute("""
                    INSERT INTO role_llm_mappings (project_id, role_name, llm_model)
                    VALUES (?, ?, ?)
                """, (project_id, role_name, llm_model))

            conn.commit()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_metagpt_workflow_stages(self, project_id: str) -> Dict[str, Any]:
        """MetaGPT 워크플로우 단계 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT stage_number, stage_name, status, result,
                       user_feedback, created_at, updated_at
                FROM metagpt_workflow_stages
                WHERE project_id = ?
                ORDER BY stage_number
            """, (project_id,))

            rows = cursor.fetchall()
            stages = []

            for row in rows:
                stage = {
                    "stage_number": row["stage_number"],
                    "stage_name": row["stage_name"],
                    "status": row["status"],
                    "result": json.loads(row["result"]) if row["result"] else None,
                    "user_feedback": row["user_feedback"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                stages.append(stage)

            conn.close()
            return {"success": True, "stages": stages}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_workflow_stage(self, project_id: str, stage_number: int, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 단계 업데이트"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 기존 단계가 있는지 확인
            cursor.execute("""
                SELECT id FROM metagpt_workflow_stages
                WHERE project_id = ? AND stage_number = ?
            """, (project_id, stage_number))

            existing = cursor.fetchone()

            if existing:
                # 업데이트
                cursor.execute("""
                    UPDATE metagpt_workflow_stages
                    SET status = ?, result = ?, user_feedback = ?, updated_at = ?
                    WHERE project_id = ? AND stage_number = ?
                """, (
                    stage_data.get("status", "pending"),
                    json.dumps(stage_data.get("result", {})),
                    stage_data.get("user_feedback", ""),
                    datetime.now().isoformat(),
                    project_id,
                    stage_number
                ))
            else:
                # 삽입
                cursor.execute("""
                    INSERT INTO metagpt_workflow_stages
                    (project_id, stage_number, stage_name, status, result, user_feedback)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    stage_number,
                    stage_data.get("stage_name", f"단계 {stage_number}"),
                    stage_data.get("status", "pending"),
                    json.dumps(stage_data.get("result", {})),
                    stage_data.get("user_feedback", "")
                ))

            conn.commit()
            conn.close()

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}