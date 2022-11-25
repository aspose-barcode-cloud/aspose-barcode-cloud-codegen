#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/dart"
targetDir="../submodules/dart"

if [ -d $tempDir ]; 
then
     rm -rf $tempDir 
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l dart & exit
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json > debugModels.dart.json & exit
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json > debugOperations.dart.json & exit
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l dart -t Templates/dart -o $tempDir -c config-dart.json


cp Templates/LICENSE "$targetDir/" > /dev/null 
mv  "$tempDir/README.md" "$targetDir" > /dev/null 
mv  "$tempDir/.gitignore" "$targetDir/" > /dev/null 
mv  "$tempDir/pubspec.yaml" "$targetDir/" > /dev/null 


rm -rf "$targetDir/lib/*" > /dev/null || mkdir -p "$targetDir/lib/" > /dev/null 
mv $tempDir/lib/*.dart $targetDir/lib/  > /dev/null 

mkdir -p "$targetDir/lib/model/" > /dev/null
mv  $tempDir/lib/model/*.dart $targetDir/lib/model/ > /dev/null 

mkdir -p "$targetDir/lib/api/" > /dev/null
mv $tempDir/lib/api/*.dart $targetDir/lib/api/ > /dev/null 

mkdir -p "$targetDir/lib/auth/"
mv  "$tempDir/lib/auth/authentication.dart" "$targetDir/lib/auth/" > /dev/null 
mv  "$tempDir/lib/auth/oauth.dart" "$targetDir/lib/auth/" > /dev/null 

rm -rf "$targetDir/doc/" > /dev/null
mkdir -p "$targetDir/doc/api/" > /dev/null 

mv  $tempDir/docs/*Api.md $targetDir/doc/api/ > /dev/null 
mkdir -p "$targetDir/doc/models/" > /dev/null 
mv  $tempDir/docs/*.md $targetDir/doc/models/ > /dev/null 

# Cleanup
rm -rf $tempDir > /dev/null 

# Format generated code etc.
pushd "$targetDir" && make after-gen && popd
