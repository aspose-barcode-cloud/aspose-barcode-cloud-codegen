cls

set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\submodules\go

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l go
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json > debugModels.go.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l go -t Templates\go -o %tempDir% -c config-go.json > debugOperations.go.json || goto :error

del /s /q "%targetDir%\barcode" > NUL || goto :error
rmdir /s /q  "%targetDir%\barcode" > NUL || goto :error

mkdir "%targetDir%\barcode\jwt" > NUL || goto :error
move /y "%tempDir%\response.go" "%targetDir%\barcode\jwt\jwt.go" > NUL || goto :error

move /y "%tempDir%\*.go" "%targetDir%\barcode\" > NUL || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
move /y "%tempDir%\docs\*" "%targetDir%\docs\" > NUL || goto :error
move /y "%tempDir%\README.md" "%targetDir%\README.md" > NUL || goto :error
copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

pushd "%targetDir%" && wsl make after-gen & popd
