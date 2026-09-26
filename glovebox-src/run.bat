@echo off
rem Glovebox launcher for Windows.
rem Double-click, or from a terminal:  run.bat   (any run.py option works)

rem Work from the folder this file lives in, even if the drive letter changes.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 run.py %*
    goto :done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python run.py %*
    goto :done
)

rem Fall back to a Python kept on the stick itself (see README).
if exist "installed\python_embed\python.exe" (
    "installed\python_embed\python.exe" run.py %*
    goto :done
)

echo.
echo Python 3.8 or newer was not found on this computer.
echo Install it from https://www.python.org/downloads/windows/
echo or put an embeddable Python in installed\python_embed\
echo.
pause
exit /b 1

:done
if errorlevel 1 pause
