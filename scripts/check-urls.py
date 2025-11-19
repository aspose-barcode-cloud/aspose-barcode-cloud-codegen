import contextlib
import fileinput
import os
import re
import sys
import typing
import urllib.parse

from github_job_summary import JobSummary
from subdomains import Subdomains
from curl_wrapper import CurlExitCodes
from url_checker import UrlChecker

"""
Read file names from stdin (feed from git ls-files)
    see `check_all_urls.sh`
Extract all URL-like strings
Check them with CURL
"""

JOIN_TIMEOUT_SEC = 120

EXIT_CODE_EXPECTATIONS: dict[str, tuple[int, int | None]] = {
    "https://api.aspose.cloud/connect/token": (CurlExitCodes.HTTP_RETURNED_ERROR, 400),
    "https://api.aspose.cloud/v3.0": (CurlExitCodes.HTTP_RETURNED_ERROR, 404),
    "https://api.aspose.cloud/v4.0": (CurlExitCodes.HTTP_RETURNED_ERROR, 404),
    "https://api.aspose.cloud/v4.0/": (CurlExitCodes.HTTP_RETURNED_ERROR, 404),
    "https://id.aspose.cloud/connect/token": (CurlExitCodes.HTTP_RETURNED_ERROR, 400),
    # TODO: Temporary fix
    "https://dashboard.aspose.cloud/applications": (CurlExitCodes.HTTP_RETURNED_ERROR, 404),
}

REGEX_TO_IGNORE: list[re.Pattern[str]] = [
    re.compile(r"^https://github\.com/(?P<user>[^/]+)/(?P<repo>[^/]+)/(?:blob|issues)/\S+$"),
]

URLS_TO_IGNORE = frozenset(
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
        ".swagger.io",
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

        with contextlib.suppress(IsADirectoryError, FileNotFoundError):
            with open(filename, "r", encoding="utf-8") as f:
                try:
                    yield filename, f.read()
                except UnicodeDecodeError:
                    print("Cant read '%s'" % filename, file=sys.stderr)
                    raise


JOB_SUMMARY = JobSummary(os.environ.get("GITHUB_STEP_SUMMARY", "step_summary.md"))
JOB_SUMMARY.add_header("Test all URLs")


def main(files: list[str]) -> int:
    url_checker = UrlChecker(
        expectations=EXIT_CODE_EXPECTATIONS,
    )

    with url_checker.start() as checker:
        for filename, text in text_extractor(files):
            for url in url_extractor(text, filename):
                checker.add_url(url)
        checker.wait(JOIN_TIMEOUT_SEC)
    results = url_checker.results

    # Collect results and write summary
    for res in results:
        if res.ok:
            JOB_SUMMARY.add_success(res.url)
        else:
            src_files = EXTRACTED_URLS_WITH_FILES.get(res.url, [])
            JOB_SUMMARY.add_error(f"Broken URL '{res.url}': {res.stderr}Files: {src_files}")

    JOB_SUMMARY.finalize("Checked {total} failed **{failed}**\nGood={success}")
    if JOB_SUMMARY.has_errors:
        print(JOB_SUMMARY, file=sys.stderr, flush=True)
        return 1
    else:
        print(JOB_SUMMARY, file=sys.stdout, flush=True)
        return 0


if __name__ == "__main__":
    exit(main([filename.strip() for filename in fileinput.input()]))
