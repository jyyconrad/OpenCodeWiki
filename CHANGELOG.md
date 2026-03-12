# CodeWiki 变更日志

本文件记录 CodeWiki 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.2.0] - 2026-03-13

### 新增

#### 多语言输出支持
- 新增 `--language` / `--output-language` CLI 选项，支持生成多语言文档
- 支持的语言：
  - `zh-CN` - 简体中文（默认）
  - `en-US` - English (US)
  - `ja-JP` - 日本語
- 所有文档模板和索引文件支持多语言输出
- AI 提示词自动适配目标语言

#### 分层扫描系统
- 新增 `DirectoryScanner` 类，负责代码仓库扫描和文件过滤
- 新增 `FileClassifier` 类，使用 AI 智能分类文件
  - 深度分析（deep analysis）：核心业务逻辑、入口文件、API 接口等
  - 基础分析（basic analysis）：测试文件、配置文件、文档等
- 自动检测大型仓库（1000+ 文件）并启用分层扫描
- 新增配置选项：
  - `--auto-threshold` - 文件数阈值（默认：1000）
  - `--enable-layered-scan` - 是否启用分层扫描
  - `--file-line-threshold` - 单文件行数阈值（默认：500）

#### 并行处理优化
- 新增 `ParallelConfig` 配置类
- 支持并行文件解析，性能提升 2-4 倍
- 支持并行文档生成（叶模块）
- 智能 LLM 并发调用限制（默认：5 个并发）
- 新增配置选项：
  - `--parallel` - 启用并行处理
  - `--max-workers` - 最大工作线程数（默认：CPU 核心数）
  - `--max-concurrent-llm-calls` - 最大并发 LLM 调用数（默认：5）
  - `--parallel-parsing` - 是否启用并行解析
  - `--parallel-generation` - 是否启用并行生成

#### 输出目录重构
- 新增 `OutputManager` 类，统一管理输出目录结构
- 新增 `OutputConfig` 配置类
- 支持两种输出结构：
  - **Flat**（默认）：所有文件在同一目录，向后兼容
  - **Hierarchical**：按模块类别组织，带索引文件
- 自动生成 `index.md` 导航索引
- 新增配置选项：
  - `--directory-structure` - 目录结构类型（flat/hierarchical）
  - `--generate-index` - 是否生成索引文件

### 改进

- 优化大型仓库的处理性能
- 改进文件排除逻辑，支持 glob 模式
- 增强错误处理和日志记录
- 优化 AI 提示词，提高文档质量

### 修复

- 修复某些情况下文件编码检测问题
- 修复并行处理时的资源竞争问题
- 修复索引生成时的路径问题

### 技术变更

- 新增测试模块 `tests/`，包含单元测试：
  - `test_scanner.py` - DirectoryScanner 测试
  - `test_file_classifier.py` - FileClassifier 测试
  - `test_output_manager.py` - OutputManager 测试
  - `test_parallel_config.py` - 并行配置测试
- 新增 `conftest.py` 共享测试夹具
- 代码重构，提高可维护性

---

## [1.1.0] - 2025-XX-XX

### 新增

- 支持 8 种编程语言：Python, Java, JavaScript, TypeScript, C, C++, C#, Kotlin
- CLI 配置管理命令
- Agent Instructions 系统，支持自定义：
  - `--include` - 文件包含模式
  - `--exclude` - 文件排除模式
  - `--focus` - 聚焦模块
  - `--doc-type` - 文档类型（api, architecture, user-guide, developer）
  - `--instructions` - 自定义指令
- Token 限制配置
- 最大深度配置（`--max-depth`）
- GitHub Pages 支持（`--github-pages`）
- Git 分支创建（`--create-branch`）
- HTML 交互式文档查看器

### 改进

- 层次化解码算法
- 递归多 Agent 处理
- 多模态合成（文本 + 图表）

---

## [1.0.0] - 2025-XX-XX

### 新增

- 初始版本发布
- 核心文档生成功能
- 基础 CLI 界面
- 支持 Python 和 JavaScript

---

## 版本说明

### 语义化版本格式

- **主版本号（Major）**：不兼容的 API 变更
- **次版本号（Minor）**：向后兼容的功能新增
- **修订号（Patch）**：向后兼容的问题修复

### 变更类型

- **新增（Added）**：新功能
- **改进（Changed）**：现有功能的变更
- **弃用（Deprecated）**：即将移除的功能
- **移除（Removed）**：已移除的功能
- **修复（Fixed）**：Bug 修复
- **安全（Security）**：安全修复

---

## 相关链接

- [GitHub Releases](https://github.com/FSoft-AI4Code/CodeWiki/releases)
- [Issue Tracker](https://github.com/FSoft-AI4Code/CodeWiki/issues)
- [Documentation](https://github.com/FSoft-AI4Code/CodeWiki#readme)
- [Paper](https://arxiv.org/abs/2510.24428)
