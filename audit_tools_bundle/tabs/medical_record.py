from __future__ import annotations

import json
import os
import random
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from components.medical_record.extractor import APP_VERSION, EXTRACTION_MODES, MODE_DEPARTMENT_TOP10, MODE_RANDOM

from ..task_runner import ProcessTaskRunner
from ..ui import ScrollablePage
from ..workers.medical_record import run_medical_extraction


SETTINGS_PATH = Path(os.getenv("APPDATA", Path.home())) / "病历自动抽取工具" / "settings.json"


def load_settings(path: Path = SETTINGS_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if date.fromisoformat(data["start_date"]) > date.fromisoformat(data["end_date"]):
            raise ValueError
        extraction_mode = data.get("extraction_mode", MODE_RANDOM)
        if extraction_mode not in EXTRACTION_MODES:
            raise ValueError
        data["extraction_mode"] = extraction_mode
        return data
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return {}


def save_settings(start: date, end: date, input_dir: str, output_dir: str, extraction_mode: str = MODE_RANDOM, path: Path = SETTINGS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "input_dir": input_dir,
        "output_dir": output_dir,
        "extraction_mode": extraction_mode,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


class MedicalRecordTab(ttk.Frame):
    display_name = "病历自动抽取"

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.scroller = ScrollablePage(self)
        self.scroller.pack(fill="both", expand=True)
        self.content = self.scroller.body
        self.files: list[str] = []
        self.runner = ProcessTaskRunner(self)
        today = date.today()
        settings = load_settings()
        self.input_dir = settings.get("input_dir") or str(Path.cwd())
        self.start_var = tk.StringVar(value=settings.get("start_date", f"{today.year}-01-01"))
        self.end_var = tk.StringVar(value=settings.get("end_date", today.isoformat()))
        self.count_var = tk.IntVar(value=5)
        self.seed_var = tk.StringVar(value=str(random.SystemRandom().randint(100000, 999999999)))
        self.mode_var = tk.StringVar(value=settings.get("extraction_mode", MODE_RANDOM))
        self.output_var = tk.StringVar(value=settings.get("output_dir") or str(Path.cwd() / "输出结果"))
        self.status_var = tk.StringVar(value="请选择 Excel 文件。")
        self._last_result = None
        self._build()

    @property
    def running(self) -> bool:
        return self.runner.running

    def _build(self) -> None:
        content = self.content
        content.configure(padding=12)
        ttk.Label(content, text=f"病历自动抽取工具 V{APP_VERSION}", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(content, text="只读源 Excel；结果写入新文件；编号与证件字段不输出。", foreground="#555555").pack(anchor="w", pady=(2, 8))
        buttons = ttk.Frame(content)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="添加 Excel", command=self.add_files).pack(side="left")
        ttk.Button(buttons, text="添加文件夹", command=self.add_folder).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="移除选中", command=self.remove_selected).pack(side="left", padx=8)
        ttk.Button(buttons, text="清空", command=self.clear_files).pack(side="left")
        self.listbox = tk.Listbox(content, height=6, selectmode="extended")
        self.listbox.pack(fill="both", expand=True, pady=6)

        options = ttk.LabelFrame(content, text="抽取参数", padding=8)
        options.pack(fill="x", pady=6)
        ttk.Label(options, text="抽取方式").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        mode_box = ttk.Combobox(options, textvariable=self.mode_var, values=EXTRACTION_MODES, state="readonly")
        mode_box.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        mode_box.bind("<<ComboboxSelected>>", self._mode_changed)
        labels = (("检查开始日", self.start_var), ("检查结束日", self.end_var), ("每文件条数", self.count_var), ("随机种子", self.seed_var))
        for index, (label, variable) in enumerate(labels):
            ttk.Label(options, text=label).grid(row=index // 2 + 1, column=(index % 2) * 2, sticky="e", padx=5, pady=5)
            entry = ttk.Entry(options, textvariable=variable, width=22)
            entry.grid(row=index // 2 + 1, column=(index % 2) * 2 + 1, sticky="ew", padx=5, pady=5)
            if variable is self.count_var:
                self.count_entry = entry
            elif variable is self.seed_var:
                self.seed_entry = entry
        options.columnconfigure(1, weight=1)
        options.columnconfigure(3, weight=1)

        out = ttk.Frame(content)
        out.pack(fill="x", pady=4)
        ttk.Label(out, text="输出目录").pack(side="left")
        ttk.Entry(out, textvariable=self.output_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(out, text="选择", command=self.choose_output).pack(side="left")
        self.run_button = ttk.Button(content, text="开始抽取", command=self.start_run)
        self.run_button.pack(anchor="e", pady=6)
        ttk.Label(content, textvariable=self.status_var, foreground="#1F4E78").pack(anchor="w")
        self._mode_changed()

    def _mode_changed(self, _event=None) -> None:
        state = "disabled" if self.mode_var.get() == MODE_DEPARTMENT_TOP10 else "normal"
        self.count_entry.configure(state=state)
        self.seed_entry.configure(state=state)

    def add_files(self) -> None:
        chosen = filedialog.askopenfilenames(parent=self, initialdir=self.input_dir, filetypes=[("Excel 文件", "*.xlsx")])
        if chosen:
            self.input_dir = str(Path(chosen[0]).resolve().parent)
        self._add_paths(chosen)

    def add_folder(self) -> None:
        chosen = filedialog.askdirectory(parent=self, initialdir=self.input_dir)
        if chosen:
            self.input_dir = str(Path(chosen).resolve())
            self._add_paths(sorted(Path(chosen).iterdir()))

    def _add_paths(self, paths) -> None:
        existing = {str(Path(item).resolve()).casefold() for item in self.files}
        for value in paths:
            path = Path(value).resolve()
            key = str(path).casefold()
            if path.suffix.casefold() == ".xlsx" and key not in existing:
                self.files.append(str(path))
                self.listbox.insert("end", str(path))
                existing.add(key)

    def remove_selected(self) -> None:
        for index in reversed(self.listbox.curselection()):
            self.listbox.delete(index)
            del self.files[index]

    def clear_files(self) -> None:
        self.files.clear()
        self.listbox.delete(0, "end")

    def choose_output(self) -> None:
        chosen = filedialog.askdirectory(parent=self, initialdir=self.output_var.get().strip() or str(Path.cwd()))
        if chosen:
            self.output_var.set(chosen)

    def start_run(self) -> None:
        try:
            if not self.files:
                raise ValueError("请至少选择一个 Excel 文件")
            start = date.fromisoformat(self.start_var.get().strip())
            end = date.fromisoformat(self.end_var.get().strip())
            extraction_mode = self.mode_var.get()
            if extraction_mode not in EXTRACTION_MODES:
                raise ValueError("请选择有效的抽取方式")
            count = int(self.count_var.get()) if extraction_mode == MODE_RANDOM else 0
            seed = int(self.seed_var.get().strip()) if extraction_mode == MODE_RANDOM else 0
            output_dir = self.output_var.get().strip()
            if start > end:
                raise ValueError("检查开始日期不能晚于结束日期")
            if extraction_mode == MODE_RANDOM and count < 1:
                raise ValueError("每文件抽取条数必须大于 0")
            if not output_dir:
                raise ValueError("请选择输出目录")
            save_settings(start, end, self.input_dir, output_dir, extraction_mode)
        except Exception as exc:
            messagebox.showerror("参数错误", str(exc), parent=self)
            return
        self.run_button.configure(state="disabled")
        self.status_var.set("正在独立进程中抽取，请稍候……")
        self._last_result = None
        self.runner.start(run_medical_extraction, {
            "files": list(self.files), "start": start.isoformat(), "end": end.isoformat(),
            "count": count, "seed": seed, "output_dir": output_dir, "extraction_mode": extraction_mode,
        }, self._on_message, self._on_complete)

    def _on_message(self, message: dict) -> None:
        if message["type"] == "progress":
            self.status_var.set(message["message"])
        elif message["type"] == "result":
            self._last_result = message
        elif message["type"] == "error":
            self._last_result = message

    def _on_complete(self, exit_code: int) -> None:
        self.run_button.configure(state="normal")
        result = self._last_result or {"type": "error", "message": f"工作进程异常退出，退出码 {exit_code}"}
        if result["type"] == "error":
            self.status_var.set("抽取失败。")
            messagebox.showerror("抽取失败", result["message"], parent=self)
            return
        errors = result.get("errors", [])
        output = result["output"]
        self.status_var.set(f"完成：{output}" if not errors else f"完成，但有 {len(errors)} 个文件失败：{output}")
        title = "抽取完成" if not errors else "抽取完成（有异常）"
        detail = f"结果已保存到：\n{output}"
        if errors:
            detail += f"\n\n有 {len(errors)} 个文件失败，请查看异常明细。"
        messagebox.showinfo(title, detail, parent=self)
