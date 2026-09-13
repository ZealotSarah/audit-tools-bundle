from datetime import date

from components.medical_record.extractor import extract_files


def run_medical_extraction(messages, cancel_event, payload: dict) -> None:
    if cancel_event.is_set():
        messages.put({"type": "cancelled"})
        return
    messages.put({"type": "progress", "message": "正在读取并抽取病历……"})
    output, errors = extract_files(
        payload["files"],
        date.fromisoformat(payload["start"]),
        date.fromisoformat(payload["end"]),
        int(payload["count"]),
        int(payload["seed"]),
        payload["output_dir"],
        return_errors=True,
    )
    messages.put({"type": "result", "output": str(output), "errors": errors})

