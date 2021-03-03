from __future__ import division, print_function

import argparse
import errno
import os
import re

SPLIT_RE = re.compile(r'//\s+[-]+\n//\s+<copyright company="Aspose" file="(?P<file>.+?\.java)">', re.MULTILINE)


def main(src_file, dst_dir):
    remaining = src_file.read()
    try:
        os.makedirs(dst_dir)
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise

    for match in reversed(list(SPLIT_RE.finditer(remaining))[1:]):
        start_pos = match.span()[0]

        with open(os.path.join(dst_dir, match.groupdict()['file']), 'wt') as out_f:
            out_f.write(remaining[start_pos:])

        remaining = remaining[:start_pos]

    src_file.seek(0)
    src_file.truncate(0)
    src_file.write(remaining)
    src_file.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src_file', type=argparse.FileType('rt+'))
    parser.add_argument('dst_dir', type=str)
    args = parser.parse_args()

    return vars(args)


if __name__ == '__main__':
    main(**parse_args())
