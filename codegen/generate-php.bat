cls
set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-php

rem set specSource=http://localhost:47972/v3.0/barcode/swagger/spec
rem set specSource=https://api-qa.aspose.cloud/v3.0/barcode/swagger/spec
rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

if exist %tempDir% del /s /q %tempDir% > NUL || goto :error
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l php -t Templates\php -o %tempDir% -c config.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l php -t Templates\php -o %tempDir% -c config.json > debugOperations.php.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l php -t Templates\php -o %tempDir% -c config.json > debugModels.php.json || goto :error

Tools\SplitPhpCodeFile.exe %tempDir%\SwaggerClient-php\lib\Api\BarcodeApi.php %tempDir%\SwaggerClient-php\lib\Requests\ || goto :error

del /s /q "%targetDir%\src\Aspose\Barcode\*Api.php" > NUL || goto :error
xcopy %tempDir%\SwaggerClient-php\lib\Api %targetDir%\src\Aspose\Barcode /i /y || goto :error
xcopy %tempDir%\SwaggerClient-php\lib %targetDir%\src\Aspose\Barcode /i /y || goto :error

del /s /q "%targetDir%\src\Aspose\Barcode\Model\" > NUL || goto :error
xcopy %tempDir%\SwaggerClient-php\lib\Model %targetDir%\src\Aspose\Barcode\Model /i /y || goto :error

del /s /q "%targetDir%\src\Aspose\Barcode\Requests\" > NUL || goto :error
xcopy %tempDir%\SwaggerClient-php\lib\Requests %targetDir%\src\Aspose\Barcode\Requests /i /y || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
xcopy /s /i /y %tempDir%\SwaggerClient-php\docs %targetDir%\docs || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error
