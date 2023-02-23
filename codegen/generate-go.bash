#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated"
targetDir="../submodules/go"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l go
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json > debugModels.go.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json > debugOperations.go.json

rm -rf "$targetDir/barcode" > /dev/null

mkdir -p "$targetDir/barcode/jwt" > /dev/null
mv  "$tempDir/response.go" "$targetDir/barcode/jwt/jwt.go" > /dev/null

mv  $tempDir/*.go $targetDir/barcode/ > /dev/null

rm -rf "$targetDir/docs/*" > /dev/null
mv  $tempDir/docs/* $targetDir/docs/ > /dev/null
mv  "$tempDir/README.md" "$targetDir/README.md" > /dev/null
cp  Templates/LICENSE "$targetDir/" > /dev/null

rm -rf  $tempDir > /dev/null

pushd "$targetDir" && make after-gen && popd
