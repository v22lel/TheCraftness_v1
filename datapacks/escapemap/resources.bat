@echo off
setlocal

set "SRC=%CD%\resources"
set "ZIP=%CD%\resources.zip"
set "DEST=%CD%\..\..\resources.zip"

if not exist "%SRC%\" (
    echo Error: resources folder not found in "%CD%"
    exit /b 1
)

if exist "%ZIP%" del /f /q "%ZIP%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Compress-Archive -Path '%SRC%\*' -DestinationPath '%ZIP%' -Force"

if errorlevel 1 (
    echo Error: failed to create resources.zip
    exit /b 1
)

move /y "%ZIP%" "%DEST%"

if errorlevel 1 (
    echo Error: failed to move resources.zip to ..\..\
    exit /b 1
)

echo Done: resources.zip moved to ..\..\
endlocal