cls

rem set specSource=http://localhost:47972/v3.0/barcode/swagger/spec
rem set specSource=https://api-qa.aspose.cloud/v3.0/barcode/swagger/spec
rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-go

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l go
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json > debugModels.go.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json > debugOperations.go.json || goto :error

del /s /q "%targetDir%\barcode" > NUL || goto :error
rmdir /s /q  "%targetDir%\barcode" > NUL || goto :error
mkdir "%targetDir%\barcode\models" > NUL || goto :error
move /y "%tempDir%\model_*.go" "%targetDir%\barcode\models\" > NUL || goto :error
mkdir "%targetDir%\barcode\jwt" > NUL || goto :error
move /y "%tempDir%\response.go" "%targetDir%\barcode\jwt\jwt.go" > NUL || goto :error
copy "%tempDir%\*.go" "%targetDir%\barcode\" /y > NUL || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
xcopy "%tempDir%\docs\*" "%targetDir%\docs\" /e /i /y > NUL || goto :error

copy "%tempDir%\README.md" "%targetDir%\README.md" /y > NUL || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error
