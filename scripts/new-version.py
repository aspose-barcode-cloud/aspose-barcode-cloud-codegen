#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import collections
import json
import os
import sys
import typing
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_CONFIG_DIR = os.path.join(SCRIPT_DIR, "..", "codegen")
SUBMODULES_DIR = os.path.join(SCRIPT_DIR, "..", "submodules")

GO_VERSION_FORMAT = "4.{0}{1:02d}.{2}"
CHANGELOG_TITLE = "# CHANGELOG\n\n"

# Normalized release version (year, month, patch), e.g. 26.7.0
# The patch is optional on the command line and defaults to 0, see `doc/versioning.md`
Version = tuple[int, int, int]
Config = collections.OrderedDict[str, object]


def get_plain_version(new_version: Version) -> str:
    return str.join(".", map(str, new_version))


def get_dart_pub_version(new_version: Version) -> str:
    pub_version = str.join(".", map(str, (4,) + new_version[:2]))
    if new_version[2] > 0:
        pub_version += "+" + str(new_version[2])
    return pub_version


def get_go_version(new_version: Version) -> str:
    return GO_VERSION_FORMAT.format(*new_version)


def get_release_month(new_version: Version) -> str:
    return datetime(2000 + new_version[0], new_version[1], 1).strftime("%B %Y")


class Sdk(typing.NamedTuple):
    """
    One SDK a release bumps.

    The config is always `codegen/config-<name>.json` and the changelog, when there
    is one, is always `submodules/<name>/CHANGELOG.md`, so the name drives both.
    See `doc/versioning.md` for the per-language version formats.
    """

    name: str
    version_field: str
    get_version: typing.Callable[[Version], str] = get_plain_version
    has_changelog: bool = False
    # Swift tags its releases vYY.M.P, so its changelog headers carry a prefix
    changelog_prefix: str = ""

    @property
    def config_filename(self) -> str:
        return os.path.join(BASE_CONFIG_DIR, "config-{}.json".format(self.name))

    @property
    def changelog_filename(self) -> str:
        return os.path.join(SUBMODULES_DIR, self.name, "CHANGELOG.md")


# Adding an SDK is one line here
SDKS = (
    Sdk("android", "artifactVersion"),
    Sdk("dart", "pubVersion", get_dart_pub_version, has_changelog=True),
    Sdk("dotnet", "packageVersion"),
    Sdk("go", "packageVersion", get_go_version),
    Sdk("java", "artifactVersion"),
    Sdk("node", "npmVersion"),
    Sdk("php", "artifactVersion"),
    Sdk("python", "packageVersion"),
    Sdk("swift", "packageVersion", has_changelog=True, changelog_prefix="v"),
)

# Every file a release rewrites, checked up front so a bad run cannot bump only some SDKs
RELEASE_FILES = tuple(sdk.config_filename for sdk in SDKS) + tuple(
    sdk.changelog_filename for sdk in SDKS if sdk.has_changelog
)


def check_release_files(filenames: typing.Iterable[str] = RELEASE_FILES) -> None:
    # Fail before the first write, otherwise a missing file leaves the SDKs on mixed versions
    missing = sorted(name for name in filenames if not os.path.isfile(name))
    if missing:
        raise SystemExit("Cannot bump version, missing files:\n  " + "\n  ".join(missing))


def read_config(filename: str) -> Config:
    # Preserve the on-disk key order so a version bump round-trips to a minimal,
    # stable diff instead of reshuffling hand-ordered keys.
    with open(filename, "rb") as rf:
        config = json.load(rf, object_pairs_hook=collections.OrderedDict)
    if not isinstance(config, collections.OrderedDict):
        raise SystemExit("Expected a JSON object in {}, got {}".format(filename, type(config).__name__))
    return config


def save_config(config: Config, filename: str) -> None:
    # Keep key order (no sort_keys) and always end with a single trailing newline
    # so releases produce stable, POSIX-friendly JSON.
    with open(filename, "wb") as wf:
        string = json.dumps(config, indent=4, separators=(",", ": "))
        wf.write((string.replace("\r", "") + "\n").encode("utf-8"))


def set_version(sdk: Sdk, new_version: Version) -> None:
    config = read_config(sdk.config_filename)
    config[sdk.version_field] = sdk.get_version(new_version)
    save_config(config, sdk.config_filename)


def update_changelog(sdk: Sdk, new_version: Version) -> None:
    entry_header = "## {}{}".format(sdk.changelog_prefix, sdk.get_version(new_version))
    filename = sdk.changelog_filename

    with open(filename, "r", encoding="utf-8") as rf:
        changelog = rf.read()

    # Match whole lines only: "## 4.26.4" is a substring of both "## 4.26.4+1" and "## 4.26.41"
    if any(line.rstrip() == entry_header for line in changelog.splitlines()):
        return

    entry = "{}\n\n* {} Release\n\n".format(entry_header, get_release_month(new_version))

    if changelog.startswith(CHANGELOG_TITLE):
        changelog = CHANGELOG_TITLE + entry + changelog[len(CHANGELOG_TITLE) :]
    else:
        changelog = entry + changelog

    with open(filename, "w", encoding="utf-8", newline="\n") as wf:
        wf.write(changelog)


def main(new_version: Version) -> None:
    check_release_files()

    for sdk in SDKS:
        set_version(sdk, new_version)
        if sdk.has_changelog:
            update_changelog(sdk, new_version)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(usage="%s %s" % (sys.argv[0], datetime.today().strftime("%y %m")))
    parser.add_argument("year", type=int, help="Two digit release year, like 26")
    parser.add_argument("month", type=int, help="Release month, 1-12")
    parser.add_argument("patch", type=int, nargs="?", default=0, help="Optional patch number, defaults to 0")
    args = parser.parse_args()

    # Validate before anything is written, a bad month used to blow up mid-release
    if not 0 <= args.year <= 99:
        parser.error("year must be a two digit number in 0..99, got {}".format(args.year))
    if not 1 <= args.month <= 12:
        parser.error("month must be in 1..12, got {}".format(args.month))
    if args.patch < 0:
        parser.error("patch must not be negative, got {}".format(args.patch))

    return args


if __name__ == "__main__":
    parsed_args = parse_args()
    main((parsed_args.year, parsed_args.month, parsed_args.patch))
