#!/bin/bash
set -euo pipefail

specSource="../spec/aspose-barcode-cloud.json"

tempDir=".generated/node"
targetDir="../submodules/node"

if [ -d $tempDir ];
then
     rm -rf $tempDir
fi

# java -jar Tools/swagger-codegen-cli.jar config-help -l typescript-node
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs -o $tempDir -c config.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs -o $tempDir -c config.json > debugModels.ts.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs -o $tempDir -c config.json > debugOperations.ts.json
# java -DdebugSupportingFiles -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs -o $tempDir -c config.json 2> debugSupportingFiles.ts.txt

mv  "$tempDir/api.ts" "$targetDir/src/"
mv  "$tempDir/package.json" "$targetDir/"
mv  "$tempDir/git_push.sh" "$targetDir/src/models.ts"

# Use typescript-node one more time because typescript-node does not generate docs
java -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs/docs -o $tempDir/docs -c config.json
# java -DdebugModels -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs/docs -o $tempDir/docs -c config.json > debugModels.docs.json
# java -DdebugOperations -jar Tools/swagger-codegen-cli.jar generate -i "$specSource" -l typescript-node -t Templates/nodejs/docs -o $tempDir/docs -c config.json > debugOperations.docs.json

mv  "$tempDir/docs/api.ts" "$targetDir/docs/index.md"
mv  "$tempDir/docs/git_push.sh" "$targetDir/docs/models.md"
mv  "$tempDir/docs/tsconfig.json" "$targetDir/README.md"
cp  Templates/LICENSE "$targetDir/"


rm -rf $tempDir

pushd "$targetDir" && make after-gen && popd >/dev/null
