@echo off
chcp 65001
echo.
cd %~dp0

%SYSTEMROOT%\py.exe -V > NUL 2>&1
IF %ERRORLEVEL% neq 0 goto reattempt
if exist "config.ini" (
    %SYSTEMROOT%\py.exe -m pipenv run python WebcamMonitor.py
) else (
    %SYSTEMROOT%\py.exe -m pipenv run python camutils.py
    echo "initialized 'config.ini'. Please configure the file before running the program."
)
PAUSE
goto end

:reattempt
py.exe -V > NUL 2>&1
if %ERRORLEVEL% neq 0 goto message
if exist "config.ini" (
    py.exe -m pipenv run python WebcamMonitor.py
) else (
    py.exe -m pipenv run python camutils.py
    echo "initialized 'config.ini'. Please configure the file before running the program."
)
PAUSE
goto end

:message
echo "There is no valid Python 3.13.0 or higher available. Please install Python ^>=3.13.0."
PAUSE

:end