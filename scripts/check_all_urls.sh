#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"

pushd "${ROOT_DIR}"
git ls-files --recurse-submodules --exclude-standard --full-name | grep -v 'package-lock.json$' | python "${SCRIPT_DIR}/check-urls.py"
popd
