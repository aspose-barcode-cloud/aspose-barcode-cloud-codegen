from __future__ import division, print_function

import argparse
import errno
import os
import re
import typing

SPLIT_RE = re.compile(
    r'/[\*]+\s*\n\s\*\s+[-]+\n\s*\*\s+<copyright company="Aspose" file="(?P<file>.+?\.php)">',
    re.MULTILINE,
)


def main(src_file: typing.IO[str], dst_dir: str) -> None:
    remaining = src_file.read()
    try:
        os.makedirs(dst_dir)
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise

    found = list(reversed(list(SPLIT_RE.finditer(remaining))[1:]))
    assert found, "No parts matching regex '%s' found" % SPLIT_RE.pattern
    for match in found:
        filename = match.groupdict()["file"]
        classname = os.path.splitext(filename)[0]

        new_filename = filename[0].upper() + filename[1:]
        new_classname = classname[0].upper() + classname[1:]
        remaining = remaining.replace(classname, new_classname)

        start_pos = match.span()[0]
        part = remaining[start_pos:]
        with open(os.path.join(dst_dir, new_filename), "wt") as out_f:
            out_f.write("<?php\n\n")
            out_f.write(part)

        remaining = remaining[:start_pos]

    src_file.seek(0)
    src_file.truncate(0)
    src_file.write(remaining)
    src_file.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("src_file", type=argparse.FileType("rt+"))
    parser.add_argument("dst_dir", type=str)

    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_args()
    main(parsed_args.src_file, parsed_args.dst_dir)
