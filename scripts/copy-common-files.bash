#!/bin/bash
# Copy the files that every SDK shares with this repository into an SDK checkout.
#
# Usage: scripts/copy-common-files.bash <sdk-dir> [--no-coverage]
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

targetDir=${1:-}
if [ ! -d "${targetDir}" ] || [ $# -gt 2 ] || { [ $# -eq 2 ] && [ "$2" != "--no-coverage" ]; }; then
    >&2 echo "Usage: $0 <sdk-dir> [--no-coverage]"
    exit 2
fi
repoDir="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"

scriptsDir="${targetDir}/scripts"
if [ -d "${targetDir}/Scripts" ]; then
    scriptsDir="${targetDir}/Scripts"
fi
mkdir -p "${scriptsDir}"

cp "${repoDir}/LICENSE" "${targetDir}/"
cp "${repoDir}/scripts/check-badges.bash" "${scriptsDir}/"
if [ "${2:-}" != "--no-coverage" ]; then
    cp "${repoDir}/scripts/coverage.py" "${repoDir}/scripts/publish-coverage.py" "${scriptsDir}/"
fi
