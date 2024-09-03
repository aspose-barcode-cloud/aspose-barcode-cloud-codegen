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
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json
# java -DdebugMorms -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json > debugMorms.py.json
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g python -t Templates/python -o $tempDir -c config-python.json > debugOperations.py.json ; exit

rm -rf $targetDir/aspose_barcode_cloud/*
cp -r $tempDir/aspose_barcode_cloud/* $targetDir/aspose_barcode_cloud/

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
