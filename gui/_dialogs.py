"""Markdown Exporter GUI - 对话框组件。

与 GUI 主类解耦，通过 DialogTheme 数据类传递样式参数。

核心组件：
  - DialogTheme       对话框样式数据类
  - show_about()      关于窗口
  - ask_overwrite()   文件覆盖确认窗口
  - ask_file_locked() 文件被占用提示窗口
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from gui._version import APP_VERSION

# ── 样式数据类 ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DialogTheme:
    """对话框样式参数，从主应用传递。"""

    root: tk.Tk
    bg: str
    header_bg: str
    header_fg: str
    label_fg: str
    btn_color: str
    btn_hover: str
    btn_run: str
    btn_run_hover: str
    border_color: str
    btn_active: str  # btn_color 的 active 色


# ── 公共对话框框架 ───────────────────────────────────────────────────────────


def _center_dialog(dlg: tk.Toplevel, parent: tk.Tk) -> None:
    """将对话框居中到父窗口上方。

    Args:
        dlg: 要居中的 Toplevel 对话框。
        parent: 父窗口。
    """
    dlg.update_idletasks()
    w = dlg.winfo_width()
    h = dlg.winfo_height()
    rx = parent.winfo_x() + (parent.winfo_width() - w) // 2
    ry = parent.winfo_y() + (parent.winfo_height() - h) // 2
    dlg.geometry(f"+{rx}+{ry}")
    dlg.grab_set()


def _create_button(
    parent: tk.Frame,
    text: str,
    bg: str,
    bg_hover: str,
    cmd: Callable[[], None],
    *,
    padx: int = 6,
) -> tk.Button:
    """统一的按钮创建函数。

    Args:
        parent: 父容器。
        text: 按钮文本。
        bg: 背景色。
        bg_hover: 悬停背景色。
        cmd: 点击回调。
        padx: 水平内边距。

    Returns:
        创建的 Button 对象。
    """
    b = tk.Button(
        parent,
        text=text,
        width=8,
        bg=bg,
        fg="#FFFFFF",
        relief="flat",
        font=("Microsoft YaHei UI", 9, "bold"),
        cursor="hand2",
        command=cmd,
    )
    b.pack(side=tk.LEFT, padx=padx)
    b.bind("<Enter>", lambda e: b.config(bg=bg_hover))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


# ── 关于对话框 ───────────────────────────────────────────────────────────────


def show_about(theme: DialogTheme) -> None:
    """显示关于信息（自定义风格）。

    Args:
        theme: 对话框样式。
    """
    dlg = tk.Toplevel(theme.root)
    dlg.overrideredirect(True)
    dlg.configure(bg=theme.bg)
    dlg.resizable(False, False)

    # 标题栏
    header = tk.Frame(dlg, bg=theme.header_bg, height=46)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(
        header,
        text=f"关于  Markdown Exporter v{APP_VERSION}",
        bg=theme.header_bg,
        fg=theme.header_fg,
        font=("Microsoft YaHei UI", 12, "bold"),
    ).pack(side=tk.LEFT, padx=16, pady=8)

    # 内容区
    body = tk.Frame(dlg, bg=theme.bg, padx=24, pady=16)
    body.pack(fill=tk.BOTH)

    sections: list[tuple[str, list[str]]] = [
        (
            "项目来源",
            [
                f"版本: {APP_VERSION}",
                "作者: pingwang1994",
                "GitHub: https://github.com/pingwang1994/markdown-exporter-gui",
            ],
        ),
        (
            "详细文档",
            [
                "点击查看 README.md 获取完整使用说明和示例",
            ],
        ),
    ]

    for title, items in sections:
        tk.Label(
            body,
            text=title,
            bg=theme.bg,
            fg=theme.header_bg,
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(anchor=tk.W, pady=(8, 2))
        for item in items:
            _add_about_item(body, item, theme)

    # 底部
    tk.Frame(dlg, bg=theme.border_color, height=1).pack(fill=tk.X, pady=(8, 0))
    btn_frame = tk.Frame(dlg, bg=theme.bg, pady=10)
    btn_frame.pack()
    ok_btn = tk.Button(
        btn_frame,
        text="确  定",
        width=10,
        bg=theme.btn_color,
        fg="#FFFFFF",
        relief="flat",
        font=("Microsoft YaHei UI", 9, "bold"),
        cursor="hand2",
        command=dlg.destroy,
    )
    ok_btn.pack()
    ok_btn.bind("<Enter>", lambda e: ok_btn.config(bg=theme.btn_active))
    ok_btn.bind("<Leave>", lambda e: ok_btn.config(bg=theme.btn_color))

    _center_dialog(dlg, theme.root)


def _add_about_item(body: tk.Frame, item: str, theme: DialogTheme) -> None:
    """向关于对话框内容区添加一条项目。"""
    # URL 链接
    if "http://" in item or "https://" in item:
        url_start = item.find("http")
        prefix = item[:url_start].rstrip(": ").rstrip()
        url = item[url_start:]

        item_frame = tk.Frame(body, bg=theme.bg)
        item_frame.pack(fill=tk.X, anchor=tk.W, pady=1)

        if prefix:
            tk.Label(
                item_frame,
                text=f"  • {prefix}: ",
                bg=theme.bg,
                fg=theme.label_fg,
                font=("Microsoft YaHei UI", 9),
                justify="left",
            ).pack(side=tk.LEFT, anchor=tk.W)
        else:
            tk.Label(
                item_frame,
                text="  • ",
                bg=theme.bg,
                fg=theme.label_fg,
                font=("Microsoft YaHei UI", 9),
                justify="left",
            ).pack(side=tk.LEFT, anchor=tk.W)

        link_label = tk.Label(
            item_frame,
            text=url,
            bg=theme.bg,
            fg="#1E90FF",
            font=("Microsoft YaHei UI", 9, "underline"),
            cursor="hand2",
            justify="left",
        )
        link_label.pack(side=tk.LEFT, anchor=tk.W)
        link_label.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        link_label.bind("<Enter>", lambda e: e.widget.config(fg="#4169E1"))
        link_label.bind("<Leave>", lambda e: e.widget.config(fg="#1E90FF"))

    # README 链接
    elif "README.md" in item:
        _add_readme_link(body, theme)

    # 普通文本
    else:
        tk.Label(
            body,
            text=f"  • {item}",
            bg=theme.bg,
            fg=theme.label_fg,
            font=("Microsoft YaHei UI", 9),
            justify="left",
        ).pack(anchor=tk.W, pady=1)


def _add_readme_link(body: tk.Frame, theme: DialogTheme) -> None:
    """添加 README.md 可点击链接。"""
    item_frame = tk.Frame(body, bg=theme.bg)
    item_frame.pack(fill=tk.X, anchor=tk.W, pady=1)

    tk.Label(
        item_frame,
        text="  • ",
        bg=theme.bg,
        fg=theme.label_fg,
        font=("Microsoft YaHei UI", 9),
        justify="left",
    ).pack(side=tk.LEFT, anchor=tk.W)

    readme_link = tk.Label(
        item_frame,
        text="查看 README.md",
        bg=theme.bg,
        fg="#1E90FF",
        font=("Microsoft YaHei UI", 9, "underline"),
        cursor="hand2",
        justify="left",
    )
    readme_link.pack(side=tk.LEFT, anchor=tk.W)

    def open_readme(e: tk.Event) -> None:  # type: ignore[type-arg]
        try:
            if getattr(sys, "frozen", False):
                base_dir = sys._MEIPASS
            else:
                base_dir = str(Path(__file__).resolve().parent.parent)
            readme_path = os.path.join(base_dir, "README.md")

            if os.path.exists(readme_path):
                system = platform.system()
                if system == "Windows":
                    os.startfile(readme_path)  # type: ignore[attr-defined]
                elif system == "Darwin":
                    subprocess.call(["open", readme_path])
                else:
                    subprocess.call(["xdg-open", readme_path])
            else:
                webbrowser.open(
                    "https://github.com/pingwang1994/markdown-exporter-gui#readme"
                )
        except Exception:
            webbrowser.open(
                "https://github.com/pingwang1994/markdown-exporter-gui#readme"
            )

    readme_link.bind("<Button-1>", open_readme)
    readme_link.bind("<Enter>", lambda e: e.widget.config(fg="#4169E1"))
    readme_link.bind("<Leave>", lambda e: e.widget.config(fg="#1E90FF"))


# ── 覆盖确认对话框 ───────────────────────────────────────────────────────────


def ask_overwrite(
    theme: DialogTheme,
    filename: str,
    *,
    is_multi: bool = False,
) -> bool:
    """在主线程弹出文件覆盖确认对话框。

    Args:
        theme: 对话框样式。
        filename: 文件名。
        is_multi: 是否为批量模式（显示"全部覆盖/全部跳过"按钮）。

    Returns:
        True 表示覆盖，False 表示跳过。
    """
    result = [False]
    event = threading.Event()

    def _show() -> None:
        dlg = tk.Toplevel(theme.root)
        dlg.overrideredirect(True)
        dlg.configure(bg=theme.bg)
        dlg.resizable(False, False)

        # 标题栏
        header = tk.Frame(dlg, bg="#E67E22", height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="文件已存在",
            bg="#E67E22",
            fg="#FFFFFF",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side=tk.LEFT, padx=12, pady=6)

        # 内容区
        body = tk.Frame(dlg, bg=theme.bg, padx=20, pady=16)
        body.pack(fill=tk.BOTH)
        tk.Label(
            body,
            text=f"「{filename}」已存在，是否覆盖？",
            bg=theme.bg,
            fg=theme.label_fg,
            font=("Microsoft YaHei UI", 10),
            wraplength=340,
            justify="left",
        ).pack(anchor=tk.W)

        btn_frame = tk.Frame(dlg, bg=theme.bg, pady=10)
        btn_frame.pack()

        def on_overwrite_one() -> None:
            result[0] = True
            dlg.destroy()

        def on_skip() -> None:
            result[0] = False
            dlg.destroy()

        if is_multi:
            _create_button(btn_frame, "本次覆盖", theme.btn_run, theme.btn_run_hover, on_overwrite_one)
            _create_button(btn_frame, "全部覆盖", "#8E44AD", "#6C3483", lambda: _set_overwrite_all_and_close(dlg, result))
            _create_button(btn_frame, "本次跳过", theme.btn_color, theme.btn_active, on_skip)
            _create_button(btn_frame, "全部跳过", "#7F8C8D", "#626567", lambda: _set_skip_all_and_close(dlg, result))
        else:
            _create_button(btn_frame, "覆  盖", theme.btn_run, theme.btn_run_hover, on_overwrite_one, padx=8)
            _create_button(btn_frame, "跳  过", theme.btn_color, theme.btn_active, on_skip, padx=8)

        _center_dialog(dlg, theme.root)
        dlg.wait_window()
        event.set()

    theme.root.after(0, _show)
    event.wait()
    return result[0]


def _set_overwrite_all_and_close(dlg: tk.Toplevel, result: list[bool]) -> None:
    """标记"全部覆盖"并关闭对话框。"""
    result[0] = True
    # 通过特殊标记通知调用方
    dlg._overwrite_all = True  # type: ignore[attr-defined]
    dlg.destroy()


def _set_skip_all_and_close(dlg: tk.Toplevel, result: list[bool]) -> None:
    """标记"全部跳过"并关闭对话框。"""
    result[0] = False
    dlg._skip_all = True  # type: ignore[attr-defined]
    dlg.destroy()


def ask_overwrite_batch(
    theme: DialogTheme,
    filename: str,
    overwrite_all: bool,
    skip_all: bool,
) -> tuple[bool, bool, bool]:
    """批量模式的覆盖确认，返回 (继续, 新的overwrite_all, 新的skip_all)。

    Args:
        theme: 对话框样式。
        filename: 文件名。
        overwrite_all: 当前"全部覆盖"标志。
        skip_all: 当前"全部跳过"标志。

    Returns:
        (should_continue, new_overwrite_all, new_skip_all)
    """
    if overwrite_all:
        return True, True, False
    if skip_all:
        return False, False, True

    result = [False]
    new_overwrite_all = [overwrite_all]
    new_skip_all = [skip_all]
    event = threading.Event()

    def _show() -> None:
        dlg = tk.Toplevel(theme.root)
        dlg.overrideredirect(True)
        dlg.configure(bg=theme.bg)
        dlg.resizable(False, False)

        # 标题栏
        header = tk.Frame(dlg, bg="#E67E22", height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="文件已存在",
            bg="#E67E22",
            fg="#FFFFFF",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side=tk.LEFT, padx=12, pady=6)

        # 内容区
        body = tk.Frame(dlg, bg=theme.bg, padx=20, pady=16)
        body.pack(fill=tk.BOTH)
        tk.Label(
            body,
            text=f"「{filename}」已存在，是否覆盖？",
            bg=theme.bg,
            fg=theme.label_fg,
            font=("Microsoft YaHei UI", 10),
            wraplength=340,
            justify="left",
        ).pack(anchor=tk.W)

        btn_frame = tk.Frame(dlg, bg=theme.bg, pady=10)
        btn_frame.pack()

        def on_overwrite_one() -> None:
            result[0] = True
            dlg.destroy()

        def on_overwrite_all() -> None:
            result[0] = True
            new_overwrite_all[0] = True
            dlg.destroy()

        def on_skip() -> None:
            result[0] = False
            dlg.destroy()

        def on_skip_all() -> None:
            result[0] = False
            new_skip_all[0] = True
            dlg.destroy()

        _create_button(btn_frame, "本次覆盖", theme.btn_run, theme.btn_run_hover, on_overwrite_one)
        _create_button(btn_frame, "全部覆盖", "#8E44AD", "#6C3483", on_overwrite_all)
        _create_button(btn_frame, "本次跳过", theme.btn_color, theme.btn_active, on_skip)
        _create_button(btn_frame, "全部跳过", "#7F8C8D", "#626567", on_skip_all)

        _center_dialog(dlg, theme.root)
        dlg.wait_window()
        event.set()

    theme.root.after(0, _show)
    event.wait()
    return result[0], new_overwrite_all[0], new_skip_all[0]


# ── 文件被占用对话框 ─────────────────────────────────────────────────────────


def ask_file_locked(theme: DialogTheme, filename: str) -> bool:
    """在主线程弹出文件被占用提示对话框。

    Args:
        theme: 对话框样式。
        filename: 文件名。

    Returns:
        True 表示关闭文件后重试，False 表示跳过。
    """
    result = [False]
    event = threading.Event()

    def _show() -> None:
        dlg = tk.Toplevel(theme.root)
        dlg.overrideredirect(True)
        dlg.configure(bg=theme.bg)
        dlg.resizable(False, False)

        # 标题栏
        header = tk.Frame(dlg, bg="#E74C3C", height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="文件被占用",
            bg="#E74C3C",
            fg="#FFFFFF",
            font=("Microsoft YaHei UI", 10, "bold"),
        ).pack(side=tk.LEFT, padx=12, pady=6)

        # 内容区
        body = tk.Frame(dlg, bg=theme.bg, padx=20, pady=16)
        body.pack(fill=tk.BOTH)

        tk.Label(
            body,
            text=f"「{filename}」正在被其他程序打开，\n无法覆盖保存。",
            bg=theme.bg,
            fg=theme.label_fg,
            font=("Microsoft YaHei UI", 10),
            wraplength=340,
            justify="center",
        ).pack(anchor=tk.CENTER, pady=(0, 8))

        tk.Label(
            body,
            text="请关闭该文件后重试，或选择跳过。",
            bg=theme.bg,
            fg="#7F8C8D",
            font=("Microsoft YaHei UI", 9),
            wraplength=340,
            justify="center",
        ).pack(anchor=tk.CENTER)

        btn_frame = tk.Frame(dlg, bg=theme.bg, pady=10)
        btn_frame.pack()

        def on_retry() -> None:
            result[0] = True
            dlg.destroy()

        def on_skip() -> None:
            result[0] = False
            dlg.destroy()

        _create_button(btn_frame, "关闭后重试", theme.btn_run, theme.btn_run_hover, on_retry, padx=8)
        _create_button(btn_frame, "跳  过", theme.btn_color, theme.btn_active, on_skip, padx=8)

        _center_dialog(dlg, theme.root)
        dlg.wait_window()
        event.set()

    theme.root.after(0, _show)
    event.wait()
    return result[0]
