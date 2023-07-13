#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud-with-deprecated.json"
tempDir=".generated/dart"
targetDir="../submodules/dart"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l dart & exit
# java -DdebugModels -jar "/opt/homebrew/Cellar/swagger-codegen/3.0.46/libexec/swagger-codegen-cli.jar" generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json > debugModels.dart.json & exit
# java -DdebugOperations -jar "/opt/homebrew/Cellar/swagger-codegen/3.0.46/libexec/swagger-codegen-cli.jar" generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json > debugOperations.dart.json & exit
swagger-codegen generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json


mv "$tempDir/README.md" "$targetDir"
mv "$tempDir/.gitignore" "$targetDir/"
mv "$tempDir/pubspec.yaml" "$targetDir/"


rm -rf "${targetDir:?}/lib/*" || mkdir -p "$targetDir/lib/"
mv $tempDir/lib/*.dart $targetDir/lib/

mkdir -p "$targetDir/lib/model/"
mv $tempDir/lib/model/*.dart $targetDir/lib/model/

mkdir -p "$targetDir/lib/api/"
mv $tempDir/lib/api/*.dart $targetDir/lib/api/

mkdir -p "$targetDir/lib/auth/"
mv "$tempDir/lib/auth/authentication.dart" "$targetDir/lib/auth/"
mv "$tempDir/lib/auth/oauth.dart" "$targetDir/lib/auth/"

rm -rf "$targetDir/doc/"
mkdir -p "$targetDir/doc/api/"

mv $tempDir/docs/*Api.md $targetDir/doc/api/
mkdir -p "$targetDir/doc/models/"
mv $tempDir/docs/*.md $targetDir/doc/models/

cp Templates/LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

# Cleanup
rm -rf $tempDir

# Format generated code etc.
pushd "$targetDir" && make after-gen && popd >/dev/null
