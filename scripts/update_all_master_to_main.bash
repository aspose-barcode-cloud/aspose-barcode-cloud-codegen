#!/bin/bash
set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    git fetch && git switch master && git merge --ff-only origin/main && git push

    popd >/dev/null
done

popd >/dev/null
