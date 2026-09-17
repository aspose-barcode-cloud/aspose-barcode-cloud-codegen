#!/bin/bash

set -euo pipefail

year=$(date +%y)
month=$(date +%-m)

major=${1:-$year}
minor=${2:-$month}
branch_name="release-${major}.${minor}"

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    (git fetch --prune && git switch "${branch_name}" && git pull --ff-only) || true

    popd >/dev/null
done

popd >/dev/null
