#!/usr/bin/env bash
# ============================================================
# AI-Markdown-to-Word Stop Hook
# 每次 Claude 响应结束，自动将回复存为 .docx 到桌面
# ============================================================
set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/AI-Markdown-to-Word"
OUTDIR="$USERPROFILE/Desktop/AI_Word_Exports"

mkdir -p "$OUTDIR"

# 从 stdin 读取 hook 事件 JSON
EVENT=$(cat)

# 提取最后一条 assistant 消息
# 方式: 通过 transcript_path 读取 JSONL，找最后一个 role=assistant
extract_message() {
    local json="$1"

    # 尝试从 transcript_path 读取 JSONL
    echo "$json" | python -c "
import sys, json, os

try:
    data = json.load(sys.stdin)
    tpath = data.get('transcript_path', '')
    if tpath and os.path.isfile(tpath):
        last_text = ''
        with open(tpath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except:
                    continue
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    if isinstance(content, list):
                        # 提取所有 text 块
                        parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                parts.append(block.get('text', ''))
                        text = ''.join(parts)
                    elif isinstance(content, str):
                        text = content
                    else:
                        continue
                    if text.strip():
                        last_text = text
        if last_text:
            print(last_text)
except: pass
" 2>/dev/null
}

CONTENT=$(extract_message "$EVENT")

# 如果没有提取到内容，跳过
if [[ -z "$CONTENT" ]]; then
    exit 0
fi

# 生成文件名（取第一行标题）
TITLE=$(echo "$CONTENT" | grep -m1 '^# ' | sed 's/^# //' | cut -c1-60 | tr ' ' '_' | tr -d '[:punct:]' | tr -d '\r\n')
if [[ -z "$TITLE" ]]; then
    TITLE="AI_Response_$(date +%Y%m%d_%H%M%S)"
fi

# 保存临时 md
TEMP_MD="/tmp/${TITLE}.md"
echo "$CONTENT" > "$TEMP_MD"

# 转换为 docx
OUTPUT="$OUTDIR/${TITLE}.docx"

# 找到 pandoc
PANDOC=""
if [[ -x "$SKILL_DIR/pandoc.exe" ]]; then
    PANDOC="$SKILL_DIR/pandoc.exe"
elif command -v pandoc &>/dev/null; then
    PANDOC=pandoc
fi

if [[ -n "$PANDOC" ]]; then
    "$PANDOC" "$TEMP_MD" -o "$OUTPUT" \
        --mathml \
        --from markdown+tex_math_dollars+tex_math_single_backslash \
        --resource-path="/tmp" 2>/dev/null && \
    echo "Word saved: $OUTPUT"
else
    echo "Pandoc not found, skipping auto-convert. Markdown saved: $TEMP_MD"
fi

rm -f "$TEMP_MD"
