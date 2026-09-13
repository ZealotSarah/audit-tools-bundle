import sys
import tempfile
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from audit_tools_bundle.task_runner import ProcessTaskRunner
from audit_tools_bundle.workers.file_renamer import run_rename_plan


class Scheduler:
    def __init__(self) -> None:
        self.callbacks = []

    def after(self, _delay_ms, callback) -> None:
        self.callbacks.append(callback)

    def run_one(self) -> None:
        callback = self.callbacks.pop(0)
        callback()


def main() -> None:
    scheduler = Scheduler()
    runner = ProcessTaskRunner(scheduler, poll_interval_ms=10)
    received = []
    completed = []
    with tempfile.TemporaryDirectory(prefix="audit-worker-smoke-") as directory:
        source = Path(directory) / "old.txt"
        target = Path(directory) / "new.txt"
        source.write_text("audit", encoding="utf-8")
        runner.start(
            run_rename_plan,
            {"operations": [(str(source), str(target))], "check_open": False},
            received.append,
            completed.append,
        )
        deadline = time.monotonic() + 15
        while not completed and time.monotonic() < deadline:
            if scheduler.callbacks:
                scheduler.run_one()
            else:
                time.sleep(0.01)
        if completed != [0] or not target.exists():
            raise RuntimeError(f"Worker smoke failed: exit={completed}, messages={received}")
    print("Worker smoke passed")


if __name__ == "__main__":
    main()
