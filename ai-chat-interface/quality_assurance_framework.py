#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
품질 보증 프레임워크
생성된 CrewAI 스크립트의 품질을 6단계로 검증하고 개선사항을 제안
"""

import ast
import re
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class QualityLevel(Enum):
    EXCELLENT = "excellent"      # 90-100점
    GOOD = "good"               # 75-89점
    SATISFACTORY = "satisfactory"  # 60-74점
    POOR = "poor"               # 40-59점
    CRITICAL = "critical"       # 0-39점

@dataclass
class QualityIssue:
    """품질 이슈"""
    category: str
    severity: str      # critical, high, medium, low
    description: str
    suggestion: str
    line_number: Optional[int] = None

@dataclass
class QualityReport:
    """품질 보고서"""
    overall_score: float
    quality_level: QualityLevel
    stage_scores: Dict[str, float]
    issues: List[QualityIssue]
    passed_checks: List[str]
    recommendations: List[str]
    is_production_ready: bool

class QualityAssuranceFramework:
    """품질 보증 프레임워크"""

    def __init__(self):
        self.quality_thresholds = {
            'syntax': 0.95,        # 구문 오류는 거의 허용하지 않음
            'logic': 0.75,         # 로직 완성도
            'requirements': 0.80,   # 요구사항 반영도
            'execution': 0.85,     # 실행 가능성
            'security': 0.90,      # 보안
            'performance': 0.70    # 성능
        }

    def assess_quality(self, script_content: str, requirement: str,
                      project_path: str) -> QualityReport:
        """종합 품질 평가"""

        issues = []
        passed_checks = []
        stage_scores = {}

        # Stage 1: 구문 및 문법 검사
        syntax_score, syntax_issues, syntax_passed = self._check_syntax(script_content)
        stage_scores['syntax'] = syntax_score
        issues.extend(syntax_issues)
        passed_checks.extend(syntax_passed)

        # Stage 2: 로직 완성도 검증
        logic_score, logic_issues, logic_passed = self._check_logic_completeness(script_content)
        stage_scores['logic'] = logic_score
        issues.extend(logic_issues)
        passed_checks.extend(logic_passed)

        # Stage 3: 요구사항 반영도 평가
        req_score, req_issues, req_passed = self._check_requirements_coverage(script_content, requirement)
        stage_scores['requirements'] = req_score
        issues.extend(req_issues)
        passed_checks.extend(req_passed)

        # Stage 4: 실행 가능성 시뮬레이션
        exec_score, exec_issues, exec_passed = self._check_execution_readiness(script_content, project_path)
        stage_scores['execution'] = exec_score
        issues.extend(exec_issues)
        passed_checks.extend(exec_passed)

        # Stage 5: 보안 검토
        sec_score, sec_issues, sec_passed = self._check_security(script_content)
        stage_scores['security'] = sec_score
        issues.extend(sec_issues)
        passed_checks.extend(sec_passed)

        # Stage 6: 성능 검토
        perf_score, perf_issues, perf_passed = self._check_performance(script_content)
        stage_scores['performance'] = perf_score
        issues.extend(perf_issues)
        passed_checks.extend(perf_passed)

        # 종합 점수 계산
        overall_score = self._calculate_overall_score(stage_scores)
        quality_level = self._determine_quality_level(overall_score)

        # 추천사항 생성
        recommendations = self._generate_recommendations(stage_scores, issues)

        # 프로덕션 준비 여부
        is_production_ready = self._assess_production_readiness(stage_scores, issues)

        return QualityReport(
            overall_score=overall_score,
            quality_level=quality_level,
            stage_scores=stage_scores,
            issues=issues,
            passed_checks=passed_checks,
            recommendations=recommendations,
            is_production_ready=is_production_ready
        )

    def _check_syntax(self, script_content: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 1: 구문 및 문법 검사"""
        issues = []
        passed_checks = []
        score = 1.0

        try:
            # Python AST 파싱
            ast.parse(script_content)
            passed_checks.append("Python 구문 검사 통과")
        except SyntaxError as e:
            issues.append(QualityIssue(
                category="syntax",
                severity="critical",
                description=f"구문 오류: {e.msg}",
                suggestion="Python 구문을 수정하세요",
                line_number=e.lineno
            ))
            score -= 0.5

        # 들여쓰기 일관성 검사
        lines = script_content.split('\n')
        indentation_issues = self._check_indentation_consistency(lines)
        if indentation_issues:
            for issue in indentation_issues:
                issues.append(issue)
                score -= 0.1
        else:
            passed_checks.append("들여쓰기 일관성 검사 통과")

        # 기본 코딩 컨벤션 검사
        convention_issues = self._check_coding_conventions(script_content)
        if convention_issues:
            issues.extend(convention_issues)
            score -= len(convention_issues) * 0.05
        else:
            passed_checks.append("기본 코딩 컨벤션 검사 통과")

        # UTF-8 인코딩 검사
        if 'utf-8' in script_content:
            passed_checks.append("UTF-8 인코딩 지원 확인")
        else:
            issues.append(QualityIssue(
                category="syntax",
                severity="medium",
                description="UTF-8 인코딩 선언이 없습니다",
                suggestion="파일 상단에 # -*- coding: utf-8 -*- 추가"
            ))
            score -= 0.1

        return max(score, 0.0), issues, passed_checks

    def _check_indentation_consistency(self, lines: List[str]) -> List[QualityIssue]:
        """들여쓰기 일관성 검사"""
        issues = []
        tab_count = 0
        space_count = 0

        for i, line in enumerate(lines, 1):
            if line.strip():  # 빈 줄이 아닌 경우
                if line.startswith('\t'):
                    tab_count += 1
                elif line.startswith('    '):
                    space_count += 1

        # 탭과 스페이스가 섞여 있는 경우
        if tab_count > 0 and space_count > 0:
            issues.append(QualityIssue(
                category="syntax",
                severity="medium",
                description="탭과 스페이스가 혼용되어 있습니다",
                suggestion="일관된 들여쓰기(스페이스 4칸 권장) 사용"
            ))

        return issues

    def _check_coding_conventions(self, script_content: str) -> List[QualityIssue]:
        """기본 코딩 컨벤션 검사"""
        issues = []

        # 함수명 컨벤션 (snake_case)
        function_pattern = r'def\s+([A-Z][a-zA-Z0-9_]*)\s*\('
        if re.search(function_pattern, script_content):
            issues.append(QualityIssue(
                category="syntax",
                severity="low",
                description="함수명이 PascalCase로 되어 있습니다",
                suggestion="함수명은 snake_case 사용 권장 (예: get_data)"
            ))

        # 긴 줄 검사 (120자 초과)
        lines = script_content.split('\n')
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > 120]
        if long_lines:
            issues.append(QualityIssue(
                category="syntax",
                severity="low",
                description=f"긴 줄이 {len(long_lines)}개 발견됨 (120자 초과)",
                suggestion="긴 줄을 여러 줄로 분할하세요"
            ))

        return issues

    def _check_logic_completeness(self, script_content: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 2: 로직 완성도 검증"""
        issues = []
        passed_checks = []
        score = 1.0

        # CrewAI 필수 요소 검사
        required_elements = {
            'Agent(': 'CrewAI Agent 정의',
            'Task(': 'CrewAI Task 정의',
            'Crew(': 'CrewAI Crew 생성',
            'kickoff()': 'Crew 실행 로직',
            'if __name__ == "__main__"': 'main 실행 블록'
        }

        for element, description in required_elements.items():
            if element in script_content:
                passed_checks.append(f"{description} 확인")
            else:
                issues.append(QualityIssue(
                    category="logic",
                    severity="critical",
                    description=f"{description}가 누락되었습니다",
                    suggestion=f"{element} 요소를 추가하세요"
                ))
                score -= 0.3

        # 에이전트-태스크 매핑 검사
        agent_count = script_content.count('Agent(')
        task_count = script_content.count('Task(')

        if agent_count > 0 and task_count > 0:
            if abs(agent_count - task_count) <= 1:  # 거의 같아야 함
                passed_checks.append("에이전트-태스크 균형 확인")
            else:
                issues.append(QualityIssue(
                    category="logic",
                    severity="high",
                    description=f"에이전트({agent_count})와 태스크({task_count}) 수 불균형",
                    suggestion="각 에이전트마다 전담 태스크를 할당하세요"
                ))
                score -= 0.2

        # 예외 처리 검사
        if 'try:' in script_content and 'except' in script_content:
            passed_checks.append("예외 처리 구현 확인")
        else:
            issues.append(QualityIssue(
                category="logic",
                severity="high",
                description="예외 처리가 구현되지 않았습니다",
                suggestion="try-except 블록으로 예외 처리 추가"
            ))
            score -= 0.2

        # 출력 처리 검사
        output_patterns = ['output', 'save', 'write', 'result']
        has_output = any(pattern in script_content.lower() for pattern in output_patterns)

        if has_output:
            passed_checks.append("결과 출력 처리 확인")
        else:
            issues.append(QualityIssue(
                category="logic",
                severity="medium",
                description="결과 출력 처리가 명확하지 않습니다",
                suggestion="결과를 파일로 저장하는 로직 추가"
            ))
            score -= 0.15

        return max(score, 0.0), issues, passed_checks

    def _check_requirements_coverage(self, script_content: str, requirement: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 3: 요구사항 반영도 평가"""
        issues = []
        passed_checks = []
        score = 1.0

        # 요구사항 키워드 추출
        req_keywords = self._extract_requirement_keywords(requirement)

        # 키워드 매칭 검사
        matched_keywords = 0
        for keyword in req_keywords:
            if keyword.lower() in script_content.lower():
                matched_keywords += 1

        coverage_ratio = matched_keywords / len(req_keywords) if req_keywords else 1.0

        if coverage_ratio >= 0.8:
            passed_checks.append(f"요구사항 키워드 {coverage_ratio:.1%} 반영")
        elif coverage_ratio >= 0.6:
            issues.append(QualityIssue(
                category="requirements",
                severity="medium",
                description=f"요구사항 반영도가 {coverage_ratio:.1%}로 보통 수준입니다",
                suggestion="누락된 요구사항 키워드를 태스크 설명에 추가하세요"
            ))
            score -= 0.2
        else:
            issues.append(QualityIssue(
                category="requirements",
                severity="high",
                description=f"요구사항 반영도가 {coverage_ratio:.1%}로 낮습니다",
                suggestion="요구사항을 더 구체적으로 태스크에 반영하세요"
            ))
            score -= 0.4

        # 구체적 기능 반영 검사
        specific_features = self._identify_specific_features(requirement)
        implemented_features = 0

        for feature in specific_features:
            if self._check_feature_implementation(feature, script_content):
                implemented_features += 1
                passed_checks.append(f"{feature} 기능 구현 확인")
            else:
                issues.append(QualityIssue(
                    category="requirements",
                    severity="medium",
                    description=f"{feature} 기능이 명확히 구현되지 않았습니다",
                    suggestion=f"{feature}을 처리하는 에이전트나 태스크 추가"
                ))
                score -= 0.15

        # 요구사항 원문 포함 검사
        if requirement[:30] in script_content:
            passed_checks.append("원본 요구사항 텍스트 포함 확인")
        else:
            issues.append(QualityIssue(
                category="requirements",
                severity="low",
                description="원본 요구사항이 스크립트에 포함되지 않았습니다",
                suggestion="주석이나 description에 원본 요구사항 추가"
            ))
            score -= 0.1

        return max(score, 0.0), issues, passed_checks

    def _extract_requirement_keywords(self, requirement: str) -> List[str]:
        """요구사항에서 키워드 추출"""
        # 한글과 영문 키워드 추출
        korean_pattern = r'[가-힣]{2,}'
        english_pattern = r'[a-zA-Z]{3,}'

        korean_words = re.findall(korean_pattern, requirement)
        english_words = re.findall(english_pattern, requirement)

        # 불용어 제거
        stop_words = {'이것', '그것', '저것', '것을', '것이', '하는', '한다', '합니다', '입니다'}
        keywords = [word for word in korean_words + english_words if word not in stop_words]

        return keywords[:10]  # 상위 10개

    def _identify_specific_features(self, requirement: str) -> List[str]:
        """구체적 기능 식별"""
        features = []

        feature_patterns = {
            '분석': ['분석', '조사', '수집'],
            '생성': ['생성', '작성', '만들기'],
            '저장': ['저장', '기록', '보관'],
            '자동화': ['자동', '스케줄', '반복'],
            '처리': ['처리', '변환', '추출'],
            '검색': ['검색', '찾기', '조회']
        }

        for feature, patterns in feature_patterns.items():
            if any(pattern in requirement for pattern in patterns):
                features.append(feature)

        return features

    def _check_feature_implementation(self, feature: str, script_content: str) -> bool:
        """기능 구현 여부 확인"""
        feature_keywords = {
            '분석': ['analyze', 'analysis', '분석', 'research'],
            '생성': ['generate', 'create', '생성', '작성'],
            '저장': ['save', 'store', '저장', 'output'],
            '자동화': ['automat', 'schedul', '자동', 'batch'],
            '처리': ['process', 'parse', '처리', 'extract'],
            '검색': ['search', 'find', '검색', 'query']
        }

        keywords = feature_keywords.get(feature, [])
        return any(keyword.lower() in script_content.lower() for keyword in keywords)

    def _check_execution_readiness(self, script_content: str, project_path: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 4: 실행 가능성 시뮬레이션"""
        issues = []
        passed_checks = []
        score = 1.0

        # import 문 검사
        required_imports = ['crewai', 'Agent', 'Task', 'Crew']
        missing_imports = []

        for imp in required_imports:
            if imp not in script_content:
                missing_imports.append(imp)

        if missing_imports:
            issues.append(QualityIssue(
                category="execution",
                severity="critical",
                description=f"필수 import 누락: {', '.join(missing_imports)}",
                suggestion="from crewai import Agent, Task, Crew, Process 추가"
            ))
            score -= 0.3
        else:
            passed_checks.append("필수 import 구문 확인")

        # 환경변수 설정 검사
        if 'os.getenv' in script_content or 'os.environ' in script_content:
            passed_checks.append("환경변수 사용 패턴 확인")
        else:
            # API 키 관련 키워드가 있으면 환경변수 사용 권장
            api_keywords = ['api_key', 'key', 'token']
            if any(keyword in script_content.lower() for keyword in api_keywords):
                issues.append(QualityIssue(
                    category="execution",
                    severity="medium",
                    description="API 키 하드코딩 가능성",
                    suggestion="os.getenv()를 사용한 환경변수 처리 권장"
                ))
                score -= 0.15

        # 파일 경로 처리 검사
        if 'Path(' in script_content or 'pathlib' in script_content:
            passed_checks.append("안전한 경로 처리 확인")
        elif '\\' in script_content or re.search(r'["\'][A-Z]:', script_content):
            issues.append(QualityIssue(
                category="execution",
                severity="medium",
                description="하드코딩된 경로 사용",
                suggestion="pathlib.Path 사용으로 크로스 플랫폼 호환성 확보"
            ))
            score -= 0.1

        # 출력 디렉토리 생성 로직 검사
        if 'mkdir' in script_content or 'makedirs' in script_content:
            passed_checks.append("출력 디렉토리 생성 로직 확인")
        else:
            issues.append(QualityIssue(
                category="execution",
                severity="medium",
                description="출력 디렉토리 생성 로직 누락",
                suggestion="output 디렉토리 자동 생성 코드 추가"
            ))
            score -= 0.1

        # 의존성 파일 검사 (requirements.txt)
        req_file_path = os.path.join(project_path, "requirements.txt")
        if os.path.exists(req_file_path):
            passed_checks.append("requirements.txt 파일 존재 확인")
        else:
            issues.append(QualityIssue(
                category="execution",
                severity="medium",
                description="requirements.txt 파일이 없습니다",
                suggestion="의존성 목록을 requirements.txt에 작성"
            ))
            score -= 0.1

        return max(score, 0.0), issues, passed_checks

    def _check_security(self, script_content: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 5: 보안 검토"""
        issues = []
        passed_checks = []
        score = 1.0

        # API 키 하드코딩 검사
        api_key_patterns = [
            r'api_key\s*=\s*["\'][^"\']{20,}["\']',
            r'token\s*=\s*["\'][^"\']{20,}["\']',
            r'key\s*=\s*["\'][^"\']{20,}["\']'
        ]

        for pattern in api_key_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                issues.append(QualityIssue(
                    category="security",
                    severity="critical",
                    description="API 키가 하드코딩되어 있습니다",
                    suggestion="환경변수나 설정 파일을 사용하세요"
                ))
                score -= 0.4
                break
        else:
            passed_checks.append("API 키 하드코딩 검사 통과")

        # 위험한 함수 사용 검사
        dangerous_functions = ['eval(', 'exec(', 'compile(', '__import__']
        found_dangerous = []

        for func in dangerous_functions:
            if func in script_content:
                found_dangerous.append(func)

        if found_dangerous:
            issues.append(QualityIssue(
                category="security",
                severity="high",
                description=f"위험한 함수 사용: {', '.join(found_dangerous)}",
                suggestion="안전한 대안 함수 사용 권장"
            ))
            score -= 0.3
        else:
            passed_checks.append("위험한 함수 사용 검사 통과")

        # 입력 검증 검사
        if 'input(' in script_content:
            if any(pattern in script_content for pattern in ['strip()', 'validate', 'check']):
                passed_checks.append("입력 검증 로직 확인")
            else:
                issues.append(QualityIssue(
                    category="security",
                    severity="medium",
                    description="사용자 입력 검증이 부족합니다",
                    suggestion="입력값 검증 및 정제 로직 추가"
                ))
                score -= 0.2

        # 파일 권한 검사
        if any(pattern in script_content for pattern in ['chmod', 'os.system', 'subprocess.call']):
            issues.append(QualityIssue(
                category="security",
                severity="medium",
                description="시스템 명령 실행이 감지되었습니다",
                suggestion="시스템 명령 실행 시 입력값 검증 필수"
            ))
            score -= 0.15
        else:
            passed_checks.append("시스템 명령 실행 검사 통과")

        # 로깅 보안 검사
        if 'logging' in script_content:
            if any(sensitive in script_content.lower() for sensitive in ['password', 'token', 'key']):
                issues.append(QualityIssue(
                    category="security",
                    severity="medium",
                    description="민감한 정보가 로그에 포함될 위험",
                    suggestion="민감한 정보는 로그에서 제외하세요"
                ))
                score -= 0.1
            else:
                passed_checks.append("안전한 로깅 패턴 확인")

        return max(score, 0.0), issues, passed_checks

    def _check_performance(self, script_content: str) -> Tuple[float, List[QualityIssue], List[str]]:
        """Stage 6: 성능 검토"""
        issues = []
        passed_checks = []
        score = 1.0

        # 비효율적 패턴 검사
        inefficient_patterns = {
            r'for.*in.*range\(len\(': '비효율적인 리스트 순회',
            r'time\.sleep\(\d+\)': '긴 sleep 구문',
            r'while\s+True:.*time\.sleep': '무한 루프와 sleep 조합'
        }

        for pattern, description in inefficient_patterns.items():
            if re.search(pattern, script_content):
                issues.append(QualityIssue(
                    category="performance",
                    severity="medium",
                    description=f"성능 이슈: {description}",
                    suggestion="더 효율적인 패턴 사용 권장"
                ))
                score -= 0.15

        # 메모리 효율성 검사
        if 'with open(' in script_content:
            passed_checks.append("파일 컨텍스트 매니저 사용 확인")
        elif 'open(' in script_content:
            issues.append(QualityIssue(
                category="performance",
                severity="medium",
                description="파일 핸들 관리가 명시적이지 않습니다",
                suggestion="with open() 구문 사용 권장"
            ))
            score -= 0.1

        # 에러 핸들링 성능 검사
        exception_count = script_content.count('except')
        if exception_count > 5:
            issues.append(QualityIssue(
                category="performance",
                severity="low",
                description=f"과도한 예외 처리 블록({exception_count}개)",
                suggestion="예외 처리를 통합하여 성능 최적화"
            ))
            score -= 0.05

        # 모니터링 코드 검사
        if any(pattern in script_content for pattern in ['time()', 'datetime.now()', 'timestamp']):
            passed_checks.append("실행 시간 측정 로직 확인")
        else:
            issues.append(QualityIssue(
                category="performance",
                severity="low",
                description="성능 모니터링 코드가 없습니다",
                suggestion="실행 시간 측정 및 로깅 추가"
            ))
            score -= 0.1

        # 리소스 사용량 고려
        if 'Process.sequential' in script_content:
            passed_checks.append("순차 실행으로 메모리 효율성 확보")
        elif 'Process.hierarchical' in script_content:
            issues.append(QualityIssue(
                category="performance",
                severity="low",
                description="계층적 프로세스는 메모리를 더 사용할 수 있습니다",
                suggestion="필요에 따라 순차 프로세스 고려"
            ))
            score -= 0.05

        return max(score, 0.0), issues, passed_checks

    def _calculate_overall_score(self, stage_scores: Dict[str, float]) -> float:
        """종합 점수 계산"""
        # 가중치 적용
        weights = {
            'syntax': 0.20,        # 구문 오류는 치명적
            'logic': 0.25,         # 로직 완성도가 가장 중요
            'requirements': 0.20,   # 요구사항 반영도
            'execution': 0.15,     # 실행 가능성
            'security': 0.15,      # 보안
            'performance': 0.05    # 성능은 보너스
        }

        weighted_score = 0.0
        for stage, score in stage_scores.items():
            weighted_score += score * weights.get(stage, 0.0)

        return min(weighted_score * 100, 100.0)  # 100점 만점으로 변환

    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """품질 등급 결정"""
        if overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif overall_score >= 75:
            return QualityLevel.GOOD
        elif overall_score >= 60:
            return QualityLevel.SATISFACTORY
        elif overall_score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _generate_recommendations(self, stage_scores: Dict[str, float],
                                issues: List[QualityIssue]) -> List[str]:
        """추천사항 생성"""
        recommendations = []

        # 심각한 이슈 우선 해결
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            recommendations.append(f"🔴 {len(critical_issues)}개 치명적 이슈 즉시 해결 필요")

        # 단계별 개선사항
        for stage, score in stage_scores.items():
            if score < self.quality_thresholds[stage]:
                stage_names = {
                    'syntax': '구문 및 문법',
                    'logic': '로직 완성도',
                    'requirements': '요구사항 반영',
                    'execution': '실행 가능성',
                    'security': '보안',
                    'performance': '성능'
                }
                recommendations.append(f"📈 {stage_names[stage]} 개선 필요 (현재: {score:.1%})")

        # 종합 개선 방향
        high_issues = [issue for issue in issues if issue.severity == "high"]
        if high_issues:
            recommendations.append(f"⚠️  {len(high_issues)}개 주요 이슈 개선으로 품질 대폭 향상 가능")

        if not recommendations:
            recommendations.append("✅ 전체적으로 우수한 품질, 세부 최적화만 필요")

        return recommendations

    def _assess_production_readiness(self, stage_scores: Dict[str, float],
                                   issues: List[QualityIssue]) -> bool:
        """프로덕션 준비 여부 평가"""
        # 치명적 이슈가 있으면 프로덕션 불가
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            return False

        # 핵심 단계들이 임계치를 넘어야 함
        critical_stages = ['syntax', 'logic', 'execution']
        for stage in critical_stages:
            if stage_scores.get(stage, 0) < self.quality_thresholds[stage]:
                return False

        return True

    def save_quality_report(self, report: QualityReport, project_path: str) -> str:
        """품질 보고서 저장"""
        report_data = {
            "overall_score": report.overall_score,
            "quality_level": report.quality_level.value,
            "stage_scores": report.stage_scores,
            "is_production_ready": report.is_production_ready,
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                    "line_number": issue.line_number
                }
                for issue in report.issues
            ],
            "passed_checks": report.passed_checks,
            "recommendations": report.recommendations
        }

        report_path = os.path.join(project_path, "quality_report.json")
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            return report_path
        except Exception as e:
            print(f"품질 보고서 저장 실패: {e}")
            return ""

def main():
    """테스트 함수"""
    qa_framework = QualityAssuranceFramework()

    # 테스트용 스크립트 (project_00053의 내용)
    test_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Quality General Project CrewAI Script (4-Agent System)
Generated: fb1e2eb1-e7aa-458c-a640-6175f317c62e
Enhanced with Enterprise-Grade Features
Requirement: 매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘. 이전에 작성된 내용이 있는 경우 는 SKIP하고 다른 주제를 찾아 야해
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Model configuration
MODELS = {'planner': 'gemini-flash', 'researcher': 'gemini-flash', 'writer': 'gemini-flash'}

# Enhanced 4-Agent System for General Projects
requirements_analyst = Agent(
    role="Senior Requirements Analyst",
    goal="Analyze and structure project requirements with precision",
    backstory="You are a senior business analyst with 15+ years of experience.",
    verbose=True,
    llm=MODELS.get('requirements_analyst', 'gpt-4'),
    allow_delegation=False
)

technology_researcher = Agent(
    role="Technology Research Specialist",
    goal="Research and recommend optimal technology stack and implementation approaches",
    backstory="You are a technology research expert with deep knowledge of modern frameworks.",
    verbose=True,
    llm=MODELS.get('technology_researcher', 'gemini-pro'),
    allow_delegation=False
)

solution_architect = Agent(
    role="Senior Solution Architect",
    goal="Design comprehensive system architecture and implementation strategy",
    backstory="You are a senior solution architect with expertise in designing scalable systems.",
    verbose=True,
    llm=MODELS.get('solution_architect', 'claude-3'),
    allow_delegation=False
)

implementation_engineer = Agent(
    role="Senior Implementation Engineer",
    goal="Create production-ready code and comprehensive project deliverables",
    backstory="You are a senior software engineer with expertise in multiple programming languages.",
    verbose=True,
    llm=MODELS.get('implementation_engineer', 'deepseek-coder'),
    allow_delegation=False
)

# Create enhanced crew with 4 specialized agents
crew = Crew(
    agents=[requirements_analyst, technology_researcher, solution_architect, implementation_engineer],
    tasks=[],  # Tasks would be defined here
    process=Process.sequential,
    verbose=True
)

def main():
    """Enhanced main execution function with comprehensive project delivery"""
    print("HIGH-QUALITY 4-Agent CrewAI System - Starting Execution")

    try:
        # Create comprehensive output structure
        output_dir = Path("output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Execute CrewAI with enhanced monitoring
        start_time = datetime.now()
        result = crew.kickoff()
        end_time = datetime.now()

        print("✅ 4-AGENT EXECUTION COMPLETED SUCCESSFULLY!")
        print(result)

        # Save comprehensive results
        result_file = output_dir / f"crew_result_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(result))

    except Exception as e:
        print(f"❌ ERROR OCCURRED: {e}")
        raise

if __name__ == "__main__":
    main()
'''

    # 테스트 요구사항
    test_requirement = "매일 국내 파워불로거 상위 10개를 조사하고, 조사 당일 주제를 확인해서 가장 많이 사용된 주제를 기반으로 리서치를 한후 블로그를 작성해줘"

    print("=== 품질 보증 프레임워크 테스트 ===")

    # 품질 평가 실행
    report = qa_framework.assess_quality(test_script, test_requirement, "test_project")

    print(f"종합 점수: {report.overall_score:.1f}/100")
    print(f"품질 등급: {report.quality_level.value}")
    print(f"프로덕션 준비: {'✅' if report.is_production_ready else '❌'}")

    print(f"\n단계별 점수:")
    for stage, score in report.stage_scores.items():
        print(f"  {stage}: {score:.1%}")

    print(f"\n발견된 이슈 ({len(report.issues)}개):")
    for issue in report.issues:
        print(f"  [{issue.severity}] {issue.description}")

    print(f"\n통과한 검사 ({len(report.passed_checks)}개):")
    for check in report.passed_checks[:5]:  # 상위 5개만
        print(f"  ✅ {check}")

    print(f"\n추천사항:")
    for rec in report.recommendations:
        print(f"  {rec}")

if __name__ == "__main__":
    main()