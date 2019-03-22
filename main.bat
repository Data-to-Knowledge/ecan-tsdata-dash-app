@echo on
echo started %date% %time% >> %~dp0\backup.log
call activate dash-map-ts >> %~dp0\backup.log
call python %~dp0\main.py >> %~dp0\backup.log
