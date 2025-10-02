#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 관리자
CrewAI 도구 및 MCP 서버 통합 관리 시스템
"""

import json
import os
from typing import List, Dict, Optional

class MCPManager:
    """MCP 및 CrewAI 도구 관리 클래스"""

    def __init__(self, registry_file: str = "mcp_registry.json"):
        """
        MCP Manager 초기화

        Args:
            registry_file: MCP 레지스트리 JSON 파일 경로
        """
        registry_path = os.path.join(os.path.dirname(__file__), registry_file)
        with open(registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

    def get_available_mcps(self, category: Optional[str] = None) -> Dict:
        """
        사용 가능한 MCP/도구 목록 반환

        Args:
            category: 필터링할 카테고리 (search, knowledge, media, file)

        Returns:
            MCP/도구 딕셔너리
        """
        if category:
            return {k: v for k, v in self.registry.items()
                   if v.get('category') == category}
        return self.registry

    def generate_tool_imports(self, selected_tools: List[str]) -> str:
        """
        선택된 도구들의 import 문 생성

        Args:
            selected_tools: 선택된 도구 ID 리스트

        Returns:
            import 문 문자열
        """
        imports = set()

        for tool_id in selected_tools:
            tool = self.registry.get(tool_id)
            if not tool:
                continue

            tool_type = tool.get('type')
            config = tool.get('config', {})

            # 기본 도구 import
            import_from = config.get('import_from')
            tool_class = config.get('tool_class')
            if import_from and tool_class:
                imports.add(f"from {import_from} import {tool_class}")

            # MCP 서버의 경우 추가 import
            if tool_type == 'mcp_server':
                adapter_import = config.get('adapter_import')
                mcp_import = config.get('mcp_import')
                if adapter_import:
                    imports.add(adapter_import)
                if mcp_import:
                    imports.add(mcp_import)

        return "\n".join(sorted(imports))

    def generate_tool_initialization(self, selected_tools: List[str],
                                    api_keys: Dict[str, str] = None) -> str:
        """
        선택된 도구들의 초기화 코드 생성

        Args:
            selected_tools: 선택된 도구 ID 리스트
            api_keys: 도구별 API 키 딕셔너리

        Returns:
            초기화 코드 문자열
        """
        if api_keys is None:
            api_keys = {}

        init_code = []

        for tool_id in selected_tools:
            tool = self.registry.get(tool_id)
            if not tool:
                continue

            tool_type = tool.get('type')
            config = tool.get('config', {})
            tool_name = tool.get('name', tool_id)

            if tool_type == 'serper_tool':
                # SerperDevTool 초기화
                params = config.get('init_params', {})
                params_str = ', '.join([f"{k}='{v}'" if isinstance(v, str)
                                       else f"{k}={v}"
                                       for k, v in params.items()])

                # 환경변수 설정 체크
                env_vars = config.get('env_vars', [])
                env_check = ""
                if env_vars:
                    api_key = api_keys.get(tool_id)
                    if api_key:
                        env_check = f"\nos.environ['{env_vars[0]}'] = '{api_key}'"

                init_code.append(f"""
# {tool_name} 초기화{env_check}
{tool_id}_tool = {config['tool_class']}({params_str})
print(f"✅ {tool_name} 초기화 완료")
""")

            elif tool_type == 'mcp_server':
                # MCP Server 초기화
                env_vars = config.get('env_vars', [])
                api_key_var = env_vars[0] if env_vars else 'SERPER_API_KEY'
                api_key = api_keys.get(tool_id, f'os.getenv("{api_key_var}")')

                # API 키가 문자열로 직접 제공된 경우
                if api_keys.get(tool_id):
                    env_setup = f'os.environ["{api_key_var}"] = "{api_keys.get(tool_id)}"'
                else:
                    env_setup = f'# {api_key_var}는 환경변수에서 가져옴'

                init_code.append(f"""
# {tool_name} MCP Server 초기화
{env_setup}
{tool_id}_params = StdioServerParameters(
    command="{config['command']}",
    args={config['args']},
    env={{"{api_key_var}": os.getenv("{api_key_var}")}}
)
{tool_id}_adapter = MCPServerAdapter({tool_id}_params, connect_timeout=60)
{tool_id}_tools = {tool_id}_adapter.__enter__()
print(f"✅ {tool_name} MCP Server 연결 완료")
""")

            elif tool_type == 'builtin_tool':
                # 내장 도구 초기화
                env_vars = config.get('env_vars', [])
                env_check = ""

                # API 키가 필요한 경우 (예: DALL-E)
                if env_vars:
                    api_key = api_keys.get(tool_id)
                    if api_key:
                        env_check = f"\nos.environ['{env_vars[0]}'] = '{api_key}'"

                init_code.append(f"""
# {tool_name} 초기화{env_check}
{tool_id}_tool = {config['tool_class']}()
print(f"✅ {tool_name} 초기화 완료")
""")

        return "\n".join(init_code)

    def get_agent_tools_list(self, selected_tools: List[str]) -> str:
        """
        에이전트에 할당할 도구 리스트 생성

        Args:
            selected_tools: 선택된 도구 ID 리스트

        Returns:
            tools 파라미터 문자열 (예: "tools=[news_search_tool, wikipedia_tool]")
        """
        if not selected_tools:
            return ""

        tool_refs = []
        for tool_id in selected_tools:
            tool = self.registry.get(tool_id)
            if not tool:
                continue

            if tool.get('type') == 'mcp_server':
                # MCP 서버는 tools 객체 사용
                tool_refs.append(f"*{tool_id}_tools")  # * 로 unpack
            else:
                # 일반 도구는 tool 객체 사용
                tool_refs.append(f"{tool_id}_tool")

        if tool_refs:
            return f"tools=[{', '.join(tool_refs)}]"
        return ""

    def get_tool_names(self, selected_tools: List[str]) -> List[str]:
        """
        선택된 도구들의 이름 리스트 반환

        Args:
            selected_tools: 선택된 도구 ID 리스트

        Returns:
            도구 이름 리스트
        """
        names = []
        for tool_id in selected_tools:
            tool = self.registry.get(tool_id)
            if tool:
                names.append(tool.get('name', tool_id))
        return names
