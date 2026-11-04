#!/bin/bash
#
# Copy the shared GitHub configuration (zizmor workflow and zizmor config)
# from codegen/github/ into a repository checkout.
#
# Usage: ./scripts/sync-github-templates.bash <repo-dir>
#   <repo-dir> is an SDK submodule checkout (e.g. submodules/dart) or "." for
#   this repository.
#
# Every codegen/generate-<lang>.bash calls this for its SDK, so `make sdk`
# keeps all repositories identical. See codegen/github/README.md.
set -euo pipefail

if [ $# -ne 1 ]; then
    >&2 echo "Usage: $0 <repo-dir>"
    exit 1
fi

target="$1"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source_dir="${SCRIPT_DIR}/../codegen/github"

if [ ! -e "${target}/.git" ]; then
    >&2 echo "Error: '${target}' is not a git repository checkout"
    exit 1
fi

mkdir -p "${target}/.github/workflows"
cp "${source_dir}/zizmor.yml"        "${target}/.github/workflows/zizmor.yml"
cp "${source_dir}/zizmor-config.yml" "${target}/.github/zizmor.yml"
