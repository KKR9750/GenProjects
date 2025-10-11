"""
동적 스크립트 생성 엔진
DB에서 Agent/Task를 읽어 Jinja2 템플릿으로 실행 스크립트를 생성
"""
import os
import json
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
from database import get_supabase_client

class DynamicScriptGenerator:
    """DB 기반 동적 스크립트 생성기"""

    def __init__(self):
        # Jinja2 환경 설정
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'scripts')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # MCP 레지스트리 로드
        self.mcp_registry = self.load_mcp_registry()

    def load_mcp_registry(self) -> Dict:
        """MCP 레지스트리 파일 로드"""
        registry_path = os.path.join(os.path.dirname(__file__), 'mcp_registry.json')
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to load MCP registry: {e}")
            return {}

    def get_project_agents(self, project_id: str, framework: str) -> List[Dict]:
        """프로젝트의 Agent 목록 조회 (Supabase)"""
        supabase = get_supabase_client()

        result = supabase.table('project_agents')\
            .select('*')\
            .eq('project_id', project_id)\
            .eq('framework', framework)\
            .eq('is_active', True)\
            .order('agent_order')\
            .execute()

        return result.data

    def get_project_tasks(self, project_id: str, framework: str) -> List[Dict]:
        """프로젝트의 Task 목록 조회 (Supabase)"""
        supabase = get_supabase_client()

        result = supabase.table('project_tasks')\
            .select('*, project_agents!project_tasks_agent_project_id_agent_framework_agent_order_fkey(role)')\
            .eq('project_id', project_id)\
            .eq('framework', framework)\
            .eq('is_active', True)\
            .order('task_order')\
            .execute()

        # Agent role 추가
        tasks = []
        for task in result.data:
            agent_role = None
            if task.get('project_agents'):
                agent_role = task['project_agents'].get('role')

            task_data = {
                'project_id': task.get('project_id'),
                'framework': task.get('framework'),
                'task_order': task.get('task_order'),
                'task_type': task.get('task_type'),
                'description': task.get('description'),
                'expected_output': task.get('expected_output'),
                'agent_order': task.get('agent_order'),
                'depends_on_task_order': task.get('depends_on_task_order'),
                'agent_role': agent_role
            }
            tasks.append(task_data)

        return tasks

    def get_project_info(self, project_id: str) -> Optional[Dict]:
        """프로젝트 기본 정보 조회 (Supabase)"""
        supabase = get_supabase_client()

        result = supabase.table('projects')\
            .select('project_id, name, framework, final_requirement, status')\
            .eq('project_id', project_id)\
            .limit(1)\
            .execute()

        if not result.data:
            return None

        project = result.data[0]
        # 'name' 필드를 'project_name'으로 매핑 (호환성)
        return {
            'project_id': project.get('project_id'),
            'project_name': project.get('name'),
            'framework': project.get('framework'),
            'final_requirement': project.get('final_requirement'),
            'status': project.get('status')
        }

    def generate_crewai_script(self, project_id: str) -> str:
        """CrewAI 실행 스크립트 생성"""
        # 프로젝트 정보 조회
        project = self.get_project_info(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if project['framework'] != 'crewai':
            raise ValueError(f"Project {project_id} is not a CrewAI project")

        # Agent 및 Task 조회
        agents = self.get_project_agents(project_id, 'crewai')
        tasks = self.get_project_tasks(project_id, 'crewai')

        # Agent들에서 선택된 도구 수집 (중복 제거)
        selected_tools = set()
        for agent in agents:
            agent_tools = agent.get('tools', [])
            if agent_tools:
                selected_tools.update(agent_tools)

        # Jinja2 템플릿 렌더링
        template = self.env.get_template('crewai_dynamic.py.j2')
        script = template.render(
            project=project,
            agents=agents,
            tasks=tasks,
            mcp_registry=self.mcp_registry,
            selected_tools=list(selected_tools)
        )

        return script

    def generate_metagpt_script(self, project_id: str) -> str:
        """MetaGPT 실행 스크립트 생성"""
        # 프로젝트 정보 조회
        project = self.get_project_info(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        if project['framework'] != 'metagpt':
            raise ValueError(f"Project {project_id} is not a MetaGPT project")

        # Agent 및 Task 조회
        agents = self.get_project_agents(project_id, 'metagpt')
        tasks = self.get_project_tasks(project_id, 'metagpt')

        # Jinja2 템플릿 렌더링
        template = self.env.get_template('metagpt_dynamic.py.j2')
        script = template.render(
            project=project,
            agents=agents,
            tasks=tasks
        )

        return script

    def generate_readme(self, project: Dict, agents: List[Dict], tasks: List[Dict]) -> str:
        """README.md 생성"""
        template = self.env.get_template('README.md.j2')
        readme = template.render(project=project, agents=agents, tasks=tasks)
        return readme

    def generate_requirements(self, agents: List[Dict]) -> str:
        """requirements.txt 생성 (사용된 LLM 기반)"""
        # 사용된 LLM 모델 파악
        llm_providers = set()
        for agent in agents:
            model = agent.get('llm_model', '')
            if model.startswith('gpt'):
                llm_providers.add('openai')
            elif model.startswith('gemini'):
                llm_providers.add('google-genai')
            elif model.startswith('claude'):
                llm_providers.add('anthropic')
            elif model.startswith('deepseek'):
                llm_providers.add('openai')  # DeepSeek uses OpenAI-compatible API

        # 기본 패키지
        packages = [
            'crewai>=0.28.0',
            'python-dotenv>=1.0.0'
        ]

        # LLM별 패키지 추가
        if 'openai' in llm_providers:
            packages.append('langchain-openai>=0.0.5')
        if 'google-genai' in llm_providers:
            packages.append('langchain-google-genai>=0.0.11')
        if 'anthropic' in llm_providers:
            packages.append('langchain-anthropic>=0.1.0')

        return '\n'.join(packages) + '\n'

    def save_all_project_files(self, project_id: str, script_content: str,
                               readme_content: str, requirements_content: str,
                               framework: str) -> Dict[str, str]:
        """스크립트, README, requirements 모두 저장"""
        # 프로젝트 디렉토리 생성
        project_dir = os.path.join(os.path.dirname(__file__), '..', 'Projects', project_id)
        os.makedirs(project_dir, exist_ok=True)

        # 1. 스크립트 저장
        script_filename = f"{framework}_script.py"
        script_path = os.path.join(project_dir, script_filename)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 2. README 저장
        readme_path = os.path.join(project_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        # 3. requirements.txt 저장
        requirements_path = os.path.join(project_dir, 'requirements.txt')
        with open(requirements_path, 'w', encoding='utf-8') as f:
            f.write(requirements_content)

        return {
            'script_path': script_path,
            'readme_path': readme_path,
            'requirements_path': requirements_path
        }

    def save_script_to_file(self, project_id: str, script_content: str, framework: str) -> str:
        """생성된 스크립트를 파일로 저장 (레거시 호환성)"""
        # 프로젝트 디렉토리 생성
        project_dir = os.path.join(os.path.dirname(__file__), '..', 'Projects', project_id)
        os.makedirs(project_dir, exist_ok=True)

        # 스크립트 파일 저장
        script_filename = f"{framework}_script.py"
        script_path = os.path.join(project_dir, script_filename)

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        return script_path

    def generate_and_save(self, project_id: str) -> Dict[str, str]:
        """스크립트 + README + requirements 생성 및 저장 (통합 메서드)"""
        # 1. 프로젝트 정보 조회
        project = self.get_project_info(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        framework = project['framework']

        # 2. Agent 및 Task 조회 (README 생성용)
        agents = self.get_project_agents(project_id, framework)
        tasks = self.get_project_tasks(project_id, framework)

        # 3. 프레임워크별 스크립트 생성
        if framework == 'crewai':
            script_content = self.generate_crewai_script(project_id)
        elif framework == 'metagpt':
            script_content = self.generate_metagpt_script(project_id)
        else:
            raise ValueError(f"Unsupported framework: {framework}")

        # 4. README 생성
        readme_content = self.generate_readme(project, agents, tasks)

        # 5. requirements.txt 생성
        requirements_content = self.generate_requirements(agents)

        # 6. 모든 파일 저장
        paths = self.save_all_project_files(
            project_id, script_content, readme_content,
            requirements_content, framework
        )

        return {
            'project_id': project_id,
            'framework': framework,
            'status': 'success',
            **paths  # script_path, readme_path, requirements_path 포함
        }


# 편의 함수
def generate_script(project_id: str) -> Dict[str, str]:
    """프로젝트 스크립트 생성 (단일 진입점)"""
    generator = DynamicScriptGenerator()
    return generator.generate_and_save(project_id)


if __name__ == '__main__':
    # 테스트 코드
    import sys
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        result = generate_script(project_id)
        print(f"Script generated: {result['script_path']}")
    else:
        print("Usage: python dynamic_script_generator.py <project_id>")
