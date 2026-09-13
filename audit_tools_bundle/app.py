from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from . import BUNDLE_VERSION
from .registry import COMPONENTS, ComponentSpec


class AuditToolsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"审计工具整合包 V{BUNDLE_VERSION}")
        self.geometry("1120x860")
        self.minsize(900, 680)
        self._loaded: dict[str, ttk.Frame] = {}
        self._placeholders: dict[str, ttk.Frame] = {}
        self._spec_by_id = {item.component_id: item for item in COMPONENTS}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        header = ttk.Frame(self, padding=(16, 12, 16, 8))
        header.pack(fill="x")
        ttk.Label(header, text="审计工具整合包", font=("Microsoft YaHei UI", 19, "bold")).pack(side="left")
        ttk.Label(header, text=f"V{BUNDLE_VERSION}  单窗口标签页  独立业务进程", foreground="#555555").pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        for spec in COMPONENTS:
            placeholder = ttk.Frame(self.notebook)
            placeholder.component_id = spec.component_id
            ttk.Label(placeholder, text=f"选择标签页后加载“{spec.label}”……", padding=24).pack(anchor="center")
            self.notebook.add(placeholder, text=spec.label)
            self._placeholders[str(placeholder)] = placeholder
        self.status_var = tk.StringVar(value="各工具业务代码相互独立；写文件任务在独立进程中执行。")
        ttk.Label(self, textvariable=self.status_var, padding=(16, 4, 16, 10), foreground="#555555").pack(fill="x")
        self.notebook.bind("<<NotebookTabChanged>>", self._load_selected)
        self.after_idle(self._load_selected)

    def _load_selected(self, _event=None) -> None:
        selected = self.notebook.select()
        if not selected or selected not in self._placeholders:
            return
        placeholder = self._placeholders.pop(selected)
        component_id = placeholder.component_id
        spec = self._spec_by_id[component_id]
        index = self.notebook.index(placeholder)
        try:
            frame = spec.load_factory()(self.notebook)
        except Exception as exc:
            frame = self._error_frame(spec, exc)
        self.notebook.forget(placeholder)
        placeholder.destroy()
        position = "end" if index >= len(self.notebook.tabs()) else index
        self.notebook.insert(position, frame, text=spec.label)
        self.notebook.select(frame)
        self._loaded[component_id] = frame
        self.status_var.set(f"{spec.label}：{spec.risk}")

    def _error_frame(self, spec: ComponentSpec, exc: Exception) -> ttk.Frame:
        frame = ttk.Frame(self.notebook, padding=24)
        ttk.Label(frame, text=f"{spec.label}加载失败", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text=str(exc), foreground="#9C2F2F", wraplength=780).pack(anchor="w", pady=(12, 0))
        return frame

    def _on_close(self) -> None:
        running = [self._spec_by_id[key].label for key, value in self._loaded.items() if getattr(value, "running", False)]
        if running:
            messagebox.showwarning("任务正在运行", "请等待以下工具到达安全结束点后再关闭：\n" + "\n".join(running), parent=self)
            return
        self.destroy()


def main() -> None:
    AuditToolsApp().mainloop()
