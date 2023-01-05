#!/bin/bash

set -euo pipefail

pushd "../codegen"
for d in $(find . -name "generate-*.bash"); do 
    "$d" || echo "Error of executing $d"
done
popd