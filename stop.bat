@echo off
echo Stopping Split Screen Prompt Paste...
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq Split*" >nul 2>&1
REM Also kill by script name if running via python.exe
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%app.py%%'" get processid /value 2^>nul ^| find "="') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo Done.
timeout /t 2
