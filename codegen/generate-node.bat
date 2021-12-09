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
rem java -DdebugSupportingFiles -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json 2> debugSupportingFiles.ts.txt || goto :error

move /y "%tempDir%\api.ts" "%targetDir%\src\" || goto :error
move /y "%tempDir%\package.json" "%targetDir%\" || goto :error
move /y "%tempDir%\git_push.sh" "%targetDir%\src\models.ts" || goto :error

REM Use typescript-node one more time because typescript-node does not generate docs
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json > debugModels.docs.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs\docs -o %tempDir%\docs -c config.json > debugOperations.docs.json || goto :error

move /y "%tempDir%\docs\api.ts" "%targetDir%\docs\index.md" || goto :error
move /y "%tempDir%\docs\git_push.sh" "%targetDir%\docs\models.md" || goto :error
move /y "%tempDir%\docs\tsconfig.json" "%targetDir%\README.md" || goto :error
copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

pushd "%targetDir%" && wsl make format && wsl make lock & popd
