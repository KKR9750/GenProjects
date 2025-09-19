# -*- coding: utf-8 -*-
"""
Ollama Local LLM Client
로컬 Ollama 서비스와의 통신을 위한 클라이언트
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime

class OllamaClient:
    """Ollama 로컬 LLM 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"

    def is_available(self) -> bool:
        """Ollama 서비스 가용성 확인"""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_models(self) -> Dict[str, Any]:
        """사용 가능한 모델 목록 조회"""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = []

                for model in data.get('models', []):
                    model_info = {
                        'id': model['name'],
                        'name': model['name'],
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at', ''),
                        'parameter_size': model.get('details', {}).get('parameter_size', 'Unknown'),
                        'family': model.get('details', {}).get('family', 'Unknown'),
                        'quantization': model.get('details', {}).get('quantization_level', 'Unknown'),
                        'provider': 'Ollama (Local)'
                    }
                    models.append(model_info)

                return {
                    'success': True,
                    'models': models,
                    'count': len(models),
                    'service': 'Ollama Local'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ollama API 오류: {response.status_code}',
                    'models': []
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama 연결 실패: {str(e)}',
                'models': []
            }

    def generate_completion(self, model: str, prompt: str, system: str = None,
                          temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """단일 완성 생성"""
        try:
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }

            if system:
                payload['system'] = system

            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response': data.get('response', ''),
                    'model': model,
                    'done': data.get('done', True),
                    'total_duration': data.get('total_duration', 0),
                    'load_duration': data.get('load_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0),
                    'provider': 'Ollama (Local)'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ollama 생성 오류: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama 완성 생성 실패: {str(e)}'
            }

    def generate_stream(self, model: str, prompt: str, system: str = None,
                       temperature: float = 0.7, max_tokens: int = 1000) -> Generator[Dict[str, Any], None, None]:
        """스트리밍 완성 생성"""
        try:
            payload = {
                'model': model,
                'prompt': prompt,
                'stream': True,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }

            if system:
                payload['system'] = system

            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                stream=True,
                timeout=60
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            yield {
                                'success': True,
                                'response': data.get('response', ''),
                                'done': data.get('done', False),
                                'model': model,
                                'provider': 'Ollama (Local)'
                            }

                            if data.get('done', False):
                                break

                        except json.JSONDecodeError:
                            continue
            else:
                yield {
                    'success': False,
                    'error': f'Ollama 스트림 오류: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            yield {
                'success': False,
                'error': f'Ollama 스트림 생성 실패: {str(e)}'
            }

    def chat_completion(self, model: str, messages: List[Dict[str, str]],
                       temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """채팅 완성 생성"""
        try:
            payload = {
                'model': model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            }

            response = requests.post(
                f"{self.api_url}/chat",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})

                return {
                    'success': True,
                    'message': {
                        'role': message.get('role', 'assistant'),
                        'content': message.get('content', '')
                    },
                    'model': model,
                    'done': data.get('done', True),
                    'total_duration': data.get('total_duration', 0),
                    'load_duration': data.get('load_duration', 0),
                    'prompt_eval_count': data.get('prompt_eval_count', 0),
                    'eval_count': data.get('eval_count', 0),
                    'provider': 'Ollama (Local)'
                }
            else:
                return {
                    'success': False,
                    'error': f'Ollama 채팅 오류: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama 채팅 완성 실패: {str(e)}'
            }

    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """모델 다운로드"""
        try:
            response = requests.post(
                f"{self.api_url}/pull",
                json={'name': model_name},
                timeout=300  # 5분 타임아웃
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'모델 {model_name} 다운로드 완료',
                    'model': model_name
                }
            else:
                return {
                    'success': False,
                    'error': f'모델 다운로드 실패: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'모델 다운로드 오류: {str(e)}'
            }

    def delete_model(self, model_name: str) -> Dict[str, Any]:
        """모델 삭제"""
        try:
            response = requests.delete(
                f"{self.api_url}/delete",
                json={'name': model_name},
                timeout=30
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'모델 {model_name} 삭제 완료',
                    'model': model_name
                }
            else:
                return {
                    'success': False,
                    'error': f'모델 삭제 실패: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'모델 삭제 오류: {str(e)}'
            }

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """특정 모델 정보 조회"""
        try:
            response = requests.post(
                f"{self.api_url}/show",
                json={'name': model_name},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'model': model_name,
                    'modelfile': data.get('modelfile', ''),
                    'parameters': data.get('parameters', ''),
                    'template': data.get('template', ''),
                    'details': data.get('details', {}),
                    'provider': 'Ollama (Local)'
                }
            else:
                return {
                    'success': False,
                    'error': f'모델 정보 조회 실패: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'모델 정보 조회 오류: {str(e)}'
            }

# 전역 Ollama 클라이언트 인스턴스
ollama_client = OllamaClient()