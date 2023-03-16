#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

pushd "${SCRIPT_DIR}/../codegen"

for gen in generate-*.bash
do
    "./${gen}"
done

popd >/dev/null
