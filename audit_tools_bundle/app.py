from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import messagebox, ttk

from . import BUNDLE_VERSION
from .registry import COMPONENTS, ComponentSpec


def get_work_area(root: tk.Tk) -> tuple[int, int, int, int]:
    if root.tk.call("tk", "windowingsystem") == "win32":
        class Rect(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        rect = Rect()
        if ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


def calculate_window_geometry(work_area: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    left, top, right, bottom = work_area
    available_width = max(1, right - left)
    available_height = max(1, bottom - top)
    width = min(1200, max(760, int(available_width * 0.90)), available_width)
    height = min(900, max(560, int(available_height * 0.90)), available_height)
    x = left + max(0, (available_width - width) // 2)
    y = top + max(0, (available_height - height) // 2)
    return width, height, x, y


class FlightInspectionToolsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"飞检工具包 V{BUNDLE_VERSION}")
        self._configure_window()
        self._loaded: dict[str, ttk.Frame] = {}
        self._placeholders: dict[str, ttk.Frame] = {}
        self._spec_by_id = {item.component_id: item for item in COMPONENTS}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_window(self) -> None:
        width, height, x, y = calculate_window_geometry(get_work_area(self))
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(min(720, width), min(500, height))
        self.resizable(True, True)

    def _build(self) -> None:
        header = ttk.Frame(self, padding=(12, 8, 12, 6))
        header.pack(fill="x")
        ttk.Label(header, text="飞检工具包", font=("Microsoft YaHei UI", 17, "bold")).pack(side="left")
        ttk.Label(header, text=f"V{BUNDLE_VERSION}  单窗口标签页  独立业务进程", foreground="#555555").pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        for spec in COMPONENTS:
            placeholder = ttk.Frame(self.notebook)
            placeholder.component_id = spec.component_id
            ttk.Label(placeholder, text=f"选择标签页后加载“{spec.label}”……", padding=24).pack(anchor="center")
            self.notebook.add(placeholder, text=spec.label)
            self._placeholders[str(placeholder)] = placeholder
        self.status_var = tk.StringVar(value="各工具业务代码相互独立；写文件任务在独立进程中执行。")
        ttk.Label(self, textvariable=self.status_var, padding=(12, 3, 12, 6), foreground="#555555").pack(fill="x")
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
    FlightInspectionToolsApp().mainloop()
