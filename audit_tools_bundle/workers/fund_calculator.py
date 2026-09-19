from decimal import Decimal
from pathlib import Path

from components.fund_calculator.fund_calculator import RunOptions, run_file


def run_fund_calculation(messages, cancel_event, payload: dict) -> None:
    options_data = payload["options"]
    options = RunOptions(
        options_data["rule_type"],
        options_data["visit_type"],
        options_data["pooling_area"],
        options_data["institution_level"],
        Decimal(options_data["deduction_price"]) if options_data["deduction_price"] is not None else None,
        Decimal(options_data["deduction_quantity"]) if options_data["deduction_quantity"] is not None else None,
        bool(options_data["overwrite_result"]),
        options_data["source_sheet"],
        options_data.get("simultaneous_scope", "同日同时同分"),
    )
    succeeded = 0
    failures: list[str] = []
    for value in payload["files"]:
        if cancel_event.is_set():
            messages.put({"type": "cancelled", "completed": succeeded, "failures": failures})
            return
        path = Path(value)
        try:
            result = run_file(path, options)
            succeeded += 1
            backup = result.backup_path.name if result.backup_path else "未创建"
            messages.put({
                "type": "file_result",
                "message": (
                    f"完成：{path.name} → {result.sheet_name}；成功 {result.successful}，"
                    f"排除 {result.excluded}，异常 {result.errors}，基金金额 "
                    f"{result.total_fund:,.2f}；备份 {backup}"
                ),
            })
        except Exception as exc:
            failure = f"{path.name}：{exc}"
            failures.append(failure)
            messages.put({"type": "file_error", "message": failure})
    messages.put({"type": "result", "succeeded": succeeded, "failures": failures})
