#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated"
targetDir="../submodules/android"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l android & exit 1
java -jar Tools/swagger-codegen-cli.jar generate -i "${specSource}" -l android -t Templates/android -o $tempDir -c config-android.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l android -t Templates/java -o $tempDir -c config-android.json > debugModels.android.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l android -t Templates/java -o $tempDir -c config-android.json > debugOperations.android.json

cp "$tempDir/README.md" "$targetDir"  > /dev/null
cp "$tempDir/.gitignore" "$targetDir"  > /dev/null
cp "$tempDir/build.gradle" "$targetDir"  > /dev/null
cp "$tempDir/git_push.sh" "$targetDir/gradle.properties"  > /dev/null
cp "$tempDir/pom.xml" "$targetDir/settings.gradle"  > /dev/null
cp "$tempDir/gradlew" "$targetDir/app/build.gradle"  > /dev/null

cp "$tempDir/src/main/AndroidManifest.xml" "$targetDir/app/src/main/"  > /dev/null

exampleDir="$targetDir/app/src/main/java/com/example/asposebarcodecloud"
rm -rf "${exampleDir:?}/*" > /dev/null
cp "$tempDir/src/main/java/com/example/asposebarcodecloud/ApiException.java" "$exampleDir/MainActivity.kt"  > /dev/null
cp  Templates/LICENSE "$targetDir/" > /dev/null
rm -rf $tempDir > /dev/null
