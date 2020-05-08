cls
set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-node\src

if exist %tempDir% del /s /q %tempDir% || goto :error
java -jar Tools\swagger-codegen-cli.jar generate -i ..\spec\aspose-barcode-cloud.json -l typescript-node -t Templates\nodejs -o %tempDir% -c config.json || goto :error

xcopy "%tempDir%\api.ts" "%targetDir%\api.ts" /e /i /y || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error
