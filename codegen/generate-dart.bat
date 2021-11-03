cls

rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json
set tempDir=.generated\dart

set targetDir=..\submodules\dart
set targetDir=..\..\flutter\aspose-barcode-cloud-dart

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l dart
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugModels.dart.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugOperations.dart.json || goto :error


mkdir "%targetDir%\barcode\" > NUL
move /y "%tempDir%\pubspec.yaml" "%targetDir%\barcode\" > NUL || goto :error
move /y "%tempDir%\.gitignore" "%targetDir%\" > NUL || goto :error

del /s /q "%targetDir%\barcode\lib\" > NUL
rmdir /s /q  "%targetDir%\barcode\lib\" > NUL

mkdir "%targetDir%\barcode\lib\" > NUL || goto :error
move /y "%tempDir%\lib\*.dart" "%targetDir%\barcode\lib\" > NUL || goto :error

mkdir "%targetDir%\barcode\lib\model\" > NUL || goto :error
move /y "%tempDir%\lib\model\*.dart" "%targetDir%\barcode\lib\model\" > NUL || goto :error

mkdir "%targetDir%\barcode\lib\api\" > NUL || goto :error
move /y "%tempDir%\lib\api\*.dart" "%targetDir%\barcode\lib\api\" > NUL || goto :error

mkdir "%targetDir%\barcode\lib\auth\" > NUL || goto :error
move /y "%tempDir%\lib\auth\authentication.dart" "%targetDir%\barcode\lib\auth\" > NUL || goto :error
move /y "%tempDir%\lib\auth\oauth.dart" "%targetDir%\barcode\lib\auth\" > NUL || goto :error


rem Cleanup
del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

rem Format generated code etc.
pushd "%targetDir%" && dart fix --apply && dart format . & popd
