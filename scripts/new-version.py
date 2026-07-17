#!/usr/bin/env python

from __future__ import division, print_function

import argparse
import collections
import json
import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_CONFIG_DIR = os.path.join(SCRIPT_DIR, "..", "codegen")
SUBMODULES_DIR = os.path.join(SCRIPT_DIR, "..", "submodules")

GO_VERSION_FORMAT = "4.{0}{1:02d}.{2}"


def get_dart_pub_version(new_version):
    pub_version = str.join(".", map(str, (4,) + new_version[:2]))
    if new_version[2] > 0:
        pub_version += "+" + str(new_version[2])
    return pub_version


def set_android_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-android.json")):
    config = read_config(filename)
    config["artifactVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_go_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-go.json")):
    go_version = GO_VERSION_FORMAT.format(*new_version)
    config = read_config(filename)
    config["packageVersion"] = go_version
    save_config(config, filename)


def set_dart_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-dart.json")):
    config = read_config(filename)
    config["pubVersion"] = get_dart_pub_version(new_version)
    save_config(config, filename)


def update_dart_changelog(new_version, filename=os.path.join(SUBMODULES_DIR, "dart", "CHANGELOG.md")):
    pub_version = get_dart_pub_version(new_version)
    entry_header = "## {}".format(pub_version)

    with open(filename, "r", encoding="utf-8") as rf:
        changelog = rf.read()

    if entry_header in changelog:
        return

    release_month = datetime(2000 + new_version[0], new_version[1], 1).strftime("%B %Y")
    entry = "{}\n\n* {} Release\n\n".format(entry_header, release_month)
    title = "# CHANGELOG\n\n"

    if changelog.startswith(title):
        changelog = title + entry + changelog[len(title):]
    else:
        changelog = entry + changelog

    with open(filename, "w", encoding="utf-8") as wf:
        wf.write(changelog)


def set_java_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-java.json")):
    config = read_config(filename)
    config["artifactVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_net_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-dotnet.json")):
    config = read_config(filename)
    config["packageVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_node_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-node.json")):
    config = read_config(filename)
    config["npmVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_php_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-php.json")):
    config = read_config(filename)
    config["artifactVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_python_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-python.json")):
    config = read_config(filename)
    config["packageVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def set_swift_version(new_version, filename=os.path.join(BASE_CONFIG_DIR, "config-swift.json")):
    config = read_config(filename)
    config["packageVersion"] = str.join(".", map(str, new_version))
    save_config(config, filename)


def read_config(filename):
    # Preserve the on-disk key order so a version bump round-trips to a minimal,
    # stable diff instead of reshuffling hand-ordered keys.
    with open(filename, "rb") as rf:
        config = json.load(rf, object_pairs_hook=collections.OrderedDict)
    return config


def save_config(config, filename):
    # Keep key order (no sort_keys) and always end with a single trailing newline
    # so releases produce stable, POSIX-friendly JSON.
    with open(filename, "wb") as wf:
        string = json.dumps(config, indent=4, separators=(",", ": "))
        wf.write((string.replace("\r", "") + "\n").encode("utf-8"))


def main(new_versions):
    assert 2 <= len(new_versions) <= 3, "Version format should be: 23 7 or 23 7 1"
    new_version = tuple(new_versions + [0] * (3 - len(new_versions)))

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


def parse_args():
    parser = argparse.ArgumentParser(usage="%s %s" % (sys.argv[0], datetime.today().strftime("%y %m")))
    parser.add_argument("new_versions", type=int, nargs="+", help="Use separate int values like: 21 6 1")
    args = parser.parse_args()
    return vars(args)


if __name__ == "__main__":
    main(**parse_args())
