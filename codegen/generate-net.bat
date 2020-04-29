cls
set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-dotnet\src
set specSource=..\spec\aspose-barcode-cloud.json

if exist %tempDir% del /s /q %tempDir% || goto :error


rem Generate Operations and Models for Debug purposes
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugOperationsCsharp.json
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugModelsCsharp.json
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json || goto :error
Tools\SplitCSharpCodeFile.exe %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\BarCodeApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error


del /s /q "%targetDir%\Model\" > NUL || goto :error
xcopy "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model" "%targetDir%\Model\" /e /i /y > NUL || goto :error

del /s /q "%targetDir%\Api\*Api.cs" > NUL || goto :error
xcopy "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\*Api.cs" "%targetDir%\Api\" /e /i /y > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q %tempDir% > NUL || goto :error
