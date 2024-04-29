#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/java"
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

rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/api/*
mv $tempDir/src/main/java/com/aspose/barcode/cloud/api/* $targetDir/src/main/java/com/aspose/barcode/cloud/api
rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/model/*
mv $tempDir/src/main/java/com/aspose/barcode/cloud/model/* $targetDir/src/main/java/com/aspose/barcode/cloud/model
rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/requests/*
mv $tempDir/src/main/java/com/aspose/barcode/cloud/requests/* $targetDir/src/main/java/com/aspose/barcode/cloud/requests
rm -f $targetDir/src/main/java/com/aspose/barcode/cloud/*.java
# Ignore some files
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/GzipRequestInterceptor.java"
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/StringUtil.java"
mv $tempDir/src/main/java/com/aspose/barcode/cloud/*.java $targetDir/src/main/java/com/aspose/barcode/cloud

rm -rf ${targetDir}/docs/*
mv $tempDir/docs/* $targetDir/docs

mv $tempDir/README.md $targetDir
mv $tempDir/pom.xml $targetDir
cp ../LICENSE $targetDir
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
