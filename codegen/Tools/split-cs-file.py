from __future__ import division, print_function

import argparse
import errno
import os
import re

SPLIT_RE = re.compile(r'//\s+[-]+\n//\s+<copyright company="Aspose" file="(?P<file>.+?\.cs)">', re.MULTILINE)


def main(src_file, dst_dir):
    remaining = src_file.read()
    try:
        os.makedirs(dst_dir)
    except OSError as e:
        # be happy if someone already created the path
        if e.errno != errno.EEXIST:
            raise

    self_content = None
    for match in reversed(list(SPLIT_RE.finditer(remaining))):
        start_pos = match.span()[0]

        new_filename = match.groupdict()['file']
        new_content = remaining[start_pos:]

        if new_filename == os.path.split(src_file.name)[-1]:
            self_content = new_content
        else:
            with open(os.path.join(dst_dir, new_filename), 'wt') as out_f:
                out_f.write(new_content)

        remaining = remaining[:start_pos]

    assert len(remaining) == 0, 'Unprocessed part: %s ' % remaining

    src_file.seek(0)
    src_file.truncate(0)
    src_file.write(self_content)
    src_file.close()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('src_file', type=argparse.FileType('rt+'))
    parser.add_argument('dst_dir', type=str)
    args = parser.parse_args()

    return vars(args)


if __name__ == '__main__':
    main(**parse_args())
