import os
from pathlib import Path


def _is_file_open(path: Path) -> bool:
    try:
        with path.open("a"):
            return False
    except OSError:
        return True


def run_rename_plan(messages, cancel_event, payload: dict) -> None:
    renamed = 0
    skipped: list[str] = []
    failures: list[str] = []
    for old_value, new_value in payload["operations"]:
        if cancel_event.is_set():
            messages.put({"type": "cancelled", "renamed": renamed, "skipped": skipped, "failures": failures})
            return
        old_path = Path(old_value)
        new_path = Path(new_value)
        if old_path == new_path:
            continue
        if not old_path.exists():
            failure = f"{old_path.name}：源文件不存在"
            failures.append(failure)
            messages.put({"type": "file_error", "message": failure})
            continue
        if payload.get("check_open", True) and _is_file_open(old_path):
            skipped.append(old_path.name)
            messages.put({"type": "file_skipped", "message": old_path.name})
            continue
        try:
            os.rename(old_path, new_path)
            renamed += 1
            messages.put({"type": "file_result", "message": f"{old_path.name} → {new_path.name}"})
        except Exception as exc:
            failure = f"{old_path.name}：{exc}"
            failures.append(failure)
            messages.put({"type": "file_error", "message": failure})
    messages.put({"type": "result", "renamed": renamed, "skipped": skipped, "failures": failures})

