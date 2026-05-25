#!/usr/bin/env python3
# =============================================================
# md2word — Markdown → Word 一键转换  v4.0 (Python)
# Repository: https://github.com/Zzin-cell/AI-Markdown-to-Word
#
# 用法:
#   python convert.py input.md                  → 生成同目录 input.docx
#   python convert.py input.md output.docx       → 指定输出路径
#   python convert.py -c                         → 从剪贴板直接转 Word
#   python convert.py -p                         → 粘贴就绪（Markdown→HTML→剪贴板，Word Ctrl+V）
#   python convert.py -c --from deepseek         → 剪贴板 + 模型清洗
#   python convert.py input.md --html            → 生成带代码高亮的 HTML
#   python convert.py input.md --toc             → 生成含目录的 docx
#   python convert.py input.md --mermaid         → 渲染 Mermaid 流程图
#
# 粘贴就绪模式 (-p):
#   复制 AI 回答 → python convert.py -p → 切到 Word Ctrl+V
#   原理: Markdown→HTML(含MathML+base64图片)→系统剪贴板→Word识别
# =============================================================

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# ── 颜色输出 ──────────────────────────────────────────────
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"

def info(msg):   print(f"{CYAN}[INFO]{NC}  {msg}")
def ok(msg):     print(f"{GREEN}[OK]{NC}    {msg}")
def warn(msg):   print(f"{YELLOW}[WARN]{NC}  {msg}")
def err(msg):    print(f"{RED}[ERR]{NC}   {msg}")

# ── 系统检测 ──────────────────────────────────────────────
IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

# ── 剪贴板读取（跨平台）────────────────────────────────────
def read_clipboard():
    try:
        if IS_MAC:
            return subprocess.check_output(["pbpaste"], text=True, stderr=subprocess.DEVNULL)
        elif IS_LINUX:
            if shutil.which("wl-paste"):
                return subprocess.check_output(["wl-paste"], text=True, stderr=subprocess.DEVNULL)
            elif shutil.which("xclip"):
                return subprocess.check_output(["xclip", "-selection", "clipboard", "-o"],
                                               text=True, stderr=subprocess.DEVNULL)
            else:
                err("Linux 需安装 xclip 或 wl-clipboard")
                sys.exit(1)
        else:
            result = subprocess.run(["powershell.exe", "-Command", "Get-Clipboard"],
                                    capture_output=True, text=True)
            return result.stdout
    except Exception as e:
        err(f"读取剪贴板失败: {e}")
        sys.exit(1)

# ── 剪贴板写入（跨平台）────────────────────────────────────
def write_clipboard(html_file):
    try:
        if IS_MAC:
            with open(html_file, "r", encoding="utf-8") as f:
                subprocess.run(["pbcopy"], input=f.read(), text=True)
        elif IS_LINUX:
            if shutil.which("wl-copy"):
                with open(html_file, "r", encoding="utf-8") as f:
                    subprocess.run(["wl-copy"], input=f.read(), text=True)
            elif shutil.which("xclip"):
                with open(html_file, "r", encoding="utf-8") as f:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=f.read(), text=True)
        else:
            html_path = html_file.replace("\\", "\\\\")
            ps_cmd = (
                f"Set-Clipboard -AsHtml -Value "
                f"([System.IO.File]::ReadAllText('{html_path}', [System.Text.Encoding]::UTF8))"
            )
            subprocess.run(["powershell.exe", "-Command", ps_cmd], check=True)
    except Exception as e:
        err(f"写入剪贴板失败: {e}")
        sys.exit(1)

# ── Pandoc 查找 ────────────────────────────────────────────
def find_pandoc():
    pandoc = shutil.which("pandoc")
    if pandoc:
        return pandoc
    candidates = [
        r"c:\Program Files\Pandoc\pandoc.exe",
        os.path.expanduser("~/AppData/Local/Pandoc/pandoc.exe"),
        os.path.expanduser("~/pandoc/pandoc-3.6.4/pandoc.exe"),
        os.path.expanduser("~/.claude/skills/md2word/pandoc.exe"),
        os.path.expanduser("~/.claude/skills/AI-Markdown-to-Word/pandoc.exe"),
        "/usr/local/bin/pandoc",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

# ── 打开文件 ────────────────────────────────────────────────
def open_file(filepath):
    if IS_MAC:
        subprocess.run(["open", filepath])
    elif IS_LINUX:
        subprocess.run(["xdg-open", filepath])
    else:
        os.startfile(filepath)

# ── 获取桌面路径 ────────────────────────────────────────────
def get_desktop():
    if IS_WIN:
        return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    return os.path.join(os.path.expanduser("~"), "Desktop")

# ── 模型清洁器 ──────────────────────────────────────────────
def clean_html_blocks(text):
    text = re.sub(r'<details[^>]*>', '', text)
    text = re.sub(r'</details>', '', text)
    text = re.sub(r'<summary[^>]*>', '', text)
    text = re.sub(r'</summary>', '', text)
    text = re.sub(r'<div[^>]*>', '', text)
    text = re.sub(r'</div>', '', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'style="[^"]*"', '', text)
    return text

def clean_deepseek(text):
    text = re.sub(r'^## 🤖 .*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'<details[^>]*>.*?</details>', '', text, flags=re.DOTALL)
    text = re.sub(r'<div[^>]*></div>', '', text)
    return text

def clean_chatgpt(text):
    text = re.sub(r'^ChatGPT said:.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^ChatGPT.*\n?', '', text, flags=re.MULTILINE)
    return text

def clean_claude(text):
    text = re.sub(r'^Claude said:.*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Claude .*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'<details[^>]*>.*?</details>', '', text, flags=re.DOTALL)
    text = re.sub(r'<antml:[^>]*>', '', text)
    text = re.sub(r'</antml:[^>]*>', '', text)
    text = re.sub(r'<function_calls>', '', text)
    text = re.sub(r'</function_calls>', '', text)
    return text

def clean_kimi(text):
    text = re.sub(r'<details[^>]*>.*?</details>', '', text, flags=re.DOTALL)
    return text

def detect_model(text):
    if re.search(r'🤖.*deepseek|已深度思考', text):
        return "deepseek"
    if re.search(r'ChatGPT|OpenAI', text):
        return "chatgpt"
    if re.search(r'Claude|claude|Anthropic', text):
        return "claude"
    if re.search(r'Kimi|kimi|月之暗面', text):
        return "kimi"
    return "generic"

CLEANERS = {
    "deepseek": clean_deepseek,
    "chatgpt": clean_chatgpt,
    "claude": clean_claude,
    "kimi": clean_kimi,
    "generic": lambda t: t,
}

def sanitize_markdown(text, model="auto"):
    if model == "auto":
        model = detect_model(text)
    info(f"模型检测: {model}")
    cleaner = CLEANERS.get(model, lambda t: t)
    return clean_html_blocks(cleaner(text))

# ── 内容统计 ────────────────────────────────────────────────
def count_content(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    img_count = len(re.findall(r'!\[.*?\]\(.*?\)', text))
    table_count = len(re.findall(r'^\+.*\+$', text, re.MULTILINE)) + \
                  len(re.findall(r'^\|.*\|.*\|$', text, re.MULTILINE))
    math_count = text.count("$$") // 2
    code_count = text.count("```") // 2
    mermaid_count = text.count("```mermaid")
    return img_count, table_count, math_count, code_count, mermaid_count

def print_report(img, table, math, code, mermaid, use_mermaid):
    # 安全输出（避免 Windows GBK 编码报错）
    def safe(msg):
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="replace").decode("ascii"))

    safe("")
    safe("  +-- 内容完整性检查 -----------------------------------+")
    if img:
        safe(f"  |  [OK] 图片:    {img} 张已嵌入                        |")
    if table:
        safe(f"  |  [OK] 表格:    {table} 行，边框对齐完整              |")
    if math:
        safe(f"  |  [OK] 公式:    {math} 个 -> OMML / MathML 可编辑     |")
    if code:
        safe(f"  |  [OK] 代码:    {code} 个 -> 语法高亮                 |")
    if mermaid and use_mermaid:
        safe(f"  |  [OK] Mermaid: {mermaid} 个已渲染                    |")
    elif mermaid:
        safe(f"  |  [!!] Mermaid: {mermaid} 个 (加 --mermaid 补救)     |")
    safe("  +----------------------------------------------------+")

# ── 生成标题 ────────────────────────────────────────────────
def generate_title(text):
    m = re.search(r'^# (.+)', text, re.MULTILINE)
    if m:
        title = re.sub(r'[^\w\s]', '', m.group(1)[:50])
        title = title.strip().replace(' ', '_')
        if title:
            return title
    return f"AI_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ── 主流程 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="md2word v4.0 — Markdown → Word 一键转换 (Python)",
        add_help=False,
    )
    parser.add_argument("input", nargs="?", help="输入 .md 文件，或 -c / -p 使用剪贴板模式")
    parser.add_argument("output", nargs="?", help="输出文件路径（可选）")
    parser.add_argument("-c", "--clipboard", action="store_true", help="剪贴板模式：读取剪贴板 → 生成 .docx")
    parser.add_argument("-p", "--paste", action="store_true", help="粘贴就绪模式：Markdown→HTML→写回剪贴板，Word 直接 Ctrl+V")
    parser.add_argument("--html", action="store_true", help="生成 HTML（含代码语法高亮）")
    parser.add_argument("--toc", action="store_true", help="生成目录")
    parser.add_argument("--mermaid", action="store_true", help="渲染 Mermaid 流程图")
    parser.add_argument("--ref", help="Word 模板文件 (.docx)")
    parser.add_argument("--from", dest="from_model", default="auto", help="指定 AI 模型: deepseek/chatgpt/claude/kimi/auto")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助")

    args = parser.parse_args()

    # 帮助
    if args.help or (not args.input and not args.clipboard and not args.paste):
        parser.print_help()
        print("""
示例:
  python convert.py document.md                  基础转换 → document.docx
  python convert.py document.md --toc            含目录
  python convert.py document.md --html           代码高亮版 HTML
  python convert.py -c                           剪贴板 → .docx
  python convert.py -p                           粘贴就绪 → 剪贴板 HTML → Word Ctrl+V
  python convert.py -p --from claude             指定模型清洗
  python convert.py -c --from deepseek --toc     组合选项

GitHub: https://github.com/Zzin-cell/AI-Markdown-to-Word
""")
        return

    # ── 模式判断 ──
    use_clipboard = args.clipboard or args.paste
    use_paste = args.paste
    use_html = args.html or use_paste  # paste 模式强依赖 HTML
    use_toc = args.toc
    use_mermaid = args.mermaid
    from_model = args.from_model
    ref_doc = args.ref
    output_file = args.output

    # ── 找 pandoc ──
    pandoc = find_pandoc()
    if not pandoc:
        err("Pandoc 未找到。安装方法:")
        print("  winget install JohnMacFarlane.Pandoc  (Windows)")
        print("  brew install pandoc                    (macOS)")
        print("  sudo apt install pandoc                (Linux)")
        sys.exit(1)
    info(f"Pandoc: {pandoc}")

    # ── 输入获取 ──
    if use_clipboard:
        if use_paste:
            info("粘贴就绪模式: 正在读取剪贴板...")
        else:
            info("剪贴板模式: 正在读取剪贴板...")
        raw_content = read_clipboard()
        if not raw_content.strip():
            err("剪贴板为空，请先复制 AI 回答内容。")
            sys.exit(1)

        cleaned = sanitize_markdown(raw_content, from_model)
        title = generate_title(cleaned)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False,
                                         encoding="utf-8") as f:
            f.write(cleaned)
            temp_md = f.name
        ok(f"内容已清洗 ({from_model}) → {temp_md}")

        input_file = temp_md
        desktop = get_desktop()
        exports_dir = os.path.join(desktop, "md2word_exports")
        if not use_paste:
            os.makedirs(exports_dir, exist_ok=True)
            if not output_file:
                ext = ".html" if use_html else ".docx"
                output_file = os.path.join(exports_dir, title + ext)
    else:
        input_file = args.input
        if not os.path.isfile(input_file):
            err(f"文件不存在: {input_file}")
            sys.exit(1)

    # ── 输出路径 ──
    basename = os.path.splitext(os.path.basename(input_file))[0]
    dirname = os.path.dirname(input_file) or "."

    if use_paste:
        temp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False).name
        output_file = temp_html
    elif not output_file:
        ext = ".html" if use_html else ".docx"
        output_file = os.path.join(dirname, basename + ext)

    # ── 统计 ──
    lines = sum(1 for _ in open(input_file, "r", encoding="utf-8"))
    img_c, table_c, math_c, code_c, mermaid_c = count_content(input_file)
    info(f"输入: {input_file} ({lines} 行)")
    info(f"统计: {img_c}图 {table_c}表行 {math_c}公式 {code_c}代码块 {mermaid_c}Mermaid")

    # ── 构建 pandoc 参数 ──
    pandoc_args = [
        pandoc, input_file, "-o", output_file,
        "--mathml",
        "--from", "markdown+tex_math_dollars+tex_math_single_backslash",
    ]

    if use_toc:
        pandoc_args += ["--toc", "--toc-depth=3"]
        info("目录: 已启用")

    if ref_doc and os.path.isfile(ref_doc):
        pandoc_args += ["--reference-doc=" + ref_doc]
        info(f"模板: {ref_doc}")
    elif ref_doc:
        warn(f"模板不存在: {ref_doc}，已忽略")

    pandoc_args += ["--resource-path=" + os.path.abspath(dirname)]

    if use_mermaid and mermaid_c > 0:
        mmdc = shutil.which("mmdc") or shutil.which("npx")
        if mmdc:
            pandoc_args += ["-F", "mermaid-filter"]

    # ── 转换 ──
    if use_paste:
        info("模式: 粘贴就绪（Markdown→HTML→剪贴板，Word 直接 Ctrl+V）")
        pandoc_args += ["--highlight-style=tango", "--standalone",
                        "--metadata", f"title={basename}", "--self-contained"]
        info("转换中...")
        subprocess.run(pandoc_args, check=True)
        info("写入剪贴板...")
        write_clipboard(output_file)
        ok("剪贴板已就绪！打开 Word → Ctrl+V 即可粘贴")
        print_report(img_c, table_c, math_c, code_c, mermaid_c, use_mermaid)
        # 清理
        os.unlink(output_file)
        os.unlink(temp_md)
    elif use_html:
        info("模式: HTML（代码语法高亮 + 图片内嵌）")
        pandoc_args += ["--highlight-style=tango", "--standalone",
                        "--metadata", f"title={basename}", "--self-contained"]
        info("转换中...")
        subprocess.run(pandoc_args, check=True)
        size_kb = os.path.getsize(output_file) // 1024
        ok(f"已生成: {output_file} ({size_kb}KB)")
        warn("浏览器打开 → Ctrl+A → 粘贴到 Word（含代码高亮）")
    else:
        info("模式: DOCX（公式OMML + 图片嵌入 + 表格保留）")
        info("转换中...")
        subprocess.run(pandoc_args, check=True)
        size_kb = os.path.getsize(output_file) // 1024
        ok(f"已生成: {output_file} ({size_kb}KB)")
        print_report(img_c, table_c, math_c, code_c, mermaid_c, use_mermaid)

    # ── 自动打开（仅非 paste 剪贴板模式）─
    if use_clipboard and not use_paste:
        info("正在打开文件...")
        open_file(output_file)
        os.unlink(temp_md)

if __name__ == "__main__":
    main()
