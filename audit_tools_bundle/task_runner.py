from __future__ import annotations

import multiprocessing as mp
import queue
from collections.abc import Callable
from typing import Any


Message = dict[str, Any]
Worker = Callable[[Any, Any, dict[str, Any]], None]


def _child_entry(worker: Worker, messages, cancel_event, payload: dict[str, Any]) -> None:
    try:
        worker(messages, cancel_event, payload)
    except BaseException as exc:
        messages.put({"type": "error", "message": str(exc)})


class ProcessTaskRunner:
    """Run one component task in a spawned process and poll it from Tk."""

    def __init__(self, widget, poll_interval_ms: int = 100) -> None:
        self.widget = widget
        self.poll_interval_ms = poll_interval_ms
        self.process = None
        self.messages = None
        self.cancel_event = None
        self._on_message: Callable[[Message], None] | None = None
        self._on_complete: Callable[[int], None] | None = None

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.is_alive()

    def start(
        self,
        worker: Worker,
        payload: dict[str, Any],
        on_message: Callable[[Message], None],
        on_complete: Callable[[int], None],
    ) -> None:
        if self.process is not None:
            raise RuntimeError("该工具已有任务正在运行")
        context = mp.get_context("spawn")
        self.messages = context.Queue()
        self.cancel_event = context.Event()
        self._on_message = on_message
        self._on_complete = on_complete
        self.process = context.Process(
            target=_child_entry,
            args=(worker, self.messages, self.cancel_event, payload),
            daemon=False,
        )
        self.process.start()
        self.widget.after(self.poll_interval_ms, self._poll)

    def request_cancel(self) -> None:
        if self.cancel_event is not None:
            self.cancel_event.set()

    def _poll(self) -> None:
        if self.process is None or self.messages is None:
            return
        self._drain_messages()
        if self.process.is_alive():
            self.widget.after(self.poll_interval_ms, self._poll)
            return
        self.process.join(timeout=1)
        self._drain_messages(wait_for_feeder=True)
        exit_code = self.process.exitcode or 0
        self.process.close()
        self.process = None
        self.messages.close()
        self.messages = None
        self.cancel_event = None
        callback, self._on_complete = self._on_complete, None
        self._on_message = None
        if callback is not None:
            callback(exit_code)

    def _drain_messages(self, wait_for_feeder: bool = False) -> None:
        if self.messages is None:
            return
        while True:
            try:
                message = self.messages.get(timeout=0.05) if wait_for_feeder else self.messages.get_nowait()
            except queue.Empty:
                break
            if self._on_message is not None:
                self._on_message(message)

