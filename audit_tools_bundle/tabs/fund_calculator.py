from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from openpyxl import load_workbook

from components.fund_calculator.fund_calculator import (
    APP_VERSION,
    AUTO_SOURCE_SHEET,
    FUND_RATES,
    OUTPUT_SHEET,
    SIMULTANEOUS_SCOPES,
    CalculationError,
    RunOptions,
    optional_decimal,
    validate_options,
)

from ..task_runner import ProcessTaskRunner
from ..ui import ScrollablePage
from ..workers.fund_calculator import run_fund_calculation


class FundCalculatorTab(ttk.Frame):
    display_name = "基金金额测算"

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.scroller = ScrollablePage(self)
        self.scroller.pack(fill="both", expand=True)
        self.content = self.scroller.body
        self.files: list[Path] = []
        self.runner = ProcessTaskRunner(self)
        self.rule_type = tk.StringVar(value="通用")
        self.visit_type = tk.StringVar(value="自动识别")
        self.pooling_area = tk.StringVar()
        self.institution_level = tk.StringVar()
        self.source_sheet = tk.StringVar(value=AUTO_SOURCE_SHEET)
        self.deduction_price = tk.StringVar()
        self.deduction_quantity = tk.StringVar()
        self.simultaneous_scope = tk.StringVar(value=SIMULTANEOUS_SCOPES[0])
        self.overwrite_result = tk.BooleanVar(value=False)
        self._last_result = None
        self._build()

    @property
    def running(self) -> bool:
        return self.runner.running

    def _build(self) -> None:
        content = self.content
        content.configure(padding=12)
        ttk.Label(content, text=f"基金金额自动测算工具 V{APP_VERSION}", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(content, text="会修改所选工作簿；成功前先校验临时文件，并保留测算前备份。", foreground="#9C2F2F").pack(anchor="w", pady=(2, 8))
        file_bar = ttk.Frame(content)
        file_bar.pack(fill="x")
        self.pick_button = ttk.Button(file_bar, text="选择 Excel 文件", command=self.pick_files)
        self.pick_button.pack(side="left")
        self.clear_button = ttk.Button(file_bar, text="清空", command=self.clear_files)
        self.clear_button.pack(side="left", padx=8)
        self.file_label = ttk.Label(file_bar, text="尚未选择文件")
        self.file_label.pack(side="left", padx=8)

        params = ttk.LabelFrame(content, text="参数", padding=8)
        params.pack(fill="x", pady=8)
        self._add_combo(params, "规则大类", self.rule_type, ["通用", "串换", "固定比例", "两项同时收取"], 0, 0)
        self._add_combo(params, "业务类型", self.visit_type, ["自动识别", "住院", "门诊"], 0, 1)
        self._add_combo(params, "参保地（比例表匹配）", self.pooling_area, list(FUND_RATES), 1, 0)
        self._add_combo(params, "医疗机构级别", self.institution_level, ["三级", "二级", "一级"], 1, 1)
        ttk.Label(params, text="源数据 Sheet").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.source_sheet_combo = ttk.Combobox(params, textvariable=self.source_sheet, values=[AUTO_SOURCE_SHEET], width=26)
        self.source_sheet_combo.grid(row=2, column=1, sticky="ew", pady=(10, 0))
        self._add_combo(params, "同时口径（仅两项同时收取）", self.simultaneous_scope, list(SIMULTANEOUS_SCOPES), 2, 1)
        ttk.Label(params, text="扣减单价（仅串换无违规金额列时）").grid(row=3, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(params, textvariable=self.deduction_price, width=26).grid(row=3, column=1, sticky="ew", pady=(8, 0))
        ttk.Label(params, text="扣减数量（串换必填）").grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(params, textvariable=self.deduction_quantity, width=26).grid(row=4, column=1, sticky="ew", pady=(8, 0))
        ttk.Checkbutton(params, text="覆盖已有“基金测算”Sheet（否则新建带时间的 Sheet）", variable=self.overwrite_result).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))
        params.columnconfigure(1, weight=1)

        controls = ttk.Frame(content)
        controls.pack(fill="x")
        self.run_button = ttk.Button(controls, text="开始测算", command=self.start)
        self.run_button.pack(side="left")
        ttk.Label(controls, text="  请先关闭已在 Excel 中打开的文件。", foreground="#A33").pack(side="left")
        self.log = tk.Text(content, height=8, wrap="word", state="disabled", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, pady=(8, 0))

    def _add_combo(self, parent, label: str, variable: tk.StringVar, values: list[str], row: int, column: int) -> None:
        base = column * 2
        ttk.Label(parent, text=label).grid(row=row, column=base, sticky="w", padx=(0, 10), pady=4)
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=26)
        combo.grid(row=row, column=base + 1, sticky="ew", padx=(0, 20), pady=4)
        parent.columnconfigure(base + 1, weight=1)

    def pick_files(self) -> None:
        selections = filedialog.askopenfilenames(parent=self, title="选择需要测算的 Excel 文件", filetypes=[("Excel 文件", "*.xlsx *.xlsm")])
        self.files = [Path(item) for item in selections]
        self.file_label.configure(text=f"已选择 {len(self.files)} 个文件" if self.files else "尚未选择文件")
        choices = [AUTO_SOURCE_SHEET]
        if self.files:
            first = self.files[0]
            try:
                workbook = load_workbook(first, read_only=True, keep_vba=first.suffix.lower() == ".xlsm")
                try:
                    choices.extend(sheet.title for sheet in workbook.worksheets if not sheet.title.startswith(OUTPUT_SHEET))
                finally:
                    workbook.close()
            except Exception as exc:
                messagebox.showerror("读取失败", f"无法读取第一个文件的 Sheet 列表：{exc}", parent=self)
        self.source_sheet_combo.configure(values=choices)
        self.source_sheet.set(AUTO_SOURCE_SHEET)

    def clear_files(self) -> None:
        self.files.clear()
        self.file_label.configure(text="尚未选择文件")

    def start(self) -> None:
        if not self.files:
            messagebox.showwarning("未选择文件", "请先选择至少一个 Excel 文件。", parent=self)
            return
        try:
            options = RunOptions(
                self.rule_type.get(), self.visit_type.get(), self.pooling_area.get(), self.institution_level.get(),
                optional_decimal(self.deduction_price.get(), "扣减单价"),
                optional_decimal(self.deduction_quantity.get(), "扣减数量"), self.overwrite_result.get(),
                None if self.source_sheet.get() in {"", AUTO_SOURCE_SHEET} else self.source_sheet.get(),
                self.simultaneous_scope.get(),
            )
            validate_options(options)
        except CalculationError as exc:
            messagebox.showerror("参数错误", str(exc), parent=self)
            return
        self.run_button.configure(state="disabled")
        self.pick_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self._last_result = None
        self._write_log("开始在独立进程中处理……\n")
        self.runner.start(run_fund_calculation, {
            "files": [str(item) for item in self.files],
            "options": {
                "rule_type": options.rule_type, "visit_type": options.visit_type,
                "pooling_area": options.pooling_area, "institution_level": options.institution_level,
                "deduction_price": str(options.deduction_price) if options.deduction_price is not None else None,
                "deduction_quantity": str(options.deduction_quantity) if options.deduction_quantity is not None else None,
                "overwrite_result": options.overwrite_result, "source_sheet": options.source_sheet,
                "simultaneous_scope": options.simultaneous_scope,
            },
        }, self._on_message, self._on_complete)

    def _on_message(self, message: dict) -> None:
        kind = message["type"]
        if kind == "file_result":
            self._write_log(message["message"] + "\n")
        elif kind == "file_error":
            self._write_log("失败：" + message["message"] + "\n")
        elif kind in {"result", "error", "cancelled"}:
            self._last_result = message

    def _on_complete(self, exit_code: int) -> None:
        self.run_button.configure(state="normal")
        self.pick_button.configure(state="normal")
        self.clear_button.configure(state="normal")
        result = self._last_result or {"type": "error", "message": f"工作进程异常退出，退出码 {exit_code}"}
        if result["type"] == "error":
            messagebox.showerror("测算失败", result["message"], parent=self)
            return
        if result["type"] == "cancelled":
            messagebox.showwarning("任务已取消", "任务已在文件之间的安全检查点停止。", parent=self)
            return
        failures = result["failures"]
        messagebox.showinfo("完成", f"处理完成：成功 {result['succeeded']} 个文件，失败 {len(failures)} 个文件。", parent=self)

    def _write_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message)
        self.log.see("end")
        self.log.configure(state="disabled")
