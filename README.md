# ECLIPTA FORGE - GW DatFetch

## GW DatFetch: Multiplatform GUI Software for Gravitational Wave Data Analysis

### **Overview**
**ECLIPTA FORGE** is a user-friendly, GUI-based software designed to streamline the process of **fetching, analyzing, and visualizing gravitational wave (GW) data**. This software aims to reduce the complexity of installing and running GW analysis tools by integrating all necessary software requirements into a single, easy-to-use platform.

### **Project Details**
- **Project Timeline:** February - April 2025
- **Lead Developer:** Shantanusinh Parmar
- **Supervisor:** Prof. Chandrasinh Parmar
- **Target Platforms:** Windows (initially), Linux (future compatibility planned)
- **Primary Software Components:**
  - LIGO data fetching
  - OMICRON analysis pipeline
  - User-friendly GUI
  - Visualization tools
  - One-click installation and setup

---
## **1. Introduction**
The **Laser Interferometer Gravitational-Wave Observatory (LIGO)** operates **four detectors** and collects data across **six runs**, with over **300 channels**, multiple sampling rates, and countless time segments. This raw time-series GW data is then analyzed using various pipelines such as:
- **OMICRON**
- **Coherent WaveBurst (cWB)**
- **Matched filtering**
- **Fourier transforms**

Currently, setting up the software environment for such analyses is a major challenge. The goal of this project is to simplify this process by creating a GUI-based tool that can handle everything—from **installation to execution**—without requiring extensive technical knowledge.

---
## **2. Background & Motivation**
While working with GW data, I encountered numerous challenges, spending over **10 weeks** resolving library conflicts, configuring environment files, and understanding poorly documented installation processes. Through collaboration with scientists, developers, and LIGO repository maintainers, I finally managed to get the **correct workflow** established.

This experience highlighted the need for a **user-friendly, platform-independent tool** that can:
- Automate the **installation** of required dependencies.
- Manage **multiple pipelines** with ease.
- Provide an **intuitive GUI** for data selection, analysis, and visualization.
- Offer a **one-click** install and execution process.

Many astrophysicists spend more time setting up the software than analyzing the data. **GW DatFetch** aims to **eliminate this technical barrier**, allowing researchers to focus on their primary goal: **gravitational wave science**.

---
## **3. Features & Functionalities**
### **✔ Multi-Platform Support**
- **Windows (initial release)**
- **Linux (future support planned)**

### **✔ Automated Setup & Installation**
- **Installs and configures** all necessary software components.
- **Manages dependencies** within a Conda environment.
- **Single executable (.exe) for Windows** with future plans for .msi installer.

### **✔ User-Friendly GUI**
- **Data fetching** from LIGO databases.
- **Channel selection and configuration**.
- **Pipeline execution for OMICRON and other analyses**.
- **Graphical visualization** of results.
- **Format conversion tools**.

### **✔ Additional Features**
- **Convert GW data to audio**.
- **Black hole merger visualizations**.

---
## **4. Installation & Dependencies**
### **Conda Environment Setup**
GW DatFetch relies on **Conda** for package and environment management. To install the required dependencies, follow these steps:

#### **Step 1: Set Up the Main Environment (Windows/Linux)**
```sh
conda create --name GWeasy python=3.8
conda activate GWeasy
```
#### **Step 2: Install Required Packages**
```sh
conda install conda-forge::omicron
conda install conda-forge::gwpy
conda install conda-forge::gwosc
conda install conda-forge::nds2-client
conda install conda-forge::python-nds2-client
conda install anaconda::pandas
conda install conda-forge::python-framel
pip install PyQt5 PIL cefPython3 sys threading subprocess os tkinter
```

#### **Step 3: Set Up the OMICRON Environment (WSL/Linux)**
```sh
conda create --name omicron python=3.8
conda activate omicron
```

### **Building the Executable (Windows Only)**
To generate a standalone `.exe` file, use **PyInstaller**:
```sh
pip install pyinstaller
pyinstaller --onefile --windowed --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageTk GWeasy.py
```
The executable will be found in the `dist/` directory.

---
## **5. Development Timeline**
| Task | Expected Completion |
|-------|------------------|
| **Project Start** | February 2025 |
| **Workflow Documentation** | March 2025 |
| **Prototype Development** | Mid-March 2025 |
| **Windows Version Testing** | April 2025 |
| **Linux Version Development** | Future Update |

## **6. Future Enhancements**
- **Cross-platform compatibility (Linux & MacOS)**
- **Expanded support for additional pipelines**
- **Real-time visualization improvements**

## **7. Contributors**
- **Shantanusinh Parmar** (Lead Developer)
- **Prof. Chandrasinh Parmar** (Project Supervisor)

## **8. License**
This project is open-source under the **MIT License**.

---
## **9. Acknowledgments**
Special thanks to the **Dr. Marco Cavaglia, Dr. Kai Staats, Dr. Florent Robinet, Dr. Jonah Kranner**, and thanks to the **LIGO team**, pipeline developers, and all researchers contributing to the field of **gravitational wave astrophysics**. Your work makes this project possible.

---
## **10. How to Contribute**
If you’d like to contribute:
1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/yourusername/GWeasy.git`
3. **Create a new branch**: `git checkout -b feature-branch`
4. **Make your changes and commit**
5. **Push to your fork and create a pull request**

For any issues, feel free to open a GitHub **issue**!

---
### 🚀 **Join the GW DatFetch Project – Making Gravitational Wave Analysis Accessible to All!** 🚀

