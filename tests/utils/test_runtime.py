from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any


class AsyncRuntimeForTests:
    """Async runtime for tests: one persistent event loop in a background thread."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            raise RuntimeError("Runtime not started")
        return self._loop

    def start(self) -> None:
        if self._thread is not None:
            return

        def _runner() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._ready.set()
            self._loop.run_forever()
            self._loop.close()

        self._thread = threading.Thread(target=_runner, daemon=True)
        self._thread.start()
        self._ready.wait()

    def submit(self, coro: Coroutine[Any, Any, Any]):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
