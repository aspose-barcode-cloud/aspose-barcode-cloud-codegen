import contextlib
import os
import re
import subprocess
import time
from typing import Optional

# To avoid 403 responses (default); caller may override per instance
DEFAULT_USER_AGENT = "Googlebot/2.1 (+http://www.google.com/bot.html)"


class CurlExitCodes:
    """
    See: https://curl.se/libcurl/c/libcurl-errors.html
    """

    OK = 0
    COULDNT_RESOLVE_HOST = 6
    HTTP_RETURNED_ERROR = 22


class CurlWrapper:
    """
    Encapsulates a single curl execution with timeouts and helpers.
    """

    CURL_STDERR_HTTP_RE = re.compile(r"^curl: \(22\) The requested URL returned error: (?P<http_code>\d+)")

    def __init__(
        self,
        url: str,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        connect_timeout: int = 5,
        max_time: int = 10,
        max_redirects: int = 3,
    ) -> None:
        self.url = url
        self._stderr: Optional[str] = None
        self._started = time.time()
        self._proc = subprocess.Popen(
            [
                "curl",
                "-sSf",
                "-L",  # follow redirects
                "--max-redirs",
                f"{max_redirects}",  # limit number of redirects
                # "--proto", "=https",  # (optional) only allow https for the initial URL
                "--proto-redir",
                "=all,https",  # only allow https after redirects; http will fail
                "--output",
                "-",  # discard body
                "--connect-timeout",
                f"{connect_timeout}",
                "--max-time",
                f"{max_time}",
                "--user-agent",
                f"{user_agent}",
                self.url,
            ],
            stdout=open(os.devnull, "w"),
            stderr=subprocess.PIPE,
        )

    @property
    def running(self) -> bool:
        return self._proc.poll() is None

    @property
    def ret_code(self) -> int:
        assert not self.running
        return self._proc.returncode

    @property
    def stderr(self) -> str:
        assert not self.running
        if self._stderr is None:
            assert self._proc.stderr is not None
            self._stderr = self._proc.stderr.read().decode()
        return self._stderr

    @property
    def age(self) -> float:
        return time.time() - self._started

    def terminate(self, timeout: float | None = None) -> None:
        try:
            self._proc.terminate()
            if timeout is not None:
                self._proc.wait(timeout=timeout)
        except Exception:
            pass

    def kill(self) -> None:
        with contextlib.suppress(Exception):
            self._proc.kill()
