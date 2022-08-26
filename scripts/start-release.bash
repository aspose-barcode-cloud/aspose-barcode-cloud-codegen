#!/bin/bash
set -euo pipefail

year=$(date +%y)
month=$(date +%-m)

major=${1:-$year}
minor=${2:-$month}

branch_name="release-${major}.${minor}"
echo "Switching to ${branch_name}"
git switch --create "${branch_name}" || git switch "${branch_name}"

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

python ./scripts/new-version.py "${major}" "${minor}"
