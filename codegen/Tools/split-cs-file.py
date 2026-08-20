from __future__ import division, print_function

import argparse
import errno
import os
import re
import typing

SPLIT_RE = re.compile(
    r'//\s+[-]+\n//\s+<copyright company="Aspose" file="(?P<file>.+?\.cs)">',
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

    for match in reversed(list(SPLIT_RE.finditer(remaining))[1:]):
        start_pos = match.span()[0]

        with open(os.path.join(dst_dir, match.groupdict()["file"]), "wt") as out_f:
            out_f.write(remaining[start_pos:])

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
