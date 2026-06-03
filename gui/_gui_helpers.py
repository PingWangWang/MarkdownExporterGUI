"""Markdown Exporter GUI - 公共工具函数。

提供与 GUI 框架无关的通用工具：
  - get_resource_path()    资源文件路径解析（兼容打包/开发环境）
  - get_icon_path()        图标文件路径
  - open_file_or_dir()     跨平台打开文件/目录
  - open_url()             打开 URL
  - parse_dnd_paths()      解析 tkinterdnd2 拖拽路径
  - resolve_log_tag()      日志消息标签解析
  - check_dependencies()   依赖缺失检测
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Final

# 依赖模块 → pip 包名映射
_DEPENDENCY_MAP: Final[dict[str, str]] = {
    "pypandoc": "pypandoc-binary",
    "docx": "python-docx",
    "xhtml2pdf": "xhtml2pdf",
    "markdown": "markdown",
    "pandas": "pandas",
    "requests": "requests",
    "PIL": "pillow",
}


# ── 资源路径 ─────────────────────────────────────────────────────────────────


def get_resource_path(relative_path: str) -> Path | None:
    """获取资源文件路径，兼容 PyInstaller 打包和开发环境。

    Args:
        relative_path: 相对于项目根目录的路径，如 ``"res/icad.ico"``。

    Returns:
        文件存在的 Path 对象，找不到返回 None。
    """
    candidates: list[Path] = []
    # 打包环境
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / relative_path)
    # 开发环境：gui/ 的上级目录
    candidates.append(Path(__file__).resolve().parent.parent / relative_path)
    for p in candidates:
        if p.exists():
            return p
    return None


def get_icon_path() -> Path | None:
    """返回 icad.ico 的路径。"""
    return get_resource_path("res/icad.ico")


# ── 文件/URL 打开 ────────────────────────────────────────────────────────────


def open_file_or_dir(path: str, *, select_in_explorer: bool = False) -> None:
    """跨平台打开文件或目录。

    Args:
        path: 文件或目录路径。
        select_in_explorer: Windows 下是否在资源管理器中选中该文件。

    Raises:
        OSError: 打开失败。
    """
    if not os.path.exists(path):
        raise OSError(f"路径不存在：{path}")

    if sys.platform == "win32":
        if select_in_explorer and os.path.isfile(path):
            subprocess.run(["explorer", "/select,", path], check=False)
        else:
            os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        if select_in_explorer and os.path.isfile(path):
            subprocess.run(["open", "-R", path], check=False)
        else:
            subprocess.run(["open", path], check=False)
    else:
        subprocess.run(["xdg-open", path], check=False)


def open_url(url: str) -> None:
    """在默认浏览器中打开 URL。"""
    webbrowser.open(url)


# ── 拖拽路径解析 ─────────────────────────────────────────────────────────────


def parse_dnd_paths(raw_data: str) -> list[str]:
    """解析 tkinterdnd2 拖拽事件返回的路径字符串。

    tkinterdnd2 返回格式：``{path with spaces} {path2}`` 或 ``path``。

    Args:
        raw_data: ``event.data`` 原始字符串。

    Returns:
        解析后的路径列表。
    """
    paths = re.findall(r"\{([^}]+)\}|([^\s]+)", raw_data)
    return [p[0] or p[1] for p in paths]


# ── 日志标签 ─────────────────────────────────────────────────────────────────


def resolve_log_tag(message: str) -> str:
    """根据消息内容判断日志标签类型。

    Args:
        message: 日志消息文本。

    Returns:
        标签名：``"success"`` / ``"error"`` / ``"warning"`` / ``"info"`` 等。
    """
    rules: list[tuple[str, tuple[str, ...]]] = [
        ("success", ("✓", "✅", "✔")),
        ("error", ("❌", "×")),
        ("warning", ("⚠", "Warning", "warning")),
        ("service", ("[服务]",)),
        ("arrow", ("→",)),
        ("complete", ("处理完成", "开始处理")),
    ]

    stripped = message.strip()
    for tag, prefixes in rules:
        if stripped.startswith(prefixes):
            return tag

    # summary: 包含关键词或以 "=" 开头的长行
    summary_keywords = ("Mermaid 转换汇总", "转换汇总", "总计:", "成功:", "失败:")
    if any(kw in stripped for kw in summary_keywords) or (
        stripped.startswith("=") and len(stripped) > 10
    ):
        return "summary"

    # info: 以 "[" 开头且包含 "]"
    if stripped.startswith("[") and "]" in stripped:
        return "info"

    return "normal"


# ── 依赖检测 ─────────────────────────────────────────────────────────────────


def check_dependencies() -> list[str]:
    """检查必要依赖是否可用。

    Returns:
        缺失的 pip 包名列表（空列表表示全部可用）。
    """
    missing: list[str] = []
    for module_name, package_name in _DEPENDENCY_MAP.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(package_name)
    return missing
