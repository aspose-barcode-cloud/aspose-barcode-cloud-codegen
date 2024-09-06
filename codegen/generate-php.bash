#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/php"
targetDir="../submodules/php"

if [ -d "${tempDir}" ];
then
     rm -rf "${tempDir}"
fi

# java -jar Tools/openapi-generator-cli.jar config-help -g php ; exit 1
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "${specSource}" -g php -t Templates/php -o "${tempDir}" -c config-php.json > debugModels.php.json; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "${specSource}" -g php -t Templates/php -o "${tempDir}" -c config-php.json > debugOperations.php.json; exit
java -jar Tools/openapi-generator-cli.jar generate -i "${specSource}" -g php -t Templates/php -o "${tempDir}" -c config-php.json

python Tools/split-php-file.py "${tempDir}/lib/Api/GenerateApi.php" "${tempDir}/lib/Requests/"
python Tools/split-php-file.py "${tempDir}/lib/Api/ScanApi.php" "${tempDir}/lib/Requests/"
python Tools/split-php-file.py "${tempDir}/lib/Api/RecognizeApi.php" "${tempDir}/lib/Requests/"
# python Tools/split-php-file.py "${tempDir}/lib/Api/StorageApi.php" "${tempDir}/lib/Requests/"

rm -f "${targetDir}/src/Aspose/BarCode/"*Api.php
mv "${tempDir}/lib/Api/"* "${targetDir}/src/Aspose/BarCode"
mv "${tempDir}/lib/"*.php "${targetDir}/src/Aspose/BarCode"

rm -f "${targetDir}/src/Aspose/BarCode/Model/"*
mv "${tempDir}/lib/Model/"* "${targetDir}/src/Aspose/BarCode/Model"

rm -f "${targetDir}/src/Aspose/BarCode/Requests/"*
mv "${tempDir}/lib/Requests/"* "${targetDir}/src/Aspose/BarCode/Requests/"

rm -rf "${targetDir}/docs/"*
mv "${tempDir}/docs/"* "${targetDir}/docs"

mv "${tempDir}/README.md" "${targetDir}/README.template"
cp ../LICENSE "${targetDir}/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"


rm -rf "${tempDir}"

pushd "${targetDir}" && make after-gen && popd >/dev/null
