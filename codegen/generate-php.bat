cls
set tempDir=.generated
set targetDir=..\..\aspose-barcode-cloud-php\src

if exist %tempDir% del /s /q %tempDir% || goto :error
java -jar Tools\swagger-codegen-cli.jar generate -i ..\spec\aspose-barcode-cloud.json -l php -t Templates\php -o %tempDir% -c config.json || goto :error

Tools\SplitPhpCodeFile.exe %tempDir%\SwaggerClient-php\lib\Api\BarCodeApi.php %tempDir%\SwaggerClient-php\lib\Requests\ || goto :error

xcopy %tempDir%\SwaggerClient-php\lib\Api %targetDir%\Aspose\BarCode /i /y || goto :error
xcopy %tempDir%\SwaggerClient-php\lib %targetDir%\Aspose\BarCode /i /y || goto :error

del /s /q "%targetDir%\Aspose\BarCode\Model\" > NUL || goto :error
xcopy %tempDir%\SwaggerClient-php\lib\Model %targetDir%\Aspose\BarCode\Model /i /y || goto :error

del /s /q "%targetDir%\Aspose\BarCode\Requests\" > NUL || goto :error
xcopy %tempDir%\SwaggerClient-php\lib\Requests %targetDir%\Aspose\BarCode\Requests /i /y || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error
