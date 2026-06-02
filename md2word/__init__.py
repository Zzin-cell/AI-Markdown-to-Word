"""md2word — Markdown 全格式转换器。

用法:
    md2word             # 交互式向导（推荐新手）
    md2word -w          # 同上
    md2word -p          # 粘贴就绪模式
    md2word -c          # 剪贴板 → .docx
    md2word doc.md      # 转 docx（默认）
    md2word doc.md -f pptx  # 转 PowerPoint
    md2word doc.md -f html --toc  # 转 HTML + 目录
    python -m md2word   # 模块方式运行
"""

__version__ = "5.0.0"
