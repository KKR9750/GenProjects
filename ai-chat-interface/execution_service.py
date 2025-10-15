# -*- coding: utf-8 -*-
"""
Execution Service - Centralized Logic for AI Project Execution
AI 프로젝트 생성 요청 처리, 승인 후 실행 재개 등 중앙 집중식 로직 관리
"""

import os
import sys
import uuid
import threading
from datetime import datetime
import subprocess

# 프로젝트 루트 경로를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

from ai_chat_interface.pre_analysis_service import pre_analysis_service
from ai_chat_interface.approval_workflow import approval_workflow_manager
from ai_chat_interface.crewai_logger import crewai_logger, ExecutionPhase
from ai_chat_interface.project_initializer import get_supabase_client
from ai_chat_interface.smart_model_allocator import SmartModelAllocator

# 전역 변수 및 설정
PROJECTS_BASE_DIR = os.path.join(os.path.dirname(current_dir), 'Projects')
execution_status = {}

def handle_crewai_request(data):
    """
    CrewAI 요청을 사전 분석하고 승인 워크플로우를 시작합니다.
    app.py의 handle_crewai_request 로직을 이전.
    """
    requirement = data.get('requirement')
    selected_models = data.get('selectedModels', {})
    pre_analysis_model = data.get('preAnalysisModel', 'gemini-flash')
    project_id = data.get('projectId')
    session_id = data.get('sessionId') # 프론트에서 전달된 세션 ID

    if not requirement:
        return {'success': False, 'error': 'Requirement is required'}, 400

    execution_id = str(uuid.uuid4())
    crew_id = f"crew_{int(datetime.now().timestamp())}"

    print(f"[EXECUTION_SERVICE] 사전 분석 시작: execution_id={execution_id}")

    # 1. 사전 분석 서비스 호출
    analysis_result = pre_analysis_service.analyze_user_request(
        user_request=requirement,
        framework="crewai",
        model=pre_analysis_model
    )

    if analysis_result.get('status') == 'error':
        error_msg = analysis_result.get('error', '사전 분석 실패')
        print(f"[EXECUTION_SERVICE ERROR] {error_msg}")
        return {'success': False, 'error': error_msg}, 500

    # 2. 프로젝트 경로 준비
    if not project_id:
        project_name = f"project_{len(os.listdir(PROJECTS_BASE_DIR)) + 1:05d}"
        project_path = os.path.join(PROJECTS_BASE_DIR, project_name)
    else:
        project_name = project_id if project_id.startswith('project_') else f"project_{project_id}"
        project_path = os.path.join(PROJECTS_BASE_DIR, project_name)

    # 3. 승인 요청 데이터 구성
    project_data = {
        'execution_id': execution_id,
        'crew_id': crew_id,
        'framework': 'crewai',
        'requirement': requirement,
        'selected_models': selected_models,
        'project_id': project_id,
        'project_name': project_name,
        'project_path': project_path,
        'session_id': session_id, # 승인 요청에 세션 ID 포함
    }

    # 4. 승인 요청 생성
    approval_id = approval_workflow_manager.create_approval_request(
        analysis_result=analysis_result,
        project_data=project_data,
        project_id=project_id,
        requester="crewai_interface"
    )

    # 5. 승인 대기 응답 반환
    response_data = {
        'success': True,
        'message': 'AI 계획이 분석되었습니다. 승인을 기다리고 있습니다.',
        'approval_id': approval_id,
        'execution_id': execution_id,
        'status': 'pending_approval',
        'analysis': analysis_result.get('analysis', {}),
        'project_info': {'name': project_name, 'path': project_path},
        'requires_approval': True
    }
    return response_data, 200

def resume_crewai_execution(execution_id, project_data):
    """
    승인 후 CrewAI 실행을 재개합니다.
    app.py의 resume_crewai_execution 로직을 이전.
    """
    def run_in_background():
        try:
            print(f"[EXECUTION_SERVICE] CrewAI 실행 재개: {execution_id}")

            requirement = project_data.get('requirement')
            selected_models = project_data.get('selected_models', {})
            crew_id = project_data.get('crew_id')
            project_path = project_data.get('project_path')

            execution_status[execution_id] = {
                'status': 'running',
                'message': '승인 완료 - CrewAI 실행 시작',
                'start_time': datetime.now(),
                'phase': 'resumed_execution'
            }

            crewai_logger.start_execution_logging(execution_id, crew_id, {'requirement': requirement, 'resumed': True})
            crewai_logger.start_step_tracking(execution_id, crew_id, total_steps=5)

            # 1. 디렉토리 생성
            os.makedirs(project_path, exist_ok=True)
            crewai_logger.advance_step(execution_id, crew_id, "디렉토리 생성", project_path, ExecutionPhase.DIRECTORY_CREATION)

            # 2. 스크립트 생성
            from ai_chat_interface.enhanced_script_generator import generate_enhanced_crewai_script
            script_content = generate_enhanced_crewai_script(requirement, selected_models, project_path, execution_id)
            script_path = os.path.join(project_path, "run_crew.py")

            # --- 프로젝트와 세션 연결 ---
            project_id_from_data = project_data.get('project_id')
            session_id_from_data = project_data.get('session_id')
            if project_id_from_data and session_id_from_data:
                try:
                    supabase = get_supabase_client()
                    if supabase:
                        # 1. projects 테이블에 session_id 업데이트
                        supabase.table('projects').update({'pre_analysis_session_id': session_id_from_data}).eq('project_id', project_id_from_data).execute()
                        # 2. pre_analysis_sessions 테이블에 project_id 업데이트
                        supabase.table('pre_analysis_sessions').update({'project_id': project_id_from_data}).eq('session_id', session_id_from_data).execute()
                        print(f"[EXECUTION_SERVICE] 프로젝트({project_id_from_data})와 세션({session_id_from_data}) 연결 완료")
                except Exception as link_error:
                    print(f"[EXECUTION_SERVICE ERROR] 프로젝트-세션 연결 실패: {link_error}")

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            crewai_logger.advance_step(execution_id, crew_id, "스크립트 생성", script_path, ExecutionPhase.FILE_GENERATION)

            # 3. 요구사항 파일 생성
            requirements_path = os.path.join(project_path, "requirements.txt")
            with open(requirements_path, 'w', encoding='utf-8') as f:
                f.write("crewai>=0.28.8\nlangchain>=0.1.0\n")
            crewai_logger.log_file_generation(execution_id, crew_id, requirements_path, "Requirements", len(requirements_content), True)

            # 4. 서브프로세스로 스크립트 실행
            crewai_logger.advance_step(execution_id, crew_id, "CrewAI 실행", "시작", ExecutionPhase.EXECUTION)
            
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                cwd=project_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            stdout, stderr = process.communicate()
            return_code = process.returncode

            # 5. 파일 목록 DB에 저장
            from ai_chat_interface.project_service import add_project_files
            if return_code == 0:
                project_id_from_data = project_data.get('project_id')
                if project_id_from_data:
                    add_project_files(project_id_from_data, project_path)
                    print(f"[EXECUTION_SERVICE] 프로젝트 파일 목록 DB 저장 완료: {project_id_from_data}")

            # 6. 최종 상태 업데이트
            if return_code == 0:
                execution_status[execution_id].update({
                    'status': 'completed',
                    'message': 'CrewAI 실행 완료',
                    'end_time': datetime.now(),
                    'output': stdout
                })
                crewai_logger.log_completion(execution_id, crew_id, True, stdout)
                print(f"[EXECUTION_SERVICE] 실행 성공: {execution_id}")
            else:
                execution_status[execution_id].update({
                    'status': 'failed',
                    'message': 'CrewAI 실행 실패',
                    'end_time': datetime.now(),
                    'error': stderr
                })
                crewai_logger.log_completion(execution_id, crew_id, False, stderr)
                print(f"[EXECUTION_SERVICE] 실행 실패: {execution_id}, error: {stderr}")

        except Exception as e:
            error_msg = f'백그라운드 실행 중 오류: {str(e)}'
            print(f"[EXECUTION_SERVICE ERROR] {error_msg}")
            execution_status[execution_id] = {
                'status': 'failed',
                'message': error_msg,
                'end_time': datetime.now()
            }
            if 'crew_id' in locals():
                crewai_logger.log_error(execution_id, crew_id, e, "CrewAI 백그라운드 실행")

    threading.Thread(target=run_in_background, daemon=True).start()
    return True

def resume_metagpt_execution(execution_id, project_data):
    """
    승인 후 MetaGPT 실행을 재개합니다.
    app.py의 resume_metagpt_execution 로직을 이전.
    """
    def run_in_background():
        try:
            print(f"[EXECUTION_SERVICE] MetaGPT 실행 재개: {execution_id}")
            requirement = project_data.get('requirement')
            selected_models = project_data.get('selected_models', {})

            execution_status[execution_id] = {'status': 'running', 'message': 'MetaGPT 실행 중...'}

            # MetaGPT 실행 로직 (기존 Blueprint의 로직을 여기에 통합)
            from MetaGPT.metagpt_blueprint import process_with_metagpt_core
            import asyncio
            
            result_text = asyncio.run(process_with_metagpt_core(requirement, project_data))

            execution_status[execution_id].update({
                'status': 'completed',
                'message': 'MetaGPT 실행 완료',
                'result': result_text
            })
            print(f"[EXECUTION_SERVICE] MetaGPT 실행 완료: {execution_id}")

        except Exception as e:
            error_msg = f'MetaGPT 백그라운드 실행 중 오류: {str(e)}'
            print(f"[EXECUTION_SERVICE ERROR] {error_msg}")
            execution_status[execution_id] = {'status': 'failed', 'message': error_msg}

    threading.Thread(target=run_in_background, daemon=True).start()
    return True