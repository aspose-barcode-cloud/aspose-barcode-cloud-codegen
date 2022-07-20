cls

set tempDir=.generated\dotnet
set targetDir=..\submodules\dotnet

set specSource=..\spec\aspose-barcode-cloud.json

if exist %tempDir% del /f /s /q %tempDir% || goto :error

REM Generate Operations and Models for Debug purposes
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugOperations.cs.json & exit
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json > debugModels.cs.json & exit
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l csharp -t Templates\csharp -o %tempDir% -c config.json || goto :error

python Tools\split-cs-file.py %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\BarCodeApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
python Tools\split-cs-file.py %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\FileApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
python Tools\split-cs-file.py %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\FolderApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error
python Tools\split-cs-file.py %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\StorageApi.cs %tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model\Requests\ || goto :error

copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error
copy /y Templates\LICENSE "%targetDir%\src\LICENSE.txt" > NUL || goto :error

rmdir /s /q "%targetDir%\src\Model\" > NUL || goto :error
move /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Model" "%targetDir%\src" > NUL || goto :error

del /f /s /q "%targetDir%\src\Api\*Api.cs" > NUL || goto :error
move /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Api\*.cs" "%targetDir%\src\Api\" > NUL || goto :error
move /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Client\Configuration.cs" "%targetDir%\src\Api\" > NUL || goto :error

rmdir /s /q "%targetDir%\docs" > NUL || goto :error
move /y "%tempDir%\docs" "%targetDir%\" > NUL || goto :error

move /y "%tempDir%\README.md" "%targetDir%\README.template" > NUL || goto :error
move /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk\Aspose.BarCode.Cloud.Sdk.csproj" "%targetDir%\src\Aspose.BarCode.Cloud.Sdk.csproj" > NUL || goto :error
copy /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk.Test\Aspose.BarCode.Cloud.Sdk.Test.csproj" "%targetDir%\examples\GenerateQR\GenerateQR.csproj" > NUL || goto :error
copy /y "%tempDir%\src\Aspose.BarCode.Cloud.Sdk.Test\Aspose.BarCode.Cloud.Sdk.Test.csproj" "%targetDir%\examples\ReadQR\ReadQR.csproj" > NUL || goto :error


rem rmdir /s /q %tempDir% > NUL || goto :error
pushd "%targetDir%" && wsl make after-gen & popd
