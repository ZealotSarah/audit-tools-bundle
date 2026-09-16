from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from components.file_renamer import APP_VERSION
from components.file_renamer.legacy_app import FileRenameApp

from ..task_runner import ProcessTaskRunner
from ..ui import ScrollablePage
from ..workers.file_renamer import run_rename_plan


class EmbeddedHost(ttk.Frame):
    """Provide the small toplevel API expected by the legacy Tkinter UI."""

    def title(self, _value: str) -> None:
        pass

    def geometry(self, _value: str) -> None:
        pass

    def bind(self, sequence=None, func=None, add=None):
        if sequence == "<F5>":
            return self.bind_all(sequence, func, add)
        return super().bind(sequence, func, add)


class IntegratedFileRenameApp(FileRenameApp):
    def __init__(self, root: EmbeddedHost) -> None:
        self.runner = ProcessTaskRunner(root)
        self._last_result = None
        super().__init__(root)

    @property
    def running(self) -> bool:
        return self.runner.running

    def execute_rename(self):
        if self.running:
            messagebox.showwarning("正在处理", "已有重命名任务正在执行。", parent=self.root)
            return
        if not self.preview_results:
            messagebox.showinfo("提示", "没有可执行的重命名操作", parent=self.root)
            return

        check_open = bool(self.open_files_check_var.get())
        if self.current_mode == "batch":
            folder = Path(self.path_entry.get())
            if not folder.is_dir():
                messagebox.showerror("错误", "请选择有效的文件夹路径", parent=self.root)
                return
            if not self.validate_rename_plan(str(folder), self.preview_results):
                return
            operations = [(str(folder / old), str(folder / new)) for old, new in self.preview_results]
        else:
            old_path = Path(self.path_entry.get())
            if check_open and self.is_file_open(str(old_path)):
                if not messagebox.askyesno("文件正在使用", "该文件正在被其他程序使用，是否仍尝试重命名？", parent=self.root):
                    return
            old_name, new_name = self.preview_results[0]
            if not self.validate_rename_plan(str(old_path.parent), [(old_name, new_name)]):
                return
            operations = [(str(old_path), str(old_path.with_name(new_name)))]
        self._start_plan(operations, check_open)

    def remove_format(self):
        if self.running:
            messagebox.showwarning("正在处理", "已有重命名任务正在执行。", parent=self.root)
            return
        operations: list[tuple[str, str]] = []
        if self.current_mode == "batch":
            folder = Path(self.path_entry.get())
            if not folder.is_dir():
                messagebox.showerror("错误", "请选择有效的文件夹路径", parent=self.root)
                return
            plan = []
            for name in os.listdir(folder):
                if self.is_sequence_filename_format(name):
                    base, extension = os.path.splitext(name)
                    parts = base.split("_")
                    if len(parts) >= 3:
                        new_name = "_".join(parts[1:-1]) + extension
                        plan.append((name, new_name))
            if not plan:
                messagebox.showinfo("提示", "没有符合序号_原文件名_日期格式的文件。", parent=self.root)
                return
            if not self.validate_rename_plan(str(folder), plan):
                return
            operations = [(str(folder / old), str(folder / new)) for old, new in plan]
        else:
            old_path = Path(self.path_entry.get())
            if not old_path.exists():
                messagebox.showerror("错误", "文件不存在", parent=self.root)
                return
            if not self.is_sequence_filename_format(old_path.name):
                messagebox.showinfo("提示", "文件不符合序号_原文件名_日期格式，无需取消格式", parent=self.root)
                return
            parts = old_path.stem.split("_")
            new_path = old_path.with_name("_".join(parts[1:-1]) + old_path.suffix)
            if not self.validate_rename_plan(str(old_path.parent), [(old_path.name, new_path.name)]):
                return
            operations = [(str(old_path), str(new_path))]
        self._start_plan(operations, bool(self.open_files_check_var.get()))

    def _start_plan(self, operations: list[tuple[str, str]], check_open: bool) -> None:
        self.execute_btn.configure(state=tk.DISABLED)
        self.remove_format_btn.configure(state=tk.DISABLED)
        self.status_var.set("正在独立进程中执行重命名……")
        self._last_result = None
        self.runner.start(run_rename_plan, {"operations": operations, "check_open": check_open}, self._on_message, self._on_complete)

    def _on_message(self, message: dict) -> None:
        if message["type"] in {"result", "error", "cancelled"}:
            self._last_result = message
        elif message["type"] == "file_result":
            self.status_var.set(f"已重命名：{message['message']}")
        elif message["type"] == "file_skipped":
            self.status_var.set(f"已跳过占用文件：{message['message']}")

    def _on_complete(self, exit_code: int) -> None:
        result = self._last_result or {"type": "error", "message": f"工作进程异常退出，退出码 {exit_code}"}
        if result["type"] == "error":
            self.status_var.set("重命名失败")
            messagebox.showerror("重命名失败", result["message"], parent=self.root)
            return
        if result["type"] == "cancelled":
            self.status_var.set("重命名已在文件之间停止")
        renamed = result.get("renamed", 0)
        skipped = result.get("skipped", [])
        failures = result.get("failures", [])
        lines = [f"成功：{renamed} 个", f"跳过：{len(skipped)} 个", f"失败：{len(failures)} 个"]
        if skipped:
            lines.append("\n跳过的文件：\n" + "\n".join(skipped))
        if failures:
            lines.append("\n失败的文件：\n" + "\n".join(failures))
        if failures:
            messagebox.showerror("重命名完成", "\n".join(lines), parent=self.root)
        else:
            messagebox.showinfo("重命名完成", "\n".join(lines), parent=self.root)
        self.status_var.set(f"重命名完成：成功 {renamed}，跳过 {len(skipped)}，失败 {len(failures)}")
        if self.current_mode == "batch" and Path(self.path_entry.get()).is_dir():
            self.show_batch_files(self.path_entry.get())
        elif renamed:
            self.path_entry.delete(0, tk.END)
            self.original_files_listbox.delete(0, tk.END)
            self.preview_listbox.delete(0, tk.END)
        self.preview_results = []
        self.execute_btn.configure(state=tk.DISABLED)
        self.remove_format_btn.configure(state=tk.DISABLED)


class FileRenamerTab(ttk.Frame):
    display_name = "文件批量编码"

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.scroller = ScrollablePage(self, horizontal=True)
        self.scroller.pack(fill="both", expand=True)
        content = self.scroller.body
        header = ttk.Frame(content, padding=(12, 8, 12, 3))
        header.pack(fill="x")
        ttk.Label(header, text=f"文件批量编码工具 V{APP_VERSION}", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(header, text="原地修改文件名；执行前必须检查预览。实际改名在独立进程中进行。", foreground="#9C2F2F").pack(anchor="w", pady=(2, 0))
        self.host = EmbeddedHost(content)
        self.host.pack(fill="both", expand=True)
        self.tool = IntegratedFileRenameApp(self.host)
        self.tool.path_entry.configure(width=36)

    @property
    def running(self) -> bool:
        return self.tool.running
