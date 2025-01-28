#!/bin/bash

set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    (git fetch --prune && git switch v4 && git pull --ff-only) || true

    popd >/dev/null
done

popd >/dev/null
