@echo off
echo Setting up Conda environment on Windows...

:: Check if Conda is installed on Windows
call conda --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Conda is not installed on Windows. Please install Anaconda or Miniconda manually.
    exit /b 1
)

:: Check if Windows Conda environment 'GWeasy' exists
call conda env list | findstr /C:"GWeasy" >nul
if %errorlevel% neq 0 (
    echo Creating Windows GWeasy environment...
    call conda env create -f environment.yml
) else (
    echo GWeasy environment already exists in Windows.
)
pause

:: WSL Setup
echo Checking for WSL...
wsl echo "WSL is available."
pause

:: Ensure Miniconda is installed in WSL (User Directory)
wsl bash -c "[ ! -d $HOME/miniconda ] && echo 'Installing Miniconda in WSL...' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && bash ~/miniconda.sh -b -p $HOME/miniconda && rm ~/miniconda.sh || echo 'Miniconda is already installed in WSL.'"
pause

:: Ensure Miniconda is in PATH permanently
wsl bash -c "echo 'export PATH=$HOME/miniconda/bin:$PATH' >> ~/.bashrc && echo 'export PATH=$HOME/miniconda/bin:$PATH' >> ~/.profile"
pause

:: Apply PATH changes for this session and install Omicron
wsl bash -c "export PATH=$HOME/miniconda/bin:$PATH && $HOME/miniconda/bin/conda install -c conda-forge omicron -y"
pause

echo WSL setup done.

:: Ensure Windows Conda environment has necessary packages
call conda activate GWeasy 
call pip install -r requirements.txt

:: Run Python script (LAST STEP)
python GWeasy.py

pause >nul
