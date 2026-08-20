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

ANDROID_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-android.json")
DART_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-dart.json")
DOTNET_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-dotnet.json")
GO_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-go.json")
JAVA_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-java.json")
NODE_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-node.json")
PHP_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-php.json")
PYTHON_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-python.json")
SWIFT_CONFIG = os.path.join(BASE_CONFIG_DIR, "config-swift.json")

DART_CHANGELOG = os.path.join(SUBMODULES_DIR, "dart", "CHANGELOG.md")
SWIFT_CHANGELOG = os.path.join(SUBMODULES_DIR, "swift", "CHANGELOG.md")

# Every file a release rewrites, checked up front so a bad run cannot bump only some SDKs
RELEASE_FILES = (
    ANDROID_CONFIG,
    DART_CONFIG,
    DOTNET_CONFIG,
    GO_CONFIG,
    JAVA_CONFIG,
    NODE_CONFIG,
    PHP_CONFIG,
    PYTHON_CONFIG,
    SWIFT_CONFIG,
    DART_CHANGELOG,
    SWIFT_CHANGELOG,
)

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


def get_release_month(new_version: Version) -> str:
    return datetime(2000 + new_version[0], new_version[1], 1).strftime("%B %Y")


def check_release_files(filenames: typing.Iterable[str] = RELEASE_FILES) -> None:
    # Fail before the first write, otherwise a missing file leaves the SDKs on mixed versions
    missing = sorted(name for name in filenames if not os.path.isfile(name))
    if missing:
        raise SystemExit("Cannot bump version, missing files:\n  " + "\n  ".join(missing))


def set_android_version(new_version: Version, filename: str = ANDROID_CONFIG) -> None:
    config = read_config(filename)
    config["artifactVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_go_version(new_version: Version, filename: str = GO_CONFIG) -> None:
    go_version = GO_VERSION_FORMAT.format(*new_version)
    config = read_config(filename)
    config["packageVersion"] = go_version
    save_config(config, filename)


def set_dart_version(new_version: Version, filename: str = DART_CONFIG) -> None:
    config = read_config(filename)
    config["pubVersion"] = get_dart_pub_version(new_version)
    save_config(config, filename)


def update_changelog(entry_version: str, release_month: str, filename: str) -> None:
    entry_header = "## {}".format(entry_version)

    with open(filename, "r", encoding="utf-8") as rf:
        changelog = rf.read()

    # Match whole lines only: "## 4.26.4" is a substring of both "## 4.26.4+1" and "## 4.26.41"
    if any(line.rstrip() == entry_header for line in changelog.splitlines()):
        return

    entry = "{}\n\n* {} Release\n\n".format(entry_header, release_month)

    if changelog.startswith(CHANGELOG_TITLE):
        changelog = CHANGELOG_TITLE + entry + changelog[len(CHANGELOG_TITLE) :]
    else:
        changelog = entry + changelog

    with open(filename, "w", encoding="utf-8", newline="\n") as wf:
        wf.write(changelog)


def update_dart_changelog(new_version: Version, filename: str = DART_CHANGELOG) -> None:
    update_changelog(get_dart_pub_version(new_version), get_release_month(new_version), filename)


def update_swift_changelog(new_version: Version, filename: str = SWIFT_CHANGELOG) -> None:
    # Swift releases are tagged vYY.M.P, see `doc/versioning.md`
    update_changelog("v" + get_plain_version(new_version), get_release_month(new_version), filename)


def set_java_version(new_version: Version, filename: str = JAVA_CONFIG) -> None:
    config = read_config(filename)
    config["artifactVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_net_version(new_version: Version, filename: str = DOTNET_CONFIG) -> None:
    config = read_config(filename)
    config["packageVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_node_version(new_version: Version, filename: str = NODE_CONFIG) -> None:
    config = read_config(filename)
    config["npmVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_php_version(new_version: Version, filename: str = PHP_CONFIG) -> None:
    config = read_config(filename)
    config["artifactVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_python_version(new_version: Version, filename: str = PYTHON_CONFIG) -> None:
    config = read_config(filename)
    config["packageVersion"] = get_plain_version(new_version)
    save_config(config, filename)


def set_swift_version(new_version: Version, filename: str = SWIFT_CONFIG) -> None:
    config = read_config(filename)
    config["packageVersion"] = get_plain_version(new_version)
    save_config(config, filename)


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


def main(new_version: Version) -> None:
    check_release_files()

    set_android_version(new_version)
    set_dart_version(new_version)
    update_dart_changelog(new_version)
    set_go_version(new_version)
    set_java_version(new_version)
    set_net_version(new_version)
    set_node_version(new_version)
    set_php_version(new_version)
    set_python_version(new_version)
    set_swift_version(new_version)
    update_swift_changelog(new_version)


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
