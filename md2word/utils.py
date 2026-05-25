"""跨平台工具函数。"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def find_pandoc() -> Optional[str]:
    """查找 pandoc 可执行文件路径。"""
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


def open_file(filepath: str) -> None:
    """用系统默认程序打开文件。"""
    if IS_MAC:
        subprocess.run(["open", filepath])
    elif IS_LINUX:
        subprocess.run(["xdg-open", filepath])
    else:
        os.startfile(filepath)


def get_desktop() -> str:
    """获取桌面路径。"""
    if IS_WIN:
        return os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    return os.path.join(os.path.expanduser("~"), "Desktop")


def generate_title(text: str) -> str:
    """从 Markdown 文本的第一行 # 标题生成安全文件名。"""
    m = re.search(r"^# (.+)", text, re.MULTILINE)
    if m:
        title = re.sub(r"[^\w\s]", "", m.group(1)[:50])
        title = title.strip().replace(" ", "_")
        if title:
            return title
    return f"AI_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def safe_print(msg: str) -> None:
    """安全打印，避免 Windows GBK 编码报错。"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))
