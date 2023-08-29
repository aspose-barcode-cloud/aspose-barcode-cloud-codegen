#!/bin/bash
set -euo pipefail

which make || (
    echo "Make is required"
    echo "Install Make or use WSL"
    exit 1
)

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    make update

    popd >/dev/null
done

popd >/dev/null
