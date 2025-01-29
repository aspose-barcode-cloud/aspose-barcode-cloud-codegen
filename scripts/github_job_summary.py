import contextlib
from threading import Lock
from typing import TextIO


class JobSummary:
    """
    See https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary
    """

    _success: list[str]
    _errors: list[str]

    def __init__(self, filename: str):
        """

        :param filename: Use $GITHUB_STEP_SUMMARY inside GitHub
        """
        self.__file: TextIO = open(filename, mode="wt", newline="\n")
        self._errors = []
        self._success = []
        self._lock = Lock()

    def close(self) -> None:
        assert not self.__file.closed
        self.__file.close()

    def __str__(self) -> str:
        if not self.has_errors:
            return "OK"
        lines = ["Errors:"] + self._errors
        return "\n\n".join(lines)

    def _write_line(self, line: str) -> None:
        with self._lock:
            self.__file.write(line.replace("\r", ""))

    @property
    def has_errors(self) -> bool:
        return bool(self._errors)

    def add_header(self, text: str, level: int = 3) -> None:
        self._write_line(f"{'#' * level} {text}\n\n")

    def add_error(self, text: str) -> None:
        """
        See https://github.com/markdown-templates/markdown-emojis
        """
        if not self._errors:
            self._write_line("Errors:\n")
        self._errors.append(text)
        self._write_line(f"\n1. :x: {text}\n")

    def add_success(self, text: str) -> None:
        self._success.append(text)

    def finalize(self, format_str: str) -> None:
        total = len(self._success) + len(self._errors)
        self._write_line(
            "\n" + format_str.format(total=total, success=len(self._success), failed=len(self._errors)) + "\n"
        )


def test() -> None:
    summary: JobSummary
    with contextlib.closing(JobSummary("test.md")) as summary:
        summary.add_header("Test results")
        summary.add_error("Text for 1 error message")
        summary.add_error("Text for 2 error message")
        summary.add_success("OK")
        summary.finalize("Total={total}, success={success}, failed={failed}")


if __name__ == "__main__":
    test()
