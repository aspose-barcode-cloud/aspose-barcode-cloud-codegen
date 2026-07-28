#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/java"
targetDir="../submodules/java"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/openapi-generator-cli.jar config-help -l java
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g java -t Templates/java -o $tempDir -c config-java.json
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g java -t Templates/java -o $tempDir -c config-java.json > debugModels.java.json ; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g java -t Templates/java -o $tempDir -c config-java.json > debugOperations.java.json ; exit
# java -DdebugSupportingFiles -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g java -t Templates/java -o $tempDir -c config-java.json > DdebugSupportingFiles.java.json ; exit

python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/GenerateApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/ScanApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/RecognizeApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/
# python Tools/split-java-file.py $tempDir/src/main/java/com/aspose/barcode/cloud/api/StorageApi.java $tempDir/src/main/java/com/aspose/barcode/cloud/requests/

rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/api/*
mv $tempDir/src/main/java/com/aspose/barcode/cloud/api/* $targetDir/src/main/java/com/aspose/barcode/cloud/api
rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/model/*
# AbstractOpenApiSchema: oneOf/anyOf scaffolding this spec never uses (no polymorphic models).
rm -f "$tempDir/src/main/java/com/aspose/barcode/cloud/model/AbstractOpenApiSchema.java"
mv $tempDir/src/main/java/com/aspose/barcode/cloud/model/* $targetDir/src/main/java/com/aspose/barcode/cloud/model
rm -rf $targetDir/src/main/java/com/aspose/barcode/cloud/requests/*
mv $tempDir/src/main/java/com/aspose/barcode/cloud/requests/* $targetDir/src/main/java/com/aspose/barcode/cloud/requests
rm -f $targetDir/src/main/java/com/aspose/barcode/cloud/*.java
# Ignore some files
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/GzipRequestInterceptor.java"
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/StringUtil.java"
# ServerConfiguration/ServerVariable: multi-server URL scaffolding; ApiClient uses a single fixed base path.
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/ServerConfiguration.java"
rm "$tempDir/src/main/java/com/aspose/barcode/cloud/ServerVariable.java"
mv $tempDir/src/main/java/com/aspose/barcode/cloud/*.java $targetDir/src/main/java/com/aspose/barcode/cloud

rm -rf ${targetDir}/docs/*
mv $tempDir/docs/* $targetDir/docs

mv "$tempDir/README.md" "$targetDir/README.template"
mv $tempDir/pom.xml $targetDir
cp ../LICENSE $targetDir
cp ../scripts/check-badges.bash "$targetDir/scripts/"

mv "$tempDir/dependency.xml" "$targetDir/snippets/dependency.xml"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
