#!/bin/bash
set -euo pipefail

which make || (
    echo "Make is required"
    echo "Install Make or use WSL"
    exit 1
)

year=$(date +%y)
month=$(date +%-m)

major=${1:-$year}
minor=${2:-$month}
branch_name="release-${major}.${minor}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
pushd "${SCRIPT_DIR}/.."

echo "Update Swagger specification..."
./scripts/update_swagger_spec.bash

echo "Switch to main all submodules for start new branch in the right place..."
./scripts/switch_all_submodules_to_default.bash

echo "Switching to ${branch_name}"
git switch --create "${branch_name}" || git switch "${branch_name}"

pushd "./submodules"
for d in */ ; do
    pushd "$d"

    git switch --create "${branch_name}" || git switch "${branch_name}" || true
    make update || true

    popd >/dev/null
done
popd >/dev/null

python "./scripts/new-version.py" "${major}" "${minor}"
popd >/dev/null
