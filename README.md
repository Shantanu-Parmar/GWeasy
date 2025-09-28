# GWeasy

**GWeasy** is a user-friendly, GUI-based software for **fetching, analyzing, and visualizing gravitational wave (GW) data** from LIGO and other observatories. It simplifies the setup and execution of GW analysis pipelines like OMICRON, making gravitational wave science accessible to researchers with minimal technical setup.

[![YouTube Demo](https://github.com/user-attachments/assets/d6054686-f59f-4ba9-a407-a137eaca1222)](https://www.youtube.com/watch?v=WbjKwl0-VA0)

## Overview

GWeasy integrates tools for:
- **Data Fetching**: Retrieve GW data from LIGO databases (Gravfetch tab).
- **Analysis**: Run OMICRON and other pipelines with configurable settings.
- **Visualization**: Display results graphically.
- **Ease of Use**: One-click installation and intuitive GUI for Windows and Linux.

For detailed documentation and usage instructions, visit: [https://shantanu-parmar.github.io/GWeasy/](https://shantanu-parmar.github.io/GWeasy/)

## Features

- **Multi-Platform Support**: Windows, Linux (Beta), MacOS (Planned).
- **Minimal Setup**: Pre-built executables for Windows (via WSL) and Linux, or script-based setup.
- **User-Friendly GUI**: Select channels, time segments, and configure pipelines easily.
- **Pipeline Integration**: Supports OMICRON with plans for additional pipelines (e.g., cWB).
- **Visualization Tools**: Built-in plotting for GW data analysis.

## Installation

### Option 1: Pre-Built Executables
- **Windows**:
  1. Download `Omeasy.exe`from the Gweasy website [GWeasy](https://shantanu-parmar.github.io/GWeasy/installation.html).
  2. Enjoy.....
  If you want to run Omicron also, follow steps 3 onwards
  3. Download `GWeasywsl.tar` and 'install.bat' from Gweasy website [GWeasy](https://shantanu-parmar.github.io/GWeasy/installation.html).
  4. Place `install.bat` and `GWeasywsl.tar` in a same directory.
  5. Double-click `install.bat` to set up WSL and OMICRON.
  6. Run `Omeasy.exe` for OMICRON analysis.

- **Linux**:
  1. Download `GWeasy` from the [Releases](https://github.com/shantanu-parmar/GWeasy/releases) page.
  2. Make executable: `chmod +x GWeasy`
  3. Run: `./GWeasy`

### Option 2: Script-Based Setup
For running `gweasy.py` directly or building from source:

1. **Install Miniconda**:
   - Download Miniconda from [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html).

2. **Create Environment**:
   - Place `environment.yml` and `requirements.txt` (below) in the same directory as `gweasy.py` from this repository (you dont need to get any other files).
   - Run:
     ```bash
     conda env create -f environment.yml
     conda activate GWeasy
     pip install -r requirements.txt
     ```

3. **Run GWeasy**:
   ```bash
   python gweasy.py
   ```

#### environment.yml
For windows
```yml
name: GWeasy
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - python-nds2-client
  - python-framel
```

For Linux/Mac
```yml
name: GWeasy
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - python-nds2-client
  - lalframe
```

#### requirements.txt
```text
pandas
gwpy
PyQt5
requests-pelican
```

## Usage

1. **Gravfetch Tab**:
   - Select `test-times.csv` for time segments and `test-chans.csv` for channels from this repository /tests.
   - Set output directory (default: `gwfout`).
   - Click "Download Data" to fetch `.gwf` files.
   - Expect 5-7 minutes per channel/segment.

2. **Omicron Tab**:
   - Select a channel from `gwfout` or enter manually.
   - Click on Custom segs and choose all time segments you would like. 
   - Configure parameters (e.g., sampling rate, frequency range).
   - Click "Save Config" to generate a config file.
   - Click "Start Omicron" to run analysis.

For detailed steps and screenshots, refer to: [https://shantanu-parmar.github.io/GWeasy/](https://shantanu-parmar.github.io/GWeasy/)

## Contributing

1. Fork the repository: `git clone https://github.com/shantanu-parmar/GWeasy.git`
2. Create a branch: `git checkout -b feature-branch`
3. Make changes and commit: `git commit -m "Add feature"`
4. Push and create a pull request: `git push origin feature-branch`
5. Report issues on the [GitHub Issues](https://github.com/shantanu-parmar/GWeasy/issues) page.

## License

This project is licensed under the **MIT License**.

## Acknowledgments

- **Lead Developer**: Shantanusinh Parmar
- **Mentors**: Dr. Marco Cavaglia, Dr. Florent Robinet, Dr. Jonah Kanner, Mr. Kai Staats, 
- **Testing**: Mr. Federico Romeo
- **Thanks**: LIGO team and GW astrophysics community

**Join the GWeasy Project – Simplifying Gravitational Wave Analysis for All!**
