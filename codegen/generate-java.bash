#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated"
targetDir="../submodules/java"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l java
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l java -t Templates/java -o $tempDir -c config-java.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l java -t Templates/java -o $tempDir -c config-java.json > debugModels.java.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l java -t Templates/java -o $tempDir -c config-java.json > debugOperations.java.json
# java -DdebugSupportingFiles -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l java -t Templates/java -o $tempDir -c config-java.json > DdebugSupportingFiles.java.json

python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/BarcodeApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/FileApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/FolderApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/StorageApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/

rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/api/*"
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/api/* $targetDir/src/main/java/com/aspose/barcode/cloud/api
rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/model/*"
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/model/* $targetDir/src/main/java/com/aspose/barcode/cloud/model
rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/requests/*"
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/requests/* $targetDir/src/main/java/com/aspose/barcode/cloud/requests
rm -f $targetDir/src/main/java/com/aspose/barcode/cloud/*.java
cp $tempDir/src/main/java/com/aspose/barcode/cloud/*.java $targetDir/src/main/java/com/aspose/barcode/cloud

rm -rf "$targetDir/docs/*"
cp $tempDir/docs/* $targetDir/docs

cp $tempDir/README.md $targetDir
cp $tempDir/pom.xml $targetDir
cp  Templates/LICENSE $targetDir


rm -rf $tempDir

pushd "$targetDir" && make format && popd >/dev/null
