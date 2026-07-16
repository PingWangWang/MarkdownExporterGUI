"""Markdown Exporter GUI - 主应用类。

仅负责 GUI 渲染和用户交互，业务逻辑委托给 ConversionService。

包含 MarkdownExporterGUI 类：
  - 窗口初始化与图标设置
  - 界面样式（ttkbootstrap 主题驱动）
  - 界面构建（输入/输出区域、格式选择、日志、底部链接、主题切换）
  - 文件选择、目录操作
  - 文件处理（多线程转换，委托给 ConversionService）
  - 对话框委托（关于、覆盖确认）
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from gui._conversion import OUTPUT_FORMATS, ConversionOptions, ConversionService
from gui._dialogs import (
    DialogTheme,
    ask_file_locked,
    ask_overwrite_batch,
    show_about,
)
from gui._gui_helpers import (
    check_dependencies,
    get_icon_path,
    open_file_or_dir,
    open_url,
    parse_dnd_paths,
    resolve_log_tag,
)
from gui._theme_manager import ThemeManager
from gui._version import APP_VERSION

# UI 尺寸常量
DEFAULT_WINDOW_WIDTH: int = 750
DEFAULT_WINDOW_HEIGHT: int = 560
DEFAULT_LISTBOX_HEIGHT: int = 4
DEFAULT_LOG_HEIGHT: int = 7


class MarkdownExporterGUI:
    """Markdown Exporter 主应用类。

    Args:
        root: Tkinter 根窗口。
        theme_manager: ThemeManager 实例，管理 ttkbootstrap 主题。
        has_dnd: 是否支持拖拽（tkinterdnd2）。
    """

    # ── 初始化 ────────────────────────────────────────────────────────────

    def __init__(
        self, root: tk.Tk, theme_manager: ThemeManager, *, has_dnd: bool = False,
    ) -> None:
        self.root = root
        self._tm = theme_manager
        self.has_dnd = has_dnd
        self.root.title(f"Markdown Exporter v{APP_VERSION}")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(
            f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}"
            f"+{(sw - DEFAULT_WINDOW_WIDTH) // 2}+{(sh - DEFAULT_WINDOW_HEIGHT) // 2}"
        )
        self.root.resizable(False, False)

        self._set_window_icon()

        # 界面状态
        self.input_files: list[str] = []
        self.output_dir = tk.StringVar()
        self.output_format = tk.StringVar(value="DOCX")
        self.is_processing: bool = False
        self.last_output_file: str | None = None
        self.last_single_output: str | None = None
        self.debug_logging = tk.BooleanVar(value=True)
        self.use_template = tk.BooleanVar(value=False)
        self.template_path = tk.StringVar()
        self.save_mermaid_images = tk.BooleanVar(value=False)
        self.convert_mermaid_images = tk.BooleanVar(value=False)

        # 转换服务（在 _create_conversion_service 中初始化）
        self._conversion: ConversionService | None = None

        # 设置GUI日志回调
        self._setup_gui_logging()

        self.setup_styles()
        self._create_conversion_service()
        self.create_widgets()

        # 启动后依赖检查
        self.root.after(500, self._check_missing_dependencies)

        # 窗口完全显示后再次应用图标
        self.root.after(100, self._set_window_icon)

    # ── 转换服务初始化 ────────────────────────────────────────────────────

    def _create_conversion_service(self) -> None:
        """创建转换服务实例。"""
        self._conversion = ConversionService(
            strategy=self,  # MarkdownExporterGUI 实现 OverwriteStrategy
            log_callback=self.log_message,
        )

    # ── OverwriteStrategy 实现 ────────────────────────────────────────────

    def ask_overwrite(
        self,
        filename: str,
        *,
        is_batch: bool,
        overwrite_all: bool,
        skip_all: bool,
    ) -> tuple[bool, bool, bool]:
        """实现 OverwriteStrategy.ask_overwrite。"""
        theme = self._get_dialog_theme()
        return ask_overwrite_batch(theme, filename, overwrite_all, skip_all)

    def ask_file_locked(self, filename: str) -> bool:
        """实现 OverwriteStrategy.ask_file_locked。"""
        theme = self._get_dialog_theme()
        return ask_file_locked(theme, filename)

    # ── 依赖检查 ──────────────────────────────────────────────────────────

    def _check_missing_dependencies(self) -> None:
        """启动后检查缺失依赖，仅警告不影响使用。"""
        missing = check_dependencies()
        if missing:
            self.log_message(
                f"\u26a0 检测到缺失依赖: {', '.join(missing)}\n"
                f"  请运行: uv sync"
            )

    # ── 对话框主题 ────────────────────────────────────────────────────────

    def _get_dialog_theme(self) -> DialogTheme:
        """从 ThemeManager 创建对话框样式数据对象。"""
        c = self._tm.colors
        return DialogTheme(
            root=self.root,
            bg=c["bg"],
            header_bg=c["header_bg"],
            header_fg=c["header_fg"],
            label_fg=c["label_fg"],
            btn_color=c["primary"],
            btn_hover=c["primary"],  # ttkbootstrap 自动处理 hover
            btn_run=c["success"],
            btn_run_hover=c["success"],
            border_color=c["border"],
            btn_active=c["primary"],
        )

    # ── 图标 ──────────────────────────────────────────────────────────────

    def _set_window_icon(self) -> None:
        """设置窗口图标（标题栏 & 任务栏）。"""
        try:
            if sys.platform == "win32":
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "MarkdownExporter.GUI.App"
                )

            icon_path = get_icon_path()
            if icon_path:
                self.root.iconbitmap(default=str(icon_path))
                try:
                    from PIL import Image, ImageTk

                    img = Image.open(str(icon_path))
                    img32 = img.resize((32, 32), Image.LANCZOS)
                    self._taskbar_photo = ImageTk.PhotoImage(img32)
                    self.root.wm_iconphoto(True, self._taskbar_photo)
                except Exception:
                    pass
        except Exception:
            pass

    # ── 日志回调设置 ──────────────────────────────────────────────────────

    def _setup_gui_logging(self) -> None:
        """设置GUI日志回调，使服务模块的日志能在GUI中显示。"""
        try:
            from md_exporter.utils.logger_utils import set_gui_log_callback

            def gui_log_callback(message: str) -> None:
                self.root.after(0, lambda: self._log_message_from_service(message))

            set_gui_log_callback(gui_log_callback)
        except ImportError:
            pass

    def _log_message_from_service(self, message: str) -> None:
        """从服务模块接收日志消息并显示在GUI中。"""
        if self.debug_logging.get():
            self.log_message(f"[服务] {message}")

    # ── 样式 ──────────────────────────────────────────────────────────────

    def setup_styles(self) -> None:
        """配置 ttkbootstrap 主题驱动的样式。

        颜色和基础样式由 ThemeManager / ttkbootstrap 自动管理。
        这里只配置自定义 style 名称的字体等非颜色属性。
        """
        s = self._tm.style

        # 设置全局默认字体
        s.configure(".", font=("Microsoft YaHei UI", 9))

        # 自定义按钮样式 — 使用 ttkbootstrap 已内置的语义样式
        # primary/success/info/warning/danger.TButton 已由 ttkbootstrap 定义
        # 我们只需配置额外的非语义样式
        s.configure("ThemeToggle.TButton", font=("Microsoft YaHei UI", 9))

        # 标签样式 — 字体覆盖
        s.configure("Field.TLabel", font=("Microsoft YaHei UI", 9))
        s.configure("Log.TLabel", font=("Microsoft YaHei UI", 9))
        s.configure(
            "Link.TLabel",
            font=("Microsoft YaHei UI", 9, "underline"),
            cursor="hand2",
        )
        s.configure(
            "Hint.TLabel",
            font=("Microsoft YaHei UI", 9),
            cursor="hand2",
        )

    # ── 界面构建 ──────────────────────────────────────────────────────────

    def create_widgets(self) -> None:
        """构建主界面所有控件。"""
        mf = ttk.Frame(self.root, padding="14 10 14 6")
        mf.pack(fill=tk.BOTH, expand=True)
        mf.columnconfigure(1, weight=1)
        self._main_frame = mf
        row = 0

        row = self._create_file_section(mf, row)
        row = self._create_output_dir_section(mf, row)
        row = self._create_format_section(mf, row)
        row = self._create_template_section(mf, row)
        row = self._create_mermaid_convert_section(mf, row)
        row = self._create_mermaid_save_section(mf, row)
        row = self._create_action_buttons(mf, row)
        row = self._create_log_section(mf, row)
        self._create_footer(mf, row)

        if self.has_dnd:
            self._register_drop_target()

    # ── 界面子区域 ────────────────────────────────────────────────────────

    def _create_file_section(self, mf: ttk.Frame, row: int) -> int:
        """文件选择区域。"""
        ttk.Label(mf, text="选择 Markdown 文件:", style="Field.TLabel").grid(
            row=row, column=0, sticky=tk.NW, pady=4, padx=(0, 8)
        )
        ff = ttk.Frame(mf)
        ff.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        ff.columnconfigure(0, weight=1)

        # 文件列表 — 使用 ttk.Treeview 替代 tk.Listbox，自动适配主题
        list_frame = ttk.Frame(ff)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6))
        list_frame.columnconfigure(0, weight=1)

        self.file_treeview = ttk.Treeview(
            list_frame,
            columns=("filename",),
            show="headings",
            height=DEFAULT_LISTBOX_HEIGHT,
            selectmode="extended",
        )
        self.file_treeview.heading("filename", text="文件名")
        self.file_treeview.column("filename", width=400, minwidth=200)
        self.file_treeview.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=0, pady=0)
        list_sb = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.file_treeview.yview,
        )
        self.file_treeview.configure(yscrollcommand=list_sb.set)
        list_sb.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 操作按钮列
        btn_col = ttk.Frame(ff)
        btn_col.grid(row=0, column=1, sticky=tk.N)
        ttk.Button(
            btn_col, text="添加文件", command=self.select_files,
            style="primary.TButton", width=10,
        ).pack(pady=(0, 4))
        ttk.Button(
            btn_col, text="删除选中", command=self.remove_selected_files,
            style="danger.TButton", width=10,
        ).pack(pady=(0, 4))
        ttk.Button(
            btn_col, text="清空列表", command=self.clear_files,
            style="warning.TButton", width=10,
        ).pack()
        self.file_treeview.bind("<Delete>", lambda e: self.remove_selected_files())
        return row + 1

    def _create_output_dir_section(self, mf: ttk.Frame, row: int) -> int:
        """保存位置区域。"""
        ttk.Label(mf, text="选择保存位置:", style="Field.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        sf = ttk.Frame(mf)
        sf.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        sf.columnconfigure(0, weight=1)
        ttk.Entry(sf, textvariable=self.output_dir, state="readonly").grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 6)
        )
        ttk.Button(
            sf, text="保存位置", command=self.select_output_dir,
            style="primary.TButton", width=10,
        ).grid(row=0, column=1)
        return row + 1

    def _create_format_section(self, mf: ttk.Frame, row: int) -> int:
        """输出格式选择区域。"""
        ttk.Label(mf, text="选择输出格式:", style="Field.TLabel").grid(
            row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8)
        )
        cf = ttk.Frame(mf)
        cf.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        format_list = [f"{desc} ({ext})" for desc, ext in OUTPUT_FORMATS.values()]
        self.format_combo = ttk.Combobox(cf, values=format_list, state="readonly", width=30)
        self.format_combo.set("Word 文档 (.docx)")
        self.format_combo.grid(row=0, column=0, sticky=tk.W, padx=(0, 6))
        self.format_combo.bind("<<ComboboxSelected>>", self.on_format_change)
        return row + 1

    def _create_template_section(self, mf: ttk.Frame, row: int) -> int:
        """模板选项区域。"""
        self.template_label = ttk.Label(mf, text="使用自定义模板:", style="Field.TLabel")
        self.template_label.grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        tf = ttk.Frame(mf)
        tf.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        tf.columnconfigure(1, weight=1)
        self.use_template_check = ttk.Checkbutton(
            tf, text="", variable=self.use_template, command=self.on_template_toggle,
        )
        self.use_template_check.grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        template_entry = ttk.Entry(tf, textvariable=self.template_path, state="readonly", width=40)
        template_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 6))
        self.select_template_btn = ttk.Button(
            tf, text="选择模板", command=self.select_template,
            style="primary.TButton", width=10, state="disabled",
        )
        self.select_template_btn.grid(row=0, column=2)
        self.template_frame = tf
        return row + 1

    def _create_mermaid_convert_section(self, mf: ttk.Frame, row: int) -> int:
        """转换 Mermaid 图片选项区域。"""
        self.convert_mermaid_label = ttk.Label(
            mf, text="转换 Mermaid 图片:", style="Field.TLabel",
        )
        self.convert_mermaid_label.grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        mf3 = ttk.Frame(mf)
        mf3.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        self.convert_mermaid_check = ttk.Checkbutton(
            mf3, text="", variable=self.convert_mermaid_images,
        )
        self.convert_mermaid_check.grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        hint_label = ttk.Label(
            mf3, text="该功能需联网访问 https://mermaid.ink", style="Link.TLabel",
        )
        hint_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 4))
        hint_label.bind(
            "<Button-1>", lambda e: open_url("https://mermaid.ink"),
        )
        self.convert_mermaid_frame = mf3
        return row + 1

    def _create_mermaid_save_section(self, mf: ttk.Frame, row: int) -> int:
        """保存 Mermaid 图片选项区域。"""
        self.save_mermaid_label = ttk.Label(
            mf, text="保存 Mermaid 图片:", style="Field.TLabel",
        )
        self.save_mermaid_label.grid(row=row, column=0, sticky=tk.W, pady=4, padx=(0, 8))
        mf2 = ttk.Frame(mf)
        mf2.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=4)
        self.save_mermaid_check = ttk.Checkbutton(
            mf2, text="", variable=self.save_mermaid_images,
        )
        self.save_mermaid_check.grid(row=0, column=0, sticky=tk.W, padx=(0, 8))
        self.save_mermaid_frame = mf2
        return row + 1

    def _create_action_buttons(self, mf: ttk.Frame, row: int) -> int:
        """分割线 + 操作按钮。"""
        ttk.Separator(mf, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=6,
        )
        row += 1
        bf = ttk.Frame(mf)
        bf.grid(row=row, column=0, columnspan=2, pady=4)
        self.process_button = ttk.Button(
            bf, text="▶  开始转换", command=self.start_processing,
            style="success.TButton", width=14,
        )
        self.process_button.pack(side=tk.LEFT, padx=6)
        ttk.Button(
            bf, text="📂  打开输出目录", command=self.open_output_dir,
            style="info.TButton", width=14,
        ).pack(side=tk.LEFT, padx=6)
        self.open_doc_button = ttk.Button(
            bf, text="📄  打开文档", command=self.open_last_document,
            style="info.TButton", width=12, state="disabled",
        )
        self.open_doc_button.pack(side=tk.LEFT, padx=6)
        # 主题切换按钮
        self.theme_toggle_btn = ttk.Button(
            bf, text="🌙 暗色", command=self._toggle_theme,
            style="ThemeToggle.TButton", width=8,
        )
        self.theme_toggle_btn.pack(side=tk.RIGHT, padx=6)
        return row + 1

    def _create_log_section(self, mf: ttk.Frame, row: int) -> int:
        """日志区域。"""
        ttk.Label(mf, text="处理日志:", style="Log.TLabel").grid(
            row=row, column=0, sticky=tk.NW, pady=(8, 2), padx=(0, 8),
        )
        log_right_frame = ttk.Frame(mf)
        log_right_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=(8, 2))
        log_right_frame.columnconfigure(0, weight=1)
        debug_check = ttk.Checkbutton(
            log_right_frame, text="显示详细日志",
            variable=self.debug_logging, command=self._on_debug_logging_change,
        )
        debug_check.grid(row=0, column=0, sticky=tk.W)
        c = self._tm.colors
        self.log_text = scrolledtext.ScrolledText(
            mf,
            height=DEFAULT_LOG_HEIGHT,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg=c["log_bg"],
            fg=c["log_fg"],
            insertbackground=c["log_fg"],
            selectbackground=c["select_bg"],
            selectforeground=c["select_fg"],
            relief="flat",
            borderwidth=0,
            state="disabled",
        )
        self.log_text.grid(row=row + 1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(2, 2))
        mf.rowconfigure(row + 1, weight=1)
        # 注册原生控件，使主题切换时自动刷新颜色（延迟求值）
        self._tm.watch(
            self.log_text,
            refresh_callback=lambda c: {
                "bg": c["log_bg"],
                "fg": c["log_fg"],
                "insertbackground": c["log_fg"],
                "selectbackground": c["select_bg"],
                "selectforeground": c["select_fg"],
            },
        )
        for tag, color in [
            ("success", "#00AA00"),
            ("error", "#CC0000"),
            ("warning", "#CC9900"),
            ("info", "#0066CC"),
            ("arrow", "#666666"),
            ("complete", "#0066CC"),
            ("summary", "#CC6600"),
            ("service", "#666666"),
            ("normal", c["log_fg"]),
        ]:
            self.log_text.tag_configure(tag, foreground=color)
        return row + 2

    def _create_footer(self, mf: ttk.Frame, row: int) -> None:
        """底部链接。"""
        lf = ttk.Frame(mf)
        lf.grid(row=row, column=0, columnspan=2, pady=(4, 2), sticky=(tk.W, tk.E))
        lbl = ttk.Label(lf, text="查看项目说明及帮助文档 >>", style="Link.TLabel")
        lbl.pack(side=tk.LEFT)
        lbl.bind("<Button-1>", lambda e: self.show_about())
        ttk.Label(lf, text=f"v{APP_VERSION}", style="Log.TLabel").pack(side=tk.RIGHT)

    def _register_drop_target(self) -> None:
        """注册整个窗口为拖拽目标。"""
        from tkinterdnd2 import DND_FILES

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """处理拖入的文件列表。"""
        raw: str = event.data
        files = parse_dnd_paths(raw)
        md_files = [f for f in files if f.lower().endswith((".md", ".markdown"))]
        if not md_files:
            self.log_message("✗ 拖入的文件不含 .md / .markdown 文件，已忽略")
            return
        self._add_files(md_files)
        self.log_message(f"已拖入 {len(md_files)} 个文件")

    def on_format_change(self, event: tk.Event | None = None) -> None:
        """当输出格式改变时的回调。"""
        output_format = self.get_selected_format()
        if output_format == "DOCX":
            self.template_label.grid()
            self.template_frame.grid()
            self.save_mermaid_label.grid()
            self.save_mermaid_frame.grid()
            self.convert_mermaid_label.grid()
            self.convert_mermaid_frame.grid()
        else:
            self.template_label.grid_remove()
            self.template_frame.grid_remove()
            self.use_template.set(False)
            self.template_path.set("")
            self.save_mermaid_label.grid_remove()
            self.save_mermaid_frame.grid_remove()
            self.save_mermaid_images.set(False)
            self.convert_mermaid_label.grid_remove()
            self.convert_mermaid_frame.grid_remove()
            self.convert_mermaid_images.set(True)

    def on_template_toggle(self) -> None:
        """模板开关变化时的回调。"""
        if self.use_template.get():
            self.select_template_btn.configure(state="normal")
        else:
            self.select_template_btn.configure(state="disabled")
            self.template_path.set("")

    def select_template(self) -> None:
        """选择模板文件。"""
        filetypes = [
            ("Word 模板文件", "*.docx"),
            ("所有文件", "*.*"),
        ]
        template = filedialog.askopenfilename(title="选择 DOCX 模板文件", filetypes=filetypes)
        if template:
            self.template_path.set(template)
            self.log_message(f"已选择模板: {Path(template).name}")

    def _on_debug_logging_change(self) -> None:
        """调试日志开关变化时的回调。"""
        if self.debug_logging.get():
            self.log_message("[信息] 已启用详细日志模式")
        else:
            self.log_message("[信息] 已关闭详细日志模式")

    # ── 主题切换 ──────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        """一键切换明暗主题。"""
        self._tm.toggle()
        # 更新主题切换按钮文本
        btn_text = "☀️ 亮色" if self._tm.is_dark else "🌙 暗色"
        self.theme_toggle_btn.configure(text=btn_text)

        # 刷新对话按钮等未注册的控件颜色
        c = self._tm.colors
        self.log_text.tag_configure("normal", foreground=c["log_fg"])

    # ── 日志 ──────────────────────────────────────────────────────────────

    def log_message(self, message: str) -> None:
        """向日志区域追加消息。"""
        self.log_text.configure(state="normal")
        tag = resolve_log_tag(message)
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    # ── 文件选择 & 目录操作 ───────────────────────────────────────────────

    def select_files(self) -> None:
        """打开文件选择对话框。"""
        filetypes = [
            ("Markdown 文件", "*.md *.markdown"),
            ("所有文件", "*.*"),
        ]
        files = filedialog.askopenfilenames(title="选择 Markdown 文件", filetypes=filetypes)
        if not files:
            return
        self._add_files(list(files))

    def _add_files(self, files: list[str]) -> None:
        """将文件添加到树形视图（自动去重）。"""
        existing = set(self.input_files)
        new_files = [f for f in files if f not in existing]
        for f in new_files:
            self.input_files.append(f)
            self.file_treeview.insert("", tk.END, values=(Path(f).name,))
        if not self.output_dir.get() and self.input_files:
            self.output_dir.set(str(Path(self.input_files[0]).parent))

    def clear_files(self) -> None:
        """清空文件列表。"""
        self.input_files = []
        for item in self.file_treeview.get_children():
            self.file_treeview.delete(item)
        self.output_dir.set("")

    def remove_selected_files(self) -> None:
        """删除选中的文件。"""
        selected = self.file_treeview.selection()
        for item_id in reversed(selected):
            index = self.file_treeview.index(item_id)
            self.file_treeview.delete(item_id)
            del self.input_files[index]

    def select_output_dir(self) -> None:
        """选择输出目录。"""
        d = filedialog.askdirectory(title="选择保存位置")
        if d:
            self.output_dir.set(d)

    def open_output_dir(self) -> None:
        """打开输出目录（资源管理器中选中最后输出的文件）。"""
        out = self.output_dir.get()
        if not out:
            messagebox.showwarning("警告", "请先选择保存位置！")
            return
        if not os.path.exists(out):
            messagebox.showerror("错误", f"目录不存在：{out}")
            return
        try:
            select_file = self.last_output_file if self.last_output_file else None
            open_file_or_dir(
                out,
                select_in_explorer=bool(select_file and os.path.exists(select_file)),
            )
            # Windows 资源管理器选中需要特殊处理
            if sys.platform == "win32" and select_file and os.path.exists(select_file):
                subprocess.run(["explorer", "/select,", select_file], check=False)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录：{e}")

    # ── 获取输出格式 ──────────────────────────────────────────────────────

    def get_selected_format(self) -> str:
        """获取用户选择的输出格式代码。"""
        selected = self.format_combo.get()
        for code, (desc, ext) in OUTPUT_FORMATS.items():
            if f"{desc} ({ext})" == selected:
                return code
        return "DOCX"

    # ── 文件处理 ──────────────────────────────────────────────────────────

    def start_processing(self) -> None:
        """开始转换（校验输入后启动后台线程）。"""
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择要处理的文件！")
            return
        if not self.output_dir.get():
            messagebox.showwarning("警告", "请选择保存位置！")
            return

        output_format = self.get_selected_format()
        self.log_message(f"输出格式: {OUTPUT_FORMATS[output_format][0]}")

        self.last_single_output = None
        self.open_doc_button.configure(state="disabled")
        self.process_button.configure(state="disabled")
        self.is_processing = True
        t = threading.Thread(target=self._process_files_thread, daemon=True)
        t.start()

    def _process_files_thread(self) -> None:
        """后台线程：批量转换文件。"""
        assert self._conversion is not None
        try:
            options = ConversionOptions(
                format_code=self.get_selected_format(),
                use_template=self.use_template.get(),
                template_path=self.template_path.get(),
                save_mermaid_images=self.save_mermaid_images.get(),
                convert_mermaid_images=self.convert_mermaid_images.get(),
            )
            converted = self._conversion.process_batch(
                self.input_files, self.output_dir.get(), options,
            )
            if len(converted) == 1:
                self.last_single_output = converted[0]
        except Exception as e:
            self.log_message(f"\n✗ 处理失败: {e}")
        finally:
            self.root.after(0, self._processing_complete)

    def _processing_complete(self) -> None:
        """转换完成后的 UI 更新。"""
        self.is_processing = False
        self.process_button.configure(state="normal")
        if self.last_single_output and os.path.exists(self.last_single_output):
            self.open_doc_button.configure(state="normal")
        else:
            self.open_doc_button.configure(state="disabled")

    def open_last_document(self) -> None:
        """直接打开最后一次单文件转换的输出文档。"""
        path = self.last_single_output
        if not path or not os.path.exists(path):
            messagebox.showwarning("警告", "文档不存在或尚未转换。")
            return
        try:
            open_file_or_dir(path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文档：{e}")

    # ── 对话框 ────────────────────────────────────────────────────────────

    def show_about(self) -> None:
        """显示关于对话框。"""
        show_about(self._get_dialog_theme())
