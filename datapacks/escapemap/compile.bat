@echo off
setlocal

if exist ".\data\escapemap\function" rmdir /s /q ".\data\escapemap\function"

call mcscript compile -fullErr

ren ".\data\escapemap\functions" "function"

echo Done.
endlocal