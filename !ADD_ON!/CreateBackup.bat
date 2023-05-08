REM 24.06.2022 -> 2022.06.24
set datestr=%date:~6,4%%date:~3,2%%date:~0,2%

REM 07:40:33,333 -> 074033
set timestr=%time:~0,2%%time:~3,2%%time:~6,2%

"C:\Program Files\7-Zip\7z.exe" a "..\..\Backup\NozzleScope\NozzleScope_%datestr%-%timestr%.7z" @CreateBackup.txt