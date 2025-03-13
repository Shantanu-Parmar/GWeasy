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
## Download or Clone the Repository  
Download the ZIP file or clone the repository from:  
[https://github.com/Shantanu909/GWeasy](https://github.com/Shantanu909/GWeasy)  

## Run the Installer  
- Open a terminal, navigate to the downloaded directory, and run:  
  ```sh
  install.bat
  ```
- Alternatively, you can simply double-click `install.bat`.

## First-Time Setup  
- The initial run of `install.bat` may take some time, depending on your internet speed, as it installs dependencies and sets up the environment.  
- After installation, you can reuse `install.bat` as an executable launcher for now. Exe setup coming up soon.

## Verification
A succesful setup will launch a window like this:
![image](https://github.com/user-attachments/assets/84124f67-21e0-41c5-a926-83a15f8944e1)

Then, to run test on the gravfetch tab, select test.csv for time segement input and 4KCHANS.csv for channels input. You can set output path, by default a new folder called gwfout in same directory will be created.
![image](https://github.com/user-attachments/assets/e1a0d90a-5e6e-4828-bec1-f00df2352ab0)

A successful initiation and message to terminal about execution finished or added to ffl will indicate succesful run. This might take some time ~5-7 mins as time segment 2 for chan 2 is a bit longer. Alternatively you can just run it on one time segment and/or on 1 channel to begin with.
![image](https://github.com/user-attachments/assets/ac8725ca-4924-466c-9bff-7bb7a3f5d4aa)

Once gwf files are created, we can switch over to the Omicron tab to verify its working.
![image](https://github.com/user-attachments/assets/3d5e3aba-e804-4540-bde5-530d1eaeac54)

If you have worked with OMICRON config files, the setup will feel familiar:
![image](https://github.com/user-attachments/assets/9b928017-f844-4bf4-9810-da309442b438)

The values can be now filled with channel and sampling rate to be done first(there's a glitch where those two have to be worked on before values can be put in other fields, working on it). there's a dropdown for some values, for eg the channel's are autopopulated upon run of gravfetch so it will have all channels from previous runs. Alternativelty, you can type in any channel name.
![image](https://github.com/user-attachments/assets/f93af41a-59cf-4d1b-a9a5-afd9ff075a33)

Next, we will select the ffl files, these can be found within each channel within the gwfout or your path for the gwf files. Typically, eahc channel has a ffl file describing all time segments. You can build a custom ffl within a channel by use of custom segments button that let's user choose the time segments for omicron analysis.
![image](https://github.com/user-attachments/assets/50fcbae3-4685-4f20-80ba-98fd88dca8a8)

Once that is done, all fields filled, and the output path set or kept as defualt Omicronout, click on the Save config. This will create a config file with input values
![image](https://github.com/user-attachments/assets/279a8508-e12e-4e64-93bc-679bc56aa4eb)

That's it, press on start omicron and if all goes well, the terminal after processing would show successful execution.
![image](https://github.com/user-attachments/assets/7fb1b036-c71b-4e96-816a-b954491f0b47)


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

