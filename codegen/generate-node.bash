#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"
tempDir=".generated/node"
targetDir="../submodules/node"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# typescript-node does not generate docs on its own, so the SDK's models.ts,
# docs and README are emitted as user-defined supporting files (see the "files"
# section in config-node.json). This keeps everything in a single generator run.
# java -jar Tools/openapi-generator-cli.jar config-help -g typescript-node
java -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g typescript-node -t Templates/nodejs -o $tempDir -c config-node.json
# java -DdebugModels -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g typescript-node -t Templates/nodejs -o $tempDir -c config-node.json > debugModels.ts.json; exit
# java -DdebugOperations -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g typescript-node -t Templates/nodejs -o $tempDir -c config-node.json > debugOperations.ts.json; exit
# java -DdebugSupportingFiles -jar Tools/openapi-generator-cli.jar generate -i "$specSource" -g typescript-node -t Templates/nodejs -o $tempDir -c config-node.json 2> debugSupportingFiles.ts.txt

mv "$tempDir/api.ts" "$targetDir/src/"
mv "$tempDir/src/models.ts" "$targetDir/src/models.ts"
mv "$tempDir/package.json" "$targetDir/"
mv "$tempDir/docs/index.md" "$targetDir/docs/index.md"
mv "$tempDir/docs/models.md" "$targetDir/docs/models.md"
mv "$tempDir/README.template" "$targetDir/README.template"
cp ../LICENSE "$targetDir/"
cp ../scripts/check-badges.bash "$targetDir/scripts/"

rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
