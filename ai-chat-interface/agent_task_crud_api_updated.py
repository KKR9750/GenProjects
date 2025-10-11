"""
Agent/Task CRUD API (Tools 지원 추가)
프로젝트의 Agent와 Task를 생성, 수정, 삭제하는 API
"""
from flask import Blueprint, request, jsonify
from database import get_db_connection
from typing import Dict
import json

agent_task_bp = Blueprint('agent_task', __name__)


@agent_task_bp.route('/api/v2/projects/<project_id>/agents', methods=['GET'])
def list_agents(project_id: str):
    """특정 프로젝트의 Agent 목록 조회 (tools 포함)"""
    conn = None
    cursor = None

    try:
        framework = request.args.get('framework', 'crewai')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                project_id,
                framework,
                agent_order,
                role,
                goal,
                backstory,
                llm_model,
                is_verbose,
                allow_delegation,
                tools,
                tool_config,
                is_active,
                created_at,
                updated_at
            FROM project_agents
            WHERE project_id = %s
              AND framework = %s
              AND COALESCE(is_active, TRUE)
            ORDER BY agent_order
            """,
            (project_id, framework)
        )

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        agents = [dict(zip(columns, row)) for row in rows]

        cursor.close()
        conn.close()

        return jsonify({'agents': agents}), 200

    except Exception as e:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500


# ============================================
# Agent CRUD
# ============================================

@agent_task_bp.route('/api/v2/projects/<project_id>/agents', methods=['POST'])
def create_agent(project_id: str):
    """
    Agent 생성 (tools 지원)

    Request Body:
    {
        "framework": "crewai",
        "agentOrder": 4,
        "role": "Reviewer",
        "goal": "...",
        "backstory": "...",
        "llmModel": "gemini-2.0-flash-exp",
        "isVerbose": true,
        "allowDelegation": false,
        "tools": ["file_write", "web_search"],  // NEW
        "toolConfig": {"file_write": {}, "web_search": {"api_key": "..."}}  // NEW
    }
    """
    try:
        data = request.get_json()

        framework = data.get('framework', 'crewai')
        agent_order = data.get('agentOrder')
        role = data.get('role')
        goal = data.get('goal')
        backstory = data.get('backstory')
        llm_model = data.get('llmModel', 'gemini-2.0-flash-exp')
        is_verbose = data.get('isVerbose', True)
        allow_delegation = data.get('allowDelegation', False)
        tools = data.get('tools', [])  # NEW
        tool_config = data.get('toolConfig', {})  # NEW

        # 검증
        if not all([agent_order, role, goal, backstory]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_agents (
                project_id,
                framework,
                agent_order,
                role,
                goal,
                backstory,
                llm_model,
                is_verbose,
                allow_delegation,
                tools,
                tool_config
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            project_id,
            framework,
            agent_order,
            role,
            goal,
            backstory,
            llm_model,
            is_verbose,
            allow_delegation,
            tools,  # NEW
            json.dumps(tool_config) if tool_config else '{}'  # NEW
        ))

        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        agent = dict(zip(columns, row))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'agent': agent}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_task_bp.route('/api/v2/projects/<project_id>/agents/<int:agent_order>', methods=['PUT'])
def update_agent(project_id: str, agent_order: int):
    """
    Agent 수정 (tools 지원)

    Request Body:
    {
        "framework": "crewai",
        "role": "Updated Role",
        "goal": "...",
        "backstory": "...",
        "llmModel": "gpt-4",
        "isVerbose": false,
        "allowDelegation": true,
        "tools": ["file_write"],  // NEW
        "toolConfig": {"file_write": {}}  // NEW
    }
    """
    try:
        data = request.get_json()
        framework = data.get('framework', 'crewai')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 업데이트할 필드 동적 생성
        update_fields = []
        params = []

        if 'role' in data:
            update_fields.append("role = %s")
            params.append(data['role'])
        if 'goal' in data:
            update_fields.append("goal = %s")
            params.append(data['goal'])
        if 'backstory' in data:
            update_fields.append("backstory = %s")
            params.append(data['backstory'])
        if 'llmModel' in data:
            update_fields.append("llm_model = %s")
            params.append(data['llmModel'])
        if 'isVerbose' in data:
            update_fields.append("is_verbose = %s")
            params.append(data['isVerbose'])
        if 'allowDelegation' in data:
            update_fields.append("allow_delegation = %s")
            params.append(data['allowDelegation'])
        # NEW: tools 필드
        if 'tools' in data:
            update_fields.append("tools = %s")
            params.append(data['tools'])
        # NEW: toolConfig 필드
        if 'toolConfig' in data:
            update_fields.append("tool_config = %s")
            params.append(json.dumps(data['toolConfig']))

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        # WHERE 조건용 파라미터
        params.extend([project_id, framework, agent_order])

        query = f"""
            UPDATE project_agents
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE project_id = %s AND framework = %s AND agent_order = %s
            RETURNING *
        """

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Agent not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        agent = dict(zip(columns, row))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'agent': agent}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_task_bp.route('/api/v2/projects/<project_id>/agents/<int:agent_order>', methods=['DELETE'])
def delete_agent(project_id: str, agent_order: int):
    """Agent 삭제 (soft delete)"""
    try:
        framework = request.args.get('framework', 'crewai')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_agents
            SET is_active = false, updated_at = NOW()
            WHERE project_id = %s AND framework = %s AND agent_order = %s
            RETURNING agent_order, role
        """, (project_id, framework, agent_order))

        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Agent not found'}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Agent deleted successfully',
            'agent_order': row[0],
            'role': row[1]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Task CRUD (변경 없음)
# ============================================

@agent_task_bp.route('/api/v2/projects/<project_id>/tasks', methods=['POST'])
def create_task(project_id: str):
    """
    Task 생성

    Request Body:
    {
        "framework": "crewai",
        "taskOrder": 4,
        "taskType": "review",
        "description": "...",
        "expectedOutput": "...",
        "agentOrder": 3,
        "dependsOnTaskOrder": 3
    }
    """
    try:
        data = request.get_json()

        framework = data.get('framework', 'crewai')
        task_order = data.get('taskOrder')
        task_type = data.get('taskType')
        description = data.get('description')
        expected_output = data.get('expectedOutput')
        agent_order = data.get('agentOrder')
        depends_on_task_order = data.get('dependsOnTaskOrder')

        # 검증
        if not all([task_order, description, expected_output]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO project_tasks (
                project_id,
                framework,
                task_order,
                task_type,
                description,
                expected_output,
                agent_project_id,
                agent_framework,
                agent_order,
                depends_on_project_id,
                depends_on_framework,
                depends_on_task_order
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            project_id,
            framework,
            task_order,
            task_type,
            description,
            expected_output,
            project_id if agent_order else None,
            framework if agent_order else None,
            agent_order,
            project_id if depends_on_task_order else None,
            framework if depends_on_task_order else None,
            depends_on_task_order
        ))

        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        task = dict(zip(columns, row))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'task': task}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_task_bp.route('/api/v2/projects/<project_id>/tasks/<int:task_order>', methods=['PUT'])
def update_task(project_id: str, task_order: int):
    """
    Task 수정

    Request Body:
    {
        "framework": "crewai",
        "taskType": "implementation",
        "description": "...",
        "expectedOutput": "...",
        "agentOrder": 2,
        "dependsOnTaskOrder": 1
    }
    """
    try:
        data = request.get_json()
        framework = data.get('framework', 'crewai')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 업데이트할 필드 동적 생성
        update_fields = []
        params = []

        if 'taskType' in data:
            update_fields.append("task_type = %s")
            params.append(data['taskType'])
        if 'description' in data:
            update_fields.append("description = %s")
            params.append(data['description'])
        if 'expectedOutput' in data:
            update_fields.append("expected_output = %s")
            params.append(data['expectedOutput'])
        if 'agentOrder' in data:
            update_fields.append("agent_project_id = %s")
            params.append(project_id)
            update_fields.append("agent_framework = %s")
            params.append(framework)
            update_fields.append("agent_order = %s")
            params.append(data['agentOrder'])
        if 'dependsOnTaskOrder' in data:
            if data['dependsOnTaskOrder']:
                update_fields.append("depends_on_project_id = %s")
                params.append(project_id)
                update_fields.append("depends_on_framework = %s")
                params.append(framework)
                update_fields.append("depends_on_task_order = %s")
                params.append(data['dependsOnTaskOrder'])
            else:
                update_fields.append("depends_on_project_id = NULL")
                update_fields.append("depends_on_framework = NULL")
                update_fields.append("depends_on_task_order = NULL")

        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400

        # WHERE 조건용 파라미터
        params.extend([project_id, framework, task_order])

        query = f"""
            UPDATE project_tasks
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE project_id = %s AND framework = %s AND task_order = %s
            RETURNING *
        """

        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Task not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        task = dict(zip(columns, row))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'task': task}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@agent_task_bp.route('/api/v2/projects/<project_id>/tasks/<int:task_order>', methods=['DELETE'])
def delete_task(project_id: str, task_order: int):
    """Task 삭제 (soft delete)"""
    try:
        framework = request.args.get('framework', 'crewai')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE project_tasks
            SET is_active = false, updated_at = NOW()
            WHERE project_id = %s AND framework = %s AND task_order = %s
            RETURNING task_order, task_type, description
        """, (project_id, framework, task_order))

        row = cursor.fetchone()

        if not row:
            return jsonify({'error': 'Task not found'}), 404

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Task deleted successfully',
            'task_order': row[0],
            'task_type': row[1],
            'description': row[2]
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
