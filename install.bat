@echo off
echo Setting up Conda environment automatically...

:: ==== WINDOWS SIDE SETUP ====

:: Step 1: Check if Conda exists using where
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo Conda not found. Installing Miniconda...

    powershell -Command "Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile 'Miniconda3.exe'"
    start /wait Miniconda3.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\Miniconda3
    del Miniconda3.exe

    :: Update current session's PATH (don’t mandate any path)
    set "PATH=%PATH%;%USERPROFILE%\Miniconda3;%USERPROFILE%\Miniconda3\Scripts"
)

:: Step 2: Activate GWeasy environment
call conda --version >nul 2>nul || (
    echo Conda still not found after install. Exiting.
    exit /b 1
)

echo Conda is available. Proceeding...

call conda env list | findstr /C:"GWeasy" >nul
if %errorlevel% neq 0 (
    echo Creating GWeasy environment from environment.yml...
    call conda env create -f environment.yml
) else (
    echo GWeasy environment already exists.
)

call conda activate GWeasy
call pip install -r requirements.txt

:: ==== WSL SIDE SETUP ====

:: Step 3: Install Miniconda in WSL if not installed
wsl bash -c "[ ! -d \$HOME/miniconda ] && echo 'Installing Miniconda in WSL...' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && bash ~/miniconda.sh -b -p \$HOME/miniconda && rm ~/miniconda.sh || echo 'Miniconda is already installed in WSL.'"
::wsl sudo apt-get install libc6-dev::
wsl bash -c "COND=\$(command -v conda); if [ -x \"\$COND\" ]; then echo '✅ Found Conda at: '\$COND; else COND=\$HOME/miniconda/bin/conda; echo '⚠️ Using fallback Conda at: '\$COND; fi; [ -x \"\$COND\" ] && \$COND list | grep -q omicron || \$COND install -c conda-forge omicron -y"

:: ==== RUN FINAL SCRIPT ====
call conda activate GWeasy
python GWeasy.py

echo.
echo ✅ All done!
exit
