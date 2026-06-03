# Markdown Exporter 打包指南

## 📋 前置要求

- Python 3.11 或更高版本
- `uv` 包管理工具（推荐）或 `pip`（传统方式）
- PyInstaller（会自动通过 `uv sync` 安装）

## 🚀 快速开始

### 1. 安装 uv（推荐）

首先安装现代 Python 包管理工具 `uv`：

```bash
# Windows / macOS / Linux
pip install uv
```

> **优势**：`uv` 比 `pip` 快 10-100 倍，自动管理虚拟环境，无需手动激活。

### 2. 同步依赖

在项目根目录运行：

```bash
# 自动创建虚拟环境并安装所有依赖（包括 PyInstaller）
uv sync
```

如果只需安装 GUI 依赖（不需要开发工具如 pytest、ruff）：

```bash
uv sync --no-group dev
```

### 3. 验证环境

```bash
# 检查虚拟环境中的 Python 版本
uv run python --version

# 检查已安装的包
uv run pip list
```

确保没有意外安装大型科学计算库（如 `scipy`、`scikit-learn`、`marker-pdf`），这些会导致打包体积暴增。

### 4. 执行打包

使用 `uv run` 在虚拟环境中运行打包脚本：

```bash
# 运行打包脚本
uv run python build/build_exe.py
```

打包完成后，生成的 exe 文件位于 `dist/` 目录。

---

## 📌 传统方式（不推荐）

如果你不想使用 `uv`，也可以用传统的 `venv` + `pip` 方式：

```bash
# 创建虚拟环境
py -3 -m venv .venv

# 激活虚拟环境（Windows）
.venv\Scripts\activate

# 激活虚拟环境（macOS/Linux）
source .venv/bin/activate

# 安装依赖
py -3 -m pip install --upgrade pip
py -3 -m pip install -e .
py -3 -m pip install pyinstaller

# 执行打包
py build/build_exe.py
```

## 📦 打包输出

- **位置**：`dist/MarkdownExporter_v{版本号}_{时间戳}.exe`
- **大小**：约 90-100 MB（正常范围）
- **模式**：单文件模式，无需安装，直接运行

## ⚠️ 常见问题

### 问题 1：打包体积过大（>200MB）

**原因**：意外安装了 `scipy`、`scikit-learn`、`marker-pdf` 等大型库。

**解决**：

```bash
# 重新同步依赖（清除旧的虚拟环境）
rm -rf .venv                  # Windows: rmdir /s /q .venv
uv sync
```

**预防**：始终使用 `uv sync` 从 `pyproject.toml` 安装，不要手动用 `pip install` 安装额外的包。

### 问题 2：找不到 Pandoc

**原因**：未安装 `pypandoc-binary`（应该由 `uv sync` 自动安装）。

**解决**：

```bash
uv sync
```

### 问题 3：打包失败

**原因**：依赖缺失或版本冲突。

**解决**：

```bash
# 清理虚拟环境，重新同步
rm -rf .venv
uv sync
uv run python build/build_exe.py
```

## 🔍 依赖检查清单

依赖定义在 `pyproject.toml` 中。`uv sync` 会自动安装正确的版本。

如需检查已安装的包：

```bash
uv run pip list
```

以下包**不应存在**（如果出现说明环境有问题）：

- ❌ scipy
- ❌ scikit-learn
- ❌ marker-pdf
- ❌ matplotlib

检查命令：

```bash
# Windows
uv run pip list | findstr /i "scipy scikit marker matplotlib"

# macOS/Linux
uv run pip list | grep -E "scipy|scikit|marker|matplotlib"
```

如果输出为空，说明环境干净。

## 💡 最佳实践

1. **始终使用 uv 管理依赖**

   ```bash
   # 不要直接用 pip install，使用 uv sync
   uv sync
   ```

2. **所有操作都在虚拟环境中进行**

   ```bash
   # 不要全局安装，uv 会自动管理虚拟环境
   uv run python build/build_exe.py
   ```

3. **定期清理虚拟环境**

   ```bash
   # 如果发现包体积异常，重建虚拟环境
   rm -rf .venv
   uv sync
   ```

4. **记录打包日志**

   ```bash
   # 保存打包输出到文件
   uv run python build/build_exe.py > build_log.txt 2>&1
   ```

5. **测试生成的 exe**
   ```bash
   # 运行生成的 exe，验证功能
   dist\MarkdownExporter_v*.exe
   ```

## 📝 版本管理

版本号定义在 `gui/_version.py`：

```python
APP_VERSION = "3.6.9"
```

修改版本号后重新打包即可。

## 🎯 总结（推荐方式）

| 步骤        | 命令                 |
| ----------- | -------------------- |
| 1. 安装 uv  | `pip install uv`     |
| 2. 同步依赖 | `uv sync`            |
| 3. 执行打包 | `uv run python build/build_exe.py` |

遵循以上流程，可确保打包体积稳定在 90-100 MB，避免因依赖污染导致的体积暴增问题。
