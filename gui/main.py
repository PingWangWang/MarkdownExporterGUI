"""Markdown Exporter GUI - 程序入口。

模块结构：
  _version.py       版本信息（从 pyproject.toml 动态读取）
  _gui_helpers.py   公共工具函数
  _dialogs.py       对话框（关于、覆盖确认、文件锁定检测）
  _conversion.py    转换业务逻辑层
  _app.py           主应用类 MarkdownExporterGUI
  main.py           程序入口点
"""

from __future__ import annotations

import os
import sys

# 确保 gui/ 目录在 sys.path（开发环境 & PyInstaller 均适用）
_gui_dir = os.path.dirname(os.path.abspath(__file__))
if _gui_dir not in sys.path:
    sys.path.insert(0, _gui_dir)

# PyInstaller 打包环境：将 _MEIPASS 加入 sys.path
_meipass = getattr(sys, "_MEIPASS", None)
if _meipass and _meipass not in sys.path:
    sys.path.insert(0, _meipass)

# PyInstaller 打包环境：设置 pandoc 路径
# pypandoc 内部用 'files/pandoc'（无 .exe 后缀）作为全路径查找，Windows 下会失败，
# 必须通过 PYPANDOC_PANDOC 环境变量显式指定带 .exe 后缀的完整路径。
if _meipass:
    _pandoc_exe_name = "pandoc.exe" if sys.platform == "win32" else "pandoc"
    _pandoc_exe = os.path.join(_meipass, "pypandoc", "files", _pandoc_exe_name)
    os.environ["PYPANDOC_PANDOC"] = _pandoc_exe

import tkinter as tk  # noqa: E402

try:
    from tkinterdnd2 import TkinterDnD

    _HAS_DND = True
except ImportError:
    _HAS_DND = False

from _app import MarkdownExporterGUI  # noqa: E402


def main() -> None:
    """启动 GUI 主窗口。"""
    root: tk.Tk = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    MarkdownExporterGUI(root, has_dnd=_HAS_DND)
    root.mainloop()


if __name__ == "__main__":
    main()
