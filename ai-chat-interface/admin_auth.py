# -*- coding: utf-8 -*-
"""
Admin Authentication System
관리자 인증 및 권한 관리 시스템
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import List
from flask import request, jsonify, current_app
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 모듈 import (메인 토큰 검증을 위해)
try:
    from database import db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

class AdminAuth:
    def __init__(self):
        # JWT 시크릿 키 (환경변수에서 가져오거나 생성)
        self.secret_key = os.getenv('JWT_SECRET_KEY') or secrets.token_urlsafe(32)

        # 관리자 비밀번호 환경변수 검증
        admin_password = os.getenv('ADMIN_PASSWORD')
        if not admin_password:
            raise ValueError(
                "ADMIN_PASSWORD must be set in environment variables. "
                "Add ADMIN_PASSWORD to your .env file with a strong password."
            )

        # 기본 관리자 계정 설정
        self.admin_users = {
            'admin': {
                'password_hash': self._hash_password(admin_password),
                'role': 'admin',
                'permissions': ['all']
            }
        }

    def _hash_password(self, password):
        """패스워드 해시 생성"""
        return hashlib.sha256(f"{password}{self.secret_key}".encode()).hexdigest()

    def verify_password(self, username, password):
        """패스워드 검증"""
        if username not in self.admin_users:
            return False

        password_hash = self._hash_password(password)
        return password_hash == self.admin_users[username]['password_hash']

    def generate_token(self, username):
        """JWT 토큰 생성"""
        if username not in self.admin_users:
            return None

        payload = {
            'username': username,
            'role': self.admin_users[username]['role'],
            'permissions': self.admin_users[username]['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=24),  # 24시간 유효
            'iat': datetime.utcnow()
        }

        return jwt.encode(payload, self.secret_key, algorithm='HS256')

    def verify_token(self, token):
        """JWT 토큰 검증 (관리자 토큰 또는 메인 대시보드 토큰)"""
        # 1. 먼저 관리자 전용 토큰으로 검증 시도
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # 관리자 토큰인 경우
            if 'role' in payload and payload['role'] == 'admin':
                return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            pass

        # 2. 메인 대시보드 토큰으로 검증 시도 (데이터베이스 사용)
        if DB_AVAILABLE and db:
            try:
                result = db.verify_jwt_token(token)
                if result.get('success'):
                    # 메인 대시보드 토큰이 유효한 경우, 관리자 권한 확인
                    user_data = result.get('user', {})
                    # 사용자 역할 기반 권한 확인
                    user_role = user_data.get('role', 'user')
                    if user_role != 'admin':
                        return None  # 관리자가 아닌 경우 접근 거부

                    return {
                        'username': user_data.get('user_id', 'user'),
                        'role': user_role,
                        'permissions': self._get_role_permissions(user_role),
                        'from_main_dashboard': True
                    }
            except Exception:
                pass

        return None

    def _get_role_permissions(self, role: str) -> List[str]:
        """역할별 권한 목록 반환"""
        role_permissions = {
            'admin': ['all'],
            'moderator': ['read', 'moderate'],
            'user': ['read']
        }
        return role_permissions.get(role, ['read'])

    def has_permission(self, token, required_permission):
        """권한 확인"""
        payload = self.verify_token(token)
        if not payload:
            return False

        permissions = payload.get('permissions', [])
        return 'all' in permissions or required_permission in permissions

# 전역 인스턴스
admin_auth = AdminAuth()

def admin_required(permission='admin'):
    """관리자 권한 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Authorization 헤더에서 토큰 추출
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({'error': '인증 토큰이 필요합니다'}), 401

            try:
                # Bearer 토큰 형식 확인
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'error': '잘못된 토큰 형식입니다'}), 401

            # 토큰 검증
            if not admin_auth.verify_token(token):
                return jsonify({'error': '유효하지 않은 토큰입니다'}), 401

            # 권한 확인
            if not admin_auth.has_permission(token, permission):
                return jsonify({'error': '권한이 부족합니다'}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_admin():
    """현재 로그인한 관리자 정보 조회"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        token = auth_header.split(' ')[1]
        payload = admin_auth.verify_token(token)
        return payload
    except:
        return None