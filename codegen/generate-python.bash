#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/python"
targetDir="../submodules/python"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l python
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l python -t Templates/python -o $tempDir -c config-python.json
# java -DdebugMorms -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l python -t Templates/python -o $tempDir -c config-python.json > debugMorms.py.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l python -t Templates/python -o $tempDir -c config-python.json > debugOperations.py.json

rm -rf $targetDir/aspose_barcode_cloud/* > /dev/null
cp -r $tempDir/aspose_barcode_cloud/* $targetDir/aspose_barcode_cloud/ > /dev/null

rm -rf $targetDir/docs/* > /dev/null
cp $tempDir/docs/* $targetDir/docs/ > /dev/null

cp "$tempDir/setup.py" "$targetDir/setup.py" > /dev/null
cp "$tempDir/requirements.txt" "$targetDir/requirements.txt" > /dev/null
cp "$tempDir/test-requirements.txt" "$targetDir/test-requirements.txt" > /dev/null
cp "$tempDir/tox.ini" "$targetDir/tox.ini" > /dev/null
cp "$tempDir/README.md" "$targetDir/README.md" > /dev/null
cp Templates/LICENSE "$targetDir/" > /dev/null


rm -rf $tempDir > /dev/null

pushd "$targetDir" && make format && popd
