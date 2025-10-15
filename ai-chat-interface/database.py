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

# Load environment variables from the correct .env file
import pathlib
_current_dir = pathlib.Path(__file__).parent
load_dotenv(dotenv_path=_current_dir / '.env', override=True)

class Database:
    """Database connection and operations handler"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        # JWT Secret Key - MUST be set in environment variables for security
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not self.jwt_secret:
            raise ValueError(
                "JWT_SECRET_KEY must be set in environment variables. "
                "Generate a secure random key and add it to your .env file."
            )

        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", 24))

        if not self.supabase_url or not self.supabase_key:
            print("ERROR: Supabase 환경 변수가 설정되지 않았습니다. 데이터베이스 연결이 불가능합니다.")
            self.supabase = None
            self.service_client = None
        else:
            try:
                # 네트워크 연결 진단 실행
                network_diagnosis = self._diagnose_network_connection()
                if not network_diagnosis["can_connect"]:
                    print(f"ERROR: 네트워크 연결 문제 감지: {network_diagnosis['details']}")
                    print("데이터베이스 연결이 불가능합니다.")
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

    def reconnect(self) -> Dict[str, Any]:
        """Attempt to reconnect to the database"""
        try:
            if not self.supabase_url or not self.supabase_key:
                return {
                    "success": False,
                    "error": "MISSING_CREDENTIALS",
                    "message": "Supabase 환경 변수가 설정되지 않았습니다."
                }

            # 네트워크 연결 다시 테스트
            network_diagnosis = self._diagnose_network_connection()
            if not network_diagnosis["can_connect"]:
                return {
                    "success": False,
                    "error": "NETWORK_UNREACHABLE",
                    "message": f"네트워크 연결 실패: {network_diagnosis['details'].get('diagnosis', '알 수 없는 오류')}",
                    "recommendations": self._get_connection_recommendations(network_diagnosis)
                }

            # Supabase 연결 재시도
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            self.service_client = create_client(
                self.supabase_url,
                self.service_role_key or self.supabase_key
            )

            # 연결 테스트
            test_result = self.supabase.table('projects').select('count').execute()

            return {
                "success": True,
                "message": "데이터베이스 연결이 성공적으로 복구되었습니다.",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.supabase = None
            self.service_client = None
            return {
                "success": False,
                "error": "CONNECTION_FAILED",
                "message": f"데이터베이스 연결 재시도 실패: {str(e)}"
            }

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
                "message": "데이터베이스 연결에 실패했습니다",
                "error": "DATABASE_CONNECTION_FAILED",
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            # Prepare project data
            review_iterations = project_data.get("review_iterations", 1)
            try:
                review_iterations = int(review_iterations)
            except (TypeError, ValueError):
                review_iterations = 0 # 기본값을 0으로 변경
            review_iterations = max(0, min(5, review_iterations))

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
                # "review_iterations": review_iterations, # 존재하지 않는 컬럼 제거
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            result = self.supabase.table('projects').insert(insert_data).execute()

            if result.data:
                project = result.data[0]
                # Create default project stages
                self._create_project_stages(project['project_id'])
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            query = self.supabase.table('projects').select(
                # review_iterations 컬럼을 제거하고, 존재하는 컬럼만 명시적으로 선택
                'project_id, name, description, created_by_user_id, selected_ai, project_type, status, current_stage, progress_percentage, created_at, updated_at'
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            result = self.supabase.table('projects').select('*').eq('project_id', project_id).execute()

            if result.data:
                project = result.data[0]
                # Get project stages
                stages = self._get_project_stages(project_id)
                # Get role-LLM mappings
                role_mappings = self._get_project_role_mappings(project_id)
                # Get project tools
                tools_result = self.get_project_tools(project_id)
                tools = tools_result.get('tools', []) if tools_result.get('success', False) else []

                return {
                    "success": True,
                    "project": {
                        **project,
                        "stages": stages,
                        "role_mappings": role_mappings,
                        "tools": tools
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            if 'review_iterations' in update_data:
                try:
                    review_iterations = int(update_data['review_iterations'])
                except (TypeError, ValueError):
                    review_iterations = 1
                review_iterations = max(0, min(5, review_iterations))
                # update_data['review_iterations'] = review_iterations # 존재하지 않는 컬럼 제거

            update_data['updated_at'] = datetime.now().isoformat()

            result = self.supabase.table('projects').update(update_data).eq('project_id', project_id).execute()

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

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """Delete project and all related data based on the current schema."""
        if not self.is_connected():
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            # The database schema uses ON DELETE CASCADE for related tables like
            # project_tools, project_stages, project_role_llm_mapping, etc.
            # Therefore, we only need to delete from the main 'projects' table.
            
            result = self.supabase.table('projects').delete().eq('project_id', project_id).execute()

            if result.data:
                return {
                    "success": True,
                    "message": f"프로젝트 {project_id}가 성공적으로 삭제되었습니다"
                }
            else:
                # This can happen if the project_id doesn't exist, which is not necessarily an error in a DELETE operation.
                # For simplicity, we'll count it as a success if there's no data, as the end state (project is gone) is achieved.
                return {
                    "success": True,
                    "message": f"프로젝트 {project_id}가 이미 삭제되었거나 존재하지 않습니다."
                }

        except Exception as e:
            # Check for specific PostgREST errors if possible
            error_str = str(e)
            return {
                "success": False,
                "error": f"프로젝트 삭제 중 오류 발생: {error_str}"
            }

    # ==================== ROLE-LLM MAPPING ====================

    def _normalize_llm_model_name(self, model_name: str) -> str:
        """
        Normalize LLM model names for database compatibility
        임시 해결책: gemini-2.5-flash -> gemini-flash 매핑
        """
        model_mapping = {
            'gemini-2.5-flash': 'gemini-flash',
            'gemini-2.5-pro': 'gemini-pro',
            'gemini-2.0-flash': 'gemini-flash'
        }

        normalized = model_mapping.get(model_name, model_name)
        if normalized != model_name:
            print(f"INFO: 모델명 변환 - {model_name} -> {normalized}")

        return normalized

    def set_project_role_llm_mapping(self, project_id: str, mappings: List[Dict[str, str]]) -> Dict[str, Any]:
        """Set role-LLM mappings for a project"""
        if not self.is_connected():
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            # Delete existing mappings
            self.supabase.table('project_role_llm_mapping').delete().eq('projects_project_id', project_id).execute()

            # Insert new mappings
            insert_data = []
            for mapping in mappings:
                # 모델명 정규화 적용
                normalized_model = self._normalize_llm_model_name(mapping["llm_model"])

                insert_data.append({
                    "projects_project_id": project_id,
                    "role_name": mapping["role_name"],
                    "llm_model": normalized_model,
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            result = self.supabase.table('project_role_llm_mapping').select('*').eq('projects_project_id', project_id).eq('is_active', True).execute()

            return {
                "success": True,
                "mappings": result.data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"역할-LLM 매핑 조회 실패: {str(e)}"
            }

    # ==================== PROJECT TOOLS ====================

    def set_project_tools(self, project_id: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Set tool configurations for a project"""
        if not self.is_connected():
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            # Remove existing tool configurations
            self.supabase.table('project_tools').delete().eq('projects_project_id', project_id).execute()

            insert_data = []
            for tool in tools or []:
                tool_key = tool.get('tool_key')
                if not tool_key:
                    continue

                insert_data.append({
                    "projects_project_id": project_id,
                    "tool_key": tool_key,
                    "tool_config": tool.get('tool_config', {}),
                    "is_active": bool(tool.get('is_active', True)),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })

            if insert_data:
                result = self.supabase.table('project_tools').insert(insert_data).execute()
                return {
                    "success": True,
                    "tools": result.data,
                    "message": "프로젝트 도구 구성이 저장되었습니다"
                }

            return {
                "success": True,
                "tools": [],
                "message": "프로젝트 도구 구성이 비워졌습니다"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 도구 구성 저장 실패: {str(e)}"
            }

    def get_project_tools(self, project_id: str) -> Dict[str, Any]:
        """Get tool configurations for a project"""
        if not self.is_connected():
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            result = self.supabase.table('project_tools').select('*').eq('projects_project_id', project_id).execute()

            return {
                "success": True,
                "tools": result.data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"프로젝트 도구 조회 실패: {str(e)}"
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
                "projects_project_id": project_id,
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
            result = self.supabase.table('project_stages').select('*').eq('projects_project_id', project_id).order('stage_order').execute()
            return result.data
        except:
            return []

    def _get_project_role_mappings(self, project_id: str) -> List[Dict[str, Any]]:
        """Get project role mappings"""
        try:
            result = self.supabase.table('project_role_llm_mapping').select('*').eq('projects_project_id', project_id).eq('is_active', True).execute()
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


    # ==================== METAGPT SPECIFIC FUNCTIONS ====================

    def create_metagpt_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new MetaGPT project with workflow stages"""
        if not self.is_connected():
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            # 1. Create base project
            project_result = self.create_project(project_data)
            if not project_result.get("success"):
                return project_result

            project_id = project_result["project"]["project_id"]

            # 2. Create workflow stages
            stages_data = [
                {"stage_number": 1, "stage_name": "요구사항 분석", "stage_description": "PRD 작성 및 요구사항 정의", "responsible_role": "Product Manager", "role_icon": "📋", "status": "pending"},
                {"stage_number": 2, "stage_name": "시스템 설계", "stage_description": "아키텍처 설계 및 API 명세", "responsible_role": "Architect", "role_icon": "🏗️", "status": "blocked"},
                {"stage_number": 3, "stage_name": "프로젝트 계획", "stage_description": "작업 분석 및 일정 수립", "responsible_role": "Project Manager", "role_icon": "📊", "status": "blocked"},
                {"stage_number": 4, "stage_name": "코드 개발", "stage_description": "실제 코드 구현", "responsible_role": "Engineer", "role_icon": "💻", "status": "blocked"},
                {"stage_number": 5, "stage_name": "품질 보증", "stage_description": "테스트 및 품질 검증", "responsible_role": "QA Engineer", "role_icon": "🧪", "status": "blocked"}
            ]

            for stage_data in stages_data:
                stage_data["projects_project_id"] = project_id
                stage_data["created_at"] = datetime.now().isoformat()
                stage_data["updated_at"] = datetime.now().isoformat()

            stages_result = self.supabase.table('metagpt_workflow_stages').insert(stages_data).execute()

            # 3. Create default LLM mapping
            llm_mapping = {
                "projects_project_id": project_id,
                "product_manager_llm": "gemini-2.5-flash",
                "architect_llm": "gemini-2.5-flash",
                "project_manager_llm": "gemini-2.5-flash",
                "engineer_llm": "gemini-2.5-flash",
                "qa_engineer_llm": "gemini-2.5-flash",
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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            result = self.supabase.table('metagpt_workflow_stages').select('*').eq('projects_project_id', project_id).order('stage_number').execute()

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            update_data = mapping_data.copy()
            update_data["updated_at"] = datetime.now().isoformat()

            result = self.supabase.table('metagpt_role_llm_mapping').update(update_data).eq('projects_project_id', project_id).execute()

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
            return {"success": False, "error": "DATABASE_CONNECTION_FAILED", "message": "데이터베이스 연결에 실패했습니다."}

        try:
            result = self.supabase.table('metagpt_role_llm_mapping').select('*').eq('projects_project_id', project_id).execute()

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



# Global database instance
def get_database():
    """Get database instance with current environment variables"""
    return Database()

db = get_database()


# PostgreSQL 직접 연결 함수 (psycopg2 사용)
def get_supabase_client():
    """
    Supabase Client 반환 (REST API 기반)
    psycopg2 대신 Supabase Python Client 사용
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL 또는 SUPABASE_ANON_KEY 환경변수가 설정되지 않았습니다.")

    try:
        client = create_client(supabase_url, supabase_key)
        return client
    except Exception as e:
        print(f"Supabase Client 생성 실패: {e}")
        raise


def get_db_connection():
    """
    PostgreSQL 직접 연결 반환 (Supabase PostgreSQL)
    psycopg2를 사용한 저수준 연결

    ⚠️ DEPRECATED: Supabase 연결 문제로 인해 get_supabase_client() 사용 권장
    """
    import psycopg2
    import psycopg2.extras

    # Supabase PostgreSQL 연결 정보
    # URL 파싱: postgresql://[user]:[password]@[host]:[port]/[database]
    supabase_url = os.getenv("SUPABASE_URL")

    if not supabase_url:
        raise ValueError("SUPABASE_URL 환경변수가 설정되지 않았습니다.")

    # Supabase PostgreSQL 직접 연결 정보
    # 형식: postgresql://postgres.[project_ref]:[password]@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
    db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not db_password:
        raise ValueError(
            "SUPABASE_DB_PASSWORD must be set in environment variables. "
            "Get this password from your Supabase project settings."
        )

    # project_ref 추출 (URL에서)
    project_ref = supabase_url.split("//")[1].split(".")[0] if "//" in supabase_url else None

    if not project_ref:
        raise ValueError("Invalid SUPABASE_URL format. Cannot extract project reference.")

    # 연결 설정
    conn_params = {
        "host": f"aws-0-ap-northeast-2.pooler.supabase.com",
        "port": 6543,
        "database": "postgres",
        "user": f"postgres.{project_ref}",
        "password": db_password,
        "sslmode": "require"
    }

    try:
        conn = psycopg2.connect(**conn_params)
        # RealDictCursor 사용 - dict 형태로 결과 반환
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    except psycopg2.OperationalError as e:
        print(f"PostgreSQL 연결 실패: {e}")
        print(f"연결 정보: host={conn_params['host']}, port={conn_params['port']}, user={conn_params['user']}")
        raise
