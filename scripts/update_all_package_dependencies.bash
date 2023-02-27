#!/bin/bash

set -euo pipefail

pushd "$(dirname "$0")/../submodules"

for d in */ ; do
    pushd "$d"

    wsl make update

    popd >/dev/null
done

popd >/dev/null
