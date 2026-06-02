"""md2word v5.0 — Markdown 全格式转换器

交互式向导 + 命令行双模式，零门槛使用。
"""

import os
import sys
import tempfile
from argparse import ArgumentParser, Namespace
from pathlib import Path

from . import clipboard, cleaners, converter, utils

# ── 颜色 ──
_R = "\033[0;31m"; _G = "\033[0;32m"; _Y = "\033[1;33m"
_C = "\033[0;36m"; _B = "\033[1m"; _N = "\033[0m"

_e = lambda m: utils.safe_print(f"{_R}[ERR]{_N}   {m}")
_i = lambda m: utils.safe_print(f"{_C}[*]{_N}    {m}")
_ok = lambda m: utils.safe_print(f"{_G}[OK]{_N}   {m}")
_w = lambda m: utils.safe_print(f"{_Y}[!]{_N}    {m}")

BANNER = rf"""
{_C}╔══════════════════════════════════════════════╗
║      md2word v5.0 · Markdown 全格式转换       ║
║      pip install md2word · 零依赖 · 零门槛     ║
╚══════════════════════════════════════════════╝{_N}"""


def build_parser() -> ArgumentParser:
    p = ArgumentParser(prog="md2word", description="v5.0 — Markdown 全格式转换器")
    p.add_argument("input", nargs="?", help="输入 .md 文件（可选）")
    p.add_argument("output", nargs="?", help="输出文件路径（可选）")
    p.add_argument("-c", "--clipboard", action="store_true",
                   help="剪贴板 → .docx")
    p.add_argument("-p", "--paste", action="store_true",
                   help="粘贴就绪：Markdown→HTML→剪贴板，Word Ctrl+V")
    p.add_argument("-w", "--wizard", action="store_true",
                   help="交互式向导模式 — 新手推荐")
    p.add_argument("-f", "--format", dest="fmt", default="docx",
                   help="输出格式: docx/pptx/html/pdf/epub/odt/latex/rst/md/txt (默认: docx)")
    p.add_argument("--html", action="store_true", help="等同于 --format html")
    p.add_argument("--toc", action="store_true", help="生成目录")
    p.add_argument("--mermaid", action="store_true", help="渲染 Mermaid 流程图")
    p.add_argument("--ref", default="", help="参考模板文件 (.docx/.pptx)")
    p.add_argument("--from", dest="from_model", default="auto",
                   help="AI 模型: deepseek/chatgpt/claude/kimi/auto")
    return p


# ═══════════════════════════════════════════════════════════════
# 交互式向导
# ═══════════════════════════════════════════════════════════════

def _ask(prompt: str, default: str = "") -> str:
    """带默认值的输入。"""
    if default:
        result = input(f"  {prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"  {prompt}: ").strip()


def _ask_choice(prompt: str, choices: list, show_index: bool = True) -> str:
    """数字选择。"""
    for i, (label, _, _) in enumerate(choices, 1):
        rec = "  ← 推荐" if _ and show_index else ""
        print(f"    [{i}] {label}{rec}")
    while True:
        ans = _ask(prompt, "1")
        try:
            idx = int(ans) - 1
            if 0 <= idx < len(choices):
                return choices[idx][1]  # return the key
        except ValueError:
            pass
        utils.safe_print(f"{_R}  请输入 1-{len(choices)}{_N}")


def wizard() -> None:
    """交互式转换向导 — 零学习成本。"""
    utils.safe_print(BANNER)
    print("  欢迎使用 md2word！跟着提示一步步来就行。\n")

    # ── 步骤 1: 输入源 ──
    print(f" {_B}--- 步骤 1/4: 输入源 ---{_N}")
    source = _ask_choice("选择输入方式", [
        ("从剪贴板读取（复制 AI 回答后选这个）", "clipboard", True),
        ("选择 Markdown 文件", "file", True),
    ])

    input_file = ""
    temp_md = ""
    raw_text = ""

    if source == "clipboard":
        _i("正在读取剪贴板...")
        raw_text = clipboard.read()
        if not raw_text.strip():
            _e("剪贴板为空！请先复制 AI 回答，再运行 md2word -w")
            sys.exit(1)
        _ok(f"读取到 {len(raw_text)} 个字符")

        # 自动检测 AI 模型
        model = cleaners.detect(raw_text)
        if model != "generic":
            print(f"  [{_G}+{_N}] 检测到 AI 模型: {_B}{model}{_N}")
            ans = _ask("要清洗掉 AI 专属标记吗？(Y/n)", "y").lower()
            if ans in ("", "y", "yes"):
                raw_text = cleaners.sanitize(raw_text, model)
                _ok("已清洗")
        else:
            _i("未检测到特定 AI 模型标记，使用原始内容")

        title = utils.generate_title(raw_text)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                         encoding="utf-8") as f:
            f.write(raw_text)
            temp_md = f.name
        input_file = temp_md
    else:
        ans = _ask("输入 .md 文件路径（或拖拽文件到终端）")
        # 去除拖拽可能带入的引号
        ans = ans.strip().strip('"').strip("'")
        if not os.path.isfile(ans):
            _e(f"文件不存在: {ans}")
            sys.exit(1)
        input_file = ans

    # ── 步骤 2: 内容预览 ──
    img_c, table_c, math_c, code_c, mermaid_c, headings = converter.stats(input_file)
    print(f"\n {_B}--- 步骤 2/4: 内容概览 ---{_N}")
    print(f"  标题: {headings} 个  |  图片: {img_c} 张  |  表格: {table_c} 行")
    print(f"  公式: {math_c} 个  |  代码块: {code_c} 个  |  Mermaid: {mermaid_c} 个")

    # ── 步骤 3: 选择输出格式 ──
    print(f"\n {_B}--- 步骤 3/4: 输出格式 ---{_N}")
    fmt_choices = [
        ("Word 文档 (.docx)  ← 推荐", "docx", True),
        ("PowerPoint (.pptx) — # 标题变幻灯片", "pptx", True),
        ("HTML 网页 (.html) — 代码有颜色", "html", True),
        ("PDF (.pdf) — 需装 wkhtmltopdf", "pdf", False),
        ("ePub 电子书 (.epub) — Kindle 可读", "epub", False),
        ("纯文本 (.txt) — 只要文字", "txt", False),
        ("更多格式...", "more", False),
    ]
    fmt_key = _ask_choice("选择输出格式", fmt_choices)
    if fmt_key == "more":
        print(converter.list_formats(show_all=True))
        fmt_key = _ask("输入格式名 (如 odt/latex/rst):", "odt").strip().lower()
        if fmt_key not in converter.FORMATS:
            _e(f"不支持的格式: {fmt_key}")
            sys.exit(1)

    fmt = converter.get_format(fmt_key)
    print(f"  [{_G}+{_N}] {fmt['icon']} {fmt['desc']}")

    # ── 步骤 4: 选项 ──
    print(f"\n {_B}--- 步骤 4/4: 附加选项 ---{_N}")
    use_toc = headings > 3 and _ask("生成目录？(Y/n)", "y").lower() in ("", "y", "yes")
    use_mer = mermaid_c > 0 and _ask("渲染 Mermaid 流程图？(y/N)", "n").lower() in ("y", "yes")

    # 输出路径
    base = os.path.splitext(os.path.basename(input_file))[0]
    out_default = os.path.join(utils.get_desktop(), f"md2word_exports",
                               base + fmt["ext"])
    out = _ask("输出路径", out_default)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    # ── 转换 ──
    print(f"\n {_B}正在转换...{_N}")
    pandoc = _ensure_pandoc()
    pandoc_path = pandoc
    converter.run(pandoc_path, input_file, out, fmt_key,
                  toc=use_toc, mermaid=use_mer,
                  resource_path=os.path.dirname(input_file) or ".")
    size_kb = os.path.getsize(out) // 1024
    _ok(f"已生成: {out} ({size_kb}KB)")
    converter.report(img_c, table_c, math_c, code_c, mermaid_c, headings, use_mer)

    # 打开
    ans = _ask("要打开文件吗？(Y/n)", "y").lower()
    if ans in ("", "y", "yes"):
        utils.open_file(out)

    if temp_md and os.path.isfile(temp_md):
        os.unlink(temp_md)

    utils.safe_print(f"\n{_G}  转换完成！感谢使用 md2word v5.0{_N}\n")


# ═══════════════════════════════════════════════════════════════
# 命令行模式
# ═══════════════════════════════════════════════════════════════

def _ensure_pandoc() -> str:
    pandoc = utils.find_pandoc()
    if not pandoc:
        _e("Pandoc 未找到。")
        print("  winget install JohnMacFarlane.Pandoc  (Windows)")
        print("  brew install pandoc                    (macOS)")
        print("  sudo apt install pandoc                (Linux)")
        sys.exit(1)
    return pandoc


def _clipboard_flow(args: Namespace, pandoc: str) -> None:
    """剪贴板 → 转换。"""
    is_paste = args.paste
    if is_paste:
        _i("粘贴就绪模式: 读取剪贴板...")
    else:
        _i("剪贴板模式: 读取剪贴板...")

    raw = clipboard.read()
    if not raw.strip():
        _e("剪贴板为空，请先复制 AI 回答。")
        sys.exit(1)

    cleaned = cleaners.sanitize(raw, args.from_model)
    title = utils.generate_title(cleaned)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                     encoding="utf-8") as f:
        f.write(cleaned)
        temp_md = f.name
    _ok(f"已清洗 → {temp_md}")

    resource_path = os.path.dirname(temp_md) or "."
    img_c, table_c, math_c, code_c, mermaid_c, headings = converter.stats(temp_md)
    _i(f"统计: {img_c}图 {table_c}表行 {math_c}公式 {code_c}代码块 {mermaid_c}Mermaid")

    if is_paste:
        out = tempfile.NamedTemporaryFile(suffix=".html", delete=False).name
        converter.run_clipboard_html(pandoc, temp_md, out, toc=args.toc,
                                     resource_path=resource_path)
        _i("写入剪贴板...")
        clipboard.write_html(out)
        _ok("剪贴板已就绪！打开 Word → Ctrl+V")
        os.unlink(out)
    else:
        desktop = utils.get_desktop()
        exports = os.path.join(desktop, "md2word_exports")
        os.makedirs(exports, exist_ok=True)
        if args.html:
            out = args.output or os.path.join(exports, title + ".html")
            converter.run(pandoc, temp_md, out, "html", toc=args.toc,
                          resource_path=resource_path)
        else:
            out = args.output or os.path.join(exports, title + ".docx")
            converter.run(pandoc, temp_md, out, "docx", toc=args.toc,
                          mermaid=args.mermaid, ref_doc=args.ref,
                          resource_path=resource_path)
        size_kb = os.path.getsize(out) // 1024
        _ok(f"已生成: {out} ({size_kb}KB)")
        converter.report(img_c, table_c, math_c, code_c, mermaid_c, headings, args.mermaid)
        _i("正在打开...")
        utils.open_file(out)

    if os.path.isfile(temp_md):
        os.unlink(temp_md)


def _file_flow(args: Namespace, pandoc: str) -> None:
    """文件 → 转换。"""
    if not os.path.isfile(args.input):
        _e(f"文件不存在: {args.input}")
        sys.exit(1)

    fmt_key = args.fmt
    if args.html:
        fmt_key = "html"

    out = converter.resolve_output(args.input, fmt_key, args.output)
    resource_path = os.path.dirname(args.input) or "."
    img_c, table_c, math_c, code_c, mermaid_c, headings = converter.stats(args.input)
    _i(f"统计: {img_c}图 {table_c}表行 {math_c}公式 {code_c}代码块 {mermaid_c}Mermaid")

    fmt = converter.get_format(fmt_key)
    _i(f"格式: {fmt['icon']} {fmt_key} → {fmt['desc']}")
    converter.run(pandoc, args.input, out, fmt_key,
                  toc=args.toc, mermaid=args.mermaid,
                  ref_doc=args.ref, resource_path=resource_path,
                  metadata_title=Path(args.input).stem)
    size_kb = os.path.getsize(out) // 1024
    _ok(f"已生成: {out} ({size_kb}KB)")
    converter.report(img_c, table_c, math_c, code_c, mermaid_c, headings, args.mermaid)


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main(argv: list = None) -> None:
    parser = build_parser()

    # 无参数 → 自动进入向导
    if len(sys.argv) == 1:
        wizard()
        return

    args = parser.parse_args(argv)

    # 显式向导模式
    if args.wizard:
        wizard()
        return

    # 命令行模式
    pandoc = _ensure_pandoc()
    _i(f"Pandoc: {pandoc}")

    if args.clipboard or args.paste:
        _clipboard_flow(args, pandoc)
    else:
        if not args.input:
            wizard()
            return
        _file_flow(args, pandoc)
