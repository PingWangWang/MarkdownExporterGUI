# Markdown Exporter GUI - 项目指南

## 📌 项目概览

**名称**: Markdown Exporter GUI  
**版本**: 3.6.9  
**描述**: 桌面 GUI 应用，将 Markdown 文件转换为 DOCX、PDF、HTML 等格式

## 🛠️ 开发环境设置

### 快速开始

```bash
# 安装 uv（现代 Python 包管理工具）
pip install uv

# 同步项目依赖
uv sync

# 运行 GUI 应用
uv run python run_gui.py

# 或直接运行
python run_gui.py
```

### 依赖管理

所有依赖定义在 `pyproject.toml` 中：

- **运行依赖**: markdown, pandas, xhtml2pdf, reportlab, pillow, pypandoc-binary, tkinterdnd2, python-docx, requests
- **开发依赖**: pytest, ruff

使用 `uv sync` 会自动创建虚拟环境 `.venv` 并安装所有依赖。

## 📁 项目结构

```
markdown-exporter-gui/
├── gui/                    # GUI 应用主代码
│   ├── main.py            # 程序入口点
│   ├── _app.py            # 主应用类 MarkdownExporterGUI
│   ├── _dialogs.py        # 对话框组件
│   └── _version.py        # 版本信息（与 pyproject.toml 同步）
├── res/                    # 资源文件（图标等）
├── build/                  # 打包脚本和文档
│   ├── build_exe.py       # PyInstaller 打包脚本
│   └── README_PACKAGING.md # 打包指南
├── pyproject.toml         # 项目配置（依赖、版本、工具配置）
├── uv.lock                # 依赖版本锁定文件
├── run_gui.py             # 快速启动脚本
└── CLAUDE.md              # 本文件
```

## 🔧 工具配置

### Ruff（代码检查）

配置在 `pyproject.toml` 的 `[tool.ruff]` 部分：

```bash
# 检查代码
ruff check gui/

# 自动修复
ruff check --fix gui/
```

### Pytest（测试框架）

配置在 `pyproject.toml` 的 `[tool.pytest.ini_options]` 部分。

## 📦 打包为 EXE

### 步骤

```bash
# 1. 同步依赖
uv sync

# 2. 运行打包脚本
uv run python build/build_exe.py
```

输出文件位于 `dist/` 目录，文件名格式：`MarkdownExporter_v3.6.9_YYYYMMDD-HHMMSS.exe`

详见 [build/README_PACKAGING.md](build/README_PACKAGING.md)

## 🔑 关键文件说明

### `pyproject.toml`

- 定义项目元数据（名称、版本、许可证）
- 列出所有依赖
- 配置 Ruff、Pytest 等工具
- 指定构建系统（uv_build）

### `gui/_version.py`

应用版本号，与 `pyproject.toml` 中的版本号保持一致。

打包脚本会从 `pyproject.toml` 或 `_version.py` 读取版本号。

### `run_gui.py`

快速启动脚本，自动配置模块路径。

### `build/build_exe.py`

PyInstaller 打包脚本，负责：
- 清理旧文件
- 定位 Pandoc 二进制
- 构建 PyInstaller 命令
- 生成单文件 EXE

## 📝 常见任务

### 开发与测试

```bash
# 启动 GUI
uv run python run_gui.py

# 检查代码
uv run ruff check gui/

# 运行测试（如果有）
uv run pytest
```

### 版本更新

1. 编辑 `pyproject.toml` 中的 `version` 字段
2. `gui/_version.py` 会自动同步（手动编辑）
3. 重新运行打包脚本

### 添加依赖

```bash
# 编辑 pyproject.toml，在 dependencies 列表中添加新包
# 然后运行
uv sync
```

## 🐛 故障排除

### 打包后 EXE 体积过大（>200MB）

原因：意外安装了 scipy、scikit-learn 等大型库。

解决：
```bash
rm -rf .venv
uv sync
uv run python build/build_exe.py
```

### 找不到 Pandoc

原因：pypandoc-binary 未安装。

解决：
```bash
uv sync
```

### 模块导入错误

原因：虚拟环境未激活或依赖缺失。

解决：
```bash
# 使用 uv run 自动在虚拟环境中运行
uv run python run_gui.py
```

## 🚀 最佳实践

1. **始终使用 uv 管理依赖**
   - 不要手动 `pip install`
   - 使用 `uv sync` 同步依赖
   - 使用 `uv run` 运行 Python 脚本

2. **保持版本号一致**
   - `pyproject.toml` 是版本的唯一来源
   - `gui/_version.py` 用于运行时引用

3. **提交时检查代码**
   ```bash
   uv run ruff check gui/
   ```

4. **定期清理虚拟环境**
   ```bash
   rm -rf .venv
   uv sync
   ```

## 📚 相关文档

- [build/README_PACKAGING.md](build/README_PACKAGING.md) - 详细的打包指南
- [pyproject.toml](pyproject.toml) - 项目配置

## 📞 联系方式

作者: bowenliang123  
邮箱: liang.bowen.123@qq.com  
仓库: https://github.com/bowenliang123/markdown-exporter/
