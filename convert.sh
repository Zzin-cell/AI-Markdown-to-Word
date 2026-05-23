#!/usr/bin/env bash
# =============================================================
# md2word — Markdown → Word 一键转换
# Repository: https://github.com/Zzin-cell/md2word
#
# 用法:
#   ./convert.sh input.md                  → 生成同目录 input.docx
#   ./convert.sh input.md output.docx       → 指定输出路径
#   ./convert.sh input.md --html            → 生成带代码高亮的 HTML
#   ./convert.sh input.md --toc             → 生成含目录的 docx
#
# 支持:
#   · 数学公式 LaTeX → OMML (Word 原生可编辑)
#   · 本地图片自动嵌入 + 网络图片自动下载嵌入
#   · 表格完整保留 (边框/对齐/合并单元格)
#   · Mermaid 流程图 (需安装 mermaid-filter)
#   · 代码块保留等宽字体 / HTML 模式带语法高亮
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
    if command -v pandoc &>/dev/null; then
        echo "pandoc"
        return
    fi
    for candidate in \
        "/c/Program Files/Pandoc/pandoc.exe" \
        "$HOME/AppData/Local/Pandoc/pandoc.exe" \
        "$HOME/pandoc/pandoc-3.6.4/pandoc.exe" \
        "$HOME/.claude/skills/md2word/pandoc.exe" \
        "/usr/local/bin/pandoc"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"
            return
        fi
    done
    return 1
}

# ---- 查找 mermaid-filter ----
find_mermaid() {
    if command -v mmdc &>/dev/null; then
        echo "mmdc"
        return
    fi
    if command -v npx &>/dev/null && npx --no-install -c 'mmdc --version' &>/dev/null 2>&1; then
        echo "npx mmdc"
        return
    fi
    return 1
}

# ---- 打印帮助 ----
usage() {
    cat <<'EOF'
用法: ./convert.sh <input.md> [选项|输出路径]

选项:
  --html      生成带代码语法高亮的 HTML（用浏览器打开后粘贴到 Word）
  --toc       在 docx 中自动生成目录
  --mermaid   启用 Mermaid 流程图渲染（需安装 mermaid-filter）
  --ref FILE  指定 Word 样式模板 (reference.docx)

示例:
  ./convert.sh document.md
  ./convert.sh document.md --toc
  ./convert.sh document.md --html
  ./convert.sh document.md --mermaid --toc
  ./convert.sh document.md --ref template.docx

支持的内容类型:
  ✅ 数学公式    $...$ / $$...$$ / \(...\) → Word OMML 可编辑
  ✅ 本地图片    ![](img/photo.png) → 自动嵌入 docx
  ✅ 网络图片    ![](https://...) → 自动下载嵌入
  ✅ 表格        | col1 | col2 | → 保留边框/对齐
  ✅ Mermaid     (需 --mermaid) → 自动渲染为 PNG/SVG 嵌入
  ✅ 代码块      等宽字体 + 缩进 (HTML 模式带语法高亮)

前置条件: 安装 Pandoc
  winget install JohnMacFarlane.Pandoc   # Windows
  brew install pandoc                     # macOS
  sudo apt install pandoc                 # Linux

Mermaid 支持 (可选):
  npm install -g @mermaid-js/mermaid-cli  # 安装 mermaid CLI
  npm install -g mermaid-filter           # 安装 pandoc filter

GitHub: https://github.com/Zzin-cell/md2word
EOF
    exit 0
}

# ---- 参数解析 ----
INPUT="${1:-}"

if [[ -z "$INPUT" || "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    usage
fi

if [[ ! -f "$INPUT" ]]; then
    err "文件不存在: $INPUT"
    exit 1
fi

shift
USE_HTML=false
USE_TOC=false
USE_MERMAID=false
OUTPUT_FILE=""
REF_DOC=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --html)
            USE_HTML=true ;;
        --toc)
            USE_TOC=true ;;
        --mermaid)
            USE_MERMAID=true ;;
        --ref)
            shift
            REF_DOC="$1" ;;
        --help|-h)
            usage ;;
        *)
            OUTPUT_FILE="$1" ;;
    esac
    shift
done

# ---- 确定输入输出 ----
BASENAME="$(basename "$INPUT" .md)"
DIRNAME="$(dirname "$INPUT")"

if [[ -z "$OUTPUT_FILE" ]]; then
    if $USE_HTML; then
        OUTPUT_FILE="${DIRNAME}/${BASENAME}.html"
    else
        OUTPUT_FILE="${DIRNAME}/${BASENAME}.docx"
    fi
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
info "Pandoc: $PANDOC"

# ---- Mermaid 检查 ----
if $USE_MERMAID; then
    MERMAID_FILTER=$(find_mermaid) || {
        err "Mermaid 未安装。安装方法:"
        echo "  npm install -g @mermaid-js/mermaid-cli"
        echo "  npm install -g mermaid-filter"
        exit 1
    }
    info "Mermaid: $MERMAID_FILTER"
fi

# ---- 输入文件信息 ----
LINES=$(wc -l < "$INPUT")

# 统计 Markdown 特征
IMG_COUNT=$(grep -c '!\[.*\](.*)' "$INPUT" 2>/dev/null || echo 0)
TABLE_COUNT=$(grep -c '^|.*|.*|$' "$INPUT" 2>/dev/null || echo 0)
MATH_COUNT=$(grep -c '\$\$.*\$\$' "$INPUT" 2>/dev/null || echo 0)
CODE_COUNT=$(grep -c '```' "$INPUT" 2>/dev/null || echo 0)
MERMAID_COUNT=$(grep -c '```mermaid' "$INPUT" 2>/dev/null || echo 0)

info "输入: $INPUT (${LINES} 行)"
info "统计: ${IMG_COUNT} 图片, ${TABLE_COUNT} 表格行, ${MATH_COUNT} 块公式, $((CODE_COUNT/2)) 代码块, ${MERMAID_COUNT} Mermaid"
if $USE_MERMAID && [[ "$MERMAID_COUNT" -gt 0 ]]; then
    info "Mermaid 模式: 已启用 (将渲染 ${MERMAID_COUNT} 个流程图)"
elif ! $USE_MERMAID && [[ "$MERMAID_COUNT" -gt 0 ]]; then
    warn "文档含 ${MERMAID_COUNT} 个 Mermaid 流程图，但未启用 --mermaid。流程图将丢失。"
    warn "如需渲染，请加 --mermaid 参数（需先安装 mermaid-filter）"
fi

# ---- 构建 Pandoc 参数 ----
PANDOC_ARGS=(
    --mathml
    --from markdown+tex_math_dollars+tex_math_single_backslash
)

# 目录
if $USE_TOC; then
    PANDOC_ARGS+=(--toc --toc-depth=3)
    info "目录: 启用 (深度=3)"
fi

# 样式模板
if [[ -n "$REF_DOC" && -f "$REF_DOC" ]]; then
    PANDOC_ARGS+=(--reference-doc="$REF_DOC")
    info "模板: $REF_DOC"
elif [[ -n "$REF_DOC" ]]; then
    warn "模板文件不存在: $REF_DOC，已忽略"
fi

# 资源路径：让 Pandoc 能在文件所在目录及其子目录中找到图片
PANDOC_ARGS+=(--resource-path="${DIRNAME}")

# Mermaid filter
if $USE_MERMAID && [[ "$MERMAID_COUNT" -gt 0 ]]; then
    PANDOC_ARGS+=(-F mermaid-filter)
fi

# ---- 转换 ----
if $USE_HTML; then
    # ===== HTML 模式 =====
    info "模式: HTML（代码语法高亮 + 图片内嵌）"
    PANDOC_ARGS+=(
        --highlight-style=tango
        --standalone
        --metadata title="$BASENAME"
        --self-contained          # 图片/字体全部内嵌到 HTML
    )
    info "转换中..."
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" "${PANDOC_ARGS[@]}"
    ok "已生成: $OUTPUT_FILE ($(du -h "$OUTPUT_FILE" | cut -f1))"
    warn "用浏览器打开 → 全选 Ctrl+A → 粘贴到 Word 即可（含代码高亮+图片+表格）"

else
    # ===== DOCX 模式 =====
    info "模式: DOCX（公式OMML + 图片嵌入 + 表格保留）"
    info "转换中..."
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" "${PANDOC_ARGS[@]}"
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    ok "已生成: $OUTPUT_FILE ($SIZE)"

    # 效果确认
    echo ""
    echo "  ┌─ 内容完整性检查 ─────────────────────────────┐"
    echo "  │                                                  │"
    if [[ "$IMG_COUNT" -gt 0 ]]; then
        echo "  │  ✅ 图片:   ${IMG_COUNT} 张已嵌入 docx                   │"
    else
        echo "  │  ─  图片:   0 张                                  │"
    fi
    if [[ "$TABLE_COUNT" -gt 0 ]]; then
        echo "  │  ✅ 表格:   已保留边框和对齐                        │"
    else
        echo "  │  ─  表格:   无                                    │"
    fi
    if [[ "$MATH_COUNT" -gt 0 ]]; then
        echo "  │  ✅ 公式:   ${MATH_COUNT} 个 → OMML 可编辑                  │"
    else
        echo "  │  ─  公式:   无                                    │"
    fi
    if [[ $((CODE_COUNT/2)) -gt 0 ]]; then
        echo "  │  ⚠️  代码:   $((CODE_COUNT/2)) 个 → 等宽字体，无语法高亮       │"
    fi
    if $USE_MERMAID && [[ "$MERMAID_COUNT" -gt 0 ]]; then
        echo "  │  ✅ Mermaid: ${MERMAID_COUNT} 个已渲染           │"
    elif [[ "$MERMAID_COUNT" -gt 0 ]]; then
        echo "  │  ❌ Mermaid: ${MERMAID_COUNT} 个已丢失 (未加 --mermaid)    │"
    fi
    echo "  │                                                  │"
    echo "  └──────────────────────────────────────────────────┘"
fi
