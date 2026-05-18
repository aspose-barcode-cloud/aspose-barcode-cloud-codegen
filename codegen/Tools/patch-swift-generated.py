#!/usr/bin/env python3

from __future__ import print_function

import json
import re
import sys
from pathlib import Path


def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError("Expected exactly one match in {0}, found {1}".format(path, count))
    path.write_text(text.replace(old, new), encoding="utf-8")


def replace_regex_once(path, pattern, replacement):
    text = path.read_text(encoding="utf-8")
    text, count = re.subn(pattern, replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Expected exactly one regex match in {0}, found {1}".format(path, count))
    path.write_text(text, encoding="utf-8")


def append_once(path, marker, block):
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    path.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


def patch_url_session(sources_dir):
    url_session = sources_dir / "URLSessionImplementations.swift"

    replace_once(
        url_session,
        "import Foundation\n#if !os(macOS)\nimport MobileCoreServices\n#endif",
        "import Foundation\n"
        "#if canImport(FoundationNetworking)\n"
        "import FoundationNetworking\n"
        "#endif\n"
        "#if canImport(MobileCoreServices)\n"
        "import MobileCoreServices\n"
        "#endif",
    )

    replace_once(
        url_session,
        "        } else {\n"
        "            if let uti = UTTypeCreatePreferredIdentifierForTag",
        "        } else {\n"
        "            #if canImport(MobileCoreServices)\n"
        "            if let uti = UTTypeCreatePreferredIdentifierForTag",
    )

    replace_once(
        url_session,
        "                return mimetype as String\n"
        "            }\n"
        "            return \"application/octet-stream\"",
        "                return mimetype as String\n"
        "            }\n"
        "            #endif\n"
        "            return \"application/octet-stream\"",
    )

    replace_regex_once(
        url_session,
        r"\n            #else\n            return \"application/octet-stream\"\s*\n            #endif",
        "\n            #endif",
    )

    replace_once(url_session, "private class SessionDelegate", "private final class SessionDelegate")


def patch_extensions(sources_dir):
    replace_once(
        sources_dir / "Extensions.swift",
        "extension String: CodingKey {",
        "extension Swift.String: Swift.CodingKey {",
    )


def patch_date_formatter(sources_dir):
    append_once(
        sources_dir / "OpenISO8601DateFormatter.swift",
        "extension OpenISO8601DateFormatter: @unchecked Sendable",
        "#if compiler(>=5.5)\n"
        "extension OpenISO8601DateFormatter: @unchecked Sendable {}\n"
        "#endif",
    )


def patch_client_version(sources_dir, package_version):
    replace_regex_once(
        sources_dir / "AsposeBarcodeCloudClient.swift",
        r'public static let defaultSdkVersion = "[^"]+"',
        'public static let defaultSdkVersion = "{0}"'.format(package_version),
    )


def main(target_dir, config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    package_version = config.get("packageVersion")
    if not package_version:
        raise RuntimeError("config-swift.json must define packageVersion")

    sources_dir = Path(target_dir) / "Sources" / "AsposeBarcodeCloud"
    patch_url_session(sources_dir)
    patch_extensions(sources_dir)
    patch_date_formatter(sources_dir)
    patch_client_version(sources_dir, package_version)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: patch-swift-generated.py <target-dir> <config-swift.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
