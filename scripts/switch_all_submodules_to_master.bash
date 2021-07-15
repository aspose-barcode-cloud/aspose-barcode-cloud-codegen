#!/bin/bash

set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    git switch master && git pull --ff-only

    popd > /dev/null
done

popd
