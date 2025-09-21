# -*- coding: utf-8 -*-
"""
Database connection and models for AI Chat Interface
Supabase integration with PostgreSQL
"""

import os
import json
import socket
import urllib.parse
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
                # 네트워크 연결 진단 실행
                network_diagnosis = self._diagnose_network_connection()
                if not network_diagnosis["can_connect"]:
                    print(f"WARNING: 네트워크 연결 문제 감지: {network_diagnosis['details']}")
                    print("시뮬레이션 모드로 실행합니다.")
                    self.supabase = None
                    self.service_client = None
                    return

                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                self.service_client: Client = create_client(
                    self.supabase_url,
                    self.service_role_key or self.supabase_key
                )
                print("SUCCESS: Supabase 연결 성공")
            except Exception as e:
                network_info = self._diagnose_network_connection()
                print(f"ERROR: Supabase 연결 실패: {e}")
                print(f"네트워크 진단: {network_info['details']}")
                self.supabase = None
                self.service_client = None

    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.supabase is not None

    def _diagnose_network_connection(self) -> Dict[str, Any]:
        """네트워크 연결 상태를 진단합니다"""
        if not self.supabase_url:
            return {
                "can_connect": False,
                "details": "Supabase URL이 설정되지 않았습니다"
            }

        try:
            # URL에서 호스트명 추출
            parsed_url = urllib.parse.urlparse(self.supabase_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

            # DNS 조회 시도
            try:
                ip_address = socket.gethostbyname(hostname)
                dns_success = True
                dns_error = None
            except socket.gaierror as e:
                ip_address = None
                dns_success = False
                dns_error = str(e)

            # TCP 연결 시도 (DNS가 성공한 경우에만)
            tcp_success = False
            tcp_error = None
            if dns_success:
                try:
                    with socket.create_connection((hostname, port), timeout=10):
                        tcp_success = True
                except (socket.timeout, socket.error) as e:
                    tcp_error = str(e)

            # 진단 결과 정리
            details = {
                "url": self.supabase_url,
                "hostname": hostname,
                "port": port,
                "dns_resolution": {
                    "success": dns_success,
                    "ip_address": ip_address,
                    "error": dns_error
                },
                "tcp_connection": {
                    "success": tcp_success,
                    "error": tcp_error
                }
            }

            # 연결 가능 여부 판단
            can_connect = dns_success and tcp_success

            # 상세한 진단 메시지 생성
            if not dns_success:
                if "11001" in str(dns_error):
                    diagnosis_msg = f"DNS 조회 실패 - 인터넷 연결을 확인하세요. 호스트: {hostname}"
                else:
                    diagnosis_msg = f"DNS 조회 실패: {dns_error}"
            elif not tcp_success:
                diagnosis_msg = f"TCP 연결 실패 - 방화벽 또는 네트워크 정책을 확인하세요. 포트: {port}, 오류: {tcp_error}"
            else:
                diagnosis_msg = "네트워크 연결 정상"

            details["diagnosis"] = diagnosis_msg

            return {
                "can_connect": can_connect,
                "details": details
            }

        except Exception as e:
            return {
                "can_connect": False,
                "details": f"네트워크 진단 중 오류 발생: {str(e)}"
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test database connection with detailed diagnostics"""
        if not self.is_connected():
            # 네트워크 진단 실행
            network_diagnosis = self._diagnose_network_connection()
            return {
                "connected": False,
                "message": "Supabase 연결이 설정되지 않았습니다",
                "simulation_mode": True,
                "network_diagnosis": network_diagnosis["details"],
                "recommendations": self._get_connection_recommendations(network_diagnosis)
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
            # 연결 실패 시 네트워크 진단 실행
            network_diagnosis = self._diagnose_network_connection()
            return {
                "connected": False,
                "message": f"데이터베이스 연결 테스트 실패: {str(e)}",
                "error": str(e),
                "network_diagnosis": network_diagnosis["details"],
                "recommendations": self._get_connection_recommendations(network_diagnosis)
            }

    def _get_connection_recommendations(self, network_diagnosis: Dict[str, Any]) -> List[str]:
        """네트워크 진단 결과에 따른 권장사항을 반환합니다"""
        recommendations = []

        if not network_diagnosis.get("can_connect", False):
            details = network_diagnosis.get("details", {})

            if isinstance(details, dict):
                dns_info = details.get("dns_resolution", {})
                tcp_info = details.get("tcp_connection", {})

                if not dns_info.get("success", False):
                    dns_error = dns_info.get("error", "")
                    if "11001" in dns_error:
                        recommendations.extend([
                            "인터넷 연결 상태를 확인하세요",
                            "DNS 서버 설정을 확인하세요 (8.8.8.8, 1.1.1.1 등)",
                            "방화벽에서 DNS 쿼리가 차단되지 않았는지 확인하세요",
                            "프록시 설정이 있다면 우회 설정을 확인하세요"
                        ])
                    else:
                        recommendations.append(f"DNS 오류: {dns_error}")

                elif not tcp_info.get("success", False):
                    tcp_error = tcp_info.get("error", "")
                    port = details.get("port", 443)
                    recommendations.extend([
                        f"포트 {port}에 대한 방화벽 설정을 확인하세요",
                        "회사 네트워크의 경우 IT 관리자에게 문의하세요",
                        "프록시 설정이 HTTPS 트래픽을 허용하는지 확인하세요",
                        f"TCP 연결 오류: {tcp_error}"
                    ])
            else:
                recommendations.append("네트워크 연결 문제가 감지되었습니다")

        if not recommendations:
            recommendations.append("네트워크 연결은 정상이나 Supabase 서비스 문제일 수 있습니다")

        return recommendations

    # ==================== USER MANAGEMENT ====================

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            # Hash password if provided
            password_hash = None
            if user_data.get('password'):
                password_hash = bcrypt.hashpw(
                    user_data['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

            insert_data = {
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "display_name": user_data.get("display_name"),
                "password_hash": password_hash,
                "role": user_data.get("role", "user"),
                "is_active": user_data.get("is_active", True),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            result = self.supabase.table('users').insert(insert_data).execute()

            if result.data:
                return {"success": True, "user": result.data[0]}
            else:
                return {"success": False, "error": "Failed to create user"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_users(self, role_filter: str = None) -> Dict[str, Any]:
        """Get all users with optional role filter"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            query = self.supabase.table('users').select('*')

            if role_filter:
                query = query.eq('role', role_filter)

            result = query.order('created_at', desc=True).execute()

            # Remove password hashes from response
            users = []
            for user in result.data or []:
                user_copy = user.copy()
                user_copy.pop('password_hash', None)
                users.append(user_copy)

            return {"success": True, "users": users}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by user_id"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()

            if result.data:
                user = result.data[0].copy()
                user.pop('password_hash', None)  # Remove password hash
                return {"success": True, "user": user}
            else:
                return {"success": False, "error": "User not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_user(self, user_id: str, user_data: Dict[str, Any], admin_user_id: str = None) -> Dict[str, Any]:
        """Update user (admin can update any user, users can update themselves)"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            # Check if admin or self-update
            if admin_user_id:
                admin_result = self.supabase.table('users').select('role').eq('user_id', admin_user_id).execute()
                is_admin = admin_result.data and admin_result.data[0].get('role') == 'admin'

                if not is_admin and admin_user_id != user_id:
                    return {"success": False, "error": "Permission denied"}

            # Prepare update data
            update_data = {"updated_at": datetime.now().isoformat()}

            if 'email' in user_data:
                update_data['email'] = user_data['email']
            if 'display_name' in user_data:
                update_data['display_name'] = user_data['display_name']
            if 'password' in user_data and user_data['password']:
                update_data['password_hash'] = bcrypt.hashpw(
                    user_data['password'].encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

            # Only admin can change role and is_active
            if admin_user_id:
                admin_result = self.supabase.table('users').select('role').eq('user_id', admin_user_id).execute()
                if admin_result.data and admin_result.data[0].get('role') == 'admin':
                    if 'role' in user_data:
                        update_data['role'] = user_data['role']
                    if 'is_active' in user_data:
                        update_data['is_active'] = user_data['is_active']

            result = self.supabase.table('users').update(update_data).eq('user_id', user_id).execute()

            if result.data:
                user = result.data[0].copy()
                user.pop('password_hash', None)
                return {"success": True, "user": user}
            else:
                return {"success": False, "error": "User not found"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_user(self, user_id: str, admin_user_id: str) -> Dict[str, Any]:
        """Delete user (admin only)"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            # Check if admin
            admin_result = self.supabase.table('users').select('role').eq('user_id', admin_user_id).execute()
            if not admin_result.data or admin_result.data[0].get('role') != 'admin':
                return {"success": False, "error": "Admin access required"}

            # Don't allow deleting yourself
            if admin_user_id == user_id:
                return {"success": False, "error": "Cannot delete your own account"}

            result = self.supabase.table('users').delete().eq('user_id', user_id).execute()

            return {"success": True, "message": "User deleted successfully"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_user(self, user_id: str, password: str) -> Dict[str, Any]:
        """Verify user credentials"""
        if not self.is_connected():
            return {"success": False, "error": "Database not connected"}

        try:
            result = self.supabase.table('users').select('*').eq('user_id', user_id).eq('is_active', True).execute()

            if not result.data:
                return {"success": False, "error": "User not found or inactive"}

            user = result.data[0]

            # Check password if hash exists
            if user.get('password_hash'):
                if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                    return {"success": False, "error": "Invalid password"}

            # Update last login
            self.supabase.table('users').update({
                'last_login_at': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()

            user_copy = user.copy()
            user_copy.pop('password_hash', None)
            return {"success": True, "user": user_copy}

        except Exception as e:
            return {"success": False, "error": str(e)}

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
                "created_by_user_id": project_data.get("created_by_user_id"),
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

    def get_projects(self, user_id: str = None, limit: int = 20) -> Dict[str, Any]:
        """Get list of projects (admin sees all, users see only their own)"""
        if not self.is_connected():
            return self._simulate_get_projects()

        try:
            query = self.supabase.table('projects').select(
                'id, name, description, created_by_user_id, selected_ai, project_type, status, '
                'current_stage, progress_percentage, created_at, updated_at'
            )

            # Check if user is admin
            if user_id:
                user_result = self.supabase.table('users').select('role').eq('user_id', user_id).execute()
                is_admin = user_result.data and user_result.data[0].get('role') == 'admin'

                # If not admin, only show user's own projects
                if not is_admin:
                    query = query.eq('created_by_user_id', user_id)

            result = query.order('created_at', desc=True).limit(limit).execute()

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