# -*- coding: utf-8 -*-
"""
Security utilities for AI Chat Interface
Input validation, sanitization, and security checks
"""

import re
import html
from typing import Dict, Any, List, Optional

class InputValidator:
    """입력 데이터 검증 및 정화 클래스"""

    # 허용되는 문자열 패턴
    PATTERNS = {
        'project_name': re.compile(r'^[a-zA-Z0-9\s\-_.가-힣]{1,100}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'user_id': re.compile(r'^[a-zA-Z0-9\-_.]{1,50}$'),
        'llm_model': re.compile(r'^[a-zA-Z0-9\-_.]{1,50}$'),
        'role_name': re.compile(r'^[a-zA-Z0-9\s\-_.]{1,50}$'),
        'project_type': re.compile(r'^[a-zA-Z0-9_]{1,20}$')
    }

    # 허용되는 값 목록
    ALLOWED_VALUES = {
        'project_types': ['web_app', 'mobile_app', 'api', 'desktop', 'data_analysis'],
        'ai_frameworks': ['crew-ai', 'meta-gpt'],
        'user_roles': ['user', 'admin', 'developer'],
        'llm_models': [
            'gpt-4', 'gpt-4o', 'claude-3', 'claude-3-haiku',
            'gemini-pro', 'gemini-ultra', 'llama-3', 'llama-3-8b',
            'mistral-large', 'mistral-7b', 'deepseek-coder', 'codellama'
        ],
        'role_names': [
            'Researcher', 'Writer', 'Planner',
            'Product Manager', 'Architect', 'Project Manager', 'Engineer', 'QA Engineer'
        ]
    }

    @classmethod
    def validate_string(cls, value: str, pattern_name: str, max_length: int = 1000) -> Dict[str, Any]:
        """문자열 검증"""
        if not isinstance(value, str):
            return {'valid': False, 'error': 'Value must be a string'}

        # 길이 검증
        if len(value) > max_length:
            return {'valid': False, 'error': f'String too long (max {max_length} characters)'}

        # 패턴 검증
        if pattern_name in cls.PATTERNS:
            if not cls.PATTERNS[pattern_name].match(value):
                return {'valid': False, 'error': f'Invalid format for {pattern_name}'}

        return {'valid': True, 'value': html.escape(value.strip())}

    @classmethod
    def validate_enum(cls, value: str, enum_name: str) -> Dict[str, Any]:
        """열거형 값 검증"""
        if not isinstance(value, str):
            return {'valid': False, 'error': 'Value must be a string'}

        if enum_name in cls.ALLOWED_VALUES:
            if value not in cls.ALLOWED_VALUES[enum_name]:
                return {
                    'valid': False,
                    'error': f'Invalid {enum_name}. Allowed values: {cls.ALLOWED_VALUES[enum_name]}'
                }

        return {'valid': True, 'value': value}

    @classmethod
    def validate_project_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 데이터 검증"""
        errors = []
        validated_data = {}

        # 프로젝트 이름 검증
        if 'name' in data:
            result = cls.validate_string(data['name'], 'project_name', 100)
            if result['valid']:
                validated_data['name'] = result['value']
            else:
                errors.append(f"name: {result['error']}")

        # 프로젝트 설명 검증
        if 'description' in data:
            result = cls.validate_string(data['description'], None, 500)
            if result['valid']:
                validated_data['description'] = result['value']
            else:
                errors.append(f"description: {result['error']}")

        # 프로젝트 타입 검증
        if 'project_type' in data:
            result = cls.validate_enum(data['project_type'], 'project_types')
            if result['valid']:
                validated_data['project_type'] = result['value']
            else:
                errors.append(f"project_type: {result['error']}")

        # AI 프레임워크 검증
        if 'selected_ai' in data:
            result = cls.validate_enum(data['selected_ai'], 'ai_frameworks')
            if result['valid']:
                validated_data['selected_ai'] = result['value']
            else:
                errors.append(f"selected_ai: {result['error']}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': validated_data
        }

    @classmethod
    def validate_llm_mapping(cls, mappings: List[Dict[str, str]]) -> Dict[str, Any]:
        """LLM 매핑 데이터 검증"""
        errors = []
        validated_mappings = []

        if not isinstance(mappings, list):
            return {'valid': False, 'errors': ['Mappings must be a list']}

        for i, mapping in enumerate(mappings):
            if not isinstance(mapping, dict):
                errors.append(f"Mapping {i}: Must be an object")
                continue

            validated_mapping = {}

            # 역할 이름 검증
            if 'role_name' in mapping:
                result = cls.validate_enum(mapping['role_name'], 'role_names')
                if result['valid']:
                    validated_mapping['role_name'] = result['value']
                else:
                    errors.append(f"Mapping {i} role_name: {result['error']}")

            # LLM 모델 검증
            if 'llm_model' in mapping:
                result = cls.validate_enum(mapping['llm_model'], 'llm_models')
                if result['valid']:
                    validated_mapping['llm_model'] = result['value']
                else:
                    errors.append(f"Mapping {i} llm_model: {result['error']}")

            if len(validated_mapping) == 2:  # 둘 다 유효한 경우
                validated_mappings.append(validated_mapping)

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'mappings': validated_mappings
        }

    @classmethod
    def validate_auth_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """인증 데이터 검증"""
        errors = []
        validated_data = {}

        # 사용자 ID 검증
        if 'user_id' in data:
            result = cls.validate_string(data['user_id'], 'user_id', 50)
            if result['valid']:
                validated_data['user_id'] = result['value']
            else:
                errors.append(f"user_id: {result['error']}")

        # 이메일 검증
        if 'email' in data:
            result = cls.validate_string(data['email'], 'email', 100)
            if result['valid']:
                validated_data['email'] = result['value']
            else:
                errors.append(f"email: {result['error']}")

        # 역할 검증
        if 'role' in data:
            result = cls.validate_enum(data['role'], 'user_roles')
            if result['valid']:
                validated_data['role'] = result['value']
            else:
                errors.append(f"role: {result['error']}")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'data': validated_data
        }

class SecurityChecker:
    """보안 검사 유틸리티"""

    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """SQL 인젝션 패턴 검사"""
        dangerous_patterns = [
            r"(?i)(union|select|insert|update|delete|drop|create|alter|exec|execute)",
            r"(?i)(script|javascript|vbscript)",
            r"(?i)(<script|<iframe|<object|<embed)",
            r"(?i)(onload|onerror|onclick|onmouseover)"
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, text):
                return True
        return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """파일명 정화"""
        # 위험한 문자 제거
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 상위 디렉토리 접근 방지
        filename = filename.replace('..', '')
        # 길이 제한
        return filename[:100]

    @staticmethod
    def check_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
        """파일 확장자 검증"""
        if allowed_extensions is None:
            allowed_extensions = ['.txt', '.json', '.csv', '.md', '.py', '.js', '.html', '.css']

        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return file_ext in allowed_extensions

def validate_request_data(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """요청 데이터 검증 헬퍼 함수"""
    if data_type == 'project':
        return InputValidator.validate_project_data(data)
    elif data_type == 'llm_mapping':
        mappings = data.get('mappings', [])
        return InputValidator.validate_llm_mapping(mappings)
    elif data_type == 'auth':
        return InputValidator.validate_auth_data(data)
    else:
        return {'valid': False, 'errors': ['Unknown data type']}

def check_request_security(data: Dict[str, Any]) -> List[str]:
    """요청 보안 검사"""
    issues = []

    def check_recursive(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                check_recursive(value, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_recursive(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            if SecurityChecker.check_sql_injection(obj):
                issues.append(f"Potential SQL injection in {path}: {obj[:50]}...")

    check_recursive(data)
    return issues