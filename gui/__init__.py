"""Markdown Exporter GUI 包。

模块结构：
  _version.py       版本信息（从 pyproject.toml 动态读取）
  _gui_helpers.py   公共工具函数（资源路径、文件打开、日志标签等）
  _dialogs.py       对话框组件（关于、覆盖确认、文件锁定检测）
  _conversion.py    转换业务逻辑层（与 GUI 解耦）
  _app.py           主应用类 MarkdownExporterGUI
  main.py           程序入口点
"""
