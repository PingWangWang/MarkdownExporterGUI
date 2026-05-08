# -*- mode: python ; coding: utf-8 -*-
"""
Markdown Exporter GUI 打包脚本
直接运行: py build_exe.py
"""

import sys
import subprocess
import os
import glob
from pathlib import Path
from datetime import datetime

# 强制 stdout/stderr 使用 UTF-8，避免 Windows GBK 终端报 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 日志美化函数
def log_info(msg):
    print(f"  [INFO] {datetime.now().strftime('%H:%M:%S')} | {msg}")

def log_step(msg):
    print(f"\n{'='*60}")
    print(f"  STEP: {msg}")
    print(f"{'='*60}")

def log_success(msg):
    print(f"\n  [OK] {msg}")

def log_error(msg):
    print(f"\n  [FAIL] {msg}")

# 获取项目根目录（build_exe.py 在 build/ 目录，需要向上一级）
project_root = Path(__file__).parent.parent

# 从 _version.py 读取版本号
version_file = project_root / 'gui' / '_version.py'
app_version = "0.0.0"
if version_file.exists():
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('APP_VERSION'):
                    app_version = line.split('=')[1].strip().strip("\"'")
                    break
    except Exception:
        pass

# 生成时间戳
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

# 生成 exe 文件名：MarkdownExporter_v3.6.9_20250427-143025
exe_name = f"MarkdownExporter_v{app_version}_{timestamp}"

log_step("Markdown Exporter 打包配置")
print(f"  版本号   : {app_version}")
print(f"  时间戳   : {timestamp}")
print(f"  输出文件 : {exe_name}")
print(f"{'='*60}")

# 清理旧的构建文件（在项目根目录）
log_step("步骤 1/3: 清理旧文件")
log_info("正在清理旧的构建目录...")
import importlib.util
import shutil

# 清理项目根目录的 build（除了 build_exe.py 和 README.md）和 dist
build_dir = project_root / 'build'
if build_dir.exists():
    # 只删除 build/ 目录中的 PyInstaller 临时文件，保留脚本和文档
    for item in build_dir.iterdir():
        if item.name not in ['build_exe.py', 'README.md', 'README_PACKAGING.md', 'hook_onnxruntime.py']:
            if item.is_dir():
                shutil.rmtree(item)
                log_info(f"已删除 {item.name}/")
            else:
                item.unlink()
                log_info(f"已删除 {item.name}")

log_success("清理完成")

# 清理 dist/ 目录中的旧版 exe
dist_dir = project_root / 'dist'
if dist_dir.exists():
    old_exes = list(dist_dir.glob('MarkdownExporter_v*.exe'))
    if old_exes:
        for old_exe in old_exes:
            old_exe.unlink()
            log_info(f"已删除旧版 exe: {old_exe.name}")
    else:
        log_info("dist/ 目录中无旧版 exe")

# 分隔符（Windows 用 ;，Linux/Mac 用 :）
sep = ';' if sys.platform == 'win32' else ':'

# 动态获取 pypandoc 的 pandoc 路径
log_step("步骤 1.5: 查找 Pandoc")
try:
    import pypandoc
    pandoc_path = pypandoc.get_pandoc_path()
    if pandoc_path:
        pandoc_dir = str(Path(pandoc_path).parent)
        log_info(f"找到 Pandoc: {pandoc_path}")
        log_info(f"Pandoc 目录: {pandoc_dir}")
        
        # 检查必要的文件是否存在
        pandoc_exe = Path(pandoc_dir) / 'pandoc.exe' if sys.platform == 'win32' else Path(pandoc_dir) / 'pandoc'
        if not pandoc_exe.exists():
            log_error(f"Pandoc 可执行文件不存在: {pandoc_exe}")
            sys.exit(1)
        
        copyright_file = Path(pandoc_dir) / 'COPYRIGHT.txt'
        if copyright_file.exists():
            log_info(f"找到版权文件: {copyright_file}")
    else:
        log_error("未找到 Pandoc")
        log_info("请安装 pypandoc-binary: pip install pypandoc-binary")
        sys.exit(1)
except ImportError:
    log_error("未找到 pypandoc 模块")
    log_info("请先安装: pip install pypandoc-binary")
    sys.exit(1)

# 构建 PyInstaller 命令
# 注意：使用 --distpath 和 --workpath 指定输出目录，避免覆盖 build/ 目录
cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--name', exe_name,
    '--onefile',
    '--noconfirm',
    '--clean',
    '--distpath', str(project_root / 'dist'),  # 输出到项目根目录的 dist/
    '--workpath', str(project_root / 'build'),  # 临时文件在项目根目录的 build/
    '--specpath', str(project_root / 'build'),  # spec 文件在项目根目录的 build/
    # 隐藏导入 - GUI 模块
    '--hidden-import', '_version',
    '--hidden-import', '_dialogs',
    '--hidden-import', '_app',
    # 隐藏导入 - md_exporter 核心模块
    '--hidden-import', 'md_exporter',
    '--hidden-import', 'md_exporter.services',
    '--hidden-import', 'md_exporter.services.svc_md_to_docx',
    '--hidden-import', 'md_exporter.services.svc_md_to_pdf',
    '--hidden-import', 'md_exporter.services.svc_md_to_html',
    '--hidden-import', 'md_exporter.services.svc_md_to_pptx',
    '--hidden-import', 'md_exporter.services.svc_md_to_xlsx',
    '--hidden-import', 'md_exporter.services.svc_md_to_csv',
    '--hidden-import', 'md_exporter.services.svc_md_to_json',
    '--hidden-import', 'md_exporter.services.svc_md_to_xml',
    '--hidden-import', 'md_exporter.services.svc_md_to_latex',
    '--hidden-import', 'md_exporter.services.svc_md_to_ipynb',
    '--hidden-import', 'md_exporter.services.svc_md_to_md',
    '--hidden-import', 'md_exporter.utils',
    '--hidden-import', 'md_exporter.utils.markdown_utils',
    '--hidden-import', 'md_exporter.utils.file_utils',
    '--hidden-import', 'md_exporter.utils.pandoc_utils',
    '--hidden-import', 'md_exporter.utils.table_utils',
    '--hidden-import', 'md_exporter.utils.mermaid_utils',
    # 隐藏导入 - DOCX 操作相关
    '--hidden-import', 'docx',
    '--hidden-import', 'docx.shared',
    '--hidden-import', 'lxml',
    # 隐藏导入 - 第三方依赖
    '--hidden-import', 'markdown',
    '--hidden-import', 'pandas',
    '--hidden-import', 'xhtml2pdf',
    '--collect-all', 'reportlab',  # 收集 reportlab 所有子模块（包括条形码等）
    '--hidden-import', 'PIL',
    '--hidden-import', 'PIL.Image',
    '--hidden-import', 'pypandoc',
    '--hidden-import', 'jinja2',
    '--hidden-import', 'tkinterdnd2',
    '--hidden-import', 'requests',
    '--exclude-module', 'tkinter.test',
    # 添加数据文件
    # 添加 md_exporter 的资源文件
    '--add-data', f"{project_root / 'md_exporter' / 'assets'}{sep}md_exporter/assets",
    # 添加 tkinterdnd2（含原生 DLL）
    '--add-data', f"{project_root / '.venv' / 'Lib' / 'site-packages' / 'tkinterdnd2'}{sep}tkinterdnd2",
    # 添加图标资源文件（运行时 _get_icon_path 需要读取）
    '--add-data', f"{project_root / 'res'}{sep}res",
    # 添加 README.md 文档
    '--add-data', f"{project_root / 'README.md'}{sep}.",
    # 添加 Pandoc（内置在 pypandoc-binary 包中）— 打包整个 files/ 目录
    '--add-data', f"{pandoc_dir}{sep}pypandoc/files",
]

# 继续添加其他参数
cmd += [
    # 添加图标
    '--icon', str(project_root / 'res' / 'icad.ico'),
    # 窗口模式（无控制台）
    '--windowed',
    str(project_root / 'gui' / 'main.py')
]

log_step("步骤 2/3: 执行打包")
log_info(f"PyInstaller 正在构建 {exe_name}...\n")

# 执行 PyInstaller
try:
    result = subprocess.run(cmd, cwd=str(project_root))
    
    if result.returncode == 0:
        log_step("步骤 3/3: 打包结果")
        log_success(f"打包成功！")
        
        # 单文件模式：exe 直接生成在 dist/ 目录下
        dist_output = project_root / 'dist'
        exe_file = dist_output / f"{exe_name}.exe"
        
        if exe_file.exists():
            file_size = exe_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            print(f"\n{'='*60}")
            log_info(f"输出位置: {exe_file}")
            log_info(f"文件大小: {size_mb:.2f} MB ({file_size:,} bytes)")
            log_info("单文件模式：直接将 exe 发给对方即可使用，无需安装 Python")
            print(f"{'='*60}\n")
        else:
            log_error("未找到生成的 exe 文件")
            print(f"{'='*60}\n")
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
