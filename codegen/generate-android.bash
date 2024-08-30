#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/android"
targetDir="../submodules/android"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/openapi-generator-cli.jar config-help -l android ; exit 1
java -jar Tools/openapi-generator-cli.jar generate -i "${specSource}" -g android -t Templates/android -o $tempDir -c config-android.json
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g android -t Templates/java -o $tempDir -c config-android.json > debugModels.android.json
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g android -t Templates/java -o $tempDir -c config-android.json > debugOperations.android.json

mv "$tempDir/README.md" "$targetDir"
mv "$tempDir/.gitignore" "$targetDir"
mv "$tempDir/build.gradle" "$targetDir"
mv "$tempDir/git_push.sh" "$targetDir/gradle.properties"
mv "$tempDir/pom.xml" "$targetDir/settings.gradle"
mv "$tempDir/gradlew" "$targetDir/app/build.gradle"

mv "$tempDir/src/main/AndroidManifest.xml" "$targetDir/app/src/main/"

exampleDir="$targetDir/app/src/main/java/com/aspose/barcode/cloud/demo_app"
rm -rf ${exampleDir:?}/*
mkdir -p "$exampleDir" || true
mv "$tempDir/src/main/java/com/aspose/barcode/cloud/demo_app/ApiException.java" "$exampleDir/MainActivity.kt"

cp ../LICENSE "$targetDir/"

rm -rf $tempDir
