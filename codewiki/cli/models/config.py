"""
Configuration data models for CodeWiki CLI.

This module contains the Configuration class which represents persistent
user settings stored in ~/.codewiki/config.json. These settings are converted
to the backend Config class when running documentation generation.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path

from codewiki.cli.utils.validation import (
    validate_url,
    validate_api_key,
    validate_model_name,
)


@dataclass
class ScanConfig:
    """
    Scan configuration for layered scanning system.

    Attributes:
        auto_threshold: 文件数阈值，超过则启用分层扫描 (default: 1000)
        enable_layered_scan: 是否启用分层扫描 (default: True)
        max_depth: 扫描最大深度 (default: 2)
        exclude_dirs: 排除的目录列表 (default: node_modules, .venv, __pycache__, .git 等)
        file_line_threshold: 单文件代码行数阈值，超过则标记为复杂文件 (default: 500)
    """
    auto_threshold: int = 1000
    enable_layered_scan: bool = True
    max_depth: int = 2
    exclude_dirs: List[str] = field(default_factory=lambda: [
        "node_modules", ".venv", "__pycache__", ".git",
        "venv", "env", ".idea", ".vscode", "dist", "build",
        ".eggs", "*.egg-info", "site-packages"
    ])
    file_line_threshold: int = 500

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        return {
            'auto_threshold': self.auto_threshold,
            'enable_layered_scan': self.enable_layered_scan,
            'max_depth': self.max_depth,
            'exclude_dirs': self.exclude_dirs,
            'file_line_threshold': self.file_line_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ScanConfig':
        """Create ScanConfig from dictionary."""
        return cls(
            auto_threshold=data.get('auto_threshold', 1000),
            enable_layered_scan=data.get('enable_layered_scan', True),
            max_depth=data.get('max_depth', 2),
            exclude_dirs=data.get('exclude_dirs', [
                "node_modules", ".venv", "__pycache__", ".git",
                "venv", "env", ".idea", ".vscode", "dist", "build",
                ".eggs", "*.egg-info", "site-packages"
            ]),
            file_line_threshold=data.get('file_line_threshold', 500),
        )


@dataclass
class AgentInstructions:
    """
    Custom instructions for the documentation agent.

    Allows users to customize:
    - File filtering (include/exclude patterns)
    - Module focus (prioritize certain modules)
    - Documentation type (API docs, architecture docs, etc.)
    - Custom instructions for the LLM

    Attributes:
        include_patterns: File patterns to include (e.g., ["*.cs", "*.py"])
        exclude_patterns: File/directory patterns to exclude (e.g., ["*Tests*", "*test*"])
        focus_modules: Modules to document in more detail
        doc_type: Type of documentation to generate
        custom_instructions: Additional instructions for the documentation agent
    """
    include_patterns: Optional[List[str]] = None  # e.g., ["*.cs"] for C# projects
    exclude_patterns: Optional[List[str]] = None  # e.g., ["*Tests*", "*Specs*"]
    focus_modules: Optional[List[str]] = None  # e.g., ["src/core", "src/api"]
    doc_type: Optional[str] = None  # e.g., "api", "architecture", "user-guide"
    custom_instructions: Optional[str] = None  # Free-form instructions

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.include_patterns:
            result['include_patterns'] = self.include_patterns
        if self.exclude_patterns:
            result['exclude_patterns'] = self.exclude_patterns
        if self.focus_modules:
            result['focus_modules'] = self.focus_modules
        if self.doc_type:
            result['doc_type'] = self.doc_type
        if self.custom_instructions:
            result['custom_instructions'] = self.custom_instructions
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'AgentInstructions':
        """Create AgentInstructions from dictionary."""
        return cls(
            include_patterns=data.get('include_patterns'),
            exclude_patterns=data.get('exclude_patterns'),
            focus_modules=data.get('focus_modules'),
            doc_type=data.get('doc_type'),
            custom_instructions=data.get('custom_instructions'),
        )

    def is_empty(self) -> bool:
        """Check if all fields are empty/None."""
        return not any([
            self.include_patterns,
            self.exclude_patterns,
            self.focus_modules,
            self.doc_type,
            self.custom_instructions,
        ])

    def get_prompt_addition(self) -> str:
        """Generate prompt additions based on instructions."""
        additions = []

        if self.doc_type:
            doc_type_instructions = {
                'api': "Focus on API documentation: endpoints, parameters, return types, and usage examples.",
                'architecture': "Focus on architecture documentation: system design, component relationships, and data flow.",
                'user-guide': "Focus on user guide documentation: how to use features, step-by-step tutorials.",
                'developer': "Focus on developer documentation: code structure, contribution guidelines, and implementation details.",
            }
            if self.doc_type.lower() in doc_type_instructions:
                additions.append(doc_type_instructions[self.doc_type.lower()])
            else:
                additions.append(f"Focus on generating {self.doc_type} documentation.")

        if self.focus_modules:
            additions.append(f"Pay special attention to and provide more detailed documentation for these modules: {', '.join(self.focus_modules)}")

        if self.custom_instructions:
            additions.append(f"Additional instructions: {self.custom_instructions}")

        return "\n".join(additions) if additions else ""


@dataclass
class Configuration:
    """
    CodeWiki configuration data model.

    Attributes:
        base_url: LLM API base URL
        main_model: Primary model for documentation generation
        cluster_model: Model for module clustering
        fallback_model: Fallback model for documentation generation
        default_output: Default output directory
        max_tokens: Maximum tokens for LLM response (default: 32768)
        max_token_per_module: Maximum tokens per module for clustering (default: 36369)
        max_token_per_leaf_module: Maximum tokens per leaf module (default: 16000)
        max_depth: Maximum depth for hierarchical decomposition (default: 2)
        agent_instructions: Custom instructions for documentation generation
        output_language: Output document language (default: zh-CN)
        scan: Scan configuration for layered scanning system
    """
    base_url: str
    main_model: str
    cluster_model: str
    fallback_model: str = "glm-4p5"
    default_output: str = "docs"
    max_tokens: int = 32768
    max_token_per_module: int = 36369
    max_token_per_leaf_module: int = 16000
    max_depth: int = 2
    agent_instructions: AgentInstructions = field(default_factory=AgentInstructions)
    output_language: str = "zh-CN"
    scan: ScanConfig = field(default_factory=ScanConfig)

    def validate(self):
        """
        Validate all configuration fields.

        Raises:
            ConfigurationError: If validation fails
        """
        validate_url(self.base_url)
        validate_model_name(self.main_model)
        validate_model_name(self.cluster_model)
        validate_model_name(self.fallback_model)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            'base_url': self.base_url,
            'main_model': self.main_model,
            'cluster_model': self.cluster_model,
            'default_output': self.default_output,
            'max_tokens': self.max_tokens,
            'max_token_per_module': self.max_token_per_module,
            'max_token_per_leaf_module': self.max_token_per_leaf_module,
            'max_depth': self.max_depth,
            'output_language': self.output_language,
        }
        if self.agent_instructions and not self.agent_instructions.is_empty():
            result['agent_instructions'] = self.agent_instructions.to_dict()
        if self.scan:
            result['scan'] = self.scan.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'Configuration':
        """
        Create Configuration from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Configuration instance
        """
        agent_instructions = AgentInstructions()
        if 'agent_instructions' in data:
            agent_instructions = AgentInstructions.from_dict(data['agent_instructions'])

        scan = ScanConfig()
        if 'scan' in data:
            scan = ScanConfig.from_dict(data['scan'])

        return cls(
            base_url=data.get('base_url', ''),
            main_model=data.get('main_model', ''),
            cluster_model=data.get('cluster_model', ''),
            fallback_model=data.get('fallback_model', 'glm-4p5'),
            default_output=data.get('default_output', 'docs'),
            max_tokens=data.get('max_tokens', 32768),
            max_token_per_module=data.get('max_token_per_module', 36369),
            max_token_per_leaf_module=data.get('max_token_per_leaf_module', 16000),
            max_depth=data.get('max_depth', 2),
            agent_instructions=agent_instructions,
            output_language=data.get('output_language', 'zh-CN'),
            scan=scan,
        )

    def is_complete(self) -> bool:
        """Check if all required fields are set."""
        return bool(
            self.base_url and
            self.main_model and
            self.cluster_model and
            self.fallback_model
        )

    def to_backend_config(self, repo_path: str, output_dir: str, api_key: str, runtime_instructions: AgentInstructions = None):
        """
        Convert CLI Configuration to Backend Config.

        This method bridges the gap between persistent user settings (CLI Configuration)
        and runtime job configuration (Backend Config).

        Args:
            repo_path: Path to the repository to document
            output_dir: Output directory for generated documentation
            api_key: LLM API key (from keyring)
            runtime_instructions: Runtime agent instructions (override persistent settings)

        Returns:
            Backend Config instance ready for documentation generation
        """
        from codewiki.src.config import Config, ScanConfig as BackendScanConfig

        # Merge runtime instructions with persistent settings
        # Runtime instructions take precedence
        final_instructions = self.agent_instructions
        if runtime_instructions and not runtime_instructions.is_empty():
            final_instructions = AgentInstructions(
                include_patterns=runtime_instructions.include_patterns or self.agent_instructions.include_patterns,
                exclude_patterns=runtime_instructions.exclude_patterns or self.agent_instructions.exclude_patterns,
                focus_modules=runtime_instructions.focus_modules or self.agent_instructions.focus_modules,
                doc_type=runtime_instructions.doc_type or self.agent_instructions.doc_type,
                custom_instructions=runtime_instructions.custom_instructions or self.agent_instructions.custom_instructions,
            )

        return Config.from_cli(
            repo_path=repo_path,
            output_dir=output_dir,
            llm_base_url=self.base_url,
            llm_api_key=api_key,
            main_model=self.main_model,
            cluster_model=self.cluster_model,
            fallback_model=self.fallback_model,
            max_tokens=self.max_tokens,
            max_token_per_module=self.max_token_per_module,
            max_token_per_leaf_module=self.max_token_per_leaf_module,
            max_depth=self.max_depth,
            agent_instructions=final_instructions.to_dict() if final_instructions else None,
            output_language=self.output_language,
            scan=self.scan.to_dict() if self.scan else None
        )
