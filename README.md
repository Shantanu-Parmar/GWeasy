# GWeasy

## GWeasy: Multiplatform GUI Software for Gravitational Wave Data Analysis

### **Overview**
<iframe width="560" height="315" src="https://www.youtube.com/embed/WbjKwl0-VA0?si=Lbzc76FiiRq6LxEm" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
**GWeasy** is a user-friendly, GUI-based software designed to streamline the process of **fetching, analyzing, and visualizing gravitational wave (GW) data**. This software aims to reduce the complexity of installing and running GW analysis tools by integrating all necessary software requirements into a single, easy-to-use platform.

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

Many astrophysicists spend more time setting up the software than analyzing the data. **GWeasy** aims to **eliminate this technical barrier**, allowing researchers to focus on their primary goal: **gravitational wave science**.

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
## Download or Clone the Repository  
Download the ZIP file or clone the repository from:  
[https://github.com/Shantanu909/GWeasy](https://github.com/Shantanu909/GWeasy)  
Alternatively, download a prepackaged bundle of all libararies for WSL and conda within windows through:
[https://drive.google.com/drive/folders/1P4sjy4w6m63KSCEu4XFm3C9VN7iWJUlK](https://drive.google.com/drive/folders/1P4sjy4w6m63KSCEu4XFm3C9VN7iWJUlK)

## Run the Installer  
- Open a terminal, navigate to the downloaded directory, and run:  
  ```sh
  install.bat
  ```
- Alternatively, you can simply double-click `install.bat`.
  ------------------------------------
- If you are working with the prepackaged bundle,follow the same steps by running install.bat
- This is unpack a conda envrionment with all libraries except Omicron
- Omicron is in the wsl.tar.gz, a Linux image that will be extracted into your wsl as a separate distro
- Password for wsl is omicronuser or omicron.
## First-Time Setup  
- The initial run of `install.bat` may take some time, depending on your internet speed, as it installs dependencies and sets up the environment.  
- After installation, you can reuse `install.bat` as an executable launcher for now. Exe setup coming up soon.

## Verification

---

### 1. Running a Test in the Gravfetch Tab
To perform a test run:
- Select **`test.csv`** as the time segment input.
- Select **`4KCHANS.csv`** as the channels input.
- Optionally, specify an output directory. By default, GWEasy will create a folder named `gwfout` in the same directory.

![Gravfetch Tab](https://github.com/user-attachments/assets/e1a0d90a-5e6e-4828-bec1-f00df2352ab0)

Once execution starts, a completion message will appear in the terminal, indicating a successful run. Processing time varies (~5-7 minutes) depending on the number of time segments and channels selected. To speed up testing, start with a single time segment and channel.

![Execution Completion](https://github.com/user-attachments/assets/ac8725ca-4924-466c-9bff-7bb7a3f5d4aa)

### 2. Running Omicron Analysis
After generating `gwf` files, switch to the **Omicron** tab to proceed with analysis.

![Omicron Tab](https://github.com/user-attachments/assets/e1a0d90a-5e6e-4828-bec1-f00df2352ab0)

#### Configuring Omicron Settings
If you have worked with **Omicron configuration files**, this setup will feel familiar:

![Omicron Config](https://github.com/user-attachments/assets/9b928017-f844-4bf4-9810-da309442b438)

**Steps:**
1. **Set Channel & Sampling Rate First** (due to an existing UI issue, these must be configured before modifying other fields).
2. Channels are pre-populated based on the **Gravfetch** output, but you can also manually enter any channel name.

![Channel Selection](https://github.com/user-attachments/assets/f93af41a-59cf-4d1b-a9a5-afd9ff075a33)

3. **Select the `.ffl` files** corresponding to each channel. These are located in the **`gwfout`** directory or your chosen output path. Each channel has an `.ffl` file listing all time segments.
4. Use the **Custom Segments** feature to manually specify time segments for analysis if needed.

![Custom Segments](https://github.com/user-attachments/assets/50fcbae3-4685-4f20-80ba-98fd88dca8a8)

5. Once all fields are filled, specify an output directory (default: `Omicronout`).
6. Click **Save Config** to generate a configuration file with the selected inputs.

![Save Config](https://github.com/user-attachments/assets/279a8508-e12e-4e64-93bc-679bc56aa4eb)

7. Press **Start Omicron** to begin processing. Upon successful execution, a completion message will be displayed in the terminal.

![Omicron Execution](https://github.com/user-attachments/assets/7fb1b036-c71b-4e96-816a-b954491f0b47)

---
Additonal tabs

![image](https://github.com/user-attachments/assets/5255dcde-fcd2-4dcd-a59c-074b6588bd01)

![image](https://github.com/user-attachments/assets/9c5b8f3f-48d8-4114-9873-044423973a8d)

![image](https://github.com/user-attachments/assets/abb221ec-b5b9-4266-9e3e-4b35bffa1fb7)


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
### 🚀 **Join the GWeasy Project – Making Gravitational Wave Analysis Accessible to All!** 🚀

