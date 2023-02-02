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

python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/BarCodeApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/FileApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/FolderApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/StorageApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/

rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/api/*" > /dev/null
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/api/* $targetDir/src/main/java/com/aspose/barcode/cloud/api  > /dev/null
rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/model/*" > /dev/null
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/model/* $targetDir/src/main/java/com/aspose/barcode/cloud/model  > /dev/null
rm -rf "$targetDir/src/main/java/com/aspose/barcode/cloud/requests/*" > /dev/null
cp -r $tempDir/src/main/java/com/aspose/barcode/cloud/requests/* $targetDir/src/main/java/com/aspose/barcode/cloud/requests  > /dev/null
rm -f $targetDir/src/main/java/com/aspose/barcode/cloud/*.java > /dev/null
cp $tempDir/src/main/java/com/aspose/barcode/cloud/*.java $targetDir/src/main/java/com/aspose/barcode/cloud  > /dev/null

rm -rf "$targetDir/docs/*" > /dev/null
cp $tempDir/docs/* $targetDir/docs  > /dev/null

cp $tempDir/README.md $targetDir  > /dev/null
cp $tempDir/pom.xml $targetDir  > /dev/null
cp  Templates/LICENSE $targetDir > /dev/null


rm -rf $tempDir > /dev/null

pushd "$targetDir" && make format && popd
