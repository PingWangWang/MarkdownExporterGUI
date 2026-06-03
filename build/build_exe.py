# -*- mode: python ; coding: utf-8 -*-
"""Markdown Exporter GUI 打包脚本。

使用 uv 管理依赖：
  uv sync                              # 同步依赖
  uv run python build/build_exe.py     # 运行打包

或直接运行：
  python build/build_exe.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 强制 stdout/stderr 使用 UTF-8，避免 Windows GBK 终端报 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── 日志函数 ─────────────────────────────────────────────────────────────────


def log_info(msg: str) -> None:
    """输出 INFO 级别日志。"""
    print(f"  [INFO] {datetime.now().strftime('%H:%M:%S')} | {msg}")


def log_step(msg: str) -> None:
    """输出步骤标题。"""
    print(f"\n{'=' * 60}")
    print(f"  STEP: {msg}")
    print(f"{'=' * 60}")


def log_success(msg: str) -> None:
    """输出成功消息。"""
    print(f"\n  [OK] {msg}")


def log_error(msg: str) -> None:
    """输出错误消息。"""
    print(f"\n  [FAIL] {msg}")


# ── 项目配置 ─────────────────────────────────────────────────────────────────

# 获取项目根目录（build_exe.py 在 build/ 目录，需要向上一级）
project_root = Path(__file__).parent.parent

# 从 _version.py 读取版本号（通过 exec 避免导入依赖）
version_file = project_root / "gui" / "_version.py"
app_version = "0.0.0"
if version_file.exists():
    try:
        # 读取文件内容，提取 _FALLBACK_VERSION 或 APP_VERSION
        content = version_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("_FALLBACK_VERSION"):
                app_version = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    except Exception:
        pass

# 生成时间戳和 exe 文件名
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
exe_name = f"MarkdownExporter_v{app_version}_{timestamp}"

log_step("Markdown Exporter 打包配置")
print(f"  版本号   : {app_version}")
print(f"  时间戳   : {timestamp}")
print(f"  输出文件 : {exe_name}")
print(f"{'=' * 60}")

# ── 步骤 1: 清理旧文件 ──────────────────────────────────────────────────────

log_step("步骤 1/3: 清理旧文件")
log_info("正在清理旧的构建目录...")

# 清理 build/ 目录中的 PyInstaller 临时文件
build_dir = project_root / "build"
_KEEP_FILES = {"build_exe.py", "README.md", "README_PACKAGING.md", "hook_onnxruntime.py"}
if build_dir.exists():
    for item in build_dir.iterdir():
        if item.name in _KEEP_FILES:
            continue
        if item.is_dir():
            shutil.rmtree(item)
            log_info(f"已删除 {item.name}/")
        else:
            item.unlink()
            log_info(f"已删除 {item.name}")

# 清理 dist/ 目录中的旧版 exe
dist_dir = project_root / "dist"
if dist_dir.exists():
    old_exes = list(dist_dir.glob("MarkdownExporter_v*.exe"))
    if old_exes:
        for old_exe in old_exes:
            old_exe.unlink()
            log_info(f"已删除旧版 exe: {old_exe.name}")
    else:
        log_info("dist/ 目录中无旧版 exe")

log_success("清理完成")

# ── 步骤 1.5: 查找 Pandoc ───────────────────────────────────────────────────

log_step("步骤 1.5: 查找 Pandoc")

sep = ";" if sys.platform == "win32" else ":"

try:
    import pypandoc

    pandoc_path = pypandoc.get_pandoc_path()
    if not pandoc_path:
        log_error("未找到 Pandoc")
        log_info("请安装 pypandoc-binary: pip install pypandoc-binary")
        sys.exit(1)

    pandoc_dir = str(Path(pandoc_path).parent)
    log_info(f"找到 Pandoc: {pandoc_path}")
    log_info(f"Pandoc 目录: {pandoc_dir}")

    pandoc_exe = Path(pandoc_dir) / ("pandoc.exe" if sys.platform == "win32" else "pandoc")
    if not pandoc_exe.exists():
        log_error(f"Pandoc 可执行文件不存在: {pandoc_exe}")
        sys.exit(1)
except ImportError:
    log_error("未找到 pypandoc 模块")
    log_info("请先安装: pip install pypandoc-binary")
    sys.exit(1)

# ── 步骤 2: 执行打包 ────────────────────────────────────────────────────────

log_step("步骤 2/3: 执行打包")
log_info(f"PyInstaller 正在构建 {exe_name}...\n")

# 构建 PyInstaller 命令
cmd: list[str] = [
    sys.executable, "-m", "PyInstaller",
    "--name", exe_name,
    "--onefile",
    "--noconfirm",
    "--clean",
    "--distpath", str(project_root / "dist"),
    "--workpath", str(project_root / "build"),
    "--specpath", str(project_root / "build"),
    # GUI 模块隐藏导入
    "--hidden-import", "_version",
    "--hidden-import", "_dialogs",
    "--hidden-import", "_app",
    "--hidden-import", "_conversion",
    "--hidden-import", "_gui_helpers",
    # md_exporter 核心模块
    "--hidden-import", "md_exporter",
    "--hidden-import", "md_exporter.services",
    "--hidden-import", "md_exporter.services.svc_md_to_docx",
    "--hidden-import", "md_exporter.services.svc_md_to_pdf",
    "--hidden-import", "md_exporter.services.svc_md_to_html",
    "--hidden-import", "md_exporter.services.svc_md_to_html_text",
    "--hidden-import", "md_exporter.utils",
    "--hidden-import", "md_exporter.utils.markdown_utils",
    "--hidden-import", "md_exporter.utils.file_utils",
    "--hidden-import", "md_exporter.utils.pandoc_utils",
    "--hidden-import", "md_exporter.utils.table_utils",
    "--hidden-import", "md_exporter.utils.mermaid_utils",
    "--hidden-import", "md_exporter.utils.logger_utils",
    "--hidden-import", "md_exporter.utils.text_utils",
    "--hidden-import", "md_exporter.utils.mimetype_utils",
    "--hidden-import", "md_exporter.utils.param_utils",
    # DOCX 操作相关
    "--hidden-import", "docx",
    "--hidden-import", "docx.shared",
    "--hidden-import", "lxml",
    # 第三方依赖
    "--hidden-import", "markdown",
    "--hidden-import", "pandas",
    "--hidden-import", "xhtml2pdf",
    "--collect-all", "reportlab",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "pypandoc",
    "--hidden-import", "jinja2",
    "--hidden-import", "tkinterdnd2",
    "--hidden-import", "requests",
    "--hidden-import", "bs4",
    "--hidden-import", "bs4.builder",
    # 排除不需要的模块
    "--exclude-module", "tkinter.test",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "scikit-learn",
    # 数据文件
    "--add-data", f"{project_root / 'md_exporter' / 'assets'}{sep}md_exporter/assets",
    "--add-data", f"{project_root / '.venv' / 'Lib' / 'site-packages' / 'tkinterdnd2'}{sep}tkinterdnd2",
    "--add-data", f"{project_root / 'res'}{sep}res",
    "--add-data", f"{pandoc_dir}{sep}pypandoc/files",
    # 图标和窗口模式
    "--icon", str(project_root / "res" / "icad.ico"),
    "--windowed",
    str(project_root / "gui" / "main.py"),
]

try:
    result = subprocess.run(cmd, cwd=str(project_root))

    if result.returncode == 0:
        log_step("步骤 3/3: 打包结果")
        log_success("打包成功！")

        exe_file = project_root / "dist" / f"{exe_name}.exe"
        if exe_file.exists():
            file_size = exe_file.stat().st_size
            size_mb = file_size / (1024 * 1024)

            print(f"\n{'=' * 60}")
            log_info(f"输出位置: {exe_file}")
            log_info(f"文件大小: {size_mb:.2f} MB ({file_size:,} bytes)")
            log_info("单文件模式：直接将 exe 发给对方即可使用，无需安装 Python")
            print(f"{'=' * 60}\n")
        else:
            log_error("未找到生成的 exe 文件")
            print(f"{'=' * 60}\n")
    else:
        log_error(f"打包失败，退出码: {result.returncode}")
        sys.exit(result.returncode)

except FileNotFoundError:
    log_error("未找到 PyInstaller")
    log_info("请先安装: pip install pyinstaller")
    sys.exit(1)
except KeyboardInterrupt:
    log_error("用户取消打包")
    sys.exit(1)
