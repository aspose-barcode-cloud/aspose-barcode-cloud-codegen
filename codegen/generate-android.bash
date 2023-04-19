#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/android"
targetDir="../submodules/android"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l android & exit 1
java -jar Tools/swagger-codegen-cli.jar generate -i "${specSource}" -l android -t Templates/android -o $tempDir -c config-android.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l android -t Templates/java -o $tempDir -c config-android.json > debugModels.android.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l android -t Templates/java -o $tempDir -c config-android.json > debugOperations.android.json

cp "$tempDir/README.md" "$targetDir"
cp "$tempDir/.gitignore" "$targetDir"
cp "$tempDir/build.gradle" "$targetDir"
cp "$tempDir/git_push.sh" "$targetDir/gradle.properties"
cp "$tempDir/pom.xml" "$targetDir/settings.gradle"
cp "$tempDir/gradlew" "$targetDir/app/build.gradle"

cp "$tempDir/src/main/AndroidManifest.xml" "$targetDir/app/src/main/"

exampleDir="$targetDir/app/src/main/java/com/aspose/barcode/cloud/demo_app"
rm -rf "${exampleDir:?}/*"
mkdir -p "$exampleDir" || true
cp "$tempDir/src/main/java/com/aspose/barcode/cloud/demo_app/ApiException.java" "$exampleDir/MainActivity.kt"
cp  Templates/LICENSE "$targetDir/"
rm -rf $tempDir
