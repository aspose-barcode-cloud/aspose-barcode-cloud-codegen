cls

rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\submodules\node

if exist %tempDir% del /s /q %tempDir% || goto :error
rem java -jar Tools\swagger-codegen-cli.jar config-help -l typescript-node
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json > debugModels.ts.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json > debugOperations.ts.json || goto :error

copy "%tempDir%\api.ts" "%targetDir%\src\" /y || goto :error
copy "%tempDir%\package.json" "%targetDir%\" /y || goto :error

REM Use typescript-node one more time because typescript-node does not generate docs
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json > debugModels.docs.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json > debugOperations.docs.json || goto :error

copy "%tempDir%\docs\api.ts" "%targetDir%\docs\index.md" /y || goto :error
copy "%tempDir%\docs\git_push.sh" "%targetDir%\docs\models.md" /y || goto :error
copy "%tempDir%\docs\tsconfig.json" "%targetDir%\README.md" /y || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

pushd "%targetDir%" && wsl make format & popd
