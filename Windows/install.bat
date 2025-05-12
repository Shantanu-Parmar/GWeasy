@echo off
setlocal enabledelayedexpansion

:: Detect Conda path dynamically
for /f "delims=" %%P in ('where conda') do (
    set "CONDA_PATH=%%~dpP"
    goto FOUND_CONDA
)

:FOUND_CONDA
set "CONDA_ROOT=%CONDA_PATH%\.."

echo Using Conda at: %CONDA_ROOT%

:: Initialize Conda properly
call "%CONDA_ROOT%\condabin\conda.bat" init powershell > nul 2>&1

:: Check if GWeasy environment exists
echo Checking for existing GWeasy environment...
call "%CONDA_ROOT%\condabin\conda.bat" info --envs | findstr /C:"GWeasy" > nul
if %errorlevel% neq 0 (
    echo ERROR: GWeasy environment not found! Extracting now...
    mkdir "%CONDA_ROOT%\envs\GWeasy"
    tar -xzf GWeasy.tar.gz -C "%CONDA_ROOT%\envs\GWeasy"
    echo Running conda-unpack...
    call "%CONDA_ROOT%\envs\GWeasy\Scripts\conda-unpack.bat"
) else (
    echo GWeasy environment already exists. Skipping extraction.
)

:: Properly activate the Conda environment
echo Activating GWeasy environment...
call "%CONDA_ROOT%\condabin\conda.bat" activate GWeasy

:: Run Python to confirm
python --version

echo Installation complete

:: ---------- WSL IMAGE INSTALLATION ----------
:INSTALL_WSL_IMAGE
set "USER_HOME=C:\Users\%USERNAME%"
set "WSL_IMAGE=GWeasywsl.tar"

echo Installing WSL from image...
wsl --import GWeasyWSL "%USER_HOME%\GWeasyWSL" "%CD%\%WSL_IMAGE%"


echo WSL installation complete!
pause
call python GWeasy.py
pause
