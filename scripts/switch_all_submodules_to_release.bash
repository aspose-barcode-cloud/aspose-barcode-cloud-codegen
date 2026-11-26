#!/bin/bash
# Switch every SDK submodule to an existing release branch and fast-forward it.
#
# Usage: scripts/switch_all_submodules_to_release.bash [<version>]
#
# <version> is <major>.<minor> or <major>.<minor>.<patch> (e.g. 26.10 or
# 26.7.1) and selects the release-<version> branch. It defaults to the current
# year and month, like scripts/start-release.bash. A local branch is created
# from origin/release-<version> when it does not exist yet.
#
# Submodules that cannot be switched (no such branch, local changes in the
# way) are reported and skipped; the script then exits with status 1.
set -euo pipefail

version=${1:-$(date +%y).$(date +%-m)}
branch_name="release-${version}"
failed=""

pushd "$(dirname "$0")/../submodules" >/dev/null

for d in */ ; do
    pushd "$d" >/dev/null
    echo "== ${d%/}: switching to ${branch_name}"
    if git fetch --prune && git switch "${branch_name}" && git pull --ff-only; then
        echo "== ${d%/}: on ${branch_name}"
    else
        >&2 echo "== ${d%/}: could not switch to ${branch_name}"
        failed="${failed} ${d%/}"
    fi
    popd >/dev/null
done

popd >/dev/null

if [ -n "${failed}" ]; then
    >&2 echo "Not switched to ${branch_name}:${failed}"
    exit 1
fi
