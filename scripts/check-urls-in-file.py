import re
import subprocess
import os
import fileinput
import collections


URL_REGEX=re.compile(r"\]\((http[^{})]+)\)")

GOOD_URLS = set()
BROKEN_URLS = collections.defaultdict(list)

def check_url(url):
    with open(os.devnull, 'w') as devnull:
        retcode = subprocess.call(['curl', '-sSfI', url], stdout=devnull)
    return retcode == 0


def check_file(filename):
    with open(filename, 'r') as f:
        urls = frozenset(URL_REGEX.findall(f.read()))
    for url in sorted(urls):
        good_url = False

        if url in GOOD_URLS:
            good_url = True
        elif url in BROKEN_URLS:
            good_url = False
        else:
            good_url = check_url(url)

        if good_url:
            print("OK: '%s'" % url)
            GOOD_URLS.add(url)
        else:
            print("BROKEN: '%s' in file %s" % (url, filename))
            BROKEN_URLS[url].append(filename)


def main():
    for filename in fileinput.input():
        check_file(filename.strip())

    for url, files in BROKEN_URLS.items():
        print("BROKEN URL: '%s' in files: %s" % (url, ', '.join(files)))
    if BROKEN_URLS:
        exit(1)


if __name__ == '__main__':
    main()
