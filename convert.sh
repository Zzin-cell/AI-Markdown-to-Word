#!/usr/bin/env bash
# =============================================================
# md2word — Markdown → Word 一键转换
# Repository: https://github.com/YOUR_USERNAME/md2word
#
# 用法:
#   ./convert.sh input.md              → 生成同目录 input.docx
#   ./convert.sh input.md output.docx   → 指定输出路径
#   ./convert.sh input.md --html        → 生成带代码高亮的 HTML
# =============================================================
set -euo pipefail

# ---- 颜色 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

# ---- 查找 pandoc ----
find_pandoc() {
    # 1. 系统 PATH
    if command -v pandoc &>/dev/null; then
        echo "pandoc"
        return
    fi
    # 2. 常见安装位置
    for candidate in \
        "/c/Program Files/Pandoc/pandoc.exe" \
        "$HOME/AppData/Local/Pandoc/pandoc.exe" \
        "$HOME/pandoc/pandoc-3.6.4/pandoc.exe" \
        "/usr/local/bin/pandoc"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"
            return
        fi
    done
    # 3. 未找到
    return 1
}

# ---- 打印帮助 ----
usage() {
    cat <<EOF
用法: $0 <input.md> [output.docx|--html]

示例:
  $0 document.md                → 在同目录生成 document.docx
  $0 document.md report.docx    → 指定输出为 report.docx
  $0 document.md --html         → 生成带代码高亮的 HTML

关键特性:
  · 数学公式 LaTeX → OMML（Word 原生可编辑公式）
  · 代码块保留等宽字体和缩进
  · HTML 模式支持代码语法高亮 (tango 主题)

前置条件: 需要安装 Pandoc
  winget install JohnMacFarlane.Pandoc   # Windows
  brew install pandoc                     # macOS
  sudo apt install pandoc                 # Linux

GitHub: https://github.com/YOUR_USERNAME/md2word
EOF
    exit 0
}

# ---- 参数解析 ----
INPUT="${1:-}"
OUTPUT="${2:-docx}"

if [[ -z "$INPUT" ]]; then
    usage
fi

if [[ "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    usage
fi

if [[ ! -f "$INPUT" ]]; then
    err "文件不存在: $INPUT"
    exit 1
fi

# ---- 找到 pandoc ----
PANDOC=$(find_pandoc) || {
    err "Pandoc 未找到。请安装后重试："
    echo "  winget install JohnMacFarlane.Pandoc   (Windows)"
    echo "  brew install pandoc                     (macOS)"
    echo "  sudo apt install pandoc                 (Linux)"
    echo ""
    echo "或下载便携版: https://github.com/jgm/pandoc/releases"
    exit 1
}
info "使用 Pandoc: $PANDOC"

# ---- 输入文件信息 ----
BASENAME="$(basename "$INPUT" .md)"
DIRNAME="$(dirname "$INPUT")"
LINES=$(wc -l < "$INPUT")
info "输入文件: $INPUT ($LINES 行)"

# ---- 转换 ----
if [[ "$OUTPUT" == "--html" ]]; then
    # HTML 模式：带代码高亮
    OUTPUT_FILE="${DIRNAME}/${BASENAME}.html"
    info "模式: HTML（带代码语法高亮）"
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" \
        --highlight-style=tango \
        --mathml \
        --from markdown+tex_math_dollars+tex_math_single_backslash \
        --standalone \
        --metadata title="$BASENAME"
    ok "已生成: $OUTPUT_FILE"
    warn "用浏览器打开 → 全选 Ctrl+A → 粘贴到 Word 即可获得带高亮的代码"
else
    # DOCX 模式：公式 → OMML
    if [[ "$OUTPUT" == "docx" ]]; then
        OUTPUT_FILE="${DIRNAME}/${BASENAME}.docx"
    else
        OUTPUT_FILE="$OUTPUT"
    fi
    info "模式: DOCX（数学公式 → OMML 可编辑）"
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" \
        --mathml \
        --from markdown+tex_math_dollars+tex_math_single_backslash
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    ok "已生成: $OUTPUT_FILE ($SIZE)"
    warn "注意: 代码块无语法高亮（Pandoc 原生限制）。如需高亮，请用 --html 模式。"
fi
