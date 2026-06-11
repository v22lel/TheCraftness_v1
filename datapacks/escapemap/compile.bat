@echo off
setlocal

if exist ".\data\escapemap\function" rmdir /s /q ".\data\escapemap\function"

call mcscript compile -fullErr

ren ".\data\escapemap\functions" "function"

del .mcfunction
rmdir /s /q #FILE~1

python .\scripts\post_compile.py

echo Done.
endlocal