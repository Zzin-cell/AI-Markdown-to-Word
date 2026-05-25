"""跨平台剪贴板读写。

Windows: PowerShell Get-Clipboard / Set-Clipboard
macOS:   pbpaste / pbcopy
Linux:   wl-paste / wl-copy (Wayland) 或 xclip (X11)
"""

import os
import subprocess
import sys

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def read() -> str:
    """读取系统剪贴板文本内容。"""
    try:
        if IS_MAC:
            return subprocess.check_output(
                ["pbpaste"], text=True, stderr=subprocess.DEVNULL
            )
        elif IS_LINUX:
            if _has("wl-paste"):
                return subprocess.check_output(
                    ["wl-paste"], text=True, stderr=subprocess.DEVNULL
                )
            if _has("xclip"):
                return subprocess.check_output(
                    ["xclip", "-selection", "clipboard", "-o"],
                    text=True, stderr=subprocess.DEVNULL,
                )
            raise RuntimeError("Linux 需安装 xclip 或 wl-clipboard")
        else:
            result = subprocess.run(
                ["powershell.exe", "-Command", "Get-Clipboard"],
                capture_output=True, text=True,
            )
            return result.stdout
    except subprocess.CalledProcessError:
        return ""
    except Exception:
        return ""


def write_html(html_file: str) -> None:
    """将 HTML 文件内容写入系统剪贴板（Word 可直接粘贴）。

    Args:
        html_file: HTML 文件路径。
    """
    if IS_MAC:
        with open(html_file, "r", encoding="utf-8") as f:
            subprocess.run(["pbcopy"], input=f.read(), text=True, check=True)
    elif IS_LINUX:
        if _has("wl-copy"):
            with open(html_file, "r", encoding="utf-8") as f:
                subprocess.run(["wl-copy"], input=f.read(), text=True, check=True)
        elif _has("xclip"):
            with open(html_file, "r", encoding="utf-8") as f:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=f.read(), text=True, check=True,
                )
        else:
            raise RuntimeError("Linux 需安装 xclip 或 wl-clipboard")
    else:
        import pathlib
        html_path = str(pathlib.Path(html_file).resolve())
        ps = (
            f"Set-Clipboard -AsHtml -Value "
            f"([System.IO.File]::ReadAllText('{html_path}', "
            f"[System.Text.Encoding]::UTF8))"
        )
        subprocess.run(["powershell.exe", "-Command", ps], check=True)


def _has(cmd: str) -> bool:
    """检查命令是否在 PATH 中。"""
    import shutil
    return shutil.which(cmd) is not None
