#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/php"
targetDir="../submodules/php"

if [ -d "${tempDir}" ];
then
     rm -rf "${tempDir}"
fi

# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "${specSource}" -l php -t Templates/php -o "${tempDir}" -c config.json > debugModels.php.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "${specSource}" -l php -t Templates/php -o "${tempDir}" -c config.json > debugOperations.php.json
java -jar Tools/swagger-codegen-cli.jar generate -i "${specSource}" -l php -t Templates/php -o "${tempDir}" -c config.json

python Tools/split-php-file.py "${tempDir}/SwaggerClient-php/lib/Api/BarcodeApi.php" "${tempDir}/SwaggerClient-php/lib/Requests/"
python Tools/split-php-file.py "${tempDir}/SwaggerClient-php/lib/Api/FileApi.php" "${tempDir}/SwaggerClient-php/lib/Requests/"
python Tools/split-php-file.py "${tempDir}/SwaggerClient-php/lib/Api/FolderApi.php" "${tempDir}/SwaggerClient-php/lib/Requests/"
python Tools/split-php-file.py "${tempDir}/SwaggerClient-php/lib/Api/StorageApi.php" "${tempDir}/SwaggerClient-php/lib/Requests/"

rm -f "${targetDir}/src/Aspose/BarCode/"*Api.php
mv "${tempDir}/SwaggerClient-php/lib/Api/"* "${targetDir}/src/Aspose/BarCode"
mv "${tempDir}/SwaggerClient-php/lib/"*.php "${targetDir}/src/Aspose/BarCode"

rm -f "${targetDir}/src/Aspose/BarCode/Model/"*
mv "${tempDir}/SwaggerClient-php/lib/Model/"* "${targetDir}/src/Aspose/BarCode/Model"

rm -f "${targetDir}/src/Aspose/BarCode/Requests/"*
mv "${tempDir}/SwaggerClient-php/lib/Requests/"* "${targetDir}/src/Aspose/BarCode/Requests/"

rm -rf "${targetDir}/docs/"*
mv "${tempDir}/SwaggerClient-php/docs/"* "${targetDir}/docs"

mv "${tempDir}/SwaggerClient-php/README.md" "${targetDir}/"
cp Templates/LICENSE "${targetDir}/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"


rm -rf "${tempDir}"

pushd "${targetDir}" && make format && popd >/dev/null
