#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

check_file () {
    echo "$1"
}

git ls-files --exclude-standard --full-name | grep -i '\.md$\|\.mustache$' | python "${SCRIPT_DIR}/check-urls-in-file.py"
