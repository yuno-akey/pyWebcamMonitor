@echo off
chcp 65001
echo.
cd %~dp0

%SYSTEMROOT%\py.exe -V > NUL 2>&1
IF %ERRORLEVEL% neq 0 goto reattempt
%SYSTEMROOT%\py.exe -m pip install --upgrade pip
%SYSTEMROOT%\py.exe -m pip install pipenv
%SYSTEMROOT%\py.exe -m pipenv install
echo "Installation complete. Please run run.bat to start the program."
PAUSE
goto end

:reattempt
py.exe -V > NUL 2>&1
if %ERRORLEVEL% neq 0 goto message
py.exe -m pip install --upgrade pip
py.exe -m pip install pipenv
py.exe -m pipenv install
echo "Installation complete. Please run run.bat to start the program."
PAUSE
goto end

:message
echo "There is no valid Python 3.13.0 or higher available. Please install Python ^>=3.13.0."
PAUSE

:end