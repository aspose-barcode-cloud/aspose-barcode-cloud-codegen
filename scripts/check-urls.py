import fileinput
import os
import re
import subprocess
import sys
import threading
import time
from queue import SimpleQueue
from typing import Optional

from github_job_summary import JobSummary

"""
Read file names from stdin
Extract all URL-like strings
Check them with CURL
"""


class Curl:
    """
    See: https://curl.se/libcurl/c/libcurl-errors.html
    """

    CURL_STDERR_HTTP_RE = re.compile(r"^curl: \(22\) The requested URL returned error: (?P<http_code>\d+)")
    OK = 0
    COULDNT_RESOLVE_HOST = 6
    HTTP_RETURNED_ERROR = 22


CURL_EXIT_CODES_AND_HTTP_CODES = {
    "http://schemas.android.com/aapt": (Curl.COULDNT_RESOLVE_HOST, None),
    "http://schemas.android.com/apk/res-auto": (Curl.COULDNT_RESOLVE_HOST, None),
    "http://schemas.android.com/apk/res/android": (Curl.COULDNT_RESOLVE_HOST, None),
    "http://schemas.android.com/tools": (Curl.COULDNT_RESOLVE_HOST, None),
    "https://api.aspose.cloud/connect/token": (Curl.HTTP_RETURNED_ERROR, 400),
    "https://api.aspose.cloud/v3.0": (Curl.HTTP_RETURNED_ERROR, 403),
    "https://mvnrepository.com/artifact/io.swagger/swagger-codegen-cli": (
        Curl.HTTP_RETURNED_ERROR,
        403,
    ),
    "https://barcode.qa.aspose.cloud/v3.0/barcode/swagger/spec": (
        Curl.COULDNT_RESOLVE_HOST,
        None,
    ),
    "https://storage.googleapis.com/download.dartlang.org/linux/debian": (
        Curl.HTTP_RETURNED_ERROR,
        404,
    ),
    # TODO: Temporary fix
    "https://dashboard.aspose.cloud/applications": (Curl.HTTP_RETURNED_ERROR, 404),
}

URLS_TO_IGNORE = frozenset(
    [
        "http://|https://|ftp://",
        "http://localhost:$port/",
        "http://localhost:47972",
        "http://localhost:47972/connect/token",
        "http://localhost:47972/v3.0",
        "http://localhost:47972/v3.0/barcode/swagger/spec",
        "http://some",
        "http://tools.ietf.org/html/rfc1341.html",
        "http://tools.ietf.org/html/rfc2046",
        "http://tools.ietf.org/html/rfc2388",
        "http://urllib3.readthedocs.io/en/latest/advanced-usage.html",
        "https://api.aspose.cloud/v3.0/barcode/scan",
        "https://github.com/aspose-barcode-cloud/aspose-barcode-cloud-dotnet/releases/tag/v{{packageVersion}}",
        "https://img.shields.io/badge/api-v{{appVersion}}-lightgrey",
        "https://pypi.org/project/{{projectName}}/",
        "https://repo1.maven.org/maven2/io/swagger/swagger-codegen-cli/2.4.14/swagger-codegen-cli-2.4.14.jar",
        "https://tools.ietf.org/html/rfc1521",
        "https://unknown",
        "https://www.aspose.cloud/404",
    ]
)

URL_END_CHARS = r",#\)\"'<>\*\s\\"
URL_RE_PATTERN = r"(https*://[^%s]+)[%s]?" % (URL_END_CHARS, URL_END_CHARS)
# print(URL_RE_PATTERN)
URL_REGEX = re.compile(URL_RE_PATTERN, re.MULTILINE)

# URL : [Files]
EXTRACTED_URLS_WITH_FILES: dict[str, [str]] = {k: [] for k in URLS_TO_IGNORE}


def url_extractor(text, filename):
    for url in URL_REGEX.findall(text):
        if url not in EXTRACTED_URLS_WITH_FILES:
            EXTRACTED_URLS_WITH_FILES[url] = [filename]
            yield url
        else:
            EXTRACTED_URLS_WITH_FILES[url].append(filename)


FILES_TO_IGNORE = frozenset(
    [
        ".jar",
        ".png",
    ]
)


def text_extractor(files):
    for filename in files:
        if os.path.splitext(filename)[1] in FILES_TO_IGNORE:
            continue

        with open(filename, "r", encoding="utf-8") as f:
            try:
                yield filename, f.read()
            except UnicodeDecodeError:
                print("Cant read '%s'" % filename, file=sys.stderr)
                raise


class Task:
    # To avoid 403 responses
    USER_AGENT = "Googlebot/2.1 (+http://www.google.com/bot.html)"

    def __init__(self, url):
        self.url = url
        self._proc = subprocess.Popen(
            [
                "curl",
                "-sSf",
                "--output",
                "-",
                "--user-agent",
                self.USER_AGENT,
                self.url,
            ],
            stdout=open(os.devnull, "w"),
            stderr=subprocess.PIPE,
        )
        self._stderr = None
        self._started = time.time()

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
            self._stderr = self._proc.stderr.read().decode()
        return self._stderr

    @property
    def age(self) -> float:
        return time.time() - self._started


def create_new_task(url) -> Task:
    # print("Create task:", url)
    return Task(url)


def process_finished_task(task) -> None:
    # print("Finish task:", task.url)
    expected_ret_code, expected_http_code = CURL_EXIT_CODES_AND_HTTP_CODES.get(task.url, (0, None))
    if task.ret_code == expected_ret_code:
        print("OK:", "'%s' %.2fs" % (task.url, task.age))
        JOB_SUMMARY.add_success(task.url)
        return

    if task.ret_code == Curl.HTTP_RETURNED_ERROR and expected_http_code:
        # Try parse stderr for HTTP code
        match = Curl.CURL_STDERR_HTTP_RE.match(task.stderr)
        assert match, "Unexpected output: %s" % task.stderr
        http_code = int(match.groupdict()["http_code"])
        if http_code == expected_http_code:
            print("OK HTTP:", "'%s' %.2fs" % (task.url, task.age))
            JOB_SUMMARY.add_success(task.url)
            return

    print(
        "Expected %d got %d for '%s': %s" % (expected_ret_code, task.ret_code, task.url, task.stderr),
        file=sys.stderr,
    )
    JOB_SUMMARY.add_error(f"Broken URL '{task.url}': {task.stderr}Files: {EXTRACTED_URLS_WITH_FILES[task.url]}")


WORKER_QUEUE = SimpleQueue()


def url_checker(num_workers=8):
    next_report_age_sec = 5
    workers: list[Optional[Task]] = [None for _ in range(num_workers)]

    queue_is_empty = False

    while not queue_is_empty or any(workers):
        for i, task in enumerate(workers):
            if task is None:
                continue
            if not task.running:
                process_finished_task(task)
                workers[i] = None
            elif task.age > next_report_age_sec:
                print("Long request: '%s' %.2fs" % (task.url, task.age))
                next_report_age_sec += 3

        if not queue_is_empty:
            for i in (i for (i, w) in enumerate(workers) if w is None):
                item = WORKER_QUEUE.get()
                if item is None:
                    queue_is_empty = True
                    print("URL queue is over")
                    break
                url = item
                workers[i] = create_new_task(url)
        time.sleep(0.2)
    print("Worker finished")


JOB_SUMMARY = JobSummary(os.environ.get("GITHUB_STEP_SUMMARY", "step_summary.md"))
JOB_SUMMARY.add_header("Test all URLs")


def main(files: [str]) -> int:
    checker = threading.Thread(target=url_checker)
    checker.start()

    for filename, text in text_extractor(files):
        for url in url_extractor(text, filename):
            # print("In:", url)
            WORKER_QUEUE.put_nowait(url)
    WORKER_QUEUE.put_nowait(None)
    checker.join()

    JOB_SUMMARY.finalize("Checked {total} failed **{failed}**\nGood={success}")
    if JOB_SUMMARY.has_errors:
        print(JOB_SUMMARY, file=sys.stderr, flush=True)
        return 1
    else:
        print(JOB_SUMMARY, file=sys.stdout, flush=True)
        return 0


if __name__ == "__main__":
    exit(main([filename.strip() for filename in fileinput.input()]))
