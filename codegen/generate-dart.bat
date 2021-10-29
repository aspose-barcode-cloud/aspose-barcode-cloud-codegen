cls

rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated\dart

set targetDir=..\submodules\dart
set targetDir=..\..\aspose-barcode-cloud-dart

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l dart
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugModels.dart.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugOperations.dart.json || goto :error


copy "%tempDir%\pubspec.yaml" "%targetDir%\barcode\" /y > NUL || goto :error

del /s /q "%targetDir%\barcode\lib\" > NUL || goto :error
rmdir /s /q  "%targetDir%\barcode\lib\" > NUL || goto :error
xcopy "%tempDir%\lib\*" "%targetDir%\barcode\lib\" /e /i /y > NUL || goto :error


pushd "%targetDir%" && dart fix --apply & popd
