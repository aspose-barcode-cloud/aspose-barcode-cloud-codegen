import re
import subprocess
import os
import sys
import fileinput
import collections

"""
Read file names from stdin
Extract all URL-like strings
Check them with CURL
"""

EXTENSIONS_TO_IGNORE = frozenset(
    [
        ".jar",
        ".png",
    ]
)
URLS_TO_IGNORE = frozenset(
    [
        "http://localhost:12345",
        "http://localhost:12345/v3.0",
        "http://some",
    ]
)

BROKEN_URLS = collections.defaultdict(list)


class Curl:
    """
    See: https://curl.se/libcurl/c/libcurl-errors.html
    """

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
    "https://api-qa.aspose.cloud/connect/token": (Curl.HTTP_RETURNED_ERROR, 400),
    "https://mvnrepository.com/artifact/io.swagger/swagger-codegen-cli": (
        Curl.HTTP_RETURNED_ERROR,
        403,
    ),
    # TODO: Temporary fix
    "https://dashboard.aspose.cloud/applications": (Curl.HTTP_RETURNED_ERROR, 404),
}

URL_END_CHARS = r"\)\"'<>\*\s\\"
URL_REGEX = re.compile(r"(https*://[^{%s}]+)[%s]" % (URL_END_CHARS, URL_END_CHARS))
CURL_STDERR_HTTP_RE = re.compile(
    r"^curl: \(22\) The requested URL returned error: (?P<http_code>\d+)"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    + "Chrome/110.0.0.0 Safari/537.36"
)


def check_url(url):
    with open(os.devnull, "w") as devnull:
        proc = subprocess.Popen(
            [
                "curl",
                "-sSf",
                "--output",
                "-",
                "--user-agent",
                USER_AGENT,
                url,
            ],
            stdout=devnull,
            stderr=subprocess.PIPE,
        )
        ret_code = proc.wait()
        stderr = proc.stderr.read().decode()

    expected_ret_code, expected_http_code = CURL_EXIT_CODES_AND_HTTP_CODES.get(
        url, (0, None)
    )
    if ret_code == expected_ret_code:
        return True

    if ret_code == Curl.HTTP_RETURNED_ERROR and expected_http_code:
        # Try parse stderr for HTTP code
        match = CURL_STDERR_HTTP_RE.match(stderr)
        assert match, "Unexpected output: %s" % stderr
        http_code = int(match.groupdict()["http_code"])
        if http_code == expected_http_code:
            return True

    print(
        "Expected %d got %d for '%s': %s" % (expected_ret_code, ret_code, url, stderr),
        file=sys.stderr,
    )
    return False


CHECKED_URLS = set(URLS_TO_IGNORE)


def check_file(filename):
    _, ext = os.path.splitext(filename)
    if ext in EXTENSIONS_TO_IGNORE:
        return

    with open(filename, "r", encoding="utf-8") as f:
        try:
            urls = frozenset(URL_REGEX.findall(f.read()))
        except UnicodeDecodeError:
            print("Cant read '%s'" % filename, file=sys.stderr)
            raise

    for url in sorted(urls):
        if url in CHECKED_URLS:
            continue
        if url in BROKEN_URLS:
            continue

        if check_url(url):
            print("OK: '%s'" % url)
            CHECKED_URLS.add(url)
        else:
            print("BROKEN: '%s' in file %s" % (url, filename))
            BROKEN_URLS[url].append(filename)


def main():
    for filename in fileinput.input():
        check_file(filename.strip())

    for url, files in BROKEN_URLS.items():
        print(
            "BROKEN URL: '%s' in files: %s" % (url, ", ".join(files)), file=sys.stderr
        )
    if BROKEN_URLS:
        exit(1)


if __name__ == "__main__":
    main()
