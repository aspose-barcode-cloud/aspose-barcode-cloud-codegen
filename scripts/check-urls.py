import fileinput
import os
import re
import subprocess
import sys
import threading
import time
import typing
import urllib.parse
from queue import SimpleQueue

from github_job_summary import JobSummary
from subdomains import Subdomains

"""
Read file names from stdin (feed from git ls-files)
    see `check_all_urls.sh`
Extract all URL-like strings
Check them with CURL
"""

# To avoid 403 responses
USER_AGENT = "Googlebot/2.1 (+http://www.google.com/bot.html)"


class Curl:
    """
    See: https://curl.se/libcurl/c/libcurl-errors.html
    """

    CURL_STDERR_HTTP_RE = re.compile(r"^curl: \(22\) The requested URL returned error: (?P<http_code>\d+)")
    OK = 0
    COULDNT_RESOLVE_HOST = 6
    HTTP_RETURNED_ERROR = 22


CURL_EXIT_CODES_AND_HTTP_CODES = {
    "https://api.aspose.cloud/connect/token": (Curl.HTTP_RETURNED_ERROR, 400),
    "https://api.aspose.cloud/v3.0": (Curl.HTTP_RETURNED_ERROR, 404),
    "https://api.aspose.cloud/v4.0": (Curl.HTTP_RETURNED_ERROR, 404),
    "https://api.aspose.cloud/v4.0/": (Curl.HTTP_RETURNED_ERROR, 404),
    "https://id.aspose.cloud/connect/token": (Curl.HTTP_RETURNED_ERROR, 400),
    # TODO: Temporary fix
    "https://dashboard.aspose.cloud/applications": (Curl.HTTP_RETURNED_ERROR, 404),
}

REGEX_TO_IGNORE: list[re.Pattern[str]] = [
    re.compile(r"^https://github\.com/(?P<user>[^/]+)/(?P<repo>[^/]+)/(?:blob|issues)/\S+$"),
]

URLS_TO_IGNORE: frozenset[str] = frozenset(
    [
        "https://api.aspose.cloud",
        "https://www.aspose.cloud/404",
        "https://www.aspose.cloud/404/",
    ]
)

IGNORE_DOMAINS = Subdomains(
    [
        ".android.com",
        ".apache.org",
        ".curl.se",
        ".dart.dev",
        ".dartlang.org",
        ".getcomposer.org",
        ".go.dev",
        ".golang.org",
        ".google.com",
        ".gradle.org",
        ".ietf.org",
        ".maven.org",
        ".microsoft.com",
        ".mojohaus.org",
        ".mvnrepository.com",
        ".nodejs.org",
        ".npmjs.com",
        ".nuget.org",
        ".opensource.org",
        ".packagist.org",
        ".php.net",
        ".phpunit.de",
        ".pub.dev",
        ".pypi.org",
        ".python.org",
        ".readthedocs.io",
        ".sonatype.org",
        ".w3.org",
        ".wikipedia.org",

        # Regular domains
        "barcode.qa.aspose.cloud",
        "editorconfig.org",
    ]
)

URL_END_CHARS = r",#\)\"'<>\*\s\\"
URL_RE_PATTERN = r"(https*://[^{0}]+)[{0}]?".format(URL_END_CHARS)
# print(URL_RE_PATTERN)
EXTRACT_URL_REGEX = re.compile(URL_RE_PATTERN, re.MULTILINE)

# URL : [Files]
EXTRACTED_URLS_WITH_FILES: dict[str, list[str]] = {k: [] for k in URLS_TO_IGNORE}


def should_check_url(url: str) -> bool:
    try:
        parsed: urllib.parse.ParseResult = urllib.parse.urlparse(url)
    except:
        # Malformed URL
        return False
    else:
        domain = parsed.netloc
        if "." not in domain:
            # Ignore "localhost" and other domains without .
            return False
        if IGNORE_DOMAINS.exists(domain):
            return False

    if "{{" in url or "}}" in url:
        # Ignore templates with {{var}}
        return False

    for r in REGEX_TO_IGNORE:
        if r.match(url):
            # print("Ignore by regex", r.pattern, ":", url, file=sys.stderr)
            return False

    return True


def url_extractor(text: str, filename: str) -> typing.Generator[str, None, None]:
    for url in EXTRACT_URL_REGEX.findall(text):
        if not should_check_url(url):
            # print("Ignore:", url)
            continue
        if url not in EXTRACTED_URLS_WITH_FILES:
            EXTRACTED_URLS_WITH_FILES[url] = [filename]
            yield url
        else:
            EXTRACTED_URLS_WITH_FILES[url].append(filename)


FILES_TO_IGNORE = frozenset(
    [
        ".jar",
        ".jar",
        ".jpg",
        ".jpeg",
        ".png",
    ]
)


def text_extractor(files: list[str]) -> typing.Generator[tuple[str, str], None, None]:
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
    _proc: subprocess.Popen[bytes]
    _stderr: str | None

    def __init__(self, url: str):
        self.url = url
        self._proc = subprocess.Popen(
            [
                "curl",
                "-sSf",
                "--output",
                "-",
                "--user-agent",
                USER_AGENT,
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


def create_new_task(url: str) -> Task:
    # print("Create task:", url)
    return Task(url)


def process_finished_task(task: Task) -> None:
    # print("Finish task:", task.url)
    expected_ret_code, expected_http_code = CURL_EXIT_CODES_AND_HTTP_CODES.get(task.url, (0, None))
    if task.ret_code == 0 or task.ret_code == expected_ret_code:
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


WORKER_QUEUE: SimpleQueue[str | None] = SimpleQueue()


def url_checker(num_workers: int = 8) -> None:
    next_report_age_sec = 5
    workers: list[Task | None] = [None for _ in range(num_workers)]

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
                    print("--- url queue is over ---")
                    break
                url = item
                workers[i] = create_new_task(url)
        time.sleep(0.2)
    print("Worker finished")


JOB_SUMMARY = JobSummary(os.environ.get("GITHUB_STEP_SUMMARY", "step_summary.md"))
JOB_SUMMARY.add_header("Test all URLs")


def main(files: list[str]) -> int:
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
