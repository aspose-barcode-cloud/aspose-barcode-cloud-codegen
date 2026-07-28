#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/python"
targetDir="../submodules/python"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/openapi-generator-cli.jar config-help -g python

# Restore pre-7.22.0 Python generator behavior for binary payloads:
#   --type-mappings file=bytearray
#       In 7.8.0 the Python generator already mapped OpenAPI `file` type to
#       `bytearray`; in 7.22.0 the default changed, so we map it back
#       explicitly.
#   --language-specific-primitives bytearray
#       Tell the generator that `bytearray` is a built-in primitive (not a
#       user model). Without this it would emit `from .bytearray import
#       bytearray` and a stub model file alongside the SDK code.
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json --type-mappings file=bytearray --language-specific-primitives bytearray
# java -DdebugMorms -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json > debugMorms.py.json
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json > debugOperations.py.json ; exit

rm -rf $targetDir/aspose_barcode_cloud/*
cp -r $tempDir/aspose_barcode_cloud/* $targetDir/aspose_barcode_cloud/

# Drop orphan modules emitted by the upstream python generator template that this
# SDK does not use: exceptions.py (this SDK raises aspose_barcode_cloud.rest.ApiException
# instead) and api_response.py (imports pydantic, which is not a dependency). Nothing
# imports either module; keeping them only breaks `import` and dilutes coverage.
rm -f "$targetDir/aspose_barcode_cloud/exceptions.py" "$targetDir/aspose_barcode_cloud/api_response.py"

rm -rf $targetDir/docs/*
cp $tempDir/docs/* $targetDir/docs/

cp "$tempDir/setup.py" "$targetDir/setup.py"
cp "$tempDir/requirements.txt" "$targetDir/requirements.txt"
cp "$tempDir/test-requirements.txt" "$targetDir/test-requirements.txt"
cp "$tempDir/tox.ini" "$targetDir/tox.ini"
cp "$tempDir/README.md" "$targetDir/README.template"

cp ../LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
