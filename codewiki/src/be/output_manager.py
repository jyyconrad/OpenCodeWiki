"""
Output Manager for documentation generation.

This module handles the output directory structure for generated documentation,
supporting both flat and hierarchical directory structures.

Features:
- Flat structure: All files in a single directory (default, backward compatible)
- Hierarchical structure: Organized by module categories with index files
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from codewiki.src.config import Config
from codewiki.src.utils import file_manager

logger = logging.getLogger(__name__)


class OutputManager:
    """
    Manages output directory structure and file writing for documentation generation.

    Supports two modes:
    - flat: All markdown files in a single directory (backward compatible)
    - hierarchical: Organized directory structure with index files
    """

    def __init__(self, config: Config):
        """
        Initialize the output manager.

        Args:
            config: Configuration object containing output settings
        """
        self.config = config
        self.docs_dir = config.docs_dir
        self.structure_type = config.output.directory_structure
        self.should_generate_index = config.output.generate_index

        # Hierarchical structure directories
        self.overview_dir = os.path.join(self.docs_dir, "overview")
        self.core_dir = os.path.join(self.docs_dir, "core")
        self.utils_dir = os.path.join(self.docs_dir, "utils")

    def ensure_directory_structure(self) -> None:
        """
        Create the necessary directory structure based on configuration.

        For flat structure: Only creates the main docs directory.
        For hierarchical structure: Creates overview/, core/, utils/ subdirectories.
        """
        # Always ensure main docs directory exists
        file_manager.ensure_directory(self.docs_dir)

        if self.structure_type == "hierarchical":
            # Create subdirectories for hierarchical structure
            file_manager.ensure_directory(self.overview_dir)
            file_manager.ensure_directory(self.core_dir)
            file_manager.ensure_directory(self.utils_dir)

            logger.info(f"Created hierarchical directory structure in {self.docs_dir}")
        else:
            logger.info(f"Using flat directory structure in {self.docs_dir}")

    def write_file(self, content: str, filename: str, subdirectory: Optional[str] = None) -> str:
        """
        Write content to a file in the appropriate location.

        Args:
            content: The content to write
            filename: The filename (e.g., "module.md" or "index.md")
            subdirectory: Optional subdirectory for hierarchical structure
                          (e.g., "core/module-a", "overview")

        Returns:
            The full path to the written file
        """
        if self.structure_type == "flat" or subdirectory is None:
            # Flat structure: write to docs_dir root
            filepath = os.path.join(self.docs_dir, filename)
        else:
            # Hierarchical structure: write to specified subdirectory
            target_dir = os.path.join(self.docs_dir, subdirectory)
            file_manager.ensure_directory(target_dir)
            filepath = os.path.join(target_dir, filename)

        file_manager.save_text(content, filepath)
        logger.debug(f"Written file: {filepath}")
        return filepath

    def write_module_file(self, module_name: str, content: str,
                          module_category: str = "core") -> str:
        """
        Write a module documentation file to the appropriate category directory.

        Args:
            module_name: Name of the module (used for filename)
            content: The documentation content
            module_category: Category directory ("core", "utils", or custom)

        Returns:
            The full path to the written file
        """
        if self.structure_type == "flat":
            filepath = os.path.join(self.docs_dir, f"{module_name}.md")
        else:
            # Hierarchical: create module subdirectory
            module_dir = os.path.join(self.docs_dir, module_category, module_name)
            file_manager.ensure_directory(module_dir)
            filepath = os.path.join(module_dir, "index.md")

        file_manager.save_text(content, filepath)
        logger.debug(f"Written module file: {filepath}")
        return filepath

    def generate_index(self, modules: Dict[str, Any]) -> str:
        """
        Generate an index.md file that links to all module documentation.

        Args:
            modules: Dictionary of module names to their metadata

        Returns:
            The content of the generated index file
        """
        if self.structure_type == "flat":
            return self._generate_flat_index(modules)
        else:
            return self._generate_hierarchical_index(modules)

    def _generate_flat_index(self, modules: Dict[str, Any]) -> str:
        """Generate index for flat directory structure."""
        lines = [
            "# 代码仓库文档索引",
            "",
            f"本索引包含 {len(modules)} 个模块的文档。",
            "",
            "## 模块列表",
            "",
        ]

        for module_name in sorted(modules.keys()):
            module_info = modules[module_name]
            description = module_info.get("description", "")
            lines.append(f"- [{module_name}]({module_name}.md) - {description}")

        lines.extend(["", "---", "", "此索引由 CodeWiki 自动生成。"])

        content = "\n".join(lines)
        index_path = os.path.join(self.docs_dir, "index.md")
        file_manager.save_text(content, index_path)
        logger.info(f"Generated flat index at {index_path}")
        return content

    def _generate_hierarchical_index(self, modules: Dict[str, Any]) -> str:
        """
        Generate index for hierarchical directory structure.

        Creates a main index.md at the root that links to:
        - overview/repository-overview.md
        - core/ modules
        - utils/ modules
        """
        # Categorize modules
        core_modules = []
        utils_modules = []

        for module_name, module_info in modules.items():
            category = module_info.get("category", "core")
            if category == "utils":
                utils_modules.append((module_name, module_info))
            else:
                core_modules.append((module_name, module_info))

        lines = [
            "# CodeWiki 文档索引",
            "",
            "欢迎使用 CodeWiki 生成的代码文档。本文档按模块组织，便于导航。",
            "",
            "## 目录结构",
            "",
            "```",
            "output/",
            "├── index.md              # 本索引文件",
            "├── overview/",
            "│   └── repository-overview.md  # 仓库概览",
            "├── core/                 # 核心模块",
            "│   ├── module-a/",
            "│   │   └── index.md",
            "│   └── module-b/",
            "│       └── index.md",
            "└── utils/                # 工具模块",
            "    └── index.md",
            "```",
            "",
            "## 文档导航",
            "",
            "### [仓库概览](overview/repository-overview.md)",
            "",
            "整个代码仓库的整体架构和模块关系概览。",
            "",
        ]

        # Core modules section
        if core_modules:
            lines.extend([
                "### 核心模块",
                "",
                "核心业务逻辑和主要功能模块。",
                "",
            ])

            for module_name, module_info in sorted(core_modules):
                description = module_info.get("description", "")
                lines.append(f"- [{module_name}](core/{module_name}/index.md) - {description}")

            lines.append("")

        # Utils modules section
        if utils_modules:
            lines.extend([
                "### 工具模块",
                "",
                "通用工具类和辅助功能。",
                "",
            ])

            for module_name, module_info in sorted(utils_modules):
                description = module_info.get("description", "")
                lines.append(f"- [{module_name}](utils/{module_name}/index.md) - {description}")

            lines.append("")

        lines.extend([
            "---",
            "",
            "此索引由 CodeWiki 自动生成。",
        ])

        content = "\n".join(lines)
        index_path = os.path.join(self.docs_dir, "index.md")
        file_manager.save_text(content, index_path)
        logger.info(f"Generated hierarchical index at {index_path}")
        return content

    def _generate_module_index(self, module_name: str, components: List[str]) -> str:
        """
        Generate an index.md file for a module subdirectory.

        Args:
            module_name: Name of the module
            components: List of component filenames

        Returns:
            Content of the module index file
        """
        lines = [
            f"# {module_name} 模块",
            "",
            "## 文档列表",
            "",
        ]

        for component in components:
            component_name = component.replace(".md", "").replace("-", " ").title()
            lines.append(f"- [{component_name}]({component})")

        lines.extend(["", "---", "", f"此模块索引由 CodeWiki 自动生成。"])

        return "\n".join(lines)

    def move_existing_files(self, existing_files: List[str]) -> None:
        """
        Move existing flat files to hierarchical structure.

        This is used when converting from flat to hierarchical structure.

        Args:
            existing_files: List of existing markdown files in docs_dir
        """
        if self.structure_type != "hierarchical":
            return

        # Files that should go to overview/
        overview_files = ["overview.md", "repository-overview.md"]

        for filename in existing_files:
            if not filename.endswith(".md"):
                continue

            if filename in overview_files:
                # Move to overview/
                src_path = os.path.join(self.docs_dir, filename)
                dst_path = os.path.join(self.overview_dir, filename)

                if os.path.exists(src_path) and not os.path.exists(dst_path):
                    file_manager.ensure_directory(self.overview_dir)
                    os.rename(src_path, dst_path)
                    logger.info(f"Moved {filename} to overview/")

    def get_module_path(self, module_name: str, module_category: str = "core") -> str:
        """
        Get the directory path for a module.

        Args:
            module_name: Name of the module
            module_category: Category ("core", "utils", etc.)

        Returns:
            Full directory path for the module
        """
        if self.structure_type == "flat":
            return self.docs_dir
        else:
            return os.path.join(self.docs_dir, module_category, module_name)

    def generate_all_indices(self, module_tree: Dict[str, Any],
                             overview_content: Optional[str] = None) -> None:
        """
        Generate all necessary index files for hierarchical structure.

        Args:
            module_tree: The complete module tree structure
            overview_content: Optional overview content to save
        """
        if self.structure_type != "hierarchical":
            return

        # Check if index generation is enabled
        if not self.should_generate_index:
            logger.info("Index generation is disabled, skipping index files")
            return

        # Save overview if provided
        if overview_content:
            self.write_file(overview_content, "repository-overview.md", "overview")

        # Generate main index
        modules_flat = self._flatten_module_tree(module_tree)
        self.generate_index(modules_flat)

        # Generate per-module indices
        self._generate_module_indices(module_tree)

    def _flatten_module_tree(self, tree: Dict[str, Any],
                             parent_category: str = "core") -> Dict[str, Any]:
        """
        Flatten module tree to a simple dict for index generation.

        Args:
            tree: Module tree structure
            parent_category: Parent category for nested modules

        Returns:
            Flattened module dictionary
        """
        result = {}

        for module_name, module_info in tree.items():
            # Determine category based on module name patterns
            category = parent_category
            if "util" in module_name.lower() or "helper" in module_name.lower():
                category = "utils"

            result[module_name] = {
                "category": category,
                "description": module_info.get("description", f"{module_name} 模块"),
                "components": module_info.get("components", []),
            }

            # Process nested modules
            children = module_info.get("children", {})
            if children and isinstance(children, dict):
                nested = self._flatten_module_tree(children, category)
                result.update(nested)

        return result

    def _generate_module_indices(self, module_tree: Dict[str, Any],
                                  current_path: List[str] = []) -> None:
        """
        Recursively generate index.md files for each module directory.

        Args:
            module_tree: Module tree structure
            current_path: Current module path for nested modules
        """
        for module_name, module_info in module_tree.items():
            # Determine category
            category = "core"
            if "util" in module_name.lower() or "helper" in module_name.lower():
                category = "utils"

            # Get component files
            components = module_info.get("components", [])
            component_files = [f"{comp}.md" for comp in components] if components else ["index.md"]

            # Generate module index
            index_content = self._generate_module_index(module_name, component_files)
            module_dir = self.get_module_path(module_name, category)
            index_path = os.path.join(module_dir, "index.md")

            # Only create if directory exists (meaning module was processed)
            if os.path.exists(module_dir):
                file_manager.save_text(index_content, index_path)
                logger.debug(f"Generated module index for {module_name}")

            # Process nested modules
            children = module_info.get("children", {})
            if children and isinstance(children, dict):
                self._generate_module_indices(children, current_path + [module_name])
