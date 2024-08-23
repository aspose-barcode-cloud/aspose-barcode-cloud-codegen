#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/dart"
targetDir="../submodules/dart"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/openapi-generator-cli.jar config-help -l dart ; exit
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g dart -t Templates/dart -o $tempDir -c config-dart.json > debugModels.dart.json ; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g dart -t Templates/dart -o $tempDir -c config-dart.json > debugOperations.dart.json ; exit
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g dart -t Templates/dart -o $tempDir -c config-dart.json


mv "$tempDir/README.md" "$targetDir/README.template"
mv "$tempDir/.gitignore" "$targetDir/"
mv "$tempDir/pubspec.yaml" "$targetDir/"


rm -rf "${targetDir:?}/lib/"*.dart || true
mv $tempDir/lib/api.dart $targetDir/lib/aspose_barcode_cloud.dart

mkdir -p "$targetDir/lib/src/" || true
mv $tempDir/lib/*.dart $targetDir/lib/src/

mkdir -p "$targetDir/lib/src/model/"
rm -rf "$targetDir/lib/src/model/"*.dart
mv $tempDir/lib/model/*.dart $targetDir/lib/src/model/

mkdir -p "$targetDir/lib/src/api/"
mv $tempDir/lib/api/*.dart $targetDir/lib/src/api/

mkdir -p "$targetDir/lib/src/auth/"
mv "$tempDir/lib/auth/authentication.dart" "$targetDir/lib/src/auth/"
mv "$tempDir/lib/auth/oauth.dart" "$targetDir/lib/src/auth/"

rm -rf "$targetDir/doc/"
mkdir -p "$targetDir/doc/api/"

mv $tempDir/doc/*Api.md $targetDir/doc/api/
mkdir -p "$targetDir/doc/models/"
mv $tempDir/doc/*.md $targetDir/doc/models/

cp ../LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

# Cleanup
rm -rf $tempDir

# Format generated code etc.
pushd "$targetDir" && make after-gen && popd >/dev/null
