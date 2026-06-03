"""Markdown Exporter GUI - 版本信息。

版本号读取优先级：
  1. 环境变量 ``APP_VERSION``（打包脚本注入）
  2. 项目根目录 ``pyproject.toml``（开发环境）
  3. 硬编码回退值
"""

from __future__ import annotations

import os
from pathlib import Path

# 硬编码回退值，与 pyproject.toml 保持一致
_FALLBACK_VERSION: str = "3.6.9"


def _read_version() -> str:
    """从 pyproject.toml 读取版本号，失败时回退到硬编码值。"""
    # 1. 环境变量优先（打包脚本可注入）
    env_version = os.environ.get("APP_VERSION")
    if env_version:
        return env_version

    # 2. 尝试从 pyproject.toml 读取
    try:
        import tomllib  # Python 3.11+

        # 打包环境：pyproject.toml 在 _MEIPASS 根目录
        # 开发环境：pyproject.toml 在 gui/ 的上级目录
        candidates: list[Path] = []
        import sys

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "pyproject.toml")
        candidates.append(Path(__file__).resolve().parent.parent / "pyproject.toml")

        for pyproject_path in candidates:
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                return data["project"]["version"]
    except Exception:
        pass

    # 3. 回退
    return _FALLBACK_VERSION


APP_VERSION: str = _read_version()
