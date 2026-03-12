# CodeWiki v1.2.0 升级完成报告

## 完成的升级项

### ✅ 需求 1：多语言文档输出
- 支持通过配置文件设置输出文档的自然语言（中文、英文等）
- CLI 增加 `--language/-l` 参数覆盖配置

**配置方式**：
```json
{
  "output_language": "zh-CN"
}
```

**CLI 选项**：
```bash
codewiki generate --language en-US
codewiki generate -l zh-CN
```

---

### ✅ 需求 2：性能优化（分层扫描策略）
- 初始化时自动扫描目录，过滤依赖目录
- 获取文件数量和代码行数
- 超过阈值时自动进入分层处理模式
- AI 选择：哪些需要深度分析，哪些只需基础分析

**配置方式**：
```json
{
  "scan": {
    "auto_threshold": 1000,
    "enable_layered_scan": true,
    "max_depth": 2,
    "exclude_dirs": ["node_modules", ".venv", "__pycache__", ".git"],
    "file_line_threshold": 500
  }
}
```

**CLI 选项**：
```bash
codewiki generate --auto-threshold 500
codewiki generate --no-layered-scan
codewiki generate --scan-exclude-dirs "node_modules,.venv"
```

---

### ✅ 需求 3：智能文档读取（AI 辅助判断）
- AI 快速扫描文件内容，判断是否需要深度读取
- 简单文件简化处理，复杂文件深度分析
- 减少不必要的 token 消耗，提高生成速度

**实现方式**：
- `FileClassifier` 使用 LLM 进行文件分类
- 分为 `deep_analysis` 和 `basic_analysis` 两类
- 支持规则回退分类（当 LLM 失败时）

---

### ✅ 需求 4：并行处理优化
- 文件解析并行化（目前是顺序处理）
- 多个叶模块文档并行生成
- 使用信号量控制 LLM API 并发数

**配置方式**：
```json
{
  "parallel": {
    "parallel_parsing": true,
    "parallel_generation": true,
    "max_workers": 8,
    "max_concurrent_llm_calls": 5
  }
}
```

**CLI 选项**：
```bash
codewiki generate --max-workers 8
codewiki generate --no-parallel-parsing
codewiki generate --no-parallel-generation
codewiki generate --max-concurrent-llm-calls 10
```

---

### ✅ 需求 5：输出目录重构
- 支持扁平（flat）和分层（hierarchical）两种目录结构
- 按模块分组输出文件
- 生成目录索引文件

**目录结构对比**：

**Flat（默认，向后兼容）**：
```
output/
├── overview.md
├── module-a.md
├── module-b.md
└── module-c.md
```

**Hierarchical**：
```
output/
├── index.md              # 总索引
├── overview/
│   └── repository-overview.md
├── core/                 # 核心模块目录
│   ├── module-a/
│   │   └── index.md
│   └── module-b/
│       └── index.md
└── utils/                # 工具模块目录
    └── index.md
```

**CLI 选项**：
```bash
codewiki generate --directory-structure hierarchical
codewiki generate --no-index
```

---

## 提交历史

```
75e9de1 docs: add tests and documentation for new features
340dadc feat: add hierarchical output directory structure
610eeae feat: add parallel processing for file parsing and document generation
7f8c3a2 feat: add layered scanning system with AI-assisted file classification
7e4a08d feat: add multi-language output support
2d8d623 chore: add .worktrees to gitignore
```

---

## 修改/新增文件统计

| 阶段 | 修改文件 | 新增文件 | 代码行数变化 |
|------|---------|---------|-------------|
| 多语言支持 | 7 | 0 | +200 |
| 分层扫描 | 7 | 2 | +970 |
| 并行处理 | 8 | 0 | +330 |
| 目录重构 | 5 | 1 | +500 |
| 测试文档 | 2 | 6 | +1200 |
| **总计** | **29** | **9** | **+3200** |

---

## 测试覆盖

- `tests/test_scanner.py` - DirectoryScanner 测试（260 行）
- `tests/test_file_classifier.py` - FileClassifier 测试（340 行）
- `tests/test_output_manager.py` - OutputManager 测试（420 行）
- `tests/test_parallel_config.py` - 并行配置测试（450 行）

---

## 下一步

1. 在真实项目中测试新功能
2. 根据反馈调整配置参数
3. 考虑将更改合并到主分支
