#!/bin/bash

set -euo pipefail

pushd "$( dirname "${BASH_SOURCE[0]}" )/../codegen"

generators=(
    android
    dart
    dotnet
    go
    java
    node
    php
    python
)

for gen in "${generators[@]}"
do
    "./generate-${gen}.bash"
done

popd >/dev/null
