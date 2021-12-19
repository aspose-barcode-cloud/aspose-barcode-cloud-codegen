cls

rem set specSource=https://api.aspose.cloud/v3.0/barcode/swagger/spec
set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\submodules\android

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l android & exit 1
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l android -t Templates\android -o %tempDir% -c config-android.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l android -t Templates\java -o %tempDir% -c config-android.json > debugModels.android.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l android -t Templates\java -o %tempDir% -c config-android.json > debugOperations.android.json || goto :error

copy "%tempDir%\README.md" "%targetDir%" /y > NUL || goto :error
copy "%tempDir%\.gitignore" "%targetDir%" /y > NUL || goto :error
copy "%tempDir%\build.gradle" "%targetDir%" /y > NUL || goto :error
copy "%tempDir%\git_push.sh" "%targetDir%\gradle.properties" /y > NUL || goto :error
copy "%tempDir%\pom.xml" "%targetDir%\settings.gradle" /y > NUL || goto :error
copy "%tempDir%\gradlew" "%targetDir%\app\build.gradle" /y > NUL || goto :error

copy "%tempDir%\src\main\AndroidManifest.xml" "%targetDir%\app\src\main\" /y > NUL || goto :error

del /s /q "%targetDir%\app\src\main\java\com\example\asposebarcodecloud\" > NUL || goto :error
copy "%tempDir%\src\main\java\com\example\asposebarcodecloud\ApiException.java" "%targetDir%\app\src\main\java\com\example\asposebarcodecloud\MainActivity.kt" /y > NUL || goto :error
copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q %tempDir% > NUL || goto :error
