@echo off
cd /d "%~dp0"
set "SITE_URL=http://localhost:5500"
echo Serving at %SITE_URL% - open this in your browser.
start /B cmd /c "timeout /t 2 /nobreak >nul && start \"\" \"%SITE_URL%\""
python -m http.server 5500
pause
