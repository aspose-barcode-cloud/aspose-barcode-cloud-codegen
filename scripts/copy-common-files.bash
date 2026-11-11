#!/bin/bash
# Copy the files that every SDK shares with this repository into an SDK checkout.
#
# Usage: scripts/copy-common-files.bash [--no-coverage] <sdk-dir>
#
# Called by every codegen/generate-<sdk>.bash. The copies in the SDKs are
# overwritten on each generation, so edit the files here, never in an SDK.
#
#   LICENSE                  -> <sdk-dir>/LICENSE
#   scripts/check-badges.bash, scripts/coverage.py, scripts/publish-coverage.py
#                            -> <sdk-dir>/scripts/, or <sdk-dir>/Scripts/ if it
#                               exists (swift)
#
# --no-coverage skips coverage.py and publish-coverage.py, for a submodule that
# is exempt from the coverage requirements (android, a demo application).
set -euo pipefail

usage() {
    >&2 echo "Usage: $0 [--no-coverage] <sdk-dir>"
    exit 2
}

coverage=true
if [ "${1:-}" = "--no-coverage" ]; then
    coverage=false
    shift
fi
if [ $# -ne 1 ] || [ ! -d "$1" ]; then
    usage
fi

targetDir=$1
repoDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"

scriptsDir="${targetDir}/scripts"
if [ -d "${targetDir}/Scripts" ]; then
    scriptsDir="${targetDir}/Scripts"
fi
mkdir -p "${scriptsDir}"

scripts=("${repoDir}/scripts/check-badges.bash")
if [ "${coverage}" = true ]; then
    scripts+=("${repoDir}/scripts/coverage.py" "${repoDir}/scripts/publish-coverage.py")
fi

cp "${repoDir}/LICENSE" "${targetDir}/"
cp "${scripts[@]}" "${scriptsDir}/"
