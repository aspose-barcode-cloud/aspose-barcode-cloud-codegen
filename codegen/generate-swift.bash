#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/swift"
targetDir="../submodules/swift"

if [ -d "$tempDir" ];
then
    rm -rf "$tempDir"
fi

# java -jar Tools/openapi-generator-cli.jar config-help -g swift5 ; exit 1
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json > debugModels.swift.json ; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json > debugOperations.swift.json ; exit
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift5 -o "$tempDir" -c config-swift.json

mkdir -p "$targetDir/Sources"
rm -rf "$targetDir/Sources/AsposeBarcodeCloud"
mv "$tempDir/Sources/AsposeBarcodeCloud" "$targetDir/Sources/AsposeBarcodeCloud"

rm -rf "$targetDir/docs"
mv "$tempDir/docs" "$targetDir/docs"

mv "$tempDir/.openapi-generator-ignore" "$targetDir/"
mv "$tempDir/.swiftformat" "$targetDir/"

mkdir -p "$targetDir/.openapi-generator"
mv "$tempDir/.openapi-generator/VERSION" "$targetDir/.openapi-generator/"
mv "$tempDir/.openapi-generator/FILES" "$targetDir/.openapi-generator/"

cp ../LICENSE "$targetDir/"

rm -rf "$tempDir"
