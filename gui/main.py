"""Markdown Exporter GUI - 程序入口。

模块结构：
  _version.py       版本信息（从 pyproject.toml 动态读取）
  _gui_helpers.py   公共工具函数
  _dialogs.py       对话框（关于、覆盖确认、文件锁定检测）
  _theme_manager.py 主题管理器（ttkbootstrap 主题 + 明暗切换）
  _conversion.py    转换业务逻辑层
  _app.py           主应用类 MarkdownExporterGUI
  main.py           程序入口点
"""

from __future__ import annotations

import os
import sys

# 将项目根目录加入 sys.path，使 gui._app 等包限定导入在 PyInstaller
# 模块分析阶段可被正确解析（打包环境 _MEIPASS 与根目录等效）
_gui_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_gui_dir)  # gui/ 的父目录 = 项目根目录
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

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

import ttkbootstrap  # noqa: E402

from gui._app import MarkdownExporterGUI  # noqa: E402
from gui._theme_manager import ThemeManager  # noqa: E402


def main() -> None:
    """启动 GUI 主窗口。

    创建 DnD 兼容的根窗口，附加 ttkbootstrap 主题，然后启动主循环。
    """
    # 必须先创建窗口再附加主题，以兼容 tkinterdnd2
    root: tk.Tk = TkinterDnD.Tk() if _HAS_DND else tk.Tk()

    # 在根窗口上创建 ttkbootstrap 主题
    # TkinterDnD.Tk() / tk.Tk() 已设置 tkinter._default_root，
    # ttkbootstrap.Style 会自动使用它，无需显式传递 master 参数。
    style = ttkbootstrap.Style(theme="flatly")

    # 创建主题管理器
    theme_manager = ThemeManager(style)

    # 启动主应用
    MarkdownExporterGUI(root, theme_manager=theme_manager, has_dnd=_HAS_DND)
    root.mainloop()


if __name__ == "__main__":
    main()
