#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/php"
targetDir="../submodules/php"

if [ -d $tempDir ]; 
then
     rm -rf $tempDir 
fi

# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l php -t Templates/php -o "$tempDir" -c config.json > debugModels.php.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l php -t Templates/php -o "$tempDir" -c config.json > debugOperations.php.json
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l php -t Templates/php -o "$tempDir" -c config.json

python Tools/split-php-file.py "$tempDir/SwaggerClient-php/lib/Api/BarcodeApi.php" $tempDir/SwaggerClient-php/lib/Requests/
python Tools/split-php-file.py "$tempDir/SwaggerClient-php/lib/Api/FileApi.php" $tempDir/SwaggerClient-php/lib/Requests/
python Tools/split-php-file.py "$tempDir/SwaggerClient-php/lib/Api/FolderApi.php" $tempDir/SwaggerClient-php/lib/Requests/
python Tools/split-php-file.py "$tempDir/SwaggerClient-php/lib/Api/StorageApi.php" $tempDir/SwaggerClient-php/lib/Requests/

rm -f $targetDir/src/Aspose/Barcode/*Api.php > /dev/null
cp $tempDir/SwaggerClient-php/lib/Api/* $targetDir/src/Aspose/Barcode
cp $tempDir/SwaggerClient-php/lib/*.* $targetDir/src/Aspose/Barcode

rm -rf $targetDir/src/Aspose/Barcode/Model/* > /dev/null
cp  $tempDir/SwaggerClient-php/lib/Model/* $targetDir/src/Aspose/Barcode/Model

rm -rf $targetDir/src/Aspose/Barcode/Requests/* > /dev/null
cp -r $tempDir/SwaggerClient-php/lib/Requests/* $targetDir/src/Aspose/Barcode/Requests

rm -rf $targetDir/docs/* > /dev/null
cp -r $tempDir/SwaggerClient-php/docs/* $targetDir/docs

cp "$tempDir/SwaggerClient-php/README.md" "$targetDir/" 
cp  Templates/LICENSE "$targetDir/" > /dev/null


rm -rf "$tempDir" > /dev/null

pushd "$targetDir" && make format && popd
