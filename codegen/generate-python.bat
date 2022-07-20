cls

set specSource=..\spec\aspose-barcode-cloud.json

set tempDir=.generated
set targetDir=..\submodules\python

if exist %tempDir% del /s /q %tempDir% || goto :error

rem java -jar Tools\swagger-codegen-cli.jar config-help -l python
java -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l python -t Templates\python -o %tempDir% -c config-python.json || goto :error
rem java -DdebugModels -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l python -t Templates\python -o %tempDir% -c config-python.json > debugModels.py.json || goto :error
rem java -DdebugOperations -jar Tools\swagger-codegen-cli.jar generate -i "%specSource%" -l python -t Templates\python -o %tempDir% -c config-python.json > debugOperations.py.json || goto :error

del /s /q "%targetDir%\aspose_barcode_cloud\" > NUL || goto :error
xcopy "%tempDir%\aspose_barcode_cloud\*" "%targetDir%\aspose_barcode_cloud\" /e /i /y > NUL || goto :error

del /s /q "%targetDir%\docs\" > NUL || goto :error
xcopy "%tempDir%\docs\*" "%targetDir%\docs\" /e /i /y > NUL || goto :error

copy "%tempDir%\setup.py" "%targetDir%\setup.py" /y > NUL || goto :error
copy "%tempDir%\requirements.txt" "%targetDir%\requirements.txt" /y > NUL || goto :error
copy "%tempDir%\test-requirements.txt" "%targetDir%\test-requirements.txt" /y > NUL || goto :error
copy "%tempDir%\tox.ini" "%targetDir%\tox.ini" /y > NUL || goto :error
copy "%tempDir%\README.md" "%targetDir%\README.md" /y > NUL || goto :error
copy /y Templates\LICENSE "%targetDir%\" > NUL || goto :error


del /s /q %tempDir% > NUL || goto :error
rmdir /s /q  %tempDir% > NUL || goto :error

pushd "%targetDir%" && wsl make format & popd
