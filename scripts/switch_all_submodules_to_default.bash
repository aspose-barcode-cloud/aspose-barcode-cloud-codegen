#!/bin/bash

set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"
    if [[ "$d" == *"go"* ]]
    then
        (git fetch --prune && git switch v4 && git pull --ff-only) || true
    else 
        (git fetch --prune && git switch main && git pull --ff-only) || true
    fi

    popd >/dev/null
done

popd >/dev/null
