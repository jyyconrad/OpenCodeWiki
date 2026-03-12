"""
AI-powered file classifier for layered scanning system.

This module uses LLM to classify files into deep analysis or basic analysis
categories based on their importance and complexity.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of file classification."""
    file_path: str
    analysis_type: str  # 'deep' or 'basic'
    reason: str
    priority: int  # 1-5, higher means more important


@dataclass
class ClassificationSummary:
    """Summary of all file classifications."""
    deep_analysis_files: List[ClassificationResult]
    basic_analysis_files: List[ClassificationResult]
    total_files: int
    deep_count: int
    basic_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'deep_analysis_files': [
                {'path': f.file_path, 'reason': f.reason, 'priority': f.priority}
                for f in self.deep_analysis_files
            ],
            'basic_analysis_files': [
                {'path': f.file_path, 'reason': f.reason, 'priority': f.priority}
                for f in self.basic_analysis_files
            ],
            'total_files': self.total_files,
            'deep_count': self.deep_count,
            'basic_count': self.basic_count,
        }


class FileClassifier:
    """
    AI-powered file classifier for CodeWiki layered scanning.

    Uses LLM to analyze file paths, sizes, and languages to determine
    which files need deep AI analysis vs basic analysis.
    """

    CLASSIFICATION_PROMPT = """
你是一个代码分析专家。请帮助我对代码仓库的文件进行分类，决定哪些文件需要深度分析（deep analysis），哪些只需要基础分析（basic analysis）。

**分类标准**：

需要**深度分析**的文件（priority 4-5）：
1. 核心业务逻辑文件
2. 主要架构/框架配置文件
3. 入口文件（main, app, index 等）
4. 核心工具类和公共服务
5. API 接口定义和路由文件
6. 数据库模型和 Schema 定义
7. 复杂的算法实现

只需要**基础分析**的文件（priority 1-3）：
1. 简单的数据模型/DTO
2. 配置文件（JSON, YAML 等）
3. 测试文件
4. 文档文件
5. 静态资源文件
6. 生成代码或样板代码
7. 第三方库或依赖

**仓库信息**：
- 仓库路径：{repo_path}
- 总文件数：{total_files}
- 总代码行数：{total_lines}

**待分类文件列表**（格式：[路径，语言，行数]）：
{files_json}

**输出格式要求**：
请返回一个 JSON 数组，每个元素包含：
- path: 文件路径
- analysis_type: "deep" 或 "basic"
- priority: 1-5 的优先级数字
- reason: 分类原因（简短说明）

只返回 JSON 数组，不要有其他内容。
"""

    def __init__(self, config: Any):
        """
        Initialize the file classifier.

        Args:
            config: Backend config object with LLM settings
        """
        self.config = config
        self._llm_client = None

    def _get_llm_client(self):
        """Get or create LLM client."""
        if self._llm_client is None:
            from codewiki.src.be.llm_services import call_llm
            self._call_llm = call_llm
        return self._call_llm

    def _prepare_files_context(
        self,
        files: List[Dict[str, Any]],
        max_files: int = 100
    ) -> str:
        """
        Prepare file context for LLM.

        Args:
            files: List of file info dicts
            max_files: Maximum number of files to include

        Returns:
            Formatted string for LLM prompt
        """
        # Sort by lines (descending) to prioritize larger files
        sorted_files = sorted(files, key=lambda x: x.get('lines', 0), reverse=True)

        # Take top files if too many
        selected_files = sorted_files[:max_files]

        # Format as table
        lines = []
        for f in selected_files:
            lines.append(f"- {f['path']} ({f['language']}, {f['lines']} lines)")

        return "\n".join(lines)

    def classify_files(
        self,
        files: List[Dict[str, Any]],
        repo_path: str,
        total_lines: int
    ) -> ClassificationSummary:
        """
        Classify files using LLM.

        Args:
            files: List of file info dicts with path, language, lines
            repo_path: Path to the repository
            total_lines: Total lines of code

        Returns:
            ClassificationSummary with classified files
        """
        logger.info(f"Classifying {len(files)} files using AI...")

        # Prepare context
        files_json = self._prepare_files_context(files)

        # Build prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            repo_path=repo_path,
            total_files=len(files),
            total_lines=total_lines,
            files_json=files_json
        )

        try:
            # Call LLM
            call_llm = self._get_llm_client()
            response = call_llm(prompt, self.config)

            # Parse response
            classification_data = self._parse_llm_response(response)

            # Create classification results
            deep_files = []
            basic_files = []

            for item in classification_data:
                result = ClassificationResult(
                    file_path=item['path'],
                    analysis_type=item['analysis_type'],
                    reason=item.get('reason', 'No reason provided'),
                    priority=item.get('priority', 3)
                )

                if item['analysis_type'] == 'deep':
                    deep_files.append(result)
                else:
                    basic_files.append(result)

            summary = ClassificationSummary(
                deep_analysis_files=deep_files,
                basic_analysis_files=basic_files,
                total_files=len(files),
                deep_count=len(deep_files),
                basic_count=len(basic_files)
            )

            logger.info(
                f"Classification complete: {len(deep_files)} deep, "
                f"{len(basic_files)} basic"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to classify files: {e}")
            # Fall back to rule-based classification
            return self._rule_based_classification(files)

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM JSON response."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)

            # If no JSON found, try parsing the whole response
            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _rule_based_classification(
        self,
        files: List[Dict[str, Any]]
    ) -> ClassificationSummary:
        """
        Fall back to rule-based classification if LLM fails.

        Args:
            files: List of file info dicts

        Returns:
            ClassificationSummary with classified files
        """
        logger.info("Using rule-based classification as fallback...")

        deep_files = []
        basic_files = []

        # Patterns for deep analysis
        deep_patterns = [
            'main', 'app', 'index', 'entry',
            'config', 'settings', 'constants',
            'router', 'route', 'controller', 'handler',
            'model', 'schema', 'entity',
            'service', 'repository', 'dao',
            'core', 'base', 'abstract',
            'utils', 'helpers', 'lib',
        ]

        # Patterns for basic analysis
        basic_patterns = [
            'test', 'spec', 'mock', 'fixture',
            '__init__',
            '.min.', '.bundle', '.dist',
            'generated', 'auto',
        ]

        for f in files:
            path = f['path'].lower()
            filename = os.path.basename(path).lower()

            # Check for basic analysis patterns first
            is_basic = any(p in filename or p in path for p in basic_patterns)

            # Check for deep analysis patterns
            is_deep = any(p in filename or p in path for p in deep_patterns)

            # Large files with complex logic
            is_complex = f.get('lines', 0) > 300

            # Determine classification
            if is_basic and not is_deep:
                basic_files.append(ClassificationResult(
                    file_path=f['path'],
                    analysis_type='basic',
                    reason='Test file, generated code, or simple module',
                    priority=2
                ))
            elif is_deep or is_complex:
                deep_files.append(ClassificationResult(
                    file_path=f['path'],
                    analysis_type='deep',
                    reason='Core module, entry point, or complex file' if is_deep else 'Large file with complex logic',
                    priority=4 if is_deep else 3
                ))
            else:
                # Default to basic for unknown files
                basic_files.append(ClassificationResult(
                    file_path=f['path'],
                    analysis_type='basic',
                    reason='Standard module',
                    priority=2
                ))

        return ClassificationSummary(
            deep_analysis_files=deep_files,
            basic_analysis_files=basic_files,
            total_files=len(files),
            deep_count=len(deep_files),
            basic_count=len(basic_files)
        )

    def get_analysis_priority(
        self,
        summary: ClassificationSummary
    ) -> List[Tuple[str, int]]:
        """
        Get files sorted by analysis priority.

        Args:
            summary: Classification summary

        Returns:
            List of (file_path, priority) tuples sorted by priority
        """
        all_files = summary.deep_analysis_files + summary.basic_analysis_files
        sorted_files = sorted(all_files, key=lambda x: x.priority, reverse=True)
        return [(f.file_path, f.priority) for f in sorted_files]
