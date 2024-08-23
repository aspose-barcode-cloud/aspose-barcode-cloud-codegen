#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated/go"
targetDir="../submodules/go"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/openapi-generator-cli.jar config-help -l go
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g go -t Templates/go -o $tempDir -c config-go.json
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g go -t Templates/go -o $tempDir -c config-go.json > debugModels.go.json
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g go -t Templates/go -o $tempDir -c config-go.json > debugOperations.go.json ; exit

rm -rf "$targetDir/barcode"

mkdir -p "$targetDir/barcode/jwt"
mv "$tempDir/response.go" "$targetDir/barcode/jwt/jwt.go"

mv $tempDir/*.go $targetDir/barcode/

rm -rf $targetDir/docs/*
mv $tempDir/docs/* $targetDir/docs/
mv "$tempDir/README.md" "$targetDir/README.template"
cp ../LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
