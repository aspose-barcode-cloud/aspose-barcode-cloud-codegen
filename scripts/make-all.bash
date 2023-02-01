#!/bin/bash

set -euo pipefail

pushd "../codegen"
for d in generate-*.bash
do
    "./$d" || echo "Error of executing $d"
done
popd
