from pathlib import Path

from audit_tools_bundle.workers.file_renamer import run_rename_plan


class Messages:
    def __init__(self):
        self.items = []

    def put(self, value):
        self.items.append(value)


class NotCancelled:
    def is_set(self):
        return False


def test_rename_worker_executes_plan(tmp_path: Path):
    source = tmp_path / "old.txt"
    target = tmp_path / "new.txt"
    source.write_text("audit", encoding="utf-8")
    messages = Messages()

    run_rename_plan(messages, NotCancelled(), {
        "operations": [(str(source), str(target))],
        "check_open": False,
    })

    assert not source.exists()
    assert target.read_text(encoding="utf-8") == "audit"
    assert messages.items[-1] == {"type": "result", "renamed": 1, "skipped": [], "failures": []}


def test_rename_worker_does_not_create_missing_source(tmp_path: Path):
    source = tmp_path / "missing.txt"
    target = tmp_path / "new.txt"
    messages = Messages()

    run_rename_plan(messages, NotCancelled(), {
        "operations": [(str(source), str(target))],
        "check_open": True,
    })

    assert not source.exists()
    assert not target.exists()
    assert messages.items[-1]["renamed"] == 0
    assert messages.items[-1]["failures"]
