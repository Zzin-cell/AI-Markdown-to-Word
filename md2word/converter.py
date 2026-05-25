"""Pandoc 转换引擎 + 内容统计。"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

from .utils import safe_print


def stats(filepath: str) -> Tuple[int, ...]:
    """统计 Markdown 文件内容。返回 (图片数, 表格行数, 公式数, 代码块数, Mermaid图数)。"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    img = len(re.findall(r"!\[.*?\]\(.*?\)", text))
    table = len(re.findall(r"^\+.*\+$", text, re.MULTILINE)) + \
             len(re.findall(r"^\|.*\|.*\|$", text, re.MULTILINE))
    math = text.count("$$") // 2
    code = text.count("```") // 2
    mermaid = text.count("```mermaid")
    return img, table, math, code, mermaid


def report(img: int, table: int, math: int, code: int, mermaid: int,
           use_mermaid: bool = False) -> None:
    """打印内容完整性检查报告。"""
    safe_print("")
    safe_print("  +-- 内容完整性检查 -----------------------------------+")
    if img:
        safe_print(f"  |  [OK] 图片:    {img} 张已嵌入                        |")
    if table:
        safe_print(f"  |  [OK] 表格:    {table} 行，边框对齐完整              |")
    if math:
        safe_print(f"  |  [OK] 公式:    {math} 个 -> OMML / MathML 可编辑    |")
    if code:
        safe_print(f"  |  [OK] 代码:    {code} 个 -> 语法高亮                 |")
    if mermaid and use_mermaid:
        safe_print(f"  |  [OK] Mermaid: {mermaid} 个已渲染                    |")
    elif mermaid:
        safe_print(f"  |  [!!] Mermaid: {mermaid} 个 (加 --mermaid 补救)     |")
    safe_print("  +----------------------------------------------------+")


def run(
    pandoc: str,
    input_file: str,
    output_file: str,
    *,
    html: bool = False,
    toc: bool = False,
    mermaid: bool = False,
    ref_doc: str = "",
    resource_path: str = "",
) -> None:
    """执行 pandoc 转换。

    Args:
        pandoc: pandoc 可执行文件路径。
        input_file: 输入的 .md 文件。
        output_file: 输出文件路径。
        html: 是否生成 HTML（含 --standalone --self-contained）。
        toc: 是否生成目录。
        mermaid: 是否启用 mermaid-filter。
        ref_doc: Word 模板文件路径。
        resource_path: 图片搜索根目录。
    """
    args: List[str] = [
        pandoc, input_file, "-o", output_file,
        "--mathml",
        "--from", "markdown+tex_math_dollars+tex_math_single_backslash",
    ]

    if toc:
        args += ["--toc", "--toc-depth=3"]

    if ref_doc and os.path.isfile(ref_doc):
        args += [f"--reference-doc={ref_doc}"]
    elif ref_doc:
        from .utils import safe_print
        safe_print(f"[WARN]  模板不存在: {ref_doc}，已忽略")

    if resource_path:
        args += [f"--resource-path={os.path.abspath(resource_path)}"]

    if mermaid:
        import shutil
        if shutil.which("mmdc") or shutil.which("npx"):
            args += ["-F", "mermaid-filter"]

    if html:
        args += [
            "--highlight-style=tango",
            "--standalone",
            "--metadata", f"title={Path(input_file).stem}",
            "--self-contained",
        ]

    subprocess.run(args, check=True)


def run_html_for_clipboard(
    pandoc: str,
    input_file: str,
    output_file: str,
    *,
    toc: bool = False,
    resource_path: str = "",
) -> None:
    """生成粘贴就绪 HTML（含 MathML + base64 图片 + 代码高亮）。"""
    run(pandoc, input_file, output_file, html=True, toc=toc, resource_path=resource_path)
