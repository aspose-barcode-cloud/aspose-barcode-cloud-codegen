#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/swift"
targetDir="../submodules/swift"

if [ -d "$tempDir" ];
then
    rm -rf "$tempDir"
fi

# Templates src https://github.com/OpenAPITools/openapi-generator/tree/v7.22.0/modules/openapi-generator/src/main/resources/swift6
# java -jar Tools/openapi-generator-cli.jar config-help -g swift6 ; exit 1
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift6 -t Templates/swift -o "$tempDir" -c config-swift.json > debugModels.swift.json ; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift6 -t Templates/swift -o "$tempDir" -c config-swift.json > debugOperations.swift.json ; exit
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g swift6 -t Templates/swift -o "$tempDir" -c config-swift.json

mkdir -p "$targetDir/Sources"
rm -rf "$targetDir/Sources/AsposeBarcodeCloud"
mv "$tempDir/Sources/AsposeBarcodeCloud" "$targetDir/Sources/AsposeBarcodeCloud"

mv "$tempDir/Package.swift" "$targetDir/Package.swift"
mv "$tempDir/AsposeBarcodeCloud.podspec" "$targetDir/AsposeBarcodeCloud.podspec"
mv "$tempDir/.spi.yml" "$targetDir/.spi.yml"
mv "$tempDir/README.md" "$targetDir/README.template"

rm -rf "$targetDir/docs"
mv "$tempDir/docs" "$targetDir/docs"

mv "$tempDir/.swiftformat" "$targetDir/"

cp ../LICENSE "$targetDir/"

rm -rf "$tempDir"

pushd "$targetDir" && make after-gen && popd >/dev/null
