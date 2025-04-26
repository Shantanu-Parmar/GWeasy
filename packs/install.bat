@echo off
setlocal enabledelayedexpansion

:: Elevate if needed
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

:: Paths
set "USER_HOME=C:\Users\%USERNAME%"
set "WSL_IMAGE=GWeasywsl.tar"
set "IMAGE_PATH=%~dp0%WSL_IMAGE%"

echo [INFO] Installing WSL from: %IMAGE_PATH%
"%SystemRoot%\System32\wsl.exe" --import GWeasyWSL "%USER_HOME%\GWeasyWSL" "%IMAGE_PATH%"

IF %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] WSL installation complete!
) ELSE (
    echo [ERROR] WSL installation failed with error level: %ERRORLEVEL%
)

pause
