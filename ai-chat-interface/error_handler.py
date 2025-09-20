# -*- coding: utf-8 -*-
"""
Error Handler and User Feedback System
에러 처리 및 사용자 피드백 시스템
"""

import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from flask import jsonify, request

class ErrorType(Enum):
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    INTERNAL_ERROR = "internal_error"
    PROJECT_ERROR = "project_error"
    EXECUTION_ERROR = "execution_error"
    TEMPLATE_ERROR = "template_error"

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    error_type: ErrorType
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    suggested_actions: List[str]
    recovery_steps: List[str]
    contact_support: bool = False
    error_code: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class EnhancedErrorHandler:
    """향상된 에러 처리 및 사용자 피드백 시스템"""

    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.recovery_guides = self._initialize_recovery_guides()

        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('error.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_error_patterns(self) -> Dict[str, ErrorInfo]:
        """에러 패턴 및 메시지 초기화"""
        return {
            # 템플릿 관련 에러
            'template_not_found': ErrorInfo(
                error_type=ErrorType.TEMPLATE_ERROR,
                severity=ErrorSeverity.MEDIUM,
                user_message="선택한 템플릿을 찾을 수 없습니다",
                technical_message="Template not found in template manager",
                suggested_actions=[
                    "다른 템플릿을 선택해주세요",
                    "템플릿 목록을 새로고침해주세요"
                ],
                recovery_steps=[
                    "템플릿 페이지로 돌아가기",
                    "사용 가능한 템플릿 목록 확인",
                    "다른 템플릿 선택"
                ],
                error_code="T001"
            ),

            'project_creation_failed': ErrorInfo(
                error_type=ErrorType.PROJECT_ERROR,
                severity=ErrorSeverity.HIGH,
                user_message="프로젝트 생성 중 오류가 발생했습니다",
                technical_message="Project creation failed during initialization",
                suggested_actions=[
                    "프로젝트 이름을 확인해주세요",
                    "잠시 후 다시 시도해주세요",
                    "다른 템플릿으로 시도해주세요"
                ],
                recovery_steps=[
                    "프로젝트 이름 변경",
                    "특수문자 제거",
                    "다른 템플릿 선택",
                    "관리자에게 문의"
                ],
                contact_support=True,
                error_code="P001"
            ),

            'execution_failed': ErrorInfo(
                error_type=ErrorType.EXECUTION_ERROR,
                severity=ErrorSeverity.HIGH,
                user_message="AI 프로젝트 실행 중 오류가 발생했습니다",
                technical_message="Project execution failed during AI agent processing",
                suggested_actions=[
                    "프로젝트를 다시 실행해보세요",
                    "LLM 모델 설정을 확인해주세요",
                    "네트워크 연결을 확인해주세요"
                ],
                recovery_steps=[
                    "실행 취소 후 재시작",
                    "다른 LLM 모델 선택",
                    "프로젝트 설정 확인",
                    "시스템 관리자 문의"
                ],
                contact_support=True,
                error_code="E001"
            ),

            # 네트워크 관련 에러
            'connection_timeout': ErrorInfo(
                error_type=ErrorType.TIMEOUT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                user_message="연결 시간이 초과되었습니다",
                technical_message="Request timeout exceeded",
                suggested_actions=[
                    "네트워크 연결을 확인해주세요",
                    "잠시 후 다시 시도해주세요"
                ],
                recovery_steps=[
                    "페이지 새로고침",
                    "네트워크 상태 확인",
                    "잠시 후 재시도"
                ],
                error_code="N001"
            ),

            'service_unavailable': ErrorInfo(
                error_type=ErrorType.EXTERNAL_SERVICE_ERROR,
                severity=ErrorSeverity.HIGH,
                user_message="일시적으로 서비스를 이용할 수 없습니다",
                technical_message="External service is currently unavailable",
                suggested_actions=[
                    "잠시 후 다시 시도해주세요",
                    "서비스 상태를 확인해주세요"
                ],
                recovery_steps=[
                    "5-10분 후 재시도",
                    "다른 브라우저 사용",
                    "캐시 및 쿠키 삭제"
                ],
                contact_support=True,
                error_code="S001"
            ),

            # 데이터베이스 관련 에러
            'database_connection_failed': ErrorInfo(
                error_type=ErrorType.DATABASE_ERROR,
                severity=ErrorSeverity.CRITICAL,
                user_message="데이터베이스 연결에 실패했습니다",
                technical_message="Unable to connect to database",
                suggested_actions=[
                    "잠시 후 다시 시도해주세요",
                    "관리자에게 문의해주세요"
                ],
                recovery_steps=[
                    "페이지 새로고침",
                    "로그아웃 후 재로그인",
                    "시스템 관리자 문의"
                ],
                contact_support=True,
                error_code="DB001"
            ),

            # 인증/권한 관련 에러
            'authentication_required': ErrorInfo(
                error_type=ErrorType.AUTHENTICATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                user_message="로그인이 필요합니다",
                technical_message="Authentication required for this operation",
                suggested_actions=[
                    "로그인해주세요",
                    "세션이 만료된 경우 다시 로그인해주세요"
                ],
                recovery_steps=[
                    "로그인 페이지로 이동",
                    "계정 정보 확인",
                    "비밀번호 재설정"
                ],
                error_code="A001"
            ),

            'insufficient_permissions': ErrorInfo(
                error_type=ErrorType.AUTHORIZATION_ERROR,
                severity=ErrorSeverity.MEDIUM,
                user_message="이 작업을 수행할 권한이 없습니다",
                technical_message="Insufficient permissions for this operation",
                suggested_actions=[
                    "프로젝트 소유자에게 권한을 요청해주세요",
                    "관리자에게 문의해주세요"
                ],
                recovery_steps=[
                    "프로젝트 권한 확인",
                    "소유자에게 권한 요청",
                    "관리자 문의"
                ],
                contact_support=True,
                error_code="A002"
            ),

            # 일반적인 에러
            'invalid_input': ErrorInfo(
                error_type=ErrorType.VALIDATION_ERROR,
                severity=ErrorSeverity.LOW,
                user_message="입력 정보가 올바르지 않습니다",
                technical_message="Input validation failed",
                suggested_actions=[
                    "입력 정보를 다시 확인해주세요",
                    "필수 항목을 모두 입력해주세요"
                ],
                recovery_steps=[
                    "입력 형식 확인",
                    "필수 필드 입력",
                    "특수문자 제거"
                ],
                error_code="V001"
            ),

            'rate_limit_exceeded': ErrorInfo(
                error_type=ErrorType.RATE_LIMIT_ERROR,
                severity=ErrorSeverity.MEDIUM,
                user_message="요청 횟수가 제한을 초과했습니다",
                technical_message="Rate limit exceeded",
                suggested_actions=[
                    "잠시 후 다시 시도해주세요",
                    "요청 빈도를 줄여주세요"
                ],
                recovery_steps=[
                    "1-2분 대기",
                    "불필요한 요청 중단",
                    "나중에 재시도"
                ],
                error_code="R001"
            )
        }

    def _initialize_recovery_guides(self) -> Dict[ErrorType, List[str]]:
        """에러 유형별 복구 가이드 초기화"""
        return {
            ErrorType.TEMPLATE_ERROR: [
                "템플릿 목록 새로고침",
                "브라우저 캐시 삭제",
                "다른 템플릿 선택",
                "관리자에게 문의"
            ],
            ErrorType.PROJECT_ERROR: [
                "프로젝트 이름 변경",
                "특수문자 제거",
                "프로젝트 설정 확인",
                "다른 템플릿 사용"
            ],
            ErrorType.EXECUTION_ERROR: [
                "실행 취소 후 재시작",
                "다른 LLM 모델 선택",
                "네트워크 연결 확인",
                "시스템 재시작"
            ],
            ErrorType.NETWORK_ERROR: [
                "네트워크 연결 확인",
                "VPN 연결 해제",
                "다른 네트워크 사용",
                "방화벽 설정 확인"
            ],
            ErrorType.DATABASE_ERROR: [
                "페이지 새로고침",
                "로그아웃 후 재로그인",
                "다른 브라우저 사용",
                "관리자 문의"
            ]
        }

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """에러 처리 및 사용자 친화적 응답 생성"""
        try:
            # 에러 분석
            error_info = self._analyze_error(error, context)

            # 로깅
            self._log_error(error, error_info, context)

            # 사용자 응답 생성
            response = self._create_user_response(error_info)

            return response

        except Exception as e:
            # 에러 처리 중 에러 발생
            self.logger.error(f"Error in error handler: {str(e)}")
            return self._create_fallback_response()

    def _analyze_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """에러 분석 및 적절한 ErrorInfo 반환"""
        error_str = str(error).lower()
        error_type = type(error).__name__

        # 알려진 에러 패턴 매칭
        if 'template' in error_str and 'not found' in error_str:
            return self.error_patterns['template_not_found']
        elif 'project' in error_str and ('creation' in error_str or 'initialize' in error_str):
            return self.error_patterns['project_creation_failed']
        elif 'execution' in error_str or 'agent' in error_str:
            return self.error_patterns['execution_failed']
        elif 'timeout' in error_str or 'TimeoutError' in error_type:
            return self.error_patterns['connection_timeout']
        elif 'database' in error_str or 'db' in error_str:
            return self.error_patterns['database_connection_failed']
        elif 'permission' in error_str or 'authorization' in error_str:
            return self.error_patterns['insufficient_permissions']
        elif 'authentication' in error_str or 'login' in error_str:
            return self.error_patterns['authentication_required']
        elif 'validation' in error_str or 'invalid' in error_str:
            return self.error_patterns['invalid_input']
        elif 'rate limit' in error_str:
            return self.error_patterns['rate_limit_exceeded']
        elif 'service' in error_str and 'unavailable' in error_str:
            return self.error_patterns['service_unavailable']

        # 기본 에러 정보
        return ErrorInfo(
            error_type=ErrorType.INTERNAL_ERROR,
            severity=ErrorSeverity.MEDIUM,
            user_message="예상치 못한 오류가 발생했습니다",
            technical_message=str(error),
            suggested_actions=[
                "페이지를 새로고침해주세요",
                "잠시 후 다시 시도해주세요",
                "문제가 계속되면 관리자에게 문의해주세요"
            ],
            recovery_steps=[
                "페이지 새로고침",
                "브라우저 재시작",
                "다른 브라우저 사용",
                "관리자 문의"
            ],
            contact_support=True,
            error_code="G001"
        )

    def _log_error(self, error: Exception, error_info: ErrorInfo, context: Dict[str, Any] = None):
        """에러 로깅"""
        log_data = {
            'timestamp': error_info.timestamp.isoformat(),
            'error_type': error_info.error_type.value,
            'severity': error_info.severity.value,
            'error_code': error_info.error_code,
            'user_message': error_info.user_message,
            'technical_message': error_info.technical_message,
            'original_error': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'request_info': self._get_request_info()
        }

        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.error(f"Error occurred: {log_data}")
        else:
            self.logger.warning(f"Error occurred: {log_data}")

    def _get_request_info(self) -> Dict[str, Any]:
        """현재 요청 정보 수집"""
        try:
            return {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'referrer': request.headers.get('Referer', '')
            }
        except:
            return {}

    def _create_user_response(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """사용자 친화적 응답 생성"""
        return {
            'success': False,
            'error': {
                'type': error_info.error_type.value,
                'severity': error_info.severity.value,
                'code': error_info.error_code,
                'message': error_info.user_message,
                'technical_details': error_info.technical_message,
                'suggested_actions': error_info.suggested_actions,
                'recovery_steps': error_info.recovery_steps,
                'contact_support': error_info.contact_support,
                'timestamp': error_info.timestamp.isoformat()
            },
            'support_info': {
                'error_code': error_info.error_code,
                'timestamp': error_info.timestamp.isoformat(),
                'session_id': self._get_session_id()
            } if error_info.contact_support else None
        }

    def _create_fallback_response(self) -> Dict[str, Any]:
        """폴백 응답 (에러 처리 중 에러 발생 시)"""
        return {
            'success': False,
            'error': {
                'type': 'internal_error',
                'severity': 'high',
                'code': 'FALLBACK001',
                'message': '시스템 오류가 발생했습니다',
                'technical_details': 'Internal error in error handling system',
                'suggested_actions': [
                    '페이지를 새로고침해주세요',
                    '관리자에게 문의해주세요'
                ],
                'recovery_steps': [
                    '페이지 새로고침',
                    '브라우저 재시작',
                    '관리자 문의'
                ],
                'contact_support': True,
                'timestamp': datetime.now().isoformat()
            }
        }

    def _get_session_id(self) -> str:
        """세션 ID 생성"""
        import uuid
        return str(uuid.uuid4())[:8]

    def create_error_response(self, error_pattern: str, custom_message: str = None) -> Dict[str, Any]:
        """특정 에러 패턴에 대한 응답 생성"""
        if error_pattern in self.error_patterns:
            error_info = self.error_patterns[error_pattern]
            if custom_message:
                error_info.user_message = custom_message
            return self._create_user_response(error_info)
        else:
            return self._create_fallback_response()

    def register_error_pattern(self, pattern_name: str, error_info: ErrorInfo):
        """새로운 에러 패턴 등록"""
        self.error_patterns[pattern_name] = error_info

# 전역 에러 핸들러 인스턴스
error_handler = EnhancedErrorHandler()

def handle_api_error(func):
    """API 에러 처리 데코레이터"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_response = error_handler.handle_error(e, {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs)
            })
            return jsonify(error_response), 500

    wrapper.__name__ = func.__name__
    return wrapper