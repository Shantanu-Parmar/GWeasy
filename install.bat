@echo off
echo Setting up Conda environment on Windows...

:: Step 1: Check if Conda is installed on Windows
call conda --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Conda is not installed on Windows. Downloading and installing Miniconda...
    
    :: Download Miniconda installer
    powershell -Command "Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile 'Miniconda3.exe'"
    
    :: Install Miniconda silently
    start /wait Miniconda3.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\Miniconda3
    
    :: Remove installer
    del Miniconda3.exe
    
    :: Add Miniconda to PATH temporarily for this session
    set "PATH=%USERPROFILE%\Miniconda3\Scripts;%USERPROFILE%\Miniconda3;%PATH%"
)


echo Conda is installed on Windows.

:: Step 2: Check if GWeasy Conda environment exists on Windows
call conda env list | findstr /C:"GWeasy" >nul
if %errorlevel% neq 0 (
    echo Creating Windows GWeasy environment...
    call conda env create -f environment.yml
) else (
    echo GWeasy environment already exists in Windows.
)

:: Step 3: Check for WSL
echo Checking for WSL...
wsl echo "WSL is available."

:: Step 4: Ensure Miniconda is installed in WSL if not present
wsl bash -c "[ ! -d $HOME/miniconda ] && echo 'Installing Miniconda in WSL...' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && bash ~/miniconda.sh -b -p $HOME/miniconda && rm ~/miniconda.sh || echo 'Miniconda is already installed in WSL.'"

:: Step 5: Ensure Miniconda is in PATH permanently in WSL
wsl bash -c "if ! grep -q 'miniconda' ~/.bashrc; then echo 'export PATH=\$HOME/miniconda/bin:\$PATH' >> ~/.bashrc; fi"

:: Step 6: Apply changes to PATH and install Omicron (if not installed)
wsl bash -c "source ~/.bashrc && conda activate base && conda list | grep -q omicron || conda install -c conda-forge omicron -y"

echo WSL setup done.

:: Step 7: Ensure Windows Conda environment has necessary packages
call conda activate GWeasy 
call pip install -r requirements.txt

:: Step 8: Run Python script (LAST STEP)
python GWeasy.py

pause >nul
