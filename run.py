import sys
import tempfile
import time
from multiprocessing import freeze_support
from pathlib import Path

from audit_tools_bundle.app import main
from audit_tools_bundle.task_runner import ProcessTaskRunner
from audit_tools_bundle.workers.file_renamer import run_rename_plan


class _SmokeScheduler:
    def __init__(self) -> None:
        self.callbacks = []

    def after(self, _delay_ms, callback) -> None:
        self.callbacks.append(callback)


def _worker_smoke() -> int:
    scheduler = _SmokeScheduler()
    runner = ProcessTaskRunner(scheduler, poll_interval_ms=10)
    completed = []
    received = []
    with tempfile.TemporaryDirectory(prefix="audit-bundle-worker-") as directory:
        source = Path(directory) / "old.txt"
        target = Path(directory) / "new.txt"
        source.write_text("audit", encoding="utf-8")
        runner.start(run_rename_plan, {"operations": [(str(source), str(target))], "check_open": False}, received.append, completed.append)
        deadline = time.monotonic() + 15
        while not completed and time.monotonic() < deadline:
            if scheduler.callbacks:
                scheduler.callbacks.pop(0)()
            else:
                time.sleep(0.01)
        return 0 if completed == [0] and target.exists() else 1


if __name__ == "__main__":
    freeze_support()
    if "--worker-smoke" in sys.argv:
        raise SystemExit(_worker_smoke())
    main()
