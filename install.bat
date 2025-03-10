@echo off
echo Setting up Conda environment automatically...

:: ==== Step 1: Check if Conda is installed on Windows ====
call conda --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Conda not found. Installing Miniconda silently...

    powershell -Command "Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' -OutFile 'Miniconda3.exe'"
    start /wait Miniconda3.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\Miniconda3
    del Miniconda3.exe

    :: Add Miniconda to PATH
    setx PATH "%USERPROFILE%\Miniconda3\Scripts;%USERPROFILE%\Miniconda3;%PATH%"
    set "PATH=%USERPROFILE%\Miniconda3\Scripts;%USERPROFILE%\Miniconda3;%PATH%"
)

echo Conda is installed on Windows.

:: ==== Step 2: Ensure GWeasy Conda Environment Exists ====
call conda env list | findstr /C:"GWeasy" >nul
if %errorlevel% neq 0 (
    echo Creating GWeasy environment...
    call conda env create -f environment.yml
) else (
    echo GWeasy environment already exists.
)
call conda activate GWeasy
call pip install -r requirements.txt

:: ==== Step 3: Ensure Miniconda is Installed in WSL (Root Mode) ====
wsl -u root bash -c "[ ! -d $HOME/miniconda ] && echo 'Installing Miniconda in WSL...' && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && bash ~/miniconda.sh -b -p $HOME/miniconda && rm ~/miniconda.sh || echo 'Miniconda is already installed in WSL.'"

:: ==== Step 4: Ensure Conda is in PATH in WSL (Root Mode) ====
wsl -u root bash -c "echo 'export PATH=$HOME/miniconda/bin:\$PATH' >> ~/.bashrc && echo 'export PATH=$HOME/miniconda/bin:\$PATH' >> ~/.bash_profile"
wsl -u root bash -c "source ~/.bashrc"

:: ==== Step 5: Ensure Omicron is Installed in WSL (Root Mode) ====
wsl -u root bash -ic "conda init && conda activate base && conda list | grep -q omicron || conda install -c conda-forge omicron -y"

echo WSL setup completed.

:: ==== Step 6: Run GWeasy Python Script ====
call conda activate GWeasy
python GWeasy.py

echo Installation & execution complete!
exit
