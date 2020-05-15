cls

rem set specSource=http://localhost:47972/v3.0/barcode/swagger/spec
rem set specSource=https://api-qa.aspose.cloud/v3.0/barcode/swagger/spec
rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-node\src

if exist %tempDir% del /s /q %tempDir% || goto :error
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json > debugModels.ts.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json > debugOperations.ts.json || goto :error

xcopy "%tempDir%\api.ts" "%targetDir%\api.ts" /e /i /y || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error
