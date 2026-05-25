"""AI 模型专属 Markdown 清洗器。

支持的模型:
    deepseek — 移除 🤖 标题 + "已深度思考" 折叠块
    chatgpt  — 移除 ChatGPT 标签
    claude   — 移除 Claude 标签 + 思考块 + antml XML
    kimi     — 移除 Kimi 思考引用块
    generic  — 通用 HTML 标签清洗
"""

import re

# ── 通用清洗 ──

def _strip_html_tags(text: str) -> str:
    """移除常见 HTML 标签但保留内部文字。"""
    text = re.sub(r"<details[^>]*>", "", text)
    text = re.sub(r"</details>", "", text)
    text = re.sub(r"<summary[^>]*>", "", text)
    text = re.sub(r"</summary>", "", text)
    text = re.sub(r"<div[^>]*>", "", text)
    text = re.sub(r"</div>", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r'style="[^"]*"', "", text)
    return text


# ── 模型专属 ──

def clean_deepseek(text: str) -> str:
    text = re.sub(r"^## 🤖 .*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"<details[^>]*>.*?</details>", "", text, flags=re.DOTALL)
    text = re.sub(r"<div[^>]*></div>", "", text)
    return text


def clean_chatgpt(text: str) -> str:
    text = re.sub(r"^ChatGPT said:.*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^ChatGPT.*\n?", "", text, flags=re.MULTILINE)
    return text


def clean_claude(text: str) -> str:
    text = re.sub(r"^Claude said:.*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^Claude .*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"<details[^>]*>.*?</details>", "", text, flags=re.DOTALL)
    text = re.sub(r"<antml:[^>]*>", "", text)
    text = re.sub(r"</antml:[^>]*>", "", text)
    text = re.sub(r"<function_calls>", "", text)
    text = re.sub(r"</function_calls>", "", text)
    return text


def clean_kimi(text: str) -> str:
    text = re.sub(r"<details[^>]*>.*?</details>", "", text, flags=re.DOTALL)
    return text


# ── 模型检测 ──

DETECTORS = [
    ("deepseek", r"🤖.*deepseek|已深度思考"),
    ("chatgpt", r"ChatGPT|OpenAI"),
    ("claude", r"Claude|claude|Anthropic"),
    ("kimi", r"Kimi|kimi|月之暗面"),
]


def detect(text: str) -> str:
    """根据内容特征自动检测 AI 模型来源。"""
    for name, pattern in DETECTORS:
        if re.search(pattern, text):
            return name
    return "generic"


CLEANERS = {
    "deepseek": clean_deepseek,
    "chatgpt": clean_chatgpt,
    "claude": clean_claude,
    "kimi": clean_kimi,
    "generic": lambda t: t,
}


def sanitize(text: str, model: str = "auto") -> str:
    """清洗 AI 模型输出中的非 Markdown 标记。

    Args:
        text: 原始剪贴板内容。
        model: 模型名称或 "auto" 自动检测。

    Returns:
        清洗后的纯 Markdown 文本。
    """
    if model == "auto":
        model = detect(text)
    cleaner = CLEANERS.get(model, lambda t: t)
    return _strip_html_tags(cleaner(text))
