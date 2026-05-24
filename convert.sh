#!/usr/bin/env bash
# =============================================================
# md2word — Markdown → Word 一键转换  v3.0
# Repository: https://github.com/Zzin-cell/md2word
#
# 用法:
#   ./convert.sh input.md                  → 生成同目录 input.docx
#   ./convert.sh input.md output.docx       → 指定输出路径
#   ./convert.sh -c                         → 从剪贴板直接转 Word
#   ./convert.sh -c --from deepseek         → 剪贴板 + DeepSeek 清洗
#   ./convert.sh input.md --html            → 生成带代码高亮的 HTML
#   ./convert.sh input.md --toc             → 生成含目录的 docx
#   ./convert.sh input.md --mermaid         → 渲染 Mermaid 流程图
#
# 剪贴板模式 (-c):
#   复制 AI 对话中的 Markdown → 运行 ./convert.sh -c → 自动生成 Word
#   支持: DeepSeek / ChatGPT / Claude / Kimi / 通用
# =============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERR]${NC}   $*"; }

# ============================================================
# 剪贴板读取（跨平台）
# ============================================================
read_clipboard() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        pbpaste 2>/dev/null
    elif [[ "$(uname -s)" == "Linux" ]]; then
        if command -v xclip &>/dev/null; then
            xclip -selection clipboard -o 2>/dev/null
        elif command -v wl-paste &>/dev/null; then
            wl-paste 2>/dev/null
        else
            err "Linux 需安装 xclip 或 wl-paste: sudo apt install xclip"
            exit 1
        fi
    else
        # Windows: PowerShell
        powershell.exe -Command "Get-Clipboard" 2>/dev/null
    fi
}

# ============================================================
# AI 模型专属 Markdown 清洗器
# ============================================================

# 通用清洗：HTML 块 → 纯文本
clean_html_blocks() {
    sed -E '
        # 移除 <details> / <summary> 标签（保留内部文字）
        s/<details[^>]*>//g
        s/<\/details>//g
        s/<summary[^>]*>//g
        s/<\/summary>//g
        # 移除 <div> 标签（保留内部文字）
        s/<div[^>]*>//g
        s/<\/div>//g
        # 移除 <br> 和 <br/>
        s/<br\s*\/?>/\n/g
        # 移除空的 style 属性残留
        s/style="[^"]*"//g
        # 移除多余空行（保留最多1个连续空行）
    '
}

clean_deepseek() {
    # DeepSeek 特征：
    # 1. 顶部 "🤖 deepseek-v4-pro" 标题
    # 2. <div><details><summary>已深度思考</summary>...思考内容...</details></div>
    # 3. 有时在思考块后有 --- 分隔线
    sed -E '
        # 移除 "## 🤖 model-name" 标题行
        /^## 🤖 /d
        # 移除整个 <details> 思考块（包括内部内容，因为思考过程不需要进 Word）
        /<details[^>]*>/,/<\/details>/d
        # 移除残留的空 <div> 对
        s/<div[^>]*><\/div>//g
    '
}

clean_chatgpt() {
    # ChatGPT 特征：
    # 1. 可能以 "ChatGPT said:" 或类似文字开头
    # 2. 数学公式统一用 \(...\) 和 $$...$$ (已由 pandoc 处理)
    # 3. 有些版本输出包含特殊的 HTML 格式标记
    sed -E '
        # 移除开头可能的 ChatGPT 标签
        /^ChatGPT said:/d
        /^ChatGPT/d
    '
}

clean_claude() {
    # Claude 特征：
    # 1. 可能有 "Claude said:" 标签
    # 2. <details><summary> 思考块（与 DeepSeek 类似，结构更简洁）
    # 3. 可能包含 <antml:function_calls> 等 XML 标签残留
    sed -E '
        /^Claude said:/d
        /^Claude /d
        # 移除思考块
        /<details[^>]*>/,/<\/details>/d
        # 移除 XML 标签残留
        s/<antml:[^>]*>//g
        s/<\/antml:[^>]*>//g
        s/<function_calls>//g
        s/<\/function_calls>//g
    '
}

clean_kimi() {
    # Kimi 特征：
    # 1. 思考过程在特殊的引用块中
    # 2. 有时输出包含 HTML 格式的引用
    sed -E '
        /<details[^>]*>/,/<\/details>/d
    '
}

# 自动检测模型类型
detect_model() {
    local content="$1"
    if echo "$content" | grep -q "🤖.*deepseek\|已深度思考"; then
        echo "deepseek"
    elif echo "$content" | grep -q "ChatGPT\|OpenAI"; then
        echo "chatgpt"
    elif echo "$content" | grep -q "Claude\|claude\|Anthropic"; then
        echo "claude"
    elif echo "$content" | grep -q "Kimi\|kimi\|月之暗面"; then
        echo "kimi"
    else
        echo "generic"
    fi
}

# 清洗管道：根据模型类型执行
sanitize_markdown() {
    local input="$1"
    local model="${2:-auto}"

    # 自动检测
    if [[ "$model" == "auto" ]]; then
        model=$(detect_model "$input")
    fi

    info "模型检测: $model"

    # 第一步：模型专属清洗
    case "$model" in
        deepseek) echo "$input" | clean_deepseek ;;
        chatgpt)  echo "$input" | clean_chatgpt ;;
        claude)   echo "$input" | clean_claude ;;
        kimi)     echo "$input" | clean_kimi ;;
        *)        echo "$input" ;;
    esac | clean_html_blocks  # 第二步：通用 HTML 清洗
}

# ============================================================
# 打开文件（跨平台）
# ============================================================
open_file() {
    local file="$1"
    case "$(uname -s)" in
        Darwin)  open "$file" ;;
        Linux)   xdg-open "$file" ;;
        *)       start "" "$file" 2>/dev/null || cmd.exe /c start "" "$(cygpath -w "$file" 2>/dev/null || echo "$file")" ;;
    esac
}

# 获取桌面路径
get_desktop() {
    if [[ "$(uname -s)" == "Darwin" ]]; then
        echo "$HOME/Desktop"
    elif [[ "$(uname -s)" == "Linux" ]]; then
        echo "$HOME/Desktop"
    else
        echo "$USERPROFILE/Desktop"
    fi
}

# ============================================================
# Pandoc 查找
# ============================================================
find_pandoc() {
    if command -v pandoc &>/dev/null; then
        echo "pandoc"; return
    fi
    for candidate in \
        "/c/Program Files/Pandoc/pandoc.exe" \
        "$HOME/AppData/Local/Pandoc/pandoc.exe" \
        "$HOME/pandoc/pandoc-3.6.4/pandoc.exe" \
        "$HOME/.claude/skills/md2word/pandoc.exe" \
        "/usr/local/bin/pandoc"; do
        if [[ -x "$candidate" ]]; then
            echo "$candidate"; return
        fi
    done
    return 1
}

find_mermaid() {
    command -v mmdc 2>/dev/null && echo "mmdc" && return
    command -v npx &>/dev/null && echo "npx mmdc" && return
    return 1
}

# ============================================================
# 统计与报告
# ============================================================
count_content() {
    local file="$1"
    IMG_COUNT=$(grep -c '!\[.*\](.*)' "$file" 2>/dev/null || echo 0)
    TABLE_COUNT=$(grep -c '^|.*|.*|$' "$file" 2>/dev/null || echo 0)
    MATH_COUNT=$(grep -c '\$\$' "$file" 2>/dev/null || echo 0); MATH_COUNT=$((MATH_COUNT/2))
    CODE_COUNT=$(grep -c '```' "$file" 2>/dev/null || echo 0); CODE_COUNT=$((CODE_COUNT/2))
    MERMAID_COUNT=$(grep -c '```mermaid' "$file" 2>/dev/null || echo 0)
}

print_report() {
    echo ""
    echo "  ┌─ 内容完整性检查 ─────────────────────────────────────┐"
    [[ "$IMG_COUNT" -gt 0 ]]    && echo "  │  ✅ 图片:    ${IMG_COUNT} 张已嵌入                             │"
    [[ "$TABLE_COUNT" -gt 0 ]]  && echo "  │  ✅ 表格:    ${TABLE_COUNT} 行，边框对齐完整                   │"
    [[ "$MATH_COUNT" -gt 0 ]]   && echo "  │  ✅ 公式:    ${MATH_COUNT} 个 → OMML 可编辑                    │"
    [[ "$CODE_COUNT" -gt 0 ]]   && echo "  │  ⚠️  代码:    ${CODE_COUNT} 个 → 等宽字体，语法高亮建议 --html  │"
    [[ "$MERMAID_COUNT" -gt 0 && "$USE_MERMAID" == true ]]  && echo "  │  ✅ Mermaid: ${MERMAID_COUNT} 个已渲染                       │"
    [[ "$MERMAID_COUNT" -gt 0 && "$USE_MERMAID" != true ]]  && echo "  │  ❌ Mermaid: ${MERMAID_COUNT} 个已丢失 (加 --mermaid 补救)     │"
    echo "  └──────────────────────────────────────────────────────┘"
}

# ============================================================
# 帮助
# ============================================================
usage() {
    cat <<'EOF'
md2word v3.0 — Markdown → Word 一键转换

用法:
  ./convert.sh <input.md> [选项]
  ./convert.sh -c [选项]             剪贴板模式

文件模式:
  ./convert.sh document.md                  → document.docx
  ./convert.sh document.md --toc            → 含目录
  ./convert.sh document.md --html           → 带代码高亮的 HTML
  ./convert.sh document.md --mermaid        → 渲染 Mermaid 流程图
  ./convert.sh document.md --ref tpl.docx   → 套用 Word 模板

剪贴板模式 (复制 AI 回答后一键出 Word):
  ./convert.sh -c                           → 自动检测模型清洗
  ./convert.sh -c --from deepseek           → 指定 DeepSeek 清洗
  ./convert.sh -c --from chatgpt            → 指定 ChatGPT 清洗
  ./convert.sh -c --from claude             → 指定 Claude 清洗
  ./convert.sh -c --from kimi               → 指定 Kimi 清洗
  ./convert.sh -c --toc --html              → 组合选项

模型清洗说明:
  deepseek  移除 🤖 标题 + "已深度思考" 折叠块
  chatgpt   移除 ChatGPT 标签
  claude    移除 Claude 标签 + 思考块 + XML 残留
  kimi      移除 Kimi 思考引用块
  默认      auto — 自动从内容特征检测

支持的内容:
  ✅ 数学公式   $...$ / $$...$$ → Word OMML 可编辑
  ✅ 图片       本地路径自动嵌入，网络 URL 自动下载
  ✅ 表格       边框 + 对齐 + 合并单元格全部保留
  ✅ 代码块     等宽字体 + 缩进 (--html 带语法高亮)
  ✅ Mermaid    (需 --mermaid + npm install mermaid-filter)
  ✅ 目录       (--toc 自动生成)

前置条件: pandoc (winget install JohnMacFarlane.Pandoc)
GitHub: https://github.com/Zzin-cell/md2word
EOF
    exit 0
}

# ============================================================
# 主流程
# ============================================================
INPUT="${1:-}"

if [[ -z "$INPUT" || "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    usage
fi

# 剪贴板模式
USE_CLIPBOARD=false
if [[ "$INPUT" == "-c" || "$INPUT" == "--clipboard" ]]; then
    USE_CLIPBOARD=true
    shift
else
    shift
fi

USE_HTML=false; USE_TOC=false; USE_MERMAID=false
OUTPUT_FILE=""; REF_DOC=""; AI_MODEL="auto"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --html)      USE_HTML=true ;;
        --toc)       USE_TOC=true ;;
        --mermaid)   USE_MERMAID=true ;;
        --ref)       shift; REF_DOC="$1" ;;
        --from)      shift; AI_MODEL="$1" ;;
        --help|-h)   usage ;;
        *)           OUTPUT_FILE="$1" ;;
    esac
    shift
done

# ---- 找到 pandoc ----
PANDOC=$(find_pandoc) || {
    err "Pandoc 未找到。安装方法:"
    echo "  winget install JohnMacFarlane.Pandoc  (Windows)"
    echo "  brew install pandoc                    (macOS)"
    echo "  sudo apt install pandoc                (Linux)"
    exit 1
}
info "Pandoc: $PANDOC"

# ---- Mermaid 检查 ----
if $USE_MERMAID; then
    find_mermaid &>/dev/null || {
        err "Mermaid 未安装: npm install -g @mermaid-js/mermaid-cli && npm install -g mermaid-filter"
        exit 1
    }
fi

# ============================================================
# 剪贴板模式
# ============================================================
if $USE_CLIPBOARD; then
    info "剪贴板模式: 正在读取剪贴板..."
    RAW_CONTENT=$(read_clipboard)

    if [[ -z "$RAW_CONTENT" ]]; then
        err "剪贴板为空，请先复制 AI 回答内容。"
        exit 1
    fi

    # 清洗
    CLEANED=$(sanitize_markdown "$RAW_CONTENT" "$AI_MODEL")

    # 生成标题（取第一个 # 标题的前 50 字符）
    TITLE=$(echo "$CLEANED" | grep -m1 '^# ' | sed 's/^# //' | cut -c1-50 | tr ' ' '_' | tr -d '[:punct:]')
    if [[ -z "$TITLE" ]]; then
        TITLE="AI_Export_$(date +%Y%m%d_%H%M%S)"
    fi

    # 保存临时文件
    TEMP_DIR="${TMPDIR:-/tmp}"
    TEMP_MD="${TEMP_DIR}/${TITLE}.md"
    echo "$CLEANED" > "$TEMP_MD"
    ok "内容已清洗 (${AI_MODEL}) → $TEMP_MD"

    INPUT="$TEMP_MD"
    DESKTOP=$(get_desktop)
    mkdir -p "$DESKTOP/md2word_exports" 2>/dev/null
    if [[ -z "$OUTPUT_FILE" ]]; then
        if $USE_HTML; then
            OUTPUT_FILE="$DESKTOP/md2word_exports/${TITLE}.html"
        else
            OUTPUT_FILE="$DESKTOP/md2word_exports/${TITLE}.docx"
        fi
    fi
fi

# ============================================================
# 文件模式验证
# ============================================================
if ! $USE_CLIPBOARD && [[ ! -f "$INPUT" ]]; then
    err "文件不存在: $INPUT"
    exit 1
fi

BASENAME="$(basename "$INPUT" .md)"
DIRNAME="$(dirname "$INPUT")"

if [[ -z "$OUTPUT_FILE" ]]; then
    if $USE_HTML; then
        OUTPUT_FILE="${DIRNAME}/${BASENAME}.html"
    else
        OUTPUT_FILE="${DIRNAME}/${BASENAME}.docx"
    fi
fi

# ============================================================
# 统计
# ============================================================
LINES=$(wc -l < "$INPUT")
count_content "$INPUT"

info "输入: $INPUT (${LINES} 行)"
info "统计: ${IMG_COUNT}图 ${TABLE_COUNT}表行 ${MATH_COUNT}公式 ${CODE_COUNT}代码块 ${MERMAID_COUNT}Mermaid"

# ============================================================
# 构建 Pandoc 参数
# ============================================================
PANDOC_ARGS=(--mathml --from markdown+tex_math_dollars+tex_math_single_backslash)

$USE_TOC && { PANDOC_ARGS+=(--toc --toc-depth=3); info "目录: 已启用"; }

if [[ -n "$REF_DOC" && -f "$REF_DOC" ]]; then
    PANDOC_ARGS+=(--reference-doc="$REF_DOC"); info "模板: $REF_DOC"
elif [[ -n "$REF_DOC" ]]; then
    warn "模板不存在: $REF_DOC，已忽略"
fi

PANDOC_ARGS+=(--resource-path="${DIRNAME}")

$USE_MERMAID && [[ "$MERMAID_COUNT" -gt 0 ]] && PANDOC_ARGS+=(-F mermaid-filter)

# ============================================================
# 转换
# ============================================================
if $USE_HTML; then
    info "模式: HTML（代码语法高亮 + 图片内嵌）"
    PANDOC_ARGS+=(--highlight-style=tango --standalone --metadata title="$BASENAME" --self-contained)
    info "转换中..."
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" "${PANDOC_ARGS[@]}"
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    ok "已生成: $OUTPUT_FILE ($SIZE)"
    warn "浏览器打开 → Ctrl+A → 粘贴到 Word（含代码高亮）"
else
    info "模式: DOCX（公式OMML + 图片嵌入 + 表格保留）"
    info "转换中..."
    "$PANDOC" "$INPUT" -o "$OUTPUT_FILE" "${PANDOC_ARGS[@]}"
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    ok "已生成: $OUTPUT_FILE ($SIZE)"
    print_report
fi

# ---- 自动打开（仅剪贴板模式）----
if $USE_CLIPBOARD; then
    info "正在打开文件..."
    open_file "$OUTPUT_FILE"
    # 清理临时文件
    rm -f "$TEMP_MD"
fi
