"""CLI 主入口 + 参数解析 + 主流程编排。

作为可安装包时: md2word -p
作为模块时:     python -m md2word -p
直接运行目录:   python md2word/ -p
"""

import os
import sys
import tempfile
from argparse import ArgumentParser, Namespace

from . import clipboard, cleaners, converter, utils

# ── 颜色 ──
_RED = "\033[0;31m"
_GREEN = "\033[0;32m"
_YELLOW = "\033[1;33m"
_CYAN = "\033[0;36m"
_NC = "\033[0m"


def _info(msg):   utils.safe_print(f"{_CYAN}[INFO]{_NC}  {msg}")
def _ok(msg):     utils.safe_print(f"{_GREEN}[OK]{_NC}    {msg}")
def _warn(msg):   utils.safe_print(f"{_YELLOW}[WARN]{_NC}  {msg}")
def _err(msg):    utils.safe_print(f"{_RED}[ERR]{_NC}   {msg}")


def build_parser() -> ArgumentParser:
    p = ArgumentParser(
        prog="md2word",
        description="md2word v4.0 — Markdown → Word 一键转换",
    )
    p.add_argument("input", nargs="?", help="输入 .md 文件，或 -c / -p 使用剪贴板模式")
    p.add_argument("output", nargs="?", help="输出文件路径（可选）")
    p.add_argument("-c", "--clipboard", action="store_true",
                   help="剪贴板模式：读取剪贴板 → 生成 .docx")
    p.add_argument("-p", "--paste", action="store_true",
                   help="粘贴就绪模式：Markdown→HTML→剪贴板，Word Ctrl+V")
    p.add_argument("--html", action="store_true", help="生成 HTML（含代码语法高亮）")
    p.add_argument("--toc", action="store_true", help="生成目录")
    p.add_argument("--mermaid", action="store_true", help="渲染 Mermaid 流程图")
    p.add_argument("--ref", default="", help="Word 模板文件 (.docx)")
    p.add_argument("--from", dest="from_model", default="auto",
                   help="指定 AI 模型: deepseek/chatgpt/claude/kimi/auto")
    return p


def handle_clipboard(args: Namespace) -> tuple:
    """处理剪贴板读取 + 清洗，返回 (input_file, output_file, temp_md_to_cleanup)。"""
    if args.paste:
        _info("粘贴就绪模式: 正在读取剪贴板...")
    else:
        _info("剪贴板模式: 正在读取剪贴板...")

    raw = clipboard.read()
    if not raw.strip():
        _err("剪贴板为空，请先复制 AI 回答内容。")
        sys.exit(1)

    cleaned = cleaners.sanitize(raw, args.from_model)
    title = utils.generate_title(cleaned)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                     encoding="utf-8") as f:
        f.write(cleaned)
        temp_md = f.name
    _ok(f"内容已清洗 ({args.from_model}) → {temp_md}")

    if args.paste:
        output = tempfile.NamedTemporaryFile(suffix=".html", delete=False).name
    else:
        desktop = utils.get_desktop()
        exports = os.path.join(desktop, "md2word_exports")
        os.makedirs(exports, exist_ok=True)
        ext = ".html" if args.html else ".docx"
        output = args.output or os.path.join(exports, title + ext)

    return temp_md, output


def handle_file(args: Namespace) -> tuple:
    """处理文件输入，返回 (input_file, output_file)。"""
    if not os.path.isfile(args.input):
        _err(f"文件不存在: {args.input}")
        sys.exit(1)
    input_file = args.input
    if args.output:
        output = args.output
    else:
        base = os.path.splitext(os.path.basename(input_file))[0]
        dname = os.path.dirname(input_file) or "."
        ext = ".html" if args.html else ".docx"
        output = os.path.join(dname, base + ext)
    return input_file, output


def main(argv: list = None) -> None:
    parser = build_parser()

    # 无参数时打印帮助
    if len(sys.argv) == 1:
        parser.print_help()
        print("""
示例:
  md2word -p                         粘贴就绪 → 剪贴板 HTML → Word Ctrl+V
  md2word -c                         剪贴板 → .docx
  md2word doc.md --toc               文件 → 含目录 docx
  md2word doc.md --html              文件 → 代码高亮 HTML
  md2word -p --from claude           指定模型清洗

GitHub: https://github.com/Zzin-cell/AI-Markdown-to-Word
""")
        return

    args = parser.parse_args(argv)

    use_clipboard = args.clipboard or args.paste
    use_paste = args.paste

    # ── 找到 pandoc ──
    pandoc = utils.find_pandoc()
    if not pandoc:
        _err("Pandoc 未找到。安装方法:")
        print("  winget install JohnMacFarlane.Pandoc  (Windows)")
        print("  brew install pandoc                    (macOS)")
        print("  sudo apt install pandoc                (Linux)")
        sys.exit(1)
    _info(f"Pandoc: {pandoc}")

    # ── 获取输入 ──
    temp_md = ""
    if use_clipboard:
        input_file, output_file = handle_clipboard(args)
        temp_md = input_file
    else:
        input_file, output_file = handle_file(args)

    resource_path = os.path.dirname(input_file) or "."

    # ── 统计 ──
    lines = sum(1 for _ in open(input_file, "r", encoding="utf-8"))
    img_c, table_c, math_c, code_c, mermaid_c = converter.stats(input_file)
    _info(f"输入: {input_file} ({lines} 行)")
    _info(f"统计: {img_c}图 {table_c}表行 {math_c}公式 {code_c}代码块 {mermaid_c}Mermaid")

    # ── 转换 ──
    try:
        if use_paste:
            _info("模式: 粘贴就绪（Markdown→HTML→剪贴板，Word 直接 Ctrl+V）")
            converter.run_html_for_clipboard(
                pandoc, input_file, output_file,
                toc=args.toc, resource_path=resource_path,
            )
            _info("写入剪贴板...")
            clipboard.write_html(output_file)
            _ok("剪贴板已就绪！打开 Word → Ctrl+V 即可粘贴")
            converter.report(img_c, table_c, math_c, code_c, mermaid_c, args.mermaid)
            os.unlink(output_file)
        elif args.html:
            _info("模式: HTML（代码语法高亮 + 图片内嵌）")
            converter.run(pandoc, input_file, output_file,
                          html=True, toc=args.toc, resource_path=resource_path)
            size_kb = os.path.getsize(output_file) // 1024
            _ok(f"已生成: {output_file} ({size_kb}KB)")
            _warn("浏览器打开 → Ctrl+A → 粘贴到 Word（含代码高亮）")
        else:
            _info("模式: DOCX（公式OMML + 图片嵌入 + 表格保留）")
            converter.run(pandoc, input_file, output_file,
                          toc=args.toc, mermaid=args.mermaid,
                          ref_doc=args.ref, resource_path=resource_path)
            size_kb = os.path.getsize(output_file) // 1024
            _ok(f"已生成: {output_file} ({size_kb}KB)")
            converter.report(img_c, table_c, math_c, code_c, mermaid_c, args.mermaid)

        # ── 自动打开（非 paste 剪贴板模式）──
        if use_clipboard and not use_paste:
            _info("正在打开文件...")
            utils.open_file(output_file)

    finally:
        if temp_md and os.path.isfile(temp_md):
            os.unlink(temp_md)
