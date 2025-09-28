GWeasy
GWeasy is a user-friendly, GUI-based software for fetching, analyzing, and visualizing gravitational wave (GW) data from LIGO and other observatories. It simplifies the setup and execution of GW analysis pipelines like OMICRON, making gravitational wave science accessible to researchers with minimal technical setup.

Overview
GWeasy integrates tools for:

Data Fetching: Retrieve GW data from LIGO databases (Gravfetch tab).
Analysis: Run OMICRON and other pipelines with configurable settings.
Visualization: Display results graphically.
Ease of Use: One-click installation and intuitive GUI for Windows and Linux.

For detailed documentation and usage instructions, visit: https://shantanu-parmar.github.io/GWeasy/
Features

Multi-Platform Support: Windows, Linux (Beta), MacOS (Planned).
Minimal Setup: Pre-built executables for Windows (via WSL) and Linux, or script-based setup.
User-Friendly GUI: Select channels, time segments, and configure pipelines easily.
Pipeline Integration: Supports OMICRON with plans for additional pipelines (e.g., cWB).
Visualization Tools: Built-in plotting for GW data analysis.

Installation
Option 1: Pre-Built Executables

Windows:
Download Omeasy.exe and install.bat from the Releases page.
Download GWeasywsl.tar from Google Drive.
Place install.bat and GWeasywsl.tar in the same directory.
Double-click install.bat to set up WSL and OMICRON.
Run Omeasy.exe for OMICRON analysis.


Linux:
Download GWeasy from the Releases page.
Make executable: chmod +x GWeasy
Run: ./GWeasy



Option 2: Script-Based Setup
For running gweasy.py directly or building from source:

Install Miniconda:

Download Miniconda for Python 3.9 from https://docs.conda.io/en/latest/miniconda.html.


Create Environment:

Place environment.yml and requirements.txt (below) in the same directory as gweasy.py.
Run:conda env create -f environment.yml
conda activate GWeasy
pip install -r requirements.txt




Run GWeasy:
python gweasy.py


Optional: Build Executable:

Install PyInstaller (included in requirements.txt).
Use the provided GWeasy.spec (if available) or generate one:pyinstaller --name GWeasy gweasy.py


Build: pyinstaller GWeasy.spec
Run: .\dist\GWeasy\GWeasy.exe (Windows) or ./dist/GWeasy/GWeasy (Linux).



environment.yml
name: GWeasy
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - python-nds2-client
  - python-framel
  - lalframe
  - lalsuite
  - numpy
  - scipy
  - matplotlib
  - h5py

requirements.txt
pandas
gwpy
PyQt5==5.15.9
requests-pelican
dateparser
pyinstaller

Usage

Gravfetch Tab:

Select test.csv for time segments and 4KCHANS.csv for channels.
Set output directory (default: gwfout).
Click "Download Data" to fetch .gwf files.
Expect 5-7 minutes per channel/segment.


Omicron Tab:

Select a channel from gwfout or enter manually.
Choose the corresponding .ffl file from gwfout.
Configure settings (e.g., sampling rate, frequency range).
Click "Save Config" to generate a config file.
Click "Start Omicron" to run analysis.



For detailed steps and screenshots, refer to: https://shantanu-parmar.github.io/GWeasy/
Contributing

Fork the repository: git clone https://github.com/shantanu-parmar/GWeasy.git
Create a branch: git checkout -b feature-branch
Make changes and commit: git commit -m "Add feature"
Push and create a pull request: git push origin feature-branch
Report issues on the GitHub Issues page.

License
This project is licensed under the MIT License.
Acknowledgments

Lead Developer: Shantanusinh Parmar
Mentors: Dr. Kai Staats, Dr. Marco Cavaglia, Dr. Florent Robinet, Dr. Jonah Kanner
Thanks: LIGO team and GW astrophysics community

Join the GWeasy Project – Simplifying Gravitational Wave Analysis for All!
