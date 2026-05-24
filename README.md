# md2word

> 不同 AI 模型生成的 Markdown → 一键复制转 Word · 公式可编辑 · 图片嵌入 · 表格不丢

## 为什么需要这个工具？

你在 DeepSeek、ChatGPT、Claude 里精心调教出的答案，满屏 LaTeX 公式、Python 代码、Mermaid 流程图——想存成 Word 文档时傻眼了：

- 粘贴到 Word → 公式变成 `$$...$$` 乱码
- 图片只剩裂开的链接
- 表格对齐全丢
- 代码块颜色全无
- DeepSeek 的"已深度思考"折叠块变成占位文本

**md2word 三步解决**：复制 → 终端敲一条命令 → Word 自动打开，干净整洁。

## 快速开始

### 安装

```bash
# 1. 必须：Pandoc
winget install JohnMacFarlane.Pandoc   # Windows
brew install pandoc                     # macOS
sudo apt install pandoc                 # Linux

# 2. 可选：Mermaid 流程图
npm install -g @mermaid-js/mermaid-cli mermaid-filter

# 3. 克隆
git clone https://github.com/Zzin-cell/md2word.git
cd md2word
chmod +x convert.sh
```

### 剪贴板模式（从 AI 对话框复制后一键出 Word）

```bash
# 在 AI 对话框 Ctrl+C 复制 → 终端执行：
./convert.sh -c

# 自动做的事：
# 1. 读取剪贴板
# 2. 检测是哪个模型的输出
# 3. 清洗掉 "已深度思考" 等 AI 专属标记
# 4. 公式→OMML 图片→嵌入 表格→保留
# 5. 生成 docx 并自动打开
```

### 文件模式

```bash
./convert.sh document.md              # 基础转换
./convert.sh document.md --toc        # 含目录
./convert.sh document.md --html       # 代码高亮版（HTML→粘贴到 Word）
./convert.sh document.md --mermaid    # 渲染流程图
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
```

## 支持的内容

| Markdown 写法 | 输出效果 |
|-------------|----------|
| `$E=mc^2$` / `$$\sum_{i=1}^n$$` / `\(\hat{\beta}\)` | ✅ Word OMML 可双击编辑的公式 |
| `![图片](img/photo.png)` 本地路径 | ✅ 自动查找并嵌入 docx |
| `![图片](https://example.com/img.png)` 网络 URL | ✅ 自动下载嵌入 |
| `| a | b |` 管道表 / `+--+--+` 网格表 | ✅ 边框 + 对齐 + 合并单元格 |
| ` ```python ``` ` 代码块 | ✅ 等宽字体 + 缩进（HTML 模式带语法高亮） |
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

## 常见问题

**Q: 公式在 Word 里能编辑吗？**
A: 能。双击公式进入 Word 公式编辑器，不是截图。

**Q: 代码块有颜色吗？**
A: 直接 docx 没有（Pandoc 限制）。加 `--html` 生成 HTML，浏览器打开→全选→粘贴到 Word 就有颜色了。

**Q: 剪贴板模式支持哪些 OS？**
A: Windows（PowerShell Get-Clipboard）/ macOS（pbpaste）/ Linux（xclip 或 wl-paste）。

**Q: 能批量转换吗？**
A: 能。`for f in *.md; do ./convert.sh "$f"; done`

## 文件结构

```
md2word/
├── README.md     # 说明文档
└── convert.sh    # 核心脚本 (~280行)
```

> Pandoc 不在仓库中（~200MB）。脚本自动查找系统已安装的 pandoc。

## 许可证

MIT License

---

**相关仓库**
- [python-ai-guide](https://github.com/Zzin-cell/python-ai-guide) — Python 从入门到 AI 全栈教程
