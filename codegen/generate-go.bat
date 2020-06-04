cls

rem set specSource=http://localhost:47972/v3.0/barcode/swagger/spec
rem set specSource=https://api-qa.aspose.cloud/v3.0/barcode/swagger/spec
rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-go

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l go
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-python-go.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-python-go.json > debugModels.go.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-python-go.json > debugOperations.go.json || goto :error

del /s /q "%targetDir%\aspose_barcode_cloud\" > NUL || goto :error
copy "%tempDir%\*.go" "%targetDir%\aspose_barcode_cloud\" /y > NUL || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
xcopy "%tempDir%\docs\*" "%targetDir%\docs\" /e /i /y > NUL || goto :error

copy "%tempDir%\README.md" "%targetDir%\README.md" /y > NUL || goto :error

rem del /s /q %tempDir% > NUL || goto :error
rem rmdir /s /q  %tempDir% > NUL || goto :error
