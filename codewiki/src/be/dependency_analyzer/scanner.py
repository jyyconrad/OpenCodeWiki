"""
Directory scanner module for layered scanning system.

This module provides the DirectoryScanner class for scanning code repositories,
filtering excluded directories, and determining whether to use layered scanning
based on file count thresholds.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import fnmatch

logger = logging.getLogger(__name__)


@dataclass
class FileStats:
    """Statistics for a single file."""
    path: str
    lines: int
    language: str
    needs_deep_analysis: bool = False  # Whether this file needs deep AI analysis


@dataclass
class ScanResult:
    """Result of directory scanning."""
    total_files: int
    total_lines: int
    files: List[FileStats] = field(default_factory=list)
    excluded_count: int = 0
    by_language: Dict[str, int] = field(default_factory=dict)  # language -> file count
    should_use_layered_scan: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'files_count': len(self.files),
            'excluded_count': self.excluded_count,
            'by_language': self.by_language,
            'should_use_layered_scan': self.should_use_layered_scan,
        }


class DirectoryScanner:
    """
    Directory scanner for CodeWiki layered scanning system.

    Features:
    - Scan directory recursively
    - Filter out excluded directories (node_modules, .venv, etc.)
    - Count files and lines
    - Determine if layered scanning is needed based on thresholds
    - Classify files for deep vs basic analysis
    """

    # Default excluded directories
    DEFAULT_EXCLUDE_DIRS = [
        "node_modules", ".venv", "__pycache__", ".git",
        "venv", "env", ".idea", ".vscode", "dist", "build",
        ".eggs", "*.egg-info", "site-packages",
        ".pytest_cache", ".mypy_cache", ".tox",
        "coverage", "htmlcov", ".coverage"
    ]

    # Default excluded file patterns
    DEFAULT_EXCLUDE_PATTERNS = [
        "*.min.js", "*.min.css",  # Minified files
        "*.lock",  # Lock files
        "*.pyc", "*.pyo",  # Compiled Python
        "*.so", "*.dll", "*.dylib",  # Binary files
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.ico",  # Images
        "*.pdf", "*.doc", "*.docx",  # Documents
        "*.woff", "*.woff2", "*.ttf", "*.eot",  # Fonts
    ]

    # Code file extensions (languages we care about)
    CODE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.m': 'objectivec',
        '.mm': 'objectivec',
        '.R': 'r',
        '.r': 'r',
        '.sql': 'sql',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.md': 'markdown',
        '.rst': 'rst',
        '.txt': 'text',
        '.proto': 'protobuf',
        '.graphql': 'graphql',
    }

    def __init__(
        self,
        repo_path: str,
        exclude_dirs: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        auto_threshold: int = 1000,
        enable_layered_scan: bool = True,
        file_line_threshold: int = 500,
    ):
        """
        Initialize the directory scanner.

        Args:
            repo_path: Path to the repository to scan
            exclude_dirs: List of directory names to exclude
            exclude_patterns: List of glob patterns to exclude
            auto_threshold: File count threshold for enabling layered scan
            enable_layered_scan: Whether to enable layered scanning
            file_line_threshold: Lines threshold for marking files as complex
        """
        self.repo_path = Path(repo_path).resolve()
        self.exclude_dirs = set(exclude_dirs or self.DEFAULT_EXCLUDE_DIRS)
        self.exclude_patterns = exclude_patterns or self.DEFAULT_EXCLUDE_PATTERNS
        self.auto_threshold = auto_threshold
        self.enable_layered_scan = enable_layered_scan
        self.file_line_threshold = file_line_threshold

        # Statistics cache
        self._scan_result: Optional[ScanResult] = None

    def _should_exclude_dir(self, dir_name: str) -> bool:
        """Check if a directory should be excluded."""
        # Check exact matches
        if dir_name in self.exclude_dirs:
            return True

        # Check glob patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(dir_name, pattern):
                return True

        return False

    def _should_exclude_file(self, file_name: str) -> bool:
        """Check if a file should be excluded."""
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False

    def _get_language(self, file_path: Path) -> Optional[str]:
        """Get the programming language for a file based on its extension."""
        return self.CODE_EXTENSIONS.get(file_path.suffix.lower())

    def _count_lines(self, file_path: Path) -> int:
        """Count non-empty, non-comment lines in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Count non-empty lines
            count = 0
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith(('#', '//', '/*', '*', '*/')):
                    count += 1

            return count
        except Exception as e:
            logger.debug(f"Failed to count lines in {file_path}: {e}")
            return 0

    def filter_files(self, files: List[str]) -> List[str]:
        """
        Filter out excluded files from a list.

        Args:
            files: List of file paths

        Returns:
            Filtered list of file paths
        """
        filtered = []
        for file_path in files:
            path = Path(file_path)
            # Check if any parent directory should be excluded
            should_exclude = False

            # Check all parts of the path
            all_parts = list(path.parts)
            for part in all_parts:
                if self._should_exclude_dir(part):
                    should_exclude = True
                    break

            if not should_exclude and not self._should_exclude_file(path.name):
                filtered.append(file_path)

        return filtered

    def scan(self) -> ScanResult:
        """
        Scan the repository directory.

        Returns:
            ScanResult containing file statistics and scan metadata
        """
        logger.info(f"Scanning repository: {self.repo_path}")

        total_files = 0
        total_lines = 0
        excluded_count = 0
        files: List[FileStats] = []
        by_language: Dict[str, int] = {}

        # Walk through directory
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out excluded directories (modifying dirs in-place)
            original_dir_count = len(dirs)
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]
            excluded_count += original_dir_count - len(dirs)

            for filename in filenames:
                # Check file patterns
                if self._should_exclude_file(filename):
                    excluded_count += 1
                    continue

                file_path = Path(root) / filename
                relative_path = str(file_path.relative_to(self.repo_path))

                # Get language
                language = self._get_language(file_path)
                if not language:
                    # Skip unknown file types
                    continue

                # Count lines
                lines = self._count_lines(file_path)

                # Create file stats
                file_stats = FileStats(
                    path=relative_path,
                    lines=lines,
                    language=language,
                    needs_deep_analysis=lines > self.file_line_threshold
                )

                files.append(file_stats)
                total_files += 1
                total_lines += lines

                # Update language counts
                by_language[language] = by_language.get(language, 0) + 1

        # Determine if layered scan should be used
        should_use_layered = (
            self.enable_layered_scan and
            total_files > self.auto_threshold
        )

        self._scan_result = ScanResult(
            total_files=total_files,
            total_lines=total_lines,
            files=files,
            excluded_count=excluded_count,
            by_language=by_language,
            should_use_layered_scan=should_use_layered,
        )

        logger.info(
            f"Scan complete: {total_files} files, {total_lines} lines, "
            f"{excluded_count} excluded dirs/files"
        )
        if should_use_layered:
            logger.info(
                f"Layered scan ENABLED (threshold: {self.auto_threshold}, "
                f"files: {total_files})"
            )

        return self._scan_result

    def get_file_stats(self) -> Dict[str, Any]:
        """
        Get file statistics from the last scan.

        Returns:
            Dictionary containing file statistics
        """
        if not self._scan_result:
            self.scan()

        return self._scan_result.to_dict() if self._scan_result else {}

    def should_use_layered_scan(self) -> bool:
        """
        Check if layered scanning should be used.

        Returns:
            True if layered scanning is enabled and file count exceeds threshold
        """
        if not self._scan_result:
            self.scan()

        return self._scan_result.should_use_layered_scan if self._scan_result else False

    def get_files_for_analysis(
        self,
        analysis_type: str = 'all'
    ) -> List[FileStats]:
        """
        Get files filtered by analysis type.

        Args:
            analysis_type: 'deep', 'basic', or 'all'

        Returns:
            List of FileStats matching the analysis type
        """
        if not self._scan_result:
            self.scan()

        if analysis_type == 'deep':
            return [f for f in self._scan_result.files if f.needs_deep_analysis]
        elif analysis_type == 'basic':
            return [f for f in self._scan_result.files if not f.needs_deep_analysis]
        else:
            return self._scan_result.files if self._scan_result else []
