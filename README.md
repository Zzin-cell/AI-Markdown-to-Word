# md2word

> Markdown → Word 一键转换 · 数学公式完美保留 · 代码格式不乱

## 痛点

把 Markdown 转成 Word 时，最常见的三个翻车现场：

| 问题 | 原因 |
|------|------|
| **数学公式变乱码** | Word 只认 OMML 格式，不认识 `$...$` / `$$...$$` |
| **代码块失去高亮** | 几乎所有工具都放弃了 docx 的代码着色 |
| **流程图直接消失** | Mermaid 在 Word 里根本不会被渲染 |

网络上能找到的方案要么需要手动操作十几步，要么干脆把数学公式截图贴回去——公式既不能编辑，放大还模糊。

`md2word` 用一个命令把这些全搞定。

## 原理

底层使用 [Pandoc](https://pandoc.org/)（John MacFarlane 开发的文档转换神器），关键参数：

```
pandoc input.md -o output.docx --mathml
```

`--mathml` 这一行做了什么：Pandoc 把 Markdown 里的 LaTeX 公式先转成标准 MathML，再嵌入 Word 原生的 OMML（Office Math Markup Language）。结果就是——你在 Word 里双击公式，它弹出来的是可编辑的公式编辑器，不是一张模糊的截图。

数学分隔符全面支持：

| 类型 | 写法 | 示例 |
|------|------|------|
| 行内公式（美元符） | `$...$` | `$E=mc^2$` |
| 块级公式（双美元） | `$$...$$` | `$$\sum_{i=1}^n x_i$$` |
| 行内公式（反斜杠） | `\(...\)` | `\(\hat{\beta}\)` |

## 效果演示

**转换前（Markdown）：**

```markdown
最小二乘解：
$$\hat{\beta} = (X^TX)^{-1}X^TY$$

信息增益：
$$g(D, X_j) = En(D) - En(D|X_j)$$
```

**转换后（Word .docx）：**
- 公式变为 Word 原生 OMML 对象，可双击编辑
- 字号、颜色、对齐方式与上下文一致
- 可以直接在 Word 里继续写论文、做汇报

**代码块：**

```python
def compound_interest(principal, rate, years):
    return principal * (1 + rate) ** years
```

- 转为等宽字体（Consolas / Courier New），缩进原样保留
- ⚠️ 语法高亮不在 docx 中生效（Pandoc 限制，见下方方案）

## 安装

### 前提：安装 Pandoc

**Windows (winget):**
```bash
winget install JohnMacFarlane.Pandoc
```

**macOS:**
```bash
brew install pandoc
```

**Linux:**
```bash
sudo apt install pandoc
```

### 获取本脚本

```bash
git clone https://github.com/YOUR_USERNAME/md2word.git
cd md2word
chmod +x convert.sh
```

或者直接复制 `convert.sh` 到路径中的任意位置。

## 使用

```bash
# 基础转换：.md → .docx（公式 → 可编辑 OMML）
./convert.sh input.md

# 指定输出路径
./convert.sh input.md /path/to/output.docx

# 生成 HTML（带代码语法高亮）
./convert.sh input.md --html
```

## 代码高亮怎么办？

Pandoc 的 docx 输出不支持语法高亮——这是上游限制，不是本脚本的问题。

**推荐方案：HTML 中转**

```bash
./convert.sh document.md --html
# → 生成 document.html
# → 浏览器打开 → 全选 Ctrl+A → 粘贴到 Word
```

HTML 模式下代码会带上完整的语法着色（基于 `--highlight-style=tango`）。

| 方案 | 公式 | 代码高亮 | 操作量 |
|------|------|----------|--------|
| 直接转 docx | ✅ OMML 可编辑 | ❌ 无高亮 | 一条命令 |
| HTML 中转 | ✅ MathML | ✅ 完整高亮 | 命令+复制粘贴 |
| 手动粘贴 | ❌ 乱码 | ❌ 丢失 | 噩梦 |

## 已知限制

| 限制 | 说明 | 补救 |
|------|------|------|
| 代码块无语法高亮 | Pandoc docx writer 的限制 | 用 `--html` 模式 |
| HTML 折叠块 `<details>` | 在 docx 中变成纯文本 | 手动处理 |
| Mermaid 流程图 | Pandoc 不内置渲染 | 安装 `mermaid-filter` |
| ASCII 图表 | 可能换行错位 | Word 内微调 |

## 文件结构

```
md2word/
├── README.md     # 你正在看的
└── convert.sh    # 核心转换脚本
```

> Pandoc 二进制文件不包含在仓库中（~200MB）。脚本会优先使用系统 PATH 中的 pandoc，其次提示下载。

## 许可证

MIT License — 随意使用、修改、分发。
