@echo off
setlocal

if exist ".\data\escapemap\function" rmdir /s /q ".\data\escapemap\function"

call mcscript compile -fullErr

ren ".\data\escapemap\functions" "function"

xcopy "C:\Users\v22ju\curseforge\minecraft\Instances\EscapeMap_1.21.4\saves\EscapeMap\datapacks\escapemap" "C:\Users\v22ju\Desktop\coding\mcoffline\run\saves\EscapeMap\datapacks\escapemap" /s /e /r /y

echo Done.
endlocal