#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated/go"
targetDir="../submodules/go"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l go
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json > debugModels.go.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l go -t Templates/go -o $tempDir -c config-go.json > debugOperations.go.json

rm -rf "$targetDir/barcode"

mkdir -p "$targetDir/barcode/jwt"
mv "$tempDir/response.go" "$targetDir/barcode/jwt/jwt.go"

mv $tempDir/*.go $targetDir/barcode/

rm -rf $targetDir/docs/*
mv $tempDir/docs/* $targetDir/docs/
mv "$tempDir/README.md" "$targetDir/README.md"
cp ../LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
