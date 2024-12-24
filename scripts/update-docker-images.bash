#!/bin/bash
set -euo pipefail

# This command finds all Dockerfile files in the current directory and its subdirectories,
# extracts the image names and tags from the FROM statements in each file, filters, sorts,
# and removes duplicates from the resulting list,
# and finally pulls each image and tag from a Docker registry using the docker pull command.

pushd "$( dirname -- "${BASH_SOURCE[0]}")/.."

find . -type f -name Dockerfile -exec grep -Po 'FROM\s+\K\S+' {} \; | grep -F ':' | sort | uniq | xargs -n 1 docker pull

popd
