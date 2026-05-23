# md2word

> Markdown → Word 一键转换 · 公式可编辑 · 图片自动嵌入 · 表格不丢 · 代码不乱

## 痛点

把 Markdown 转成 Word 时，最常见的五个翻车现场：

| 问题 | 原因 |
|------|------|
| **数学公式变乱码** | Word 只认 OMML 格式，不认识 `$...$` / `$$...$$` |
| **图片丢失或变模糊** | 截图方式粘贴，分辨率低；本地路径图片被忽略 |
| **表格变纯文本** | 对齐丢失，边框消失，合并单元格全乱 |
| **代码块失去高亮** | docx 几乎没有工具做代码着色 |
| **流程图直接消失** | Mermaid 语法在 Word 里不会被渲染 |

`md2word` 用一个命令全部解决。

## 支持的内容类型全览

| 内容 | Markdown 写法 | 输出效果 |
|------|--------------|----------|
| 行内公式 | `$E=mc^2$` | ✅ Word OMML 可编辑公式 |
| 块级公式 | `$$\sum_{i=1}^n$$` | ✅ Word OMML 可编辑公式 |
| 本地图片 | `![](img/arch.png)` | ✅ 自动查找并嵌入 docx |
| 网络图片 | `![](https://.../img.png)` | ✅ 自动下载嵌入 |
| 管道表格 | `\| a \| b \|` | ✅ 边框 + 对齐完整保留 |
| 网格表格 | `+---+---+` | ✅ 支持合并单元格 |
| 代码块 | ` ```python ... ``` ` | ✅ 等宽字体 + 缩进（HTML 带高亮） |
| Mermaid 图 | ` ```mermaid ... ``` ` | ✅ 需 `--mermaid`，渲染为图片嵌入 |
| 自动目录 | 基于 `#` 标题层级 | ✅ `--toc` 自动生成 |

## 原理

底层使用 [Pandoc](https://pandoc.org/)，关键参数：

```bash
pandoc input.md -o output.docx --mathml --resource-path="$(dirname input.md)"
```

### 图片是怎么保留的

```
![架构图](img/architecture.png)
   │                │
   │   --resource-path 指定搜索根目录
   │   Pandoc 自动找到图片，读入字节流
   │   直接写进 docx 的 /word/media/ 目录
   │
   └──→ Word 打开后图片就在文档里，不是链接
```

- **本地图片**：`--resource-path` 告诉 Pandoc 去哪里找相对路径的图片
- **网络图片**：Pandoc 自动下载，缓存后嵌入（需要网络连接）
- **SVG**：Pandoc 3.x 原生支持，直接嵌为矢量图
- **图片格式**：PNG / JPG / SVG / GIF 全覆盖

### 表格是怎么保留的

Pandoc 原生解析 Markdown 表格语法，直接输出 Word 的 `<w:tbl>` XML 节点：

| Markdown | Word 内部 |
|----------|-----------|
| `\|` 分隔符 | 单元格边界 |
| `:---` 左对齐 | `<w:jc w:val="left">` |
| `:---:` 居中 | `<w:jc w:val="center">` |
| `---:` 右对齐 | `<w:jc w:val="right">` |

支持四种表格语法：管道表、网格表、简单表、多行表。

## 安装

### 前提：安装 Pandoc

```bash
# Windows
winget install JohnMacFarlane.Pandoc

# macOS
brew install pandoc

# Linux
sudo apt install pandoc
```

### 可选：Mermaid 流程图支持

```bash
npm install -g @mermaid-js/mermaid-cli
npm install -g mermaid-filter
```

### 获取本脚本

```bash
git clone https://github.com/Zzin-cell/md2word.git
cd md2word
chmod +x convert.sh
```

## 使用

```bash
# 基础转换（公式 + 图片 + 表格）
./convert.sh document.md

# 指定输出路径
./convert.sh document.md report.docx

# 自动生成目录
./convert.sh document.md --toc

# 代码语法高亮（HTML 中转）
./convert.sh document.md --html

# Mermaid 流程图渲染
./convert.sh document.md --mermaid

# 自定义 Word 样式模板
./convert.sh document.md --ref template.docx

# 全套：目录 + 流程图
./convert.sh document.md --toc --mermaid
```

### 转换完成后的输出示例

```
[INFO]  Pandoc: /usr/local/bin/pandoc
[INFO]  输入: document.md (1200 行)
[INFO]  统计: 8 图片, 52 表格行, 15 块公式, 6 代码块, 3 Mermaid
[INFO]  模式: DOCX（公式OMML + 图片嵌入 + 表格保留）
[INFO]  转换中...
[OK]    已生成: document.docx (156K)

  ┌─ 内容完整性检查 ─────────────────────────────┐
  │  ✅ 图片:   8 张已嵌入 docx                    │
  │  ✅ 表格:   已保留边框和对齐                     │
  │  ✅ 公式:   15 个 → OMML 可编辑                 │
  │  ⚠️  代码:   6 个 → 等宽字体，无语法高亮         │
  │  ❌ Mermaid: 3 个已丢失 (未加 --mermaid)        │
  └───────────────────────────────────────────────┘
```

## 图片处理 FAQ

### 图片找不到怎么办？

```bash
# 检查图片路径，确保 --resource-path 正确
# 脚本默认将 .md 文件所在目录设为搜索根目录

# 如果图片在上级目录：
./convert.sh document.md --ref template.docx
# 手动调整 resource-path（编辑脚本最后一行）
```

### 网络图片下载失败？

1. 先把图片手动下载到本地
2. 把 Markdown 里的 `![](https://...)` 改成 `![](img/xxx.png)`
3. 重新转换

### 能压缩图片吗？

docx 内嵌的是原始分辨率图片。转换后在 Word 里：`文件 → 压缩图片 → 选择分辨率`。

## 表格处理 FAQ

### 支持合并单元格吗？

用 Pandoc 的**网格表（grid table）**语法：

```markdown
+----------+----------+----------+
| 列1      | 列2      | 列3      |
+==========+==========+==========+
| 跨两列             || 列3      |
+----------+----------+----------+
```

### 表格有斑马纹/主题色吗？

默认无——Pandoc 生成的表格是朴素的黑边框。需要自定义样式：

1. 在 Word 里做好模板表格（带斑马纹/主题色）
2. 保存为 `template.docx`
3. 转换时用 `--ref template.docx`

## 代码高亮对比

| 方案 | 公式 | 图片 | 表格 | 代码高亮 | 操作量 |
|------|------|------|------|----------|--------|
| **直接转 docx** | ✅ OMML | ✅ 嵌入 | ✅ 保留 | ❌ 无 | 一条命令 |
| **HTML 中转** | ✅ MathML | ✅ 嵌入 | ✅ 保留 | ✅ tango | 命令+粘贴 |
| 手动复制粘贴 | ❌ 乱码 | ❌ 丢失 | ❌ 丢失 | ❌ 丢失 | 噩梦 |

## 已知限制

| 限制 | 说明 | 补救 |
|------|------|------|
| 代码块无语法高亮（docx） | Pandoc docx writer 限制 | `--html` 模式 |
| HTML 折叠块 `<details>` | docx 中变纯文本 | 手动处理 |
| Mermaid | 需额外安装 mermaid-filter | `npm install -g mermaid-filter` |
| ASCII 图表 | 可能换行错位 | Word 内微调 |
| 网络图片 | 需要网络连接 | 预先下载到本地 |

## 文件结构

```
md2word/
├── README.md     # 说明文档
└── convert.sh    # 核心转换脚本
```

> Pandoc 二进制文件不包含在仓库中（~200MB）。脚本会按以下顺序查找：系统 PATH → 常见安装位置 → 技能目录 → 提示安装。

## 许可证

MIT License — 随意使用、修改、分发。

---

**相关资源**
- [Pandoc 官方文档](https://pandoc.org/MANUAL.html)
- [Pandoc Markdown 语法](https://pandoc.org/MANUAL.html#pandocs-markdown)
- [Python 从入门到 AI 全栈开发指导大全](https://github.com/Zzin-cell/python-ai-guide) — 配套教程
