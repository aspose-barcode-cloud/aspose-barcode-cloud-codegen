#!/bin/bash
set -euo pipefail

pushd "$( dirname "${BASH_SOURCE[0]}" )"

pushd "../submodules"
for d in */ ; do
    pushd "$d"

    # Update Repo
    git fetch
    # Rebase release-* branch on remote main
    git rebase origin/main

    git switch main
    git merge --ff-only origin/main

    popd >/dev/null
done
