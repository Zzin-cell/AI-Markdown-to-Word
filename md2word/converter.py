"""Pandoc 转换引擎 — 全格式支持 + 内容统计。"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .utils import safe_print

# ── 格式预设 ───────────────────────────────────────────────
# 每个格式定义: 扩展名, Pandoc writer, 额外参数, 说明
FORMATS: Dict[str, Dict] = {
    "docx": {
        "ext": ".docx",
        "desc": "Word 文档 — 公式 OMML 可编辑，图片嵌入，表格保留",
        "icon": "📄",
        "extra_args": [],
        "recommend": True,
    },
    "pptx": {
        "ext": ".pptx",
        "desc": "PowerPoint 幻灯片 — 每个 # 标题为一页",
        "icon": "📊",
        "extra_args": [],
        "recommend": True,
    },
    "html": {
        "ext": ".html",
        "desc": "HTML 网页 — 代码语法高亮，图片内嵌，自包含",
        "icon": "🌐",
        "extra_args": ["--standalone", "--self-contained", "--highlight-style=tango"],
        "recommend": True,
    },
    "pdf": {
        "ext": ".pdf",
        "desc": "PDF 文档 — 先转 HTML 再生成 PDF（需 wkhtmltopdf）",
        "icon": "📕",
        "extra_args": ["--standalone", "--self-contained", "--highlight-style=tango"],
        "pdf_engine": "wkhtmltopdf",
    },
    "epub": {
        "ext": ".epub",
        "desc": "ePub 电子书 — Kindle / Apple Books 可读",
        "icon": "📖",
        "extra_args": ["--standalone"],
        "recommend": False,
    },
    "odt": {
        "ext": ".odt",
        "desc": "OpenDocument — LibreOffice / OpenOffice 格式",
        "icon": "📝",
        "extra_args": [],
        "recommend": False,
    },
    "latex": {
        "ext": ".tex",
        "desc": "LaTeX 源码 — 论文 / 学术排版",
        "icon": "📐",
        "extra_args": ["--standalone"],
        "recommend": False,
    },
    "rst": {
        "ext": ".rst",
        "desc": "reStructuredText — Python 文档标准格式",
        "icon": "📋",
        "extra_args": [],
        "recommend": False,
    },
    "md": {
        "ext": ".md",
        "desc": "Markdown — 格式化 / 清洗后重新输出",
        "icon": "📝",
        "extra_args": ["--standalone"],
        "recommend": False,
    },
    "txt": {
        "ext": ".txt",
        "desc": "纯文本 — 去除所有格式，仅保留文字",
        "icon": "📃",
        "extra_args": ["--to", "plain"],
        "recommend": False,
    },
}


def list_formats(show_all: bool = False) -> str:
    """格式化列出所有支持的输出格式。"""
    lines = []
    for key, fmt in FORMATS.items():
        if show_all or fmt.get("recommend"):
            tag = " [推荐]" if fmt.get("recommend") else ""
            lines.append(f"  {fmt['icon']} {key:6s} → {fmt['ext']:5s}  {fmt['desc']}{tag}")
    return "\n".join(lines)


def get_format(key: str) -> Optional[Dict]:
    """根据 key 获取格式定义，找不到返回 None。"""
    return FORMATS.get(key.lower())


def resolve_output(input_file: str, fmt_key: str, output_file: str = "") -> str:
    """根据格式自动生成输出文件路径。"""
    fmt = get_format(fmt_key)
    if not fmt:
        raise ValueError(f"不支持的格式: {fmt_key}\n支持的格式: {', '.join(FORMATS)}")
    if output_file:
        return output_file
    base = os.path.splitext(os.path.basename(input_file))[0]
    dname = os.path.dirname(input_file) or "."
    return os.path.join(dname, base + fmt["ext"])


# ── 统计 ──

def stats(filepath: str) -> Tuple[int, ...]:
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    img = len(re.findall(r"!\[.*?\]\(.*?\)", text))
    table = len(re.findall(r"^\+.*\+$", text, re.MULTILINE)) + \
             len(re.findall(r"^\|.*\|.*\|$", text, re.MULTILINE))
    math = text.count("$$") // 2
    code = text.count("```") // 2
    mermaid = text.count("```mermaid")
    headings = len(re.findall(r"^# ", text, re.MULTILINE))
    return img, table, math, code, mermaid, headings


def report(img: int, table: int, math: int, code: int,
           mermaid: int, headings: int, use_mermaid: bool = False) -> None:
    safe_print("")
    safe_print("  +-- 内容统计 ---------------------------------------+")
    if headings:
        safe_print(f"  |  # 标题:   {headings} 个                                  |")
    if img:
        safe_print(f"  |  图片:     {img} 张                                  |")
    if table:
        safe_print(f"  |  表格:     {table} 行                                 |")
    if math:
        safe_print(f"  |  公式:     {math} 个 (OMML/MathML)                   |")
    if code:
        safe_print(f"  |  代码块:   {code} 个                                  |")
    if mermaid and use_mermaid:
        safe_print(f"  |  Mermaid:  {mermaid} 个 (已渲染)                      |")
    elif mermaid:
        safe_print(f"  |  Mermaid:  {mermaid} 个 (加 --mermaid 渲染)          |")
    safe_print("  +----------------------------------------------------+")


# ── 转换 ──

def run(
    pandoc: str,
    input_file: str,
    output_file: str,
    fmt_key: str,
    *,
    toc: bool = False,
    mermaid: bool = False,
    ref_doc: str = "",
    resource_path: str = "",
    metadata_title: str = "",
) -> None:
    """执行 pandoc 转换。

    Args:
        pandoc: pandoc 可执行文件路径。
        input_file: 输入的 .md 文件。
        output_file: 输出文件路径。
        fmt_key: 输出格式 key (docx/html/pptx/pdf/...)。
        toc: 是否生成目录。
        mermaid: 是否启用 mermaid-filter。
        ref_doc: 参考模板文件路径。
        resource_path: 图片搜索根目录。
        metadata_title: 文档标题元数据。
    """
    fmt = get_format(fmt_key)
    if not fmt:
        raise ValueError(f"未知格式: {fmt_key}")

    args: List[str] = [
        pandoc, input_file, "-o", output_file,
        "--from", "markdown+tex_math_dollars+tex_math_single_backslash",
    ]

    # 公式：docx/pptx/odt 用 --mathml，其他格式默认
    if fmt_key in ("docx", "pptx", "odt"):
        args.append("--mathml")

    # 目录
    if toc and fmt_key in ("docx", "html", "pdf", "epub", "odt", "pptx"):
        args += ["--toc", "--toc-depth=3"]

    # 模板
    if ref_doc and os.path.isfile(ref_doc):
        args += [f"--reference-doc={ref_doc}"]
    elif ref_doc:
        safe_print(f"[WARN]  模板不存在: {ref_doc}，已忽略")

    # 资源路径
    if resource_path:
        args += [f"--resource-path={os.path.abspath(resource_path)}"]

    # 标题
    if metadata_title:
        args += ["--metadata", f"title={metadata_title}"]
    elif fmt_key in ("html", "pdf", "epub"):
        args += ["--metadata", f"title={Path(input_file).stem}"]

    # Mermaid
    if mermaid:
        import shutil
        if shutil.which("mmdc") or shutil.which("npx"):
            args += ["-F", "mermaid-filter"]

    # 格式额外参数
    extra = fmt.get("extra_args", [])
    if extra:
        args += extra

    # PDF 需要 pdflatex 或 wkhtmltopdf
    pdf_engine = fmt.get("pdf_engine", "")
    if pdf_engine:
        import shutil
        if shutil.which(pdf_engine):
            args += ["--pdf-engine=" + pdf_engine]
        else:
            safe_print(f"[WARN]  {pdf_engine} 未安装，将尝试默认引擎")

    subprocess.run(args, check=True)


def run_clipboard_html(
    pandoc: str,
    input_file: str,
    output_file: str,
    *,
    toc: bool = False,
    resource_path: str = "",
) -> None:
    """生成粘贴就绪 HTML（MathML + base64 图片 + 代码高亮）。"""
    run(pandoc, input_file, output_file, "html", toc=toc, resource_path=resource_path)
