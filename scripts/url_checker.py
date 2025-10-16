import contextlib
import sys
import time
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Callable, Optional

from curl_wrapper import CurlWrapper, EXIT_CODES


@dataclass
class CheckResult:
    url: str
    ok: bool
    ret_code: int
    age: float
    stderr: str
    expected_ret_code: int
    expected_http_code: int | None
    http_code: int | None


class UrlChecker:
    def __init__(
        self,
        *,
        num_workers: int = 8,
        hard_kill_sec: int = 15,
        expectations: dict[str, tuple[int, int | None]] | None = None,
        worker_factory: Optional[Callable[[str], CurlWrapper]] = None,
    ) -> None:
        self.num_workers = num_workers
        self.hard_kill_sec = hard_kill_sec
        self.expectations = expectations or {}
        self.worker_factory = worker_factory or (lambda url: CurlWrapper(url))

        self.queue: Queue[str | None] = Queue()
        self.workers: list[CurlWrapper | None] = [None for _ in range(self.num_workers)]
        self.stop_event = False
        self.next_report_age_sec = 5
        self.results: list[CheckResult] = []

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
                    self._process_finished(task)
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

    def _process_finished(self, task: CurlWrapper) -> None:
        expected_ret_code, expected_http_code = self.expectations.get(task.url, (0, None))

        ok: bool = False
        http_code_val: int | None = None
        stderr_out: str = task.stderr

        # Fast path: exact expected ret code or success
        if task.ret_code == 0 or task.ret_code == expected_ret_code:
            print("OK:", "'%s' %.2fs" % (task.url, task.age))
            ok = True
            stderr_out = ""
        else:
            # If curl reports HTTP error (22), attempt to parse HTTP code to compare
            if task.ret_code == EXIT_CODES.HTTP_RETURNED_ERROR and expected_http_code:
                match = CurlWrapper.CURL_STDERR_HTTP_RE.match(task.stderr)
                assert match, "Unexpected output: %s" % task.stderr
                http_code_val = int(match.groupdict()["http_code"])
                if http_code_val == expected_http_code:
                    print("OK HTTP:", "'%s' %.2fs" % (task.url, task.age))
                    ok = True

        if not ok:
            # Otherwise, report error
            print(
                "Expected %d got %d for '%s': %s" % (expected_ret_code, task.ret_code, task.url, task.stderr),
                file=sys.stderr,
            )

        # Append exactly once
        self.results.append(
            CheckResult(
                url=task.url,
                ok=ok,
                ret_code=task.ret_code,
                age=task.age,
                stderr=stderr_out,
                expected_ret_code=expected_ret_code,
                expected_http_code=expected_http_code,
                http_code=http_code_val,
            )
        )
