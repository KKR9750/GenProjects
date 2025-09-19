# -*- coding: utf-8 -*-
"""
Database connection and models for AI Chat Interface
Supabase integration with PostgreSQL
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import jwt
import bcrypt

# Load environment variables
load_dotenv()

class Database:
    """Database connection and operations handler"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "default-secret-key")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", 24))

        if not self.supabase_url or not self.supabase_key:
            print("WARNING: Supabase 환경 변수가 설정되지 않았습니다. 시뮬레이션 모드로 실행합니다.")
            self.supabase = None
            self.service_client = None
        else:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                self.service_client: Client = create_client(
                    self.supabase_url,
                    self.service_role_key or self.supabase_key
                )
                print("SUCCESS: Supabase 연결 성공")
            except Exception as e:
                print(f"ERROR: Supabase 연결 실패: {e}")
                self.supabase = None
                self.service_client = None

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.supabase is not None

    def test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        if not self.is_connected():
            return {
                "connected": False,
                "message": "Supabase 연결이 설정되지 않았습니다",
                "simulation_mode": True
            }

        try:
            # Simple query to test connection
            result = self.supabase.table('projects').select('count').execute()
            return {
                "connected": True,
                "message": "데이터베이스 연결 성공",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "connected": False,
                "message": f"데이터베이스 연결 테스트 실패: {str(e)}",
                "error": str(e)
            }

    # ==================== PROJECT MANAGEMENT ====================

    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        if not self.is_connected():
            return self._simulate_create_project(project_data)

        try:
            # Prepare project data
            insert_data = {
                "name": project_data.get("name"),
                "description": project_data.get("description", ""),
                "selected_ai": project_data.get("selected_ai", "crew-ai"),
                "project_type": project_data.get("project_type", "web_app"),
                "target_audience": project_data.get("target_audience", ""),
                "technical_requirements": project_data.get("technical_requirements", {}),
                "status": "planning",
                "current_stage": "requirement",
                "progress_percentage": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            result = self.supabase.table('projects').insert(insert_data).execute()

            if result.data:
                project = result.data[0]
                # Create default project stages
                self._create_project_stages(project['id'])
                return {
                    "success": True,
                    "project": project,
                    "message": "프로젝트가 성공적으로 생성되었습니다"
                }
            else:
                return {
                    "success": False,
                    "error": "프로젝트 생성 실패"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 생성 중 오류 발생: {str(e)}"
            }

    def get_projects(self, limit: int = 20) -> Dict[str, Any]:
        """Get list of projects"""
        if not self.is_connected():
            return self._simulate_get_projects()

        try:
            result = self.supabase.table('projects').select(
                'id, name, description, selected_ai, project_type, status, '
                'current_stage, progress_percentage, created_at, updated_at'
            ).order('created_at', desc=True).limit(limit).execute()

            return {
                "success": True,
                "projects": result.data,
                "count": len(result.data)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 목록 조회 실패: {str(e)}"
            }

    def get_project_by_id(self, project_id: str) -> Dict[str, Any]:
        """Get project by ID"""
        if not self.is_connected():
            return self._simulate_get_project(project_id)

        try:
            result = self.supabase.table('projects').select('*').eq('id', project_id).execute()

            if result.data:
                project = result.data[0]
                # Get project stages
                stages = self._get_project_stages(project_id)
                # Get role-LLM mappings
                role_mappings = self._get_project_role_mappings(project_id)

                return {
                    "success": True,
                    "project": {
                        **project,
                        "stages": stages,
                        "role_mappings": role_mappings
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "프로젝트를 찾을 수 없습니다"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 조회 실패: {str(e)}"
            }

    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project"""
        if not self.is_connected():
            return self._simulate_update_project(project_id, update_data)

        try:
            update_data['updated_at'] = datetime.now().isoformat()

            result = self.supabase.table('projects').update(update_data).eq('id', project_id).execute()

            if result.data:
                return {
                    "success": True,
                    "project": result.data[0],
                    "message": "프로젝트가 성공적으로 업데이트되었습니다"
                }
            else:
                return {
                    "success": False,
                    "error": "프로젝트 업데이트 실패"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 업데이트 중 오류 발생: {str(e)}"
            }

    # ==================== ROLE-LLM MAPPING ====================

    def set_project_role_llm_mapping(self, project_id: str, mappings: List[Dict[str, str]]) -> Dict[str, Any]:
        """Set role-LLM mappings for a project"""
        if not self.is_connected():
            return self._simulate_set_role_mappings(project_id, mappings)

        try:
            # Delete existing mappings
            self.supabase.table('project_role_llm_mapping').delete().eq('project_id', project_id).execute()

            # Insert new mappings
            insert_data = []
            for mapping in mappings:
                insert_data.append({
                    "project_id": project_id,
                    "role_name": mapping["role_name"],
                    "llm_model": mapping["llm_model"],
                    "llm_config": mapping.get("llm_config", {}),
                    "is_active": True,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })

            if insert_data:
                result = self.supabase.table('project_role_llm_mapping').insert(insert_data).execute()

                return {
                    "success": True,
                    "mappings": result.data,
                    "message": "역할-LLM 매핑이 성공적으로 설정되었습니다"
                }
            else:
                return {
                    "success": True,
                    "mappings": [],
                    "message": "빈 매핑이 설정되었습니다"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"역할-LLM 매핑 설정 실패: {str(e)}"
            }

    def get_project_role_llm_mapping(self, project_id: str) -> Dict[str, Any]:
        """Get role-LLM mappings for a project"""
        if not self.is_connected():
            return self._simulate_get_role_mappings(project_id)

        try:
            result = self.supabase.table('project_role_llm_mapping').select('*').eq('project_id', project_id).eq('is_active', True).execute()

            return {
                "success": True,
                "mappings": result.data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"역할-LLM 매핑 조회 실패: {str(e)}"
            }

    # ==================== PROJECT STAGES ====================

    def _create_project_stages(self, project_id: str):
        """Create default project stages"""
        stages = [
            {"stage_name": "requirement", "stage_order": 1, "responsible_role": "Product Manager"},
            {"stage_name": "design", "stage_order": 2, "responsible_role": "Architect"},
            {"stage_name": "architecture", "stage_order": 3, "responsible_role": "Architect"},
            {"stage_name": "development", "stage_order": 4, "responsible_role": "Engineer"},
            {"stage_name": "testing", "stage_order": 5, "responsible_role": "QA Engineer"}
        ]

        insert_data = []
        for stage in stages:
            insert_data.append({
                "project_id": project_id,
                "stage_name": stage["stage_name"],
                "stage_order": stage["stage_order"],
                "responsible_role": stage["responsible_role"],
                "stage_status": "pending" if stage["stage_order"] > 1 else "in_progress",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })

        self.supabase.table('project_stages').insert(insert_data).execute()

    def _get_project_stages(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project stages"""
        try:
            result = self.supabase.table('project_stages').select('*').eq('project_id', project_id).order('stage_order').execute()
            return result.data
        except:
            return []

    def _get_project_role_mappings(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project role mappings"""
        try:
            result = self.supabase.table('project_role_llm_mapping').select('*').eq('project_id', project_id).eq('is_active', True).execute()
            return result.data
        except:
            return []

    # ==================== JWT AUTHENTICATION ====================

    def generate_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_data.get("id"),
            "email": user_data.get("email"),
            "role": user_data.get("role", "user"),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expire_hours),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return {
                "success": True,
                "payload": payload
            }
        except jwt.ExpiredSignatureError:
            return {
                "success": False,
                "error": "토큰이 만료되었습니다"
            }
        except jwt.InvalidTokenError:
            return {
                "success": False,
                "error": "유효하지 않은 토큰입니다"
            }

    # ==================== SIMULATION METHODS ====================

    def _simulate_create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate project creation"""
        import uuid

        project = {
            "id": str(uuid.uuid4()),
            "name": project_data.get("name"),
            "description": project_data.get("description", ""),
            "selected_ai": project_data.get("selected_ai", "crew-ai"),
            "project_type": project_data.get("project_type", "web_app"),
            "status": "planning",
            "current_stage": "requirement",
            "progress_percentage": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        return {
            "success": True,
            "project": project,
            "message": "프로젝트가 시뮬레이션 모드에서 생성되었습니다",
            "simulation": True
        }

    def _simulate_get_projects(self) -> Dict[str, Any]:
        """Simulate getting projects"""
        projects = [
            {
                "id": "sim-project-1",
                "name": "E-commerce 웹사이트",
                "description": "온라인 쇼핑몰 개발",
                "selected_ai": "meta-gpt",
                "project_type": "web_app",
                "status": "in_progress",
                "current_stage": "development",
                "progress_percentage": 60,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": "sim-project-2",
                "name": "AI 챗봇 시스템",
                "description": "고객 서비스용 AI 챗봇",
                "selected_ai": "crew-ai",
                "project_type": "api",
                "status": "planning",
                "current_stage": "requirement",
                "progress_percentage": 20,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]

        return {
            "success": True,
            "projects": projects,
            "count": len(projects),
            "simulation": True
        }

    def _simulate_get_project(self, project_id: str) -> Dict[str, Any]:
        """Simulate getting single project"""
        project = {
            "id": project_id,
            "name": "시뮬레이션 프로젝트",
            "description": "테스트용 시뮬레이션 프로젝트",
            "selected_ai": "crew-ai",
            "project_type": "web_app",
            "status": "planning",
            "current_stage": "requirement",
            "progress_percentage": 25,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stages": [],
            "role_mappings": []
        }

        return {
            "success": True,
            "project": project,
            "simulation": True
        }

    def _simulate_update_project(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate project update"""
        return {
            "success": True,
            "project": {"id": project_id, **update_data},
            "message": "프로젝트가 시뮬레이션 모드에서 업데이트되었습니다",
            "simulation": True
        }

    def _simulate_set_role_mappings(self, project_id: str, mappings: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simulate role-LLM mapping"""
        return {
            "success": True,
            "mappings": mappings,
            "message": "역할-LLM 매핑이 시뮬레이션 모드에서 설정되었습니다",
            "simulation": True
        }

    def _simulate_get_role_mappings(self, project_id: str) -> Dict[str, Any]:
        """Simulate getting role mappings"""
        mappings = [
            {"role_name": "Researcher", "llm_model": "gpt-4"},
            {"role_name": "Writer", "llm_model": "claude-3"},
            {"role_name": "Planner", "llm_model": "gemini-pro"}
        ]

        return {
            "success": True,
            "mappings": mappings,
            "simulation": True
        }

    # ==================== METAGPT SPECIFIC FUNCTIONS ====================

    def create_metagpt_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new MetaGPT project with workflow stages"""
        if not self.is_connected():
            return self._simulate_create_metagpt_project(project_data)

        try:
            # 1. Create base project
            project_result = self.create_project(project_data)
            if not project_result.get("success"):
                return project_result

            project_id = project_result["project"]["id"]

            # 2. Create workflow stages
            stages_data = [
                {"stage_number": 1, "stage_name": "요구사항 분석", "stage_description": "PRD 작성 및 요구사항 정의", "responsible_role": "Product Manager", "role_icon": "📋", "status": "pending"},
                {"stage_number": 2, "stage_name": "시스템 설계", "stage_description": "아키텍처 설계 및 API 명세", "responsible_role": "Architect", "role_icon": "🏗️", "status": "blocked"},
                {"stage_number": 3, "stage_name": "프로젝트 계획", "stage_description": "작업 분석 및 일정 수립", "responsible_role": "Project Manager", "role_icon": "📊", "status": "blocked"},
                {"stage_number": 4, "stage_name": "코드 개발", "stage_description": "실제 코드 구현", "responsible_role": "Engineer", "role_icon": "💻", "status": "blocked"},
                {"stage_number": 5, "stage_name": "품질 보증", "stage_description": "테스트 및 품질 검증", "responsible_role": "QA Engineer", "role_icon": "🧪", "status": "blocked"}
            ]

            for stage_data in stages_data:
                stage_data["project_id"] = project_id
                stage_data["created_at"] = datetime.now().isoformat()
                stage_data["updated_at"] = datetime.now().isoformat()

            stages_result = self.supabase.table('metagpt_workflow_stages').insert(stages_data).execute()

            # 3. Create default LLM mapping
            llm_mapping = {
                "project_id": project_id,
                "product_manager_llm": "gpt-4",
                "architect_llm": "claude-3-sonnet",
                "project_manager_llm": "gpt-4o",
                "engineer_llm": "deepseek-coder",
                "qa_engineer_llm": "claude-3-haiku",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            mapping_result = self.supabase.table('metagpt_role_llm_mapping').insert(llm_mapping).execute()

            return {
                "success": True,
                "project": project_result["project"],
                "stages": stages_result.data if stages_result.data else [],
                "llm_mapping": mapping_result.data[0] if mapping_result.data else llm_mapping,
                "message": "MetaGPT 프로젝트가 성공적으로 생성되었습니다"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"MetaGPT 프로젝트 생성 실패: {str(e)}"
            }

    def get_metagpt_workflow_stages(self, project_id: str) -> Dict[str, Any]:
        """Get MetaGPT workflow stages for a project"""
        if not self.is_connected():
            return self._simulate_get_metagpt_stages(project_id)

        try:
            result = self.supabase.table('metagpt_workflow_stages').select('*').eq('project_id', project_id).order('stage_number').execute()

            return {
                "success": True,
                "stages": result.data if result.data else [],
                "count": len(result.data) if result.data else 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"워크플로우 단계 조회 실패: {str(e)}"
            }

    def update_metagpt_stage_status(self, stage_id: str, status: str, output_content: str = None) -> Dict[str, Any]:
        """Update MetaGPT stage status and output"""
        if not self.is_connected():
            return self._simulate_update_metagpt_stage(stage_id, status, output_content)

        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }

            if output_content:
                update_data["output_content"] = output_content

            if status == "completed":
                update_data["end_time"] = datetime.now().isoformat()
                update_data["progress_percentage"] = 100
            elif status == "in_progress":
                update_data["start_time"] = datetime.now().isoformat()

            result = self.supabase.table('metagpt_workflow_stages').update(update_data).eq('id', stage_id).execute()

            return {
                "success": True,
                "stage": result.data[0] if result.data else {},
                "message": "워크플로우 단계가 업데이트되었습니다"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"워크플로우 단계 업데이트 실패: {str(e)}"
            }

    def set_metagpt_role_llm_mapping(self, project_id: str, mapping_data: Dict[str, str]) -> Dict[str, Any]:
        """Set MetaGPT role-LLM mapping"""
        if not self.is_connected():
            return self._simulate_set_metagpt_mapping(project_id, mapping_data)

        try:
            update_data = mapping_data.copy()
            update_data["updated_at"] = datetime.now().isoformat()

            result = self.supabase.table('metagpt_role_llm_mapping').update(update_data).eq('project_id', project_id).execute()

            return {
                "success": True,
                "mapping": result.data[0] if result.data else {},
                "message": "MetaGPT LLM 매핑이 저장되었습니다"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"LLM 매핑 저장 실패: {str(e)}"
            }

    def get_metagpt_role_llm_mapping(self, project_id: str) -> Dict[str, Any]:
        """Get MetaGPT role-LLM mapping"""
        if not self.is_connected():
            return self._simulate_get_metagpt_mapping(project_id)

        try:
            result = self.supabase.table('metagpt_role_llm_mapping').select('*').eq('project_id', project_id).execute()

            return {
                "success": True,
                "mapping": result.data[0] if result.data else {},
                "found": len(result.data) > 0 if result.data else False
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"LLM 매핑 조회 실패: {str(e)}"
            }

    # ==================== METAGPT SIMULATION FUNCTIONS ====================

    def _simulate_create_metagpt_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MetaGPT project creation"""
        project_id = f"metagpt-project-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        stages = [
            {"id": f"stage-{i}", "stage_number": i, "stage_name": name, "status": "pending" if i == 1 else "blocked", "responsible_role": role}
            for i, (name, role) in enumerate([
                ("요구사항 분석", "Product Manager"),
                ("시스템 설계", "Architect"),
                ("프로젝트 계획", "Project Manager"),
                ("코드 개발", "Engineer"),
                ("품질 보증", "QA Engineer")
            ], 1)
        ]

        return {
            "success": True,
            "project": {
                "id": project_id,
                "name": project_data.get("name"),
                "description": project_data.get("description"),
                "selected_ai": "meta-gpt",
                "status": "planning",
                "created_at": datetime.now().isoformat()
            },
            "stages": stages,
            "llm_mapping": {
                "product_manager_llm": "gpt-4",
                "architect_llm": "claude-3-sonnet",
                "project_manager_llm": "gpt-4o",
                "engineer_llm": "deepseek-coder",
                "qa_engineer_llm": "claude-3-haiku"
            },
            "message": "MetaGPT 프로젝트가 시뮬레이션 모드에서 생성되었습니다",
            "simulation": True
        }

    def _simulate_get_metagpt_stages(self, project_id: str) -> Dict[str, Any]:
        """Simulate getting MetaGPT stages"""
        stages = [
            {"id": f"stage-{i}", "stage_number": i, "stage_name": name, "status": "in_progress" if i == 1 else "pending", "responsible_role": role, "progress_percentage": 30 if i == 1 else 0}
            for i, (name, role) in enumerate([
                ("요구사항 분석", "Product Manager"),
                ("시스템 설계", "Architect"),
                ("프로젝트 계획", "Project Manager"),
                ("코드 개발", "Engineer"),
                ("품질 보증", "QA Engineer")
            ], 1)
        ]

        return {
            "success": True,
            "stages": stages,
            "count": len(stages),
            "simulation": True
        }

    def _simulate_update_metagpt_stage(self, stage_id: str, status: str, output_content: str = None) -> Dict[str, Any]:
        """Simulate updating MetaGPT stage"""
        return {
            "success": True,
            "stage": {
                "id": stage_id,
                "status": status,
                "output_content": output_content,
                "updated_at": datetime.now().isoformat()
            },
            "message": "워크플로우 단계가 시뮬레이션 모드에서 업데이트되었습니다",
            "simulation": True
        }

    def _simulate_set_metagpt_mapping(self, project_id: str, mapping_data: Dict[str, str]) -> Dict[str, Any]:
        """Simulate setting MetaGPT LLM mapping"""
        return {
            "success": True,
            "mapping": mapping_data,
            "message": "MetaGPT LLM 매핑이 시뮬레이션 모드에서 저장되었습니다",
            "simulation": True
        }

    def _simulate_get_metagpt_mapping(self, project_id: str) -> Dict[str, Any]:
        """Simulate getting MetaGPT LLM mapping"""
        return {
            "success": True,
            "mapping": {
                "product_manager_llm": "gpt-4",
                "architect_llm": "claude-3-sonnet",
                "project_manager_llm": "gpt-4o",
                "engineer_llm": "deepseek-coder",
                "qa_engineer_llm": "claude-3-haiku"
            },
            "found": True,
            "simulation": True
        }


# Global database instance
db = Database()