cls

rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=C:\Users\Denex\aspose\aspose-barcode-cloud-java

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l java
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l java -t Templates\java -o %tempDir% -c config-java.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l java -t Templates\java -o %tempDir% -c config-java.json > debugModels.java.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l java -t Templates\java -o %tempDir% -c config-java.json > debugOperations.java.json || goto :error

del /s /q "%targetDir%\src\main\" > NUL || goto :error
xcopy "%tempDir%\src\main\java\com\aspose\barcode\cloud\api" "%targetDir%\src\main\java\com\aspose\barcode\cloud\api" /e /i /y > NUL || goto :error
xcopy "%tempDir%\src\main\java\com\aspose\barcode\cloud\model" "%targetDir%\src\main\java\com\aspose\barcode\cloud\model" /e /i /y > NUL || goto :error
copy "%tempDir%\src\main\java\com\aspose\barcode\cloud\*.java" "%targetDir%\src\main\java\com\aspose\barcode\cloud" /y > NUL || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
xcopy "%tempDir%\docs" "%targetDir%\docs" /e /i /y > NUL || goto :error

xcopy "%tempDir%\README.md" "%targetDir%\" /y > NUL || goto :error
copy Templates\LICENSE "%targetDir%\" /y > NUL || goto :error
xcopy "%tempDir%\pom.xml" "%targetDir%\" /y > NUL || goto :error

del /s /q %tempDir% > NUL || goto :error
rmdir /s /q %tempDir% > NUL || goto :error

pushd "%targetDir%" && wsl make format & popd
