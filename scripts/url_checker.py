import contextlib
import time
from queue import Queue, Empty
from typing import Callable, Optional

from curl_wrapper import CurlWrapper


class UrlChecker:
    def __init__(
        self,
        *,
        num_workers: int = 8,
        hard_kill_sec: int = 15,
        on_finish: Optional[Callable[[CurlWrapper], None]] = None,
        worker_factory: Optional[Callable[[str], CurlWrapper]] = None,
    ) -> None:
        self.num_workers = num_workers
        self.hard_kill_sec = hard_kill_sec
        self.on_finish = on_finish
        self.worker_factory = worker_factory or (lambda url: CurlWrapper(url))

        self.queue: Queue[str | None] = Queue()
        self.workers: list[CurlWrapper | None] = [None for _ in range(self.num_workers)]
        self.stop_event = False
        self.next_report_age_sec = 5

    def add_url(self, url: str) -> None:
        self.queue.put_nowait(url)

    def close(self) -> None:
        self.queue.put_nowait(None)

    def stop(self) -> None:
        self.stop_event = True
        with contextlib.suppress(Exception):
            self.queue.put_nowait(None)

    def run(self) -> None:
        queue_is_empty = False
        while not queue_is_empty or any(self.workers):
            # Graceful stop: cancel running curls
            if self.stop_event:
                queue_is_empty = True
                for t in self.workers:
                    if t is not None and t.running:
                        t.terminate(timeout=1)
                        if t.running:
                            t.kill()

            # Tick workers
            for i, task in enumerate(self.workers):
                if task is None:
                    continue
                if not task.running:
                    if self.on_finish is not None:
                        self.on_finish(task)
                    self.workers[i] = None
                elif task.age > self.next_report_age_sec:
                    print("Long request: '%s' %.2fs" % (task.url, task.age))
                    self.next_report_age_sec += 3
                    if task.age > self.hard_kill_sec:
                        task.terminate(timeout=2)
                        if task.running:
                            task.kill()
                        print("Killed long request: '%s' %.2fs" % (task.url, task.age))

            # Fill idle workers
            if not queue_is_empty:
                for i in (i for (i, w) in enumerate(self.workers) if w is None):
                    try:
                        item = self.queue.get_nowait()
                    except Empty:
                        break
                    if item is None:
                        queue_is_empty = True
                        print("--- url queue is over ---")
                        break
                    url = item
                    self.workers[i] = self.worker_factory(url)
            time.sleep(0.2)
        print("Worker finished")
