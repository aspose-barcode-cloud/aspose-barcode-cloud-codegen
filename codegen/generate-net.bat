cls
set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-dotnet

rem set specSource=http://localhost:47972/v3.0/barcode/swagger/spec
rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

if exist %tempDir% del /s /q %tempDir% || goto :error


REM Generate Operations and Models for Debug purposes
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugOperations.cs.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugModels.cs.json || goto :error
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json || goto :error

Tools\SplitCSharpCodeFile.exe %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\BarCodeApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
Tools\SplitCSharpCodeFile.exe %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\FileApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
Tools\SplitCSharpCodeFile.exe %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\FolderApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
Tools\SplitCSharpCodeFile.exe %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\StorageApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error


del /s /q "%targetDir%\src\Model\" > NUL || goto :error
xcopy "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model" "%targetDir%\src\Model\" /e /i /y > NUL || goto :error

del /s /q "%targetDir%\src\Api\*Api.cs" > NUL || goto :error
xcopy "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\*Api.cs" "%targetDir%\src\Api\" /e /i /y > NUL || goto :error

del /s /q "%targetDir%\docs" > NUL || goto :error
xcopy "%tempDir%\docs" "%targetDir%\docs" /e /i /y > NUL || goto :error

xcopy "%tempDir%\README.md" "%targetDir%\" /y > NUL || goto :error
xcopy "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Aspose.BarCode.Cloud.Sdk.csproj" "%targetDir%\src\Aspose.BarCode.Cloud.Sdk.csproj" /y > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q %tempDir% > NUL || goto :error
