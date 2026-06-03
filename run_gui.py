"""
Markdown Exporter GUI 启动脚本

使用方法：
  # 开发环境
  python run_gui.py

  # 使用 uv 运行
  uv run python run_gui.py
  uv run run_gui.py
"""

import os
import sys

# 添加 gui 目录到路径
gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gui")
if gui_dir not in sys.path:
    sys.path.insert(0, gui_dir)

# 导入并运行 GUI
from gui.main import main

if __name__ == "__main__":
    main()
