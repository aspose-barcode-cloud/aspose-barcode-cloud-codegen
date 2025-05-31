#!/bin/bash

set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    branch="v3"
    if [ "$d" = "dart/" ] || [ "$d" = "go/" ]; then
        branch="v1"
    elif [ "$d" = "android/" ]; then
        # Do not update Android to legacy v3 versions
        branch="main"
    fi
    (git fetch --prune && git switch "$branch" && git pull --ff-only) || true

    popd >/dev/null
done

popd >/dev/null
