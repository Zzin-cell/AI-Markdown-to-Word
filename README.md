# AI-Markdown-to-Word

> 🔥 AI 生成的 Markdown → Word/PPT/PDF/HTML/ePub 全格式 · 交互式向导零门槛 · 粘贴即用

[![GitHub stars](https://img.shields.io/github/stars/Zzin-cell/AI-Markdown-to-Word)](https://github.com/Zzin-cell/AI-Markdown-to-Word/stargazers)
[![GitHub license](https://img.shields.io/github/license/Zzin-cell/AI-Markdown-to-Word)](https://github.com/Zzin-cell/AI-Markdown-to-Word/blob/master/LICENSE)

**关键词**：Markdown 全格式转换 | AI 剪贴板 | Word PPT PDF HTML ePub | 交互式向导 | AI小白友好 | Pandoc

## 为什么需要这个工具？

你在 DeepSeek、ChatGPT、Claude 里精心调教出的答案——想保存成文档时傻眼了：

- 粘贴到 Word → 公式变成 `$$...$$` 乱码
- 想做成 PPT → 手动复制粘贴到手软
- 图片只剩裂开的链接 · 表格对齐全丢 · 代码高亮全无

**v5 一句话**：安装 Pandoc → 终端输入 `md2word` → 跟着提示走 → 完成。

## 快速开始（AI 小白友好）

### 第一步：安装 Pandoc

```bash
winget install JohnMacFarlane.Pandoc   # Windows
brew install pandoc                     # macOS
sudo apt install pandoc                 # Linux
```

### 第二步：安装 md2word

```bash
pip install git+https://github.com/Zzin-cell/AI-Markdown-to-Word.git
```

### 第三步：使用

```bash
md2word              # 交互式向导（推荐！跟着提示走就行）
md2word -p           # 粘贴就绪：复制 AI 回答 → 执行 → Word 里 Ctrl+V
md2word -c           # 剪贴板 → .docx
md2word doc.md       # 转 Word
md2word doc.md -f pptx  # 转 PowerPoint
md2word doc.md -f html --toc   # 转 HTML + 目录
```

> 零外部依赖，仅需 Python 3.8+。Windows/macOS/Linux 全平台。

## 快速开始

## v5.0 全格式转换

| 格式 | 命令 | 输出 | 说明 |
|------|------|------|------|
| **Word** | `md2word doc.md` 或 `md2word -c` | `.docx` | 公式 OMML 可双击编辑 |
| **PowerPoint** | `md2word doc.md -f pptx` | `.pptx` | 每个 `#` 标题一页幻灯片 |
| **HTML** | `md2word doc.md -f html` | `.html` | 代码语法高亮，自包含 |
| **PDF** | `md2word doc.md -f pdf` | `.pdf` | 需 wkhtmltopdf |
| **ePub** | `md2word doc.md -f epub` | `.epub` | Kindle/Apple Books |
| **粘贴就绪** | `md2word -p` | HTML→剪贴板 | Word Ctrl+V，公式表格图片完美 |
| **纯文本** | `md2word doc.md -f txt` | `.txt` | 只要文字 |

## 三大使用方式

### 1. 交互式向导（零门槛 · 新手推荐）

```bash
md2word        # 直接回车，跟着提示一步步走
md2word -w     # 同上

# 向导会问你:
#   → 从剪贴板还是文件？
#   → 自动检测 AI 模型并清洗
#   → 选输出格式（Word/PPT/HTML/PDF...）
#   → 要不要目录？
#   → 保存到哪？
#   → 转换完自动打开
```

### 2. 剪贴板模式（快）

```bash
md2word -p                    # 粘贴就绪：复制→敲命令→Word Ctrl+V
md2word -c                    # 剪贴板→docx，自动打开
md2word -p --from deepseek    # 指定 AI 模型清洗
```

### 3. 文件模式（命令行）

```bash
md2word doc.md                # 默认转 docx
md2word doc.md -f pptx        # 转 PowerPoint
md2word doc.md -f html --toc  # 转 HTML + 目录
```

## 多模型支持

| AI 模型 | `--from` 参数 | 自动清洗内容 |
|---------|--------------|-------------|
| **DeepSeek** | `--from deepseek` | 🤖 标题 + "已深度思考" 折叠块 + 分隔线 |
| **ChatGPT** | `--from chatgpt` | ChatGPT 标签行 |
| **Claude** | `--from claude` | Claude 标签 + 思考块 + XML 残留 |
| **Kimi** | `--from kimi` | Kimi 思考引用块 |
| **自动检测** | 默认 | 根据内容特征自动判断 |

```bash
# 剪贴板 + 指定模型 + 多选项
./convert.sh -c --from deepseek --toc
./convert.sh -c --from claude --html

# v4.0 粘贴就绪 + 指定模型
./convert.sh -p --from deepseek
./convert.sh -p --from claude --toc
```

## 支持的内容

| Markdown 写法 | 输出效果 |
|-------------|----------|
| `$E=mc^2$` / `$$\sum_{i=1}^n$$` / `\(\hat{\beta}\)` | ✅ Word OMML 可双击编辑的公式 |
| `![图片](img/photo.png)` 本地路径 | ✅ 自动查找并嵌入 docx |
| `![图片](https://example.com/img.png)` 网络 URL | ✅ 自动下载嵌入 |
| `| a | b |` 管道表 / `+--+--+` 网格表 | ✅ 边框 + 对齐 + 合并单元格 |
| ` ```python ``` ` 代码块 | ✅ 等宽字体 + 缩进（`-p` / `--html` 带语法高亮） |
| ` ```mermaid ``` ` 流程图 | ✅ `--mermaid` 渲染为图片嵌入 |
| `#` `##` `###` 标题 | ✅ `--toc` 自动生成目录 |

## 效果

```bash
$ ./convert.sh -c --from deepseek
[INFO]  Pandoc: /usr/local/bin/pandoc
[INFO]  剪贴板模式: 正在读取剪贴板...
[INFO]  模型检测: deepseek
[OK]    内容已清洗 (deepseek) → /tmp/统计机器学习_完全统一知识体系.md
[INFO]  输入: /tmp/统计机器学习_完全统一知识体系.md (2327 行)
[INFO]  统计: 0图 18表行 129公式 3代码块 0Mermaid
[INFO]  模式: DOCX（公式OMML + 图片嵌入 + 表格保留）
[INFO]  转换中...
[OK]    已生成: ~/Desktop/md2word_exports/统计机器学习_完全统一知识体系.docx (76K)

  ┌─ 内容完整性检查 ─────────────────────────────────────┐
  │  ✅ 表格:    18 行，边框对齐完整                       │
  │  ✅ 公式:    129 个 → OMML 可编辑                      │
  │  ⚠️  代码:    3 个 → 等宽字体，语法高亮建议 --html      │
  └──────────────────────────────────────────────────────┘
[INFO]  正在打开文件...
```

粘贴就绪模式 v4.0：

```bash
$ ./convert.sh -p --from claude
[INFO]  Pandoc: /usr/local/bin/pandoc
[INFO]  粘贴就绪模式: 正在读取剪贴板...
[INFO]  模型检测: claude
[OK]    内容已清洗 (claude) → /tmp/SQL数据库完全指南.md
[INFO]  输入: /tmp/SQL数据库完全指南.md (1184 行)
[INFO]  统计: 0图 18表行 0公式 19代码块 0Mermaid
[INFO]  模式: 粘贴就绪（Markdown→HTML→剪贴板，Word 直接 Ctrl+V）
[INFO]  转换中...
[INFO]  写入剪贴板...
[OK]    剪贴板已就绪！打开 Word → Ctrl+V 即可粘贴

  ┌─ 内容完整性检查 ─────────────────────────────────────┐
  │  ✅ 表格:    18 行，边框对齐完整                      │
  │  ✅ 代码:    19 个 → 语法高亮                         │
  └──────────────────────────────────────────────────────┘
```

## 常见问题

**Q: 公式在 Word 里能编辑吗？**
A: 能。双击公式进入 Word 公式编辑器，不是截图。

**Q: 代码块有颜色吗？**
A: 用 `-p` 粘贴就绪模式，粘贴到 Word 自带语法高亮。docx 直接输出没有（Pandoc 限制）。

**Q: `-p` 和 `-c` 有什么区别？**
A: `-p` 把 HTML 写回剪贴板，你 Ctrl+V 粘贴到 Word；`-c` 生成 .docx 文件并自动打开。日常用 `-p` 更快。

**Q: 支持哪些 OS？**
A: Windows（PowerShell Get-Clipboard）/ macOS（pbpaste）/ Linux（xclip 或 wl-paste）。

**Q: 能批量转换吗？**
A: 能。`for f in *.md; do ./convert.sh "$f"; done`

## 文件结构

```
md2word/
├── README.md         # 说明文档
├── pyproject.toml    # Python 包配置 (pip install md2word)
├── convert.sh        # Bash 版 (v4.0, 需 Git Bash / WSL)
├── convert.py        # Python 单文件版 (零依赖, 无需 pip)
├── hook-stop.sh      # Claude Code 自动转换钩子 (可选)
└── md2word/          # Python 包 v5.0
    ├── __init__.py   # 包入口, 版本号
    ├── __main__.py   # python -m md2word
    ├── cli.py        # CLI + 交互式向导
    ├── clipboard.py  # 跨平台剪贴板
    ├── cleaners.py   # AI 模型清洗器
    ├── converter.py  # 全格式转换引擎
    └── utils.py      # 工具函数
```
```

> Pandoc 不在仓库中（~200MB）。脚本自动查找系统已安装的 pandoc。

## Claude Code 全自动转换（可选）

用 [Claude Code](https://claude.ai/code) 的话，可以更进一步——**连复制和敲命令都省了**。

配置 Stop Hook 后，每次 Claude 回复完，Word 文档自动出现在桌面。你只管对话，存文档的事全自动。

### 配置方法

把 `hook-stop.sh` 放到你的 Claude Code skill 目录（或任意路径），在 `~/.claude/settings.json` 中加入：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/skills/AI-Markdown-to-Word/hook-stop.sh",
            "async": true
          }
        ]
      }
    ]
  }
}
```

### 运行流程

```
你问 → Claude 答 → 回答结束 → Stop hook 自动触发
                                    ↓
                          从 transcript 提取回复
                                    ↓
                          Pandoc 转 .docx
                          （公式 OMML + 表格保留 + 代码等宽）
                                    ↓
                          桌面 AI_Word_Exports/
                          自动生成 .docx 文件
```

### 与剪贴板模式对比

| | 剪贴板 `-c` | Stop Hook |
|---|---|---|
| 操作 | 对话完 → Ctrl+C → 终端敲命令 | **零操作，全自动** |
| 触发 | 手动 | Claude 每次回复结束 |
| 适用 | 任何 AI 网页版 / 客户端 | Claude Code 用户专属 |
| 输出 | `桌面/md2word_exports/` | `桌面/AI_Word_Exports/` |

> 前置：系统需安装 Python 3。Pandoc 自动查找同目录 `pandoc.exe` 或系统 PATH，无需额外配置。

## 许可证

MIT License

---

**相关仓库**
- [python-ai-guide](https://github.com/Zzin-cell/python-ai-guide) — Python 从入门到 AI 全栈教程
