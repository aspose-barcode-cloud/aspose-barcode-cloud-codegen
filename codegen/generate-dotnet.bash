#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated/dotnet"
targetDir="../submodules/dotnet"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# Generate Operations and Models for Debug purposes
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l csharp -t Templates/csharp -o $tempDir -c config.json > debugOperations.cs.json ; exit
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l csharp -t Templates/csharp -o $tempDir -c config.json > debugModels.cs.json ; exit
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l csharp -t Templates/csharp -o $tempDir -c config.json

python Tools/split-cs-file.py $tempDir/src/Aspose.BarCode.Cloud.Sdk/Api/BarcodeApi.cs $tempDir/src/Aspose.BarCode.Cloud.Sdk/Model/Requests/
python Tools/split-cs-file.py $tempDir/src/Aspose.BarCode.Cloud.Sdk/Api/FileApi.cs $tempDir/src/Aspose.BarCode.Cloud.Sdk/Model/Requests/
python Tools/split-cs-file.py $tempDir/src/Aspose.BarCode.Cloud.Sdk/Api/FolderApi.cs $tempDir/src/Aspose.BarCode.Cloud.Sdk/Model/Requests/
python Tools/split-cs-file.py $tempDir/src/Aspose.BarCode.Cloud.Sdk/Api/StorageApi.cs $tempDir/src/Aspose.BarCode.Cloud.Sdk/Model/Requests/

cp ../LICENSE "$targetDir/"
cp ../LICENSE "$targetDir/src/LICENSE.txt"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf "$targetDir/src/Model/"
mv "$tempDir/src/Aspose.BarCode.Cloud.Sdk/Model" "$targetDir/src"

rm -rf $targetDir/src/Api/*Api.cs
mv $tempDir/src/Aspose.BarCode.Cloud.Sdk/Api/*.cs $targetDir/src/Api/
mv $tempDir/src/Aspose.BarCode.Cloud.Sdk/Client/Configuration.cs $targetDir/src/Api/

rm -rf "$targetDir/docs"
mv "$tempDir/docs" "$targetDir/"

mv "$tempDir/README.md" "$targetDir/README.template"
mv "$tempDir/src/Aspose.BarCode.Cloud.Sdk/Aspose.BarCode.Cloud.Sdk.csproj" "$targetDir/src/Aspose.BarCode.Cloud.Sdk.csproj"
cp "$tempDir/src/Aspose.BarCode.Cloud.Sdk.Test/Aspose.BarCode.Cloud.Sdk.Test.csproj" "$targetDir/examples/GenerateQR/GenerateQR.csproj"
cp "$tempDir/src/Aspose.BarCode.Cloud.Sdk.Test/Aspose.BarCode.Cloud.Sdk.Test.csproj" "$targetDir/examples/ReadQR/ReadQR.csproj"


rm -rf $tempDir
pushd "$targetDir" && make after-gen && popd >/dev/null
