#!/bin/bash
#Run from aspose-barcode-cloud-codegen
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

year=$(date +%y)
month=$(date +%-m)

major=${1:-$year}
minor=${2:-$month}

branch_name="release-${major}.${minor}"
echo "Switching to ${branch_name}"
git switch --create "${branch_name}" || git switch "${branch_name}"

pushd "${SCRIPT_DIR}/../submodules"
for d in */ ; do
    pushd "$d"

    git switch --create "${branch_name}" || git switch "${branch_name}"
    make update || true

    popd >/dev/null
done

popd >/dev/null
