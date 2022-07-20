cls

set specSource=..\spec\aspose-barcode-cloud.json
set tempDir=.generated\dart

set targetDir=..\submodules\dart

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l dart & exit
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugModels.dart.json & exit
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json > debugOperations.dart.json & exit
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l dart -t Templates\dart -o %tempDir% -c config-dart.json || goto :error


copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error
move /y "%tempDir%\README.md" "%targetDir%" > NUL || goto :error
move /y "%tempDir%\.gitignore" "%targetDir%\" > NUL || goto :error
move /y "%tempDir%\pubspec.yaml" "%targetDir%\" > NUL || goto :error


del /s /q "%targetDir%\lib\" > NUL || mkdir "%targetDir%\lib\" > NUL || goto :error

move /y "%tempDir%\lib\*.dart" "%targetDir%\lib\" > NUL || goto :error

mkdir "%targetDir%\lib\model\" > NUL
move /y "%tempDir%\lib\model\*.dart" "%targetDir%\lib\model\" > NUL || goto :error
mkdir "%targetDir%\lib\api\" > NUL
move /y "%tempDir%\lib\api\*.dart" "%targetDir%\lib\api\" > NUL || goto :error

mkdir "%targetDir%\lib\auth\"
move /y "%tempDir%\lib\auth\authentication.dart" "%targetDir%\lib\auth\" > NUL || goto :error
move /y "%tempDir%\lib\auth\oauth.dart" "%targetDir%\lib\auth\" > NUL || goto :error


del /s /q "%targetDir%\doc\" > NUL
rmdir /s /q  "%targetDir%\doc\" > NUL
mkdir "%targetDir%\doc\api\" > NUL || goto :error
move /y "%tempDir%\docs\*Api.md" "%targetDir%\doc\api\" > NUL || goto :error
mkdir "%targetDir%\doc\models\" > NUL || goto :error
move /y "%tempDir%\docs\*.md" "%targetDir%\doc\models\" > NUL || goto :error

rem Cleanup
del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

rem Format generated code etc.
pushd "%targetDir%" && wsl make after-gen & popd
