#!/bin/bash

set -euo pipefail

pushd "$( dirname "${BASH_SOURCE[0]}" )/../codegen"

for gen in generate-*.bash
do
    "./${gen}"
done

popd >/dev/null
