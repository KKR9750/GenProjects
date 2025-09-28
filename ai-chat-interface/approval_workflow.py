# -*- coding: utf-8 -*-
"""
승인 워크플로우 관리 시스템 (Approval Workflow Manager)
사전 분석 결과에 대한 사용자 승인 프로세스 관리
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from enum import Enum

# 로깅 설정 (import 전에 먼저 설정)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 데이터베이스 연동
try:
    from database import Database
    from supabase import create_client, Client
    supabase_available = True
    # Database 인스턴스 생성
    db = Database()
except ImportError as e:
    # 데이터베이스 모듈이 없을 경우 Mock 객체 사용
    logger.warning(f"데이터베이스 모듈 import 실패: {str(e)}")
    db = None
    Database = None
    create_client = None
    Client = None
    supabase_available = False

class ApprovalStatus(Enum):
    """승인 상태 열거형"""
    PENDING = "pending"           # 승인 대기
    APPROVED = "approved"         # 승인됨
    REJECTED = "rejected"         # 거부됨
    REVISION_REQUESTED = "revision_requested"  # 수정 요청
    EXPIRED = "expired"           # 만료됨

class ApprovalWorkflowManager:
    """승인 워크플로우 관리자 (싱글톤)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ApprovalWorkflowManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """초기화"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Database 인스턴스 사용
        if db and db.is_connected():
            self.supabase = db.supabase
            logger.info("Supabase 연결 성공")
        else:
            logger.warning("Supabase 모듈을 사용할 수 없습니다")
            self.supabase = None

        # 메모리 저장소 (데이터베이스 대체용)
        self.approval_storage = {}
        self.analysis_storage = {}

        self._initialized = True

    def create_approval_request(self,
                              analysis_result: Dict,
                              project_data: Optional[Dict] = None,
                              project_id: Optional[str] = None,
                              requester: str = "system") -> str:
        """
        승인 요청 생성

        Args:
            analysis_result: 사전 분석 결과
            project_data: 프로젝트 실행에 필요한 전체 데이터 (선택)
            project_id: 연관된 프로젝트 ID (선택)
            requester: 요청자

        Returns:
            str: 승인 요청 ID
        """
        try:
            approval_id = str(uuid.uuid4())
            timestamp = datetime.now()

            approval_request = {
                "approval_id": approval_id,
                "project_id": project_id,
                "analysis_result": analysis_result,
                "project_data": project_data,  # 프로젝트 실행에 필요한 전체 데이터
                "status": ApprovalStatus.PENDING.value,
                "requester": requester,
                "created_at": timestamp.isoformat(),
                "updated_at": timestamp.isoformat(),
                "metadata": {
                    "framework": analysis_result.get('framework', 'unknown'),
                    "analysis_id": analysis_result.get('analysis_id'),
                    "estimated_completion_time": self._estimate_completion_time(analysis_result),
                    "has_project_data": project_data is not None,
                    "project_name": project_data.get('project_name') if project_data else None
                }
            }

            # 데이터베이스 저장 시도
            if self._save_approval_to_db(approval_request):
                logger.info(f"승인 요청 데이터베이스 저장 성공: {approval_id}")
            else:
                # 메모리 저장소에 저장
                self.approval_storage[approval_id] = approval_request
                logger.info(f"승인 요청 메모리 저장 성공: {approval_id}")

            # 메모리 저장소 상태 디버깅
            logger.info(f"현재 메모리 저장소에 {len(self.approval_storage)}개의 승인 요청 저장됨")
            logger.info(f"메모리 저장된 승인 ID 목록: {list(self.approval_storage.keys())}")

            return approval_id

        except Exception as e:
            logger.error(f"승인 요청 생성 실패: {str(e)}")
            raise

    def get_approval_request(self, approval_id: str) -> Optional[Dict]:
        """승인 요청 조회 - 메모리 우선"""
        try:
            logger.info(f"승인 요청 조회 시작: {approval_id}")

            # 1. 메모리 저장소에서 먼저 조회 (빠르고 안정적)
            memory_result = self.approval_storage.get(approval_id)
            if memory_result:
                logger.info(f"메모리 저장소에서 승인 요청 발견: {approval_id}")
                return memory_result

            # 2. 데이터베이스에서 조회 시도 (메모리에 없는 경우만)
            if self.supabase:
                try:
                    logger.info(f"데이터베이스에서 승인 요청 조회 시도: {approval_id}")
                    result = self.supabase.table('approval_requests').select('*').eq('approval_id', approval_id).execute()
                    if result.data:
                        db_result = result.data[0]
                        # 데이터베이스 결과를 메모리에도 저장
                        self.approval_storage[approval_id] = db_result
                        logger.info(f"데이터베이스에서 승인 요청 발견 및 메모리에 캐시: {approval_id}")
                        return db_result
                    else:
                        logger.info(f"데이터베이스에서 승인 요청을 찾을 수 없음: {approval_id}")
                except Exception as db_error:
                    logger.warning(f"데이터베이스 조회 실패 (무시하고 계속): {str(db_error)}")

            logger.warning(f"승인 요청을 찾을 수 없음 (메모리, DB 모두): {approval_id}")
            logger.info(f"현재 메모리 저장소에 저장된 ID 목록: {list(self.approval_storage.keys())}")
            return None

        except Exception as e:
            logger.error(f"승인 요청 조회 중 예외 발생: {str(e)}")
            # 예외가 발생해도 메모리 저장소에서 한 번 더 시도
            try:
                return self.approval_storage.get(approval_id)
            except:
                return None

    def process_approval_response(self,
                                approval_id: str,
                                action: str,
                                feedback: Optional[str] = None,
                                revisions: Optional[Dict] = None) -> Dict:
        """
        승인 응답 처리

        Args:
            approval_id: 승인 요청 ID
            action: 액션 ('approve', 'reject', 'request_revision')
            feedback: 사용자 피드백
            revisions: 수정 요청 내용

        Returns:
            Dict: 처리 결과
        """
        try:
            logger.info(f"승인 응답 처리 시작: approval_id={approval_id}, action={action}")
            logger.info(f"현재 메모리 저장소에 {len(self.approval_storage)}개의 승인 요청 저장됨")
            logger.info(f"메모리 저장된 승인 ID 목록: {list(self.approval_storage.keys())}")

            approval_request = self.get_approval_request(approval_id)
            if not approval_request:
                logger.error(f"승인 요청을 찾을 수 없음: {approval_id}")
                logger.error(f"메모리 저장소 디버깅: {self.approval_storage}")
                raise ValueError(f"승인 요청을 찾을 수 없음: {approval_id}")

            timestamp = datetime.now()

            # 액션별 상태 업데이트
            if action == 'approve':
                new_status = ApprovalStatus.APPROVED.value
            elif action == 'reject':
                new_status = ApprovalStatus.REJECTED.value
            elif action == 'request_revision':
                new_status = ApprovalStatus.REVISION_REQUESTED.value
            else:
                raise ValueError(f"잘못된 액션: {action}")

            # 승인 요청 업데이트
            approval_request.update({
                "status": new_status,
                "updated_at": timestamp.isoformat(),
                "response": {
                    "action": action,
                    "feedback": feedback,
                    "revisions": revisions,
                    "processed_at": timestamp.isoformat()
                }
            })

            # 히스토리 기록
            history_entry = {
                "approval_id": approval_id,
                "action": action,
                "feedback": feedback,
                "revisions": revisions,
                "timestamp": timestamp.isoformat()
            }

            # 데이터베이스 업데이트
            if self._update_approval_in_db(approval_request, history_entry):
                logger.info(f"승인 응답 데이터베이스 업데이트 성공: {approval_id}")
            else:
                # 메모리 저장소 업데이트
                self.approval_storage[approval_id] = approval_request
                logger.info(f"승인 응답 메모리 업데이트 성공: {approval_id}, 새 상태: {new_status}")
                logger.info(f"메모리 저장소 상태 확인: {approval_id} -> {self.approval_storage[approval_id].get('status')}")

            return {
                "success": True,
                "approval_id": approval_id,
                "status": new_status,
                "message": f"승인 요청이 {action} 되었습니다.",
                "next_steps": self._get_next_steps(new_status, approval_request)
            }

        except Exception as e:
            logger.error(f"승인 응답 처리 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_pending_approvals(self, project_id: Optional[str] = None) -> List[Dict]:
        """대기 중인 승인 요청 목록 조회"""
        pending_approvals = []

        # 데이터베이스에서 조회 (실패해도 계속 진행)
        if self.supabase:
            try:
                query = self.supabase.table('approval_requests').select('*').eq('status', ApprovalStatus.PENDING.value)
                if project_id:
                    query = query.eq('project_id', project_id)

                result = query.execute()
                if result.data:
                    pending_approvals.extend(result.data)
                    logger.info(f"데이터베이스에서 승인 요청 {len(result.data)}개 조회")
            except Exception as db_error:
                logger.error(f"데이터베이스 조회 실패: {str(db_error)}")

        # 메모리 저장소에서 조회
        try:
            memory_count = 0
            logger.info(f"메모리 저장소 총 {len(self.approval_storage)}개 항목 확인 중")

            for approval_id, approval_data in self.approval_storage.items():
                current_status = approval_data.get('status')
                expected_status = ApprovalStatus.PENDING.value
                logger.info(f"승인 ID {approval_id}: 현재 상태='{current_status}', 예상 상태='{expected_status}', 일치={current_status == expected_status}")

                if (approval_data.get('status') == ApprovalStatus.PENDING.value and
                    (not project_id or approval_data.get('project_id') == project_id)):
                    pending_approvals.append(approval_data)
                    memory_count += 1

            if memory_count > 0:
                logger.info(f"메모리에서 승인 요청 {memory_count}개 조회")
            else:
                logger.info(f"메모리에서 조건에 맞는 승인 요청 없음")
        except Exception as memory_error:
            logger.error(f"메모리 조회 실패: {str(memory_error)}")

        logger.info(f"총 {len(pending_approvals)}개 승인 요청 반환")
        return pending_approvals

    def request_revision(self,
                        approval_id: str,
                        revision_requests: Dict,
                        feedback: str) -> Dict:
        """수정 요청 처리"""
        return self.process_approval_response(
            approval_id=approval_id,
            action='request_revision',
            feedback=feedback,
            revisions=revision_requests
        )

    def apply_revisions(self,
                       approval_id: str,
                       revised_analysis: Dict) -> Dict:
        """수정 사항 적용"""
        try:
            approval_request = self.get_approval_request(approval_id)
            if not approval_request:
                raise ValueError(f"승인 요청을 찾을 수 없음: {approval_id}")

            if approval_request.get('status') != ApprovalStatus.REVISION_REQUESTED.value:
                raise ValueError("수정 요청 상태가 아닙니다")

            # 수정된 분석 결과 적용
            approval_request['analysis_result'] = revised_analysis
            approval_request['status'] = ApprovalStatus.PENDING.value
            approval_request['updated_at'] = datetime.now().isoformat()

            # 저장
            if self._update_approval_in_db(approval_request):
                logger.info(f"수정 적용 데이터베이스 업데이트 성공: {approval_id}")
            else:
                self.approval_storage[approval_id] = approval_request

            return {
                "success": True,
                "approval_id": approval_id,
                "message": "수정 사항이 적용되어 재승인 대기 상태입니다."
            }

        except Exception as e:
            logger.error(f"수정 적용 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_approval_history(self, approval_id: str) -> List[Dict]:
        """승인 히스토리 조회"""
        try:
            # 데이터베이스에서 조회
            if self.supabase:
                result = self.supabase.table('approval_history').select('*').eq('approval_id', approval_id).order('timestamp').execute()
                if result.data:
                    return result.data

            # 메모리에서는 간단한 히스토리만 제공
            approval_request = self.approval_storage.get(approval_id)
            if approval_request:
                return [{
                    "approval_id": approval_id,
                    "action": "created",
                    "timestamp": approval_request.get('created_at'),
                    "status": approval_request.get('status')
                }]

            return []

        except Exception as e:
            logger.error(f"승인 히스토리 조회 실패: {str(e)}")
            return []

    def _save_approval_to_db(self, approval_request: Dict) -> bool:
        """데이터베이스에 승인 요청 저장"""
        logger.info(f"데이터베이스 저장 시도 - supabase 연결: {self.supabase is not None}")

        if not self.supabase:
            logger.warning("Supabase 연결이 없어 데이터베이스 저장 실패")
            return False

        try:
            logger.info(f"승인 요청 데이터베이스 삽입 중: approval_id={approval_request.get('approval_id')}")
            result = self.supabase.table('approval_requests').insert(approval_request).execute()
            success = len(result.data) > 0
            logger.info(f"데이터베이스 저장 결과: success={success}, result_data_length={len(result.data) if result.data else 0}")
            return success

        except Exception as e:
            logger.error(f"데이터베이스 저장 실패: {str(e)}")
            logger.error(f"저장 시도한 데이터: {approval_request}")
            return False

    def _update_approval_in_db(self, approval_request: Dict, history_entry: Optional[Dict] = None) -> bool:
        """데이터베이스 승인 요청 업데이트"""
        if not self.supabase:
            return False

        try:
            # 승인 요청 업데이트
            result = self.supabase.table('approval_requests').update(approval_request).eq('approval_id', approval_request['approval_id']).execute()

            # 히스토리 추가
            if history_entry:
                self.supabase.table('approval_history').insert(history_entry).execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"데이터베이스 업데이트 실패: {str(e)}")
            return False

    def _estimate_completion_time(self, analysis_result: Dict) -> str:
        """완료 예상 시간 계산"""
        try:
            analysis = analysis_result.get('analysis', {})
            workflow = analysis.get('workflow', [])

            total_time = 0
            for step in workflow:
                estimated_time = step.get('estimated_time', '30분')
                # 시간 파싱 (예: "30분", "1시간" 등)
                if '시간' in estimated_time:
                    hours = int(estimated_time.replace('시간', '').strip())
                    total_time += hours * 60
                elif '분' in estimated_time:
                    minutes = int(estimated_time.replace('분', '').strip())
                    total_time += minutes

            if total_time > 60:
                return f"{total_time // 60}시간 {total_time % 60}분"
            else:
                return f"{total_time}분"

        except Exception as e:
            logger.error(f"시간 계산 실패: {str(e)}")
            return "시간 미정"

    def _get_next_steps(self, status: str, approval_request: Dict) -> List[str]:
        """다음 단계 가이드"""
        next_steps = []

        if status == ApprovalStatus.APPROVED.value:
            next_steps = [
                "프로젝트 실행 준비",
                f"{approval_request.get('metadata', {}).get('framework', 'AI')} 프레임워크 시작",
                "실시간 모니터링 활성화"
            ]
        elif status == ApprovalStatus.REJECTED.value:
            next_steps = [
                "새로운 요청으로 다시 시작",
                "요구사항 재검토",
                "대안 접근 방법 고려"
            ]
        elif status == ApprovalStatus.REVISION_REQUESTED.value:
            next_steps = [
                "피드백 검토",
                "분석 결과 수정",
                "재승인 요청"
            ]

        return next_steps

    def cleanup_expired_approvals(self, days: int = 7) -> int:
        """만료된 승인 요청 정리"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned_count = 0

            # 메모리 저장소 정리
            expired_keys = []
            for approval_id, approval_data in self.approval_storage.items():
                created_at = datetime.fromisoformat(approval_data.get('created_at', ''))
                if (created_at < cutoff_date and
                    approval_data.get('status') == ApprovalStatus.PENDING.value):
                    expired_keys.append(approval_id)

            for key in expired_keys:
                self.approval_storage[key]['status'] = ApprovalStatus.EXPIRED.value
                cleaned_count += 1

            # 데이터베이스 정리
            if self.supabase:
                result = self.supabase.table('approval_requests').update({
                    'status': ApprovalStatus.EXPIRED.value
                }).lt('created_at', cutoff_date.isoformat()).eq('status', ApprovalStatus.PENDING.value).execute()

                if result.data:
                    cleaned_count += len(result.data)

            logger.info(f"만료된 승인 요청 {cleaned_count}개 정리 완료")
            return cleaned_count

        except Exception as e:
            logger.error(f"만료 승인 정리 실패: {str(e)}")
            return 0


# 승인 워크플로우 매니저 인스턴스
approval_workflow_manager = ApprovalWorkflowManager()


# 유틸리티 함수들
def create_quick_approval(analysis_result: Dict, auto_approve: bool = False) -> str:
    """빠른 승인 요청 생성"""
    approval_id = approval_workflow_manager.create_approval_request(
        analysis_result=analysis_result,
        requester="quick_approval"
    )

    if auto_approve:
        approval_workflow_manager.process_approval_response(
            approval_id=approval_id,
            action="approve",
            feedback="자동 승인됨"
        )

    return approval_id


def get_approval_summary(approval_id: str) -> Dict:
    """승인 요청 요약 정보"""
    approval_request = approval_workflow_manager.get_approval_request(approval_id)
    if not approval_request:
        return {"error": "승인 요청을 찾을 수 없습니다"}

    analysis = approval_request.get('analysis_result', {}).get('analysis', {})

    return {
        "approval_id": approval_id,
        "status": approval_request.get('status'),
        "framework": approval_request.get('metadata', {}).get('framework'),
        "project_summary": analysis.get('project_summary', 'N/A'),
        "agent_count": len(analysis.get('agents', [])),
        "workflow_steps": len(analysis.get('workflow', [])),
        "estimated_time": approval_request.get('metadata', {}).get('estimated_completion_time'),
        "created_at": approval_request.get('created_at')
    }


if __name__ == "__main__":
    # 테스트 코드
    manager = ApprovalWorkflowManager()

    # 테스트 분석 결과
    test_analysis = {
        "analysis_id": "test-123",
        "framework": "crewai",
        "analysis": {
            "project_summary": "테스트 프로젝트",
            "agents": [{"role": "Researcher"}, {"role": "Writer"}],
            "workflow": [{"title": "Step 1", "estimated_time": "30분"}]
        }
    }

    # 승인 요청 생성
    approval_id = manager.create_approval_request(test_analysis)
    print(f"생성된 승인 요청 ID: {approval_id}")

    # 승인 요청 조회
    approval = manager.get_approval_request(approval_id)
    print(f"승인 요청 상태: {approval.get('status') if approval else 'None'}")

    # 승인 처리
    result = manager.process_approval_response(approval_id, "approve", "테스트 승인")
    print(f"승인 처리 결과: {result.get('success')}")