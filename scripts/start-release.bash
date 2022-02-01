#!/bin/bash
set -euo pipefail

year=$(date +%y)
month=$(date +%-m)
branch_name="release-${year}.${month}"

pushd "$( dirname -- "${BASH_SOURCE[0]}")"

pushd "../submodules"
for d in */ ; do
    pushd "$d"

    git switch --create "${branch_name}" || git switch "${branch_name}"
    wsl make update || true

    popd > /dev/null
done
popd

popd

python ./scripts/new-version.py "${year}" "${month}"
