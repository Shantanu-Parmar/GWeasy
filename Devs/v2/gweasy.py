import os
import sys
import logging
import socket
import time
import subprocess
import json
import threading
import pandas as pd
from gwpy.timeseries import TimeSeries
from gwosc.datasets import find_datasets
from gwosc.locate import get_urls
from datetime import datetime
from scipy.signal import get_window
import argparse
import shutil
import platform
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLineEdit, QFileDialog, QLabel, QCheckBox,
                             QTextEdit, QScrollArea, QFrame, QSlider, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, QMetaObject, QGenericArgument, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QPainter
from PyQt5.QtWidgets import QDialog

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    conda_env = os.path.join(bundle_dir, 'conda_env')
    site_packages = os.path.join(conda_env, 'Lib', 'site-packages')
    dll_dir = os.path.join(conda_env, 'Library', 'bin')
    sys.path.append(site_packages)
    os.add_dll_directory(dll_dir)
    print(f"sys.path: {sys.path}")
    print(f"DLL dir: {dll_dir}")
    try:
        ctypes.WinDLL(os.path.join(dll_dir, 'libframel.dll'))
        print("libframel.dll loaded successfully")
    except OSError as e:
        print(f"Failed to load libframel.dll: {e}")
# ANSI color codes for CLI output
COLORS = {
    "reset": "\033[0m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m"
}

# Set up logging to a file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('GWeasy_log.txt'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure the path to the shared library is added to the system path
if getattr(sys, 'frozen', False):
    lib_path = os.path.join(sys._MEIPASS, 'libframel.so' if sys.platform.startswith('linux') else 'libframel.dll')
    os.environ['FRAME_LIB_PATH'] = lib_path
else:
    os.environ['FRAME_LIB_PATH'] = os.path.expanduser('~/miniconda3/envs/GWeasy/lib/')

logging.debug(f"FRAME_LIB_PATH is set to: {os.environ['FRAME_LIB_PATH']}")

# Create default GWFout directory at launch
DEFAULT_GWFOUT = "./GWFout"
if not os.path.exists(DEFAULT_GWFOUT):
    os.makedirs(DEFAULT_GWFOUT, exist_ok=True)
    logging.info(f"Created default output directory: {DEFAULT_GWFOUT}")

HISTORY_FILE = "gravfetch_history.json"
DEFAULT_CONFIG = """DATA CHANNELS\t
DATA FFL\t
DATA SAMPLEFREQUENCY\t4096
PARAMETER TIMING\t0.1 1.0
PARAMETER FREQUENCYRANGE\t10 1000
PARAMETER QRANGE\t4 100
PARAMETER MISMATCHMAX\t0.2
PARAMETER SNRTHRESHOLD\t8
PARAMETER PSDLENGTH\t10
OUTPUT DIRECTORY\t./output
OUTPUT FORMAT\troot
OUTPUT PRODUCTS\ttriggers html
OUTPUT VERBOSITY\t1
"""

# Grok-themed color scheme
COLOR_BG_TOP = "#D4D7D8"  # Pearlescent white, 50% brightness
COLOR_BG_BOTTOM = "#101718"  # Shiny black
COLOR_TAB = "#FFFFFFFF"
COLOR_FG = "#00B7EB"  # Electric blue for all text
COLOR_ACCENT = "#FFFFFF"  # Darkened gray for buttons and borders
COLOR_HOVER = "#1C2526"  # Shiny black for hover
COLOR_SUCCESS = "#28A745"  # Keep green for success
COLOR_ERROR = "#DC3545"  # Keep red for errors
COLOR_WARNING = "#FFC107"  # Keep yellow for warnings

FONT_HEADER = QFont("Helvetica", 14, QFont.Bold)
FONT_LABEL = QFont("Helvetica", 14, QFont.Bold)
FONT_BUTTON = QFont("Helvetica", 12, QFont.Bold)
FONT_TERMINAL = QFont("Consolas", 12)

class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(COLOR_BG_BOTTOM))  # Shiny black at top
        gradient.setColorAt(1, QColor(COLOR_BG_TOP))     # Dulled white at bottom
        painter.fillRect(self.rect(), QBrush(gradient))

class TerminalWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(FONT_TERMINAL)
        palette = self.palette()
        palette.setColor(QPalette.Base, QColor('#000000'))  # Pitch black
        palette.setColor(QPalette.Text, QColor(COLOR_FG))   # Electric blue
        self.setPalette(palette)
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #A9A9A9;
                border-radius: 5px;
                padding: 5px;
            }
        """)

    def append_output(self, message, level="info"):
        colors = {"error": COLOR_ERROR, "success": COLOR_SUCCESS, "warning": COLOR_WARNING, "info": COLOR_FG}
        color = colors.get(level, COLOR_FG)
        self.append(f'<span style="color:{color}">{message}</span>')
        logging.log(
            {"error": logging.ERROR, "success": logging.INFO, "warning": logging.WARNING, "info": logging.INFO}[level],
            message
        )


class SplashScreen(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.setWindowTitle("GWeasy")
        self.setFixedSize(400, 250)
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.callback = callback

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        logo = QLabel("GWeasy", self)
        logo.setFont(QFont("Helvetica", 24, QFont.Bold))
        logo.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CED4DA;
                border-radius: 5px;
                text-align: center;
                background-color: #1C2526;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #CED4DA;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress)

        version = QLabel("Version 2.0", self)
        version.setFont(FONT_LABEL)
        version.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self.setLayout(layout)
        self.setStyleSheet(f"background-color: {COLOR_BG_BOTTOM};")

        self.progress_value = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)  # 5 seconds = 5000ms / 50ms = 100 steps

    def update_progress(self):
        self.progress_value += 1
        self.progress.setValue(self.progress_value)
        if self.progress_value >= 100:
            self.timer.stop()
            self.close()
            self.callback()

class MainWindow(QMainWindow):
    def __init__(self, cli_mode=False):
        super().__init__()
        self.terminal = None
        self.cli_mode = cli_mode
        if not cli_mode:
            self.init_ui()

    def init_ui(self):
        self.setWindowTitle("GWeasy")
        self.setGeometry(100, 100, 1024, 768)

        self.terminal = TerminalWidget(self)
        self.tabs = QTabWidget()
        grav_tab = GravfetchApp(self.tabs, self.append_output)
        omicron_tab = OmicronApp(self.tabs, self.append_output)
        omiviz_tab = GradientWidget()  # Placeholder for Omiviz

        self.tabs.addTab(grav_tab, "Gravfetch")
        self.tabs.addTab(omicron_tab, "OMICRON")
        self.tabs.addTab(omiviz_tab, "Omiviz")

        main_widget = GradientWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.terminal)
        main_layout.setStretch(0, 3)
        main_layout.setStretch(1, 1)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #1C2526, stop:1 #747576);
            }
            QTabWidget::pane {
                border: 1px solid #A9A9A9;
                border-radius: 2px;
                margin-right: 4px;
            }
            QTabBar::tab {
                background: #B0B0B0;
                color: #005566;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 12px;
                min-width: 110px;
                width: auto;
                text-align: center;
                white-space: nowrap;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #D3D3D3;
                color: #005566;
                font-size: 14px;
                font-weight: bold;
                padding: 6px 12px;
                min-width: 110 px;
                width: auto;
                text-align: center;
                white-space: nowrap;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
        """)

    def append_output(self, message, level="info"):
        if self.terminal:
            self.terminal.append_output(message, level)
        else:
            color = {"error": COLORS["red"], "success": COLORS["green"], "warning": COLORS["yellow"], "info": COLORS["blue"]}.get(level, "")
            print(f"{color}{message}{COLORS['reset']}")
        logging.log(
            {"error": logging.ERROR, "success": logging.INFO, "warning": logging.WARNING, "info": logging.INFO}[level],
            message
        )



########################################################################################################################################
############################################################    GRAVFETCH    ###########################################################
########################################################################################################################################
class GravfetchApp(GradientWidget):
    def __init__(self, parent, append_output_callback):
        super().__init__(parent)
        os.environ['GW_DATAFIND_URL_TYPE'] = 'file'
        self.time_csv_file = ""
        self.channel_csv_file = ""
        self.gwfout_path = DEFAULT_GWFOUT
        self.execution_running = False
        self.process = None
        self.loaded_channels = []
        self.time_ranges = None
        self.selected_channel = None
        self.selected_segments = []
        self.channel_to_rate = {}
        self.selected_frametype = None
        self.selected_host = None
        self.append_output = append_output_callback

        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
                    self.gwfout_path = history.get("gwfout_path", DEFAULT_GWFOUT)
            except Exception as e:
                self.append_output(f"Failed to read history file: {e}", "error")

        self.setup_ui()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.public_tab = GradientWidget()
        self.assoc_tab = GradientWidget()
        self.tabs.addTab(self.public_tab, "Public")
        self.tabs.addTab(self.assoc_tab, "LIGO Assoc")

        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.setup_public_ui()
        self.setup_assoc_ui()

    def setup_public_ui(self):
        layout = QVBoxLayout()
        self.status_label_public = QLabel("Idle")
        self.status_label_public.setFont(FONT_LABEL)
        self.status_label_public.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent; ")
        layout.addWidget(self.status_label_public)

        buttons = [
            ("Select Time CSV", self.select_time_csv),
            ("Import Channel CSV", self.select_channel_csv),
            ("Select Output Dir", self.select_output_dir),
            ("Select Time Segments", self.open_segments_dialog),
            ("Start/Stop Execution", self.toggle_public_execution)
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.setFont(FONT_BUTTON)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: {COLOR_FG};
                    border: 1px solid {COLOR_FG};
                    border-radius: 5px;
                    padding: 6px;
                    min-height: 28px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: #A9A9A9;
                }}
            """)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)

        self.channel_combo_public = QComboBox()
        self.channel_combo_public.addItems(self.loaded_channels)
        self.channel_combo_public.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.channel_combo_public.currentTextChanged.connect(self.on_channel_select_public)
        layout.addWidget(self.channel_combo_public)

        layout.addStretch()
        self.public_tab.setLayout(layout)

    def setup_assoc_ui(self):
        layout = QVBoxLayout()
        self.status_label_assoc = QLabel("Idle")
        self.status_label_assoc.setFont(FONT_LABEL)
        self.status_label_assoc.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
        layout.addWidget(self.status_label_assoc)

        buttons = [
            ("Select Time CSV", self.select_time_csv),
            ("Import Channel CSV", self.select_channel_csv),
            ("Select Output Dir", self.select_output_dir),
            ("Select Time Segments", self.open_segments_dialog),
            ("Start/Stop Execution", self.toggle_assoc_execution)
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.setFont(FONT_BUTTON)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: {COLOR_FG};
                    border: 1px solid {COLOR_FG};
                    border-radius: 5px;
                    padding: 6px;
                    min-height: 28px;
                }}
                QPushButton:hover {{
                    background-color: {COLOR_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: #A9A9A9;
                }}
            """)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)

        self.channel_combo_assoc = QComboBox()
        self.channel_combo_assoc.addItems(self.loaded_channels)
        self.channel_combo_assoc.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.channel_combo_assoc.currentTextChanged.connect(self.on_channel_select_assoc)
        layout.addWidget(self.channel_combo_assoc)

        layout.addWidget(QLabel("Frame Type:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        self.frametype_edit = QLineEdit()
        self.frametype_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        layout.addWidget(self.frametype_edit)

        layout.addWidget(QLabel("Select Server:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        self.host_combo = QComboBox()
        hosts = [
            "datafind2.ldas.ligo-la.caltech.edu:80",
            "datafind.ldas.cit:80",
            "10.21.201.15:80",
            "datafind.gwosc.org",
            "nds.gwosc.org"
        ]
        self.host_combo.addItems(hosts)
        self.host_combo.setCurrentIndex(0)
        self.selected_host = hosts[0]
        self.host_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        self.host_combo.currentTextChanged.connect(lambda text: setattr(self, 'selected_host', text))
        layout.addWidget(self.host_combo)

        layout.addStretch()
        self.assoc_tab.setLayout(layout)

    def select_time_csv(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Time CSV", "", "CSV files (*.csv)")
        if file:
            try:
                self.time_csv_file = file
                self.time_ranges = pd.read_csv(self.time_csv_file)
                if not all(col in self.time_ranges.columns for col in ['GPSstart', 'GPSend']):
                    self.time_ranges = pd.read_csv(self.time_csv_file, header=None, names=['GPSstart', 'GPSend'])
                current_tab = self.tabs.currentIndex()
                status_label = self.status_label_public if current_tab == 0 else self.status_label_assoc
                status_label.setText(f"Selected Time CSV: {os.path.basename(self.time_csv_file)}")
                self.append_output(f"Selected Time CSV: {self.time_csv_file}", "success")
            except Exception as e:
                self.append_output(f"Error loading Time CSV: {e}", "error")
                QMessageBox.critical(self, "Error", str(e))

    def select_channel_csv(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Channel CSV", "", "CSV files (*.csv)")
        if file:
            try:
                self.channel_csv_file = file
                channels_df = pd.read_csv(self.channel_csv_file, header=None, skiprows=1, names=["Channel", "Sample Rate"])
                self.loaded_channels = list(channels_df["Channel"])
                self.channel_to_rate.update(dict(zip(channels_df["Channel"], channels_df["Sample Rate"])))
                self.channel_combo_public.clear()
                self.channel_combo_assoc.clear()
                self.channel_combo_public.addItems(self.loaded_channels)
                self.channel_combo_assoc.addItems(self.loaded_channels)
                if self.loaded_channels:
                    self.selected_channel = self.loaded_channels[0]
                self.save_history()
                current_tab = self.tabs.currentIndex()
                status_label = self.status_label_public if current_tab == 0 else self.status_label_assoc
                status_label.setText(f"Imported Channel CSV: {os.path.basename(self.channel_csv_file)}")
                self.append_output(f"Imported Channel CSV: {self.channel_csv_file}", "success")
            except Exception as e:
                self.append_output(f"Error loading Channel CSV: {e}", "error")
                QMessageBox.critical(self, "Error", str(e))

    def on_channel_select_public(self, channel):
        self.selected_channel = channel

    def on_channel_select_assoc(self, channel):
        self.selected_channel = channel
        if channel:
            site_prefix = channel.split(':')[0]
            self.frametype_edit.setText(f"{site_prefix}_HOFT_C02")
            self.selected_frametype = self.frametype_edit.text()

    def select_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.gwfout_path = directory
            current_tab = self.tabs.currentIndex()
            status_label = self.status_label_public if current_tab == 0 else self.status_label_assoc
            status_label.setText(f"Selected Output Dir: {self.gwfout_path}")
            self.save_history()
            self.append_output(f"Selected Output Dir: {self.gwfout_path}", "success")

    def open_segments_dialog(self):
        if self.time_ranges is None:
            self.append_output("Please select a Time CSV first.", "warning")
            QMessageBox.warning(self, "Warning", "Please select a Time CSV first.")
            return
        if not self.selected_channel:
            self.append_output("Please select a channel first.", "warning")
            QMessageBox.warning(self, "Warning", "Please select a channel first.")
            return

        segments = []
        
    def select_time_csv(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Time CSV", "", "CSV files (*.csv)")
        if file:
            try:
                # Read CSV with explicit header handling
                self.time_csv_file = file
                self.time_ranges = pd.read_csv(self.time_csv_file)
                # Check for 'Start' and 'End' columns, rename to 'GPSstart' and 'GPSend'
                if 'Start' in self.time_ranges.columns and 'End' in self.time_ranges.columns:
                    self.time_ranges = self.time_ranges.rename(columns={'Start': 'GPSstart', 'End': 'GPSend'})
                elif not all(col in self.time_ranges.columns for col in ['GPSstart', 'GPSend']):
                    # Try reading without header if columns are not named correctly
                    self.time_ranges = pd.read_csv(self.time_csv_file, header=None, names=['GPSstart', 'GPSend'], skiprows=1)
                # Validate that GPSstart and GPSend are numeric
                try:
                    self.time_ranges['GPSstart'] = pd.to_numeric(self.time_ranges['GPSstart'], errors='raise')
                    self.time_ranges['GPSend'] = pd.to_numeric(self.time_ranges['GPSend'], errors='raise')
                    # Ensure GPSstart < GPSend
                    invalid_rows = self.time_ranges[self.time_ranges['GPSstart'] >= self.time_ranges['GPSend']]
                    if not invalid_rows.empty:
                        self.append_output(f"Invalid segments found: GPSstart >= GPSend in {len(invalid_rows)} rows", "warning")
                        self.time_ranges = self.time_ranges[self.time_ranges['GPSstart'] < self.time_ranges['GPSend']]
                        if self.time_ranges.empty:
                            raise ValueError("No valid segments after filtering invalid rows (GPSstart >= GPSend)")
                except ValueError as e:
                    self.append_output(f"Error in Time CSV: Columns must contain numeric values. {e}", "error")
                    QMessageBox.critical(self, "Error", "Time CSV must have numeric GPSstart and GPSend columns.")
                    self.time_ranges = None
                    return
                current_tab = self.tabs.currentIndex()
                status_label = self.status_label_public if current_tab == 0 else self.status_label_assoc
                status_label.setText(f"Selected Time CSV: {os.path.basename(self.time_csv_file)}")
                self.append_output(f"Selected Time CSV: {self.time_csv_file}", "success")
            except Exception as e:
                self.append_output(f"Error loading Time CSV: {e}", "error")
                QMessageBox.critical(self, "Error", f"Failed to load Time CSV: {e}")
                self.time_ranges = None


    def open_segments_dialog(self):
        if self.time_ranges is None:
            self.append_output("Please select a valid Time CSV first.", "warning")
            QMessageBox.warning(self, "Warning", "Please select a valid Time CSV first.")
            return
        if not self.selected_channel:
            self.append_output("Please select a channel first.", "warning")
            QMessageBox.warning(self, "Warning", "Please select a channel first.")
            return

        segments = []
        try:
            for _, row in self.time_ranges.iterrows():
                try:
                    start = int(float(row['GPSstart']))
                    end = int(float(row['GPSend']))
                    segments.append(f"{start}_{end}")
                except (ValueError, TypeError) as e:
                    self.append_output(f"Skipping invalid segment: {row['GPSstart']}_{row['GPSend']} ({e})", "warning")
                    continue
        except Exception as e:
            self.append_output(f"Error parsing time segments: {e}", "error")
            QMessageBox.critical(self, "Error", f"Failed to parse time segments: {e}")
            return

        if not segments:
            self.append_output("No valid time segments found in the selected CSV.", "warning")
            QMessageBox.warning(self, "Warning", "No valid time segments found in the selected CSV.")
            return

        dialog = QMainWindow(self)
        dialog.setWindowTitle("Select Time Segments")
        dialog.setGeometry(200, 200, 500, 600)
        dialog.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #1C2526, stop:1 #E8ECEF);
            }
        """)

        main_widget = GradientWidget()
        dialog.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;")
        search_edit = QLineEdit()
        search_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #E8ECEF;
                color: #1C2526;
            }}
        """)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_edit)
        layout.addLayout(search_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = GradientWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CED4DA;
                border-radius: 5px;
            }
        """)
        layout.addWidget(scroll_area)

        self.segment_checkboxes = {}
        for seg in segments:
            chk = QCheckBox(seg)
            chk.setFont(FONT_LABEL)
            chk.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
            scroll_layout.addWidget(chk)
            self.segment_checkboxes[seg] = chk

        def filter_segments():
            search_term = search_edit.text().lower()
            for seg, chk in self.segment_checkboxes.items():
                chk.setVisible(search_term in seg.lower())

        search_edit.textChanged.connect(filter_segments)

        button_layout = QHBoxLayout()
        buttons = [
            ("Select All", lambda: [chk.setChecked(True) for chk in self.segment_checkboxes.values()]),
            ("Deselect All", lambda: [chk.setChecked(False) for chk in self.segment_checkboxes.values()]),
            ("Deselect Processed", self.deselect_processed),
            ("Confirm", lambda: self.confirm_segments(dialog))
        ]

        for text, cmd in buttons:
            btn = QPushButton(text)
            btn.setFont(FONT_BUTTON)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLOR_ACCENT};
                    color: {COLOR_FG};
                    border: 1px solid {COLOR_FG};
                    border-radius: 5px;
                    padding: 6px;
                    min-height: 28px;
                }}
                QPushButton:hover {{
                    background-color: #1C2526;
                }}
                QPushButton:pressed {{
                    background-color: #A9A9A9;
                }}
            """)
            btn.clicked.connect(cmd)
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        dialog.show()

    def deselect_processed(self):
        ch_dir = os.path.join(self.gwfout_path, self.selected_channel.replace(":", "_"))
        for seg, chk in self.segment_checkboxes.items():
            tdir = os.path.join(ch_dir, seg)
            outfile = os.path.join(tdir, f"{self.selected_channel.replace(':','_')}_{seg}.gwf")
            if os.path.exists(tdir) and os.path.exists(outfile):
                chk.setChecked(False)
                self.append_output(f"Deselected processed segment: {seg}", "info")

    def confirm_segments(self, dialog):
        self.selected_segments = [seg for seg, chk in self.segment_checkboxes.items() if chk.isChecked()]
        if not self.selected_segments:
            QMessageBox.warning(self, "Warning", "No segments selected.")
        else:
            self.append_output(f"Selected {len(self.selected_segments)} time segments.", "success")
            dialog.close()

    def toggle_public_execution(self):
        if self.execution_running:
            self.execution_running = False
            self.status_label_public.setText("Execution Stopped")
            self.status_label_public.setStyleSheet(f"color: {COLOR_ERROR}; background-color: transparent;")
            self.append_output("Execution stopped.", "warning")
        else:
            self.selected_channel = self.channel_combo_public.currentText()
            if not all([self.time_ranges is not None, self.selected_channel, self.selected_segments]):
                self.append_output("Please select time CSV, a channel, and time segments.", "warning")
                QMessageBox.warning(self, "Warning", "Please select time CSV, a channel, and time segments.")
                return
            self.execution_running = True
            self.status_label_public.setText("Execution Started")
            self.status_label_public.setStyleSheet(f"color: {COLOR_SUCCESS}; background-color: transparent;")
            self.append_output("Execution started...", "success")
            threading.Thread(target=self.run_gravfetch_public, daemon=True).start()

    def toggle_assoc_execution(self):
        if self.execution_running:
            self.execution_running = False
            self.status_label_assoc.setText("Execution Stopped")
            self.status_label_assoc.setStyleSheet(f"color: {COLOR_ERROR}; background-color: transparent;")
            self.append_output("Execution stopped.", "warning")
        else:
            self.selected_channel = self.channel_combo_assoc.currentText()
            self.selected_frametype = self.frametype_edit.text()
            self.selected_host = self.host_combo.currentText()
            if not all([self.time_ranges is not None, self.selected_channel, self.selected_segments, self.selected_frametype, self.selected_host]):
                self.append_output("Please select time CSV, a channel, frame type, server, and time segments.", "warning")
                QMessageBox.warning(self, "Warning", "Please select time CSV, a channel, frame type, server, and time segments.")
                return
            self.execution_running = True
            self.status_label_assoc.setText("Execution Started")
            self.status_label_assoc.setStyleSheet(f"color: {COLOR_SUCCESS}; background-color: transparent;")
            self.append_output("Execution started...", "success")
            threading.Thread(target=self.run_gravfetch_assoc, daemon=True).start()

    def is_internet_connected(self):
        try:
            subprocess.check_call(["ping", "-c" if sys.platform.startswith('linux') else "-n", "1", "google.com"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def wait_for_internet(self, channel, start, end):
        log_file = "internet_disconnection_log.txt"
        with open(log_file, "a") as log:
            log.write(f"{datetime.now()}: Internet disconnected while fetching {channel} from {start} to {end}\n")
        while not self.is_internet_connected():
            self.append_output("Internet disconnected. Waiting 10 minutes to retry...", "warning")
            time.sleep(600)
        self.append_output("Internet reconnected. Resuming download...", "success")

    def run_gravfetch_public(self):
        try:
            os.makedirs(self.gwfout_path, exist_ok=True)
            ch = self.selected_channel
            ch_dir = os.path.join(self.gwfout_path, ch.replace(":", "_"))
            os.makedirs(ch_dir, exist_ok=True)
            fin_path = os.path.join(ch_dir, "fin.ffl")

            current_dir = os.getcwd()

            with open(fin_path, 'a') as fin:
                for seg in self.selected_segments:
                    if not self.execution_running:
                        self.append_output("Execution stopped by user.", "warning")
                        break
                    start_end = seg.split("_")
                    start, end = int(start_end[0]), int(start_end[1])
                    tdir = os.path.join(ch_dir, f"{start}_{end}")
                    os.makedirs(tdir, exist_ok=True)
                    outfile = os.path.join(tdir, f"{ch.replace(':','_')}_{start}_{end}.gwf")

                    if os.path.exists(outfile):
                        self.append_output(f"Segment {seg} already fetched. Skipping.", "warning")
                        continue

                    while self.execution_running:
                        try:
                            self.append_output(f"Fetching {ch} from {start} to {end}...", "info")
                            data = TimeSeries.fetch(ch, start=start, end=end, host="nds.gwosc.org")
                            data.write(outfile)
                            rel_path = os.path.relpath(outfile, current_dir).replace("\\", "/")
                            dt = end - start
                            fin.write(f"./{rel_path} {start} {dt} 0 0\n")
                            self.append_output(f"Saved to {outfile}", "success")
                            break
                        except (ValueError, RuntimeError, socket.error) as e:
                            self.append_output(f"Error fetching {ch} {start}-{end}: {e}", "error")
                            if os.path.exists(outfile):
                                os.remove(outfile)
                                self.append_output(f"Deleted interrupted file: {outfile}", "warning")
                            if not self.execution_running:
                                self.append_output("Execution stopped by user.", "warning")
                                break
                            self.wait_for_internet(ch, start, end)
                        except Exception as e:
                            self.append_output(f"Unexpected error: {e}", "error")
                            break

            if ch not in self.loaded_channels and self.execution_running:
                self.loaded_channels.append(ch)
                self.save_history()

            self.execution_running = False
            self.status_label_public.setText("Execution Finished")
            self.status_label_public.setStyleSheet(f"color: {COLOR_SUCCESS}; background-color: transparent;")
            self.append_output("Execution complete.", "success")

        except Exception as e:
            self.append_output(f"Error: {e}", "error")
            self.execution_running = False
            self.status_label_public.setText("Execution Failed")
            self.status_label_public.setStyleSheet(f"color: {COLOR_ERROR}; background-color: transparent;")


    def run_gravfetch_assoc(self):
        try:
            os.makedirs(self.gwfout_path, exist_ok=True)
            ch = self.selected_channel
            ch_dir = os.path.join(self.gwfout_path, ch.replace(":", "_"))
            os.makedirs(ch_dir, exist_ok=True)
            fin_path = os.path.join(ch_dir, "fin.ffl")

            current_dir = os.getcwd()

            with open(fin_path, 'a') as fin:
                for seg in self.selected_segments:
                    if not self.execution_running:
                        self.append_output("Execution stopped by user.", "warning")
                        break
                    start_end = seg.split("_")
                    start, end = int(start_end[0]), int(start_end[1])
                    tdir = os.path.join(ch_dir, f"{start}_{end}")
                    os.makedirs(tdir, exist_ok=True)
                    outfile = os.path.join(tdir, f"{ch.replace(':','_')}_{start}_{end}.gwf")

                    if os.path.exists(outfile):
                        self.append_output(f"Segment {seg} already fetched. Skipping.", "warning")
                        continue

                    while self.execution_running:
                        try:
                            self.append_output(f"Fetching {ch} from {start} to {end}...", "info")
                            site = self.selected_frametype[0]
                            frametype = self.selected_frametype
                            host = self.selected_host
                            urls = get_urls(ch, start, end, host=host)
                            self.append_output(f"Found {len(urls)} URLs for {ch} {start}-{end}: {urls}", "info")
                            if not urls:
                                self.append_output(f"No data available for {ch} {start}-{end}. Skipping segment.", "warning")
                                break
                            data = TimeSeries.read(urls, channel=ch, start=start, end=end)
                            data.write(outfile)
                            rel_path = os.path.relpath(outfile, current_dir).replace("\\", "/")
                            dt = end - start
                            fin.write(f"./{rel_path} {start} {dt} 0 0\n")
                            self.append_output(f"Saved to {outfile}", "success")
                            break
                        except (ValueError, RuntimeError, socket.error) as e:
                            self.append_output(f"Error fetching {ch} {start}-{end}: {e}", "error")
                            if os.path.exists(outfile):
                                os.remove(outfile)
                                self.append_output(f"Deleted interrupted file: {outfile}", "warning")
                            if not self.execution_running:
                                self.append_output("Execution stopped by user.", "warning")
                                break
                            self.wait_for_internet(ch, start, end)
                        except Exception as e:
                            self.append_output(f"Unexpected error: {e}", "error")
                            break

            if ch not in self.loaded_channels and self.execution_running:
                self.loaded_channels.append(ch)
                self.save_history()

            self.execution_running = False
            self.status_label_assoc.setText("Execution Finished")
            self.status_label_assoc.setStyleSheet(f"color: {COLOR_SUCCESS}; background-color: transparent;")
            self.append_output("Execution complete.", "success")

        except Exception as e:
            self.append_output(f"Error: {e}", "error")
            self.execution_running = False
            self.status_label_assoc.setText("Execution Failed")
            self.status_label_assoc.setStyleSheet(f"color: {COLOR_ERROR}; background-color: transparent;")

    def save_history(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump({"gwfout_path": self.gwfout_path, "channels": self.loaded_channels}, f, indent=2)
            self.append_output("History saved.", "info")
        except Exception as e:
            self.append_output(f"Error saving history: {e}", "error")

########################################################################################################################################
#############################################################    OMICRON    ############################################################
########################################################################################################################################

class OmicronApp(QWidget):
    append_output_signal = pyqtSignal(str, str)
    show_message_box_signal = pyqtSignal(str, str, str)

    def __init__(self, parent, append_output_callback):
        super().__init__(parent)
        self.project_dir = os.getcwd().replace("\\", "/")
        self.wsl_project_dir = f"/mnt/{self.project_dir[0].lower()}/{self.project_dir[2:]}"
        self.GWFOUT_DIRECTORY = "./GWFout"
        self.config_path = "config.txt"
        self.default_output_dir = "./OmicronOut"
        self.config_data = {}
        self.ui_elements = {}
        self.append_output_signal.connect(append_output_callback)
        self.show_message_box_signal.connect(self._show_message_box)

        # Create default output directory
        if not os.path.exists(self.default_output_dir):
            os.makedirs(self.default_output_dir, exist_ok=True)
            self.append_output_signal.emit(f"Created default output directory: {self.default_output_dir}\n", "info")

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.channel_combo = QComboBox()
        self.channel_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)

        layout.addWidget(QLabel("Select Channel:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        layout.addWidget(self.channel_combo)
        self.ui_elements["DATA CHANNELS"] = self.channel_combo
        QTimer.singleShot(0, self.update_channel_options)
        self.create_file_selector("Select .ffl File:", "DATA FFL", layout)
        self.create_editable_dropdown("Sampling Frequency:", "DATA SAMPLEFREQUENCY", ["1024", "2048", "4096"], layout)

        button_layout = QHBoxLayout()
        custom_segs_btn = QPushButton("Custom Segs")
        custom_segs_btn.setFont(FONT_BUTTON)
        custom_segs_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        custom_segs_btn.clicked.connect(self.open_custom_segs_dialog)
        
        save_btn = QPushButton("Save Config")
        save_btn.setFont(FONT_BUTTON)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        save_btn.clicked.connect(self.save_config)
        start_btn = QPushButton("Start OMICRON")
        start_btn.setFont(FONT_BUTTON)
        start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        start_btn.clicked.connect(self.run_omicron_script)
        button_layout.addWidget(custom_segs_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(start_btn)
        layout.addLayout(button_layout)

        param_frame = QFrame()
        param_layout = QVBoxLayout(param_frame)
        double_entry_sizer = QHBoxLayout()
        self.create_double_entry("Timing:", "PARAMETER TIMING", double_entry_sizer)
        self.create_double_entry("Frequency Range:", "PARAMETER FREQUENCYRANGE", double_entry_sizer)
        self.create_double_entry("Q-Range:", "PARAMETER QRANGE", double_entry_sizer)
        param_layout.addLayout(double_entry_sizer)

        single_entry_sizer = QHBoxLayout()
        self.create_entry("Mismatch Max:", "PARAMETER MISMATCHMAX", single_entry_sizer)
        self.create_entry("SNR Threshold:", "PARAMETER SNRTHRESHOLD", single_entry_sizer)
        self.create_entry("PSD Length:", "PARAMETER PSDLENGTH", single_entry_sizer)
        param_layout.addLayout(single_entry_sizer)
        layout.addWidget(param_frame)

        output_frame = QFrame()
        output_layout = QVBoxLayout(output_frame)
        self.create_file_selector("Select Output Directory:", "OUTPUT DIRECTORY", output_layout, is_directory=True)
        self.create_output_products_selection(output_layout)
        self.create_dropdown("Select Format:", "OUTPUT FORMAT", ["root", "hdf5", "Format3"], output_layout)
        self.create_slider("Verbosity (0-3):", "OUTPUT VERBOSITY", 0, 3, output_layout)
        layout.addWidget(output_frame)
        layout.addWidget(QLabel("Username (optional, WSL on Windows):", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        self.wsl_username_input = QLineEdit()
        self.wsl_username_input.setPlaceholderText("Enter username for WSL (Windows only) or leave blank")
        self.wsl_username_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        layout.addWidget(self.wsl_username_input)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def create_entry(self, label, key, layout):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        element = QLineEdit(self.config_data.get(key, ""))
        element.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        layout.addWidget(element)
        self.ui_elements[key] = element

    def create_double_entry(self, label, key, layout):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        values = self.config_data.get(key, "0 0").split()
        element1 = QLineEdit(values[0] if len(values) > 0 else "0")
        element1.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        element2 = QLineEdit(values[1] if len(values) > 1 else "0")
        element2.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        layout.addWidget(element1)
        layout.addWidget(element2)
        self.ui_elements[key] = (element1, element2)

    def create_file_selector(self, label, key, layout, is_directory=False):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        element = QLineEdit(self.config_data.get(key, ""))
        element.setReadOnly(True)
        element.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
        """)
        button = QPushButton("Select")
        button.setFont(FONT_BUTTON)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        button.clicked.connect(lambda: self.select_file(element, is_directory))
        layout.addWidget(element)
        layout.addWidget(button)
        self.ui_elements[key] = element

    def create_output_products_selection(self, layout):
        layout.addWidget(QLabel("Select Output Products:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        self.ui_elements["OUTPUT PRODUCTS"] = {}
        for product in ["triggers", "html"]:
            chk = QCheckBox(product)
            chk.setFont(FONT_LABEL)
            chk.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
            layout.addWidget(chk)
            self.ui_elements["OUTPUT PRODUCTS"][product] = chk

    def create_dropdown(self, label, key, options, layout):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        element = QComboBox()
        element.addItems(options)
        element.setCurrentText(self.config_data.get(key, options[0]))
        element.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        layout.addWidget(element)
        self.ui_elements[key] = element

    def create_editable_dropdown(self, label, key, options, layout):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        element = QComboBox()
        element.setEditable(True)
        element.addItems(options)
        element.setCurrentText(self.config_data.get(key, options[0]))
        element.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 4px;
                background-color: #747576;
                color: {COLOR_FG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """)
        layout.addWidget(element)
        self.ui_elements[key] = element
        return element

    def create_slider(self, label, key, min_val, max_val, layout):
        layout.addWidget(QLabel(label, font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
        element = QSlider(Qt.Horizontal)
        element.setMinimum(min_val)
        element.setMaximum(max_val)
        element.setValue(int(self.config_data.get(key, min_val)))
        element.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {COLOR_FG};
                height: 8px;
                background: #747576;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }}
        """)
        layout.addWidget(element)
        self.ui_elements[key] = element
        return element

    def select_file(self, text_ctrl, is_directory=False):
        file_path = None
        if is_directory:
            file_path = QFileDialog.getExistingDirectory(self, "Choose a directory")
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Choose a file", "", "FFL files (*.ffl)")
        if file_path:
            relative_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
            text_ctrl.setText(relative_path)
            self.append_output_signal.emit(f"File selected: {relative_path}\n", "info")

    def update_ui_from_config(self):
        for key, element in self.ui_elements.items():
            if isinstance(element, QLineEdit):
                element.setText(self.config_data.get(key, ""))
            elif isinstance(element, QComboBox):
                element.setCurrentText(self.config_data.get(key, element.itemText(0)))
            elif isinstance(element, tuple):
                values = self.config_data.get(key, "0 0").split()
                element[0].setText(values[0] if len(values) > 0 else "0")
                element[1].setText(values[1] if len(values) > 1 else "0")
            elif isinstance(element, QSlider):
                element.setValue(int(self.config_data.get(key, 0)))
            elif isinstance(element, dict):
                products = self.config_data.get(key, "").split()
                for product, chk in element.items():
                    chk.setChecked(product in products)

    def run_omicron_script(self):
        self.append_output_signal.emit("Starting OMICRON script...\n", "info")
        threading.Thread(target=self.start_omicron_process, daemon=True).start()

    def start_omicron_process(self):
        try:
            ffl_widget = self.ui_elements["DATA FFL"]
            ffl_file = ffl_widget.text().strip() if ffl_widget else ""
            if not ffl_file or not os.path.exists(ffl_file):
                self.append_output_signal.emit("Error: No valid .ffl file selected.\n", "error")
                self.show_message_box_signal.emit("Error", "No valid .ffl file selected.", "critical")
                return
            with open(ffl_file, "r") as f:
                lines = [line.strip().split() for line in f if line.strip()]
            if not lines or len(lines[0]) < 2 or len(lines[-1]) < 2:
                self.append_output_signal.emit("Error: Invalid .ffl file format.\n", "error")
                self.show_message_box_signal.emit("Error", "Invalid .ffl file format.", "critical")
                return
            first_time_segment = lines[0][1]
            last_time_segment = lines[-1][1]
            omicron_cmd_lx = f'eval "$(conda shell.bash hook)" && conda activate GWeasy && omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1'
            omicron_cmd = f"omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1"
            
            if platform.system() == "Windows":
                # Validate WSL environment
                process = subprocess.Popen(
                    ["wsl", "--list", "--all"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False
                )
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    self.append_output_signal.emit(f"Error: WSL not available: {stderr.strip()}\n", "error")
                    self.show_message_box_signal.emit("Error", f"WSL not available: {stderr.strip()}", "critical")
                    return

                # Use user-specified WSL username if provided, else find non-root user
                username = self.wsl_username_input.text().strip() if hasattr(self, 'wsl_username_input') and self.wsl_username_input.text().strip() else None
                if not username:
                    process = subprocess.Popen(
                        ["wsl", "cat", "/etc/passwd"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=False
                    )
                    stdout, stderr = process.communicate()
                    if process.returncode == 0 and stdout.strip():
                        for line in stdout.splitlines():
                            if line.startswith("nobody:") or line.startswith("root:"):
                                continue
                            if "/home/" in line:
                                username = line.split(":")[0]
                                break
                if not username:
                    self.append_output_signal.emit("Error: No valid WSL username provided or found in /etc/passwd.\n", "error")
                    self.show_message_box_signal.emit("Error", "No valid WSL username provided or found in /etc/passwd.", "critical")
                    return

                # Locate Conda and validate environment
                process = subprocess.Popen(
                    ["wsl", "--user", username, "bash", "-lic", "which conda"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False
                )
                stdout, stderr = process.communicate()
                if process.returncode != 0 or not stdout.strip():
                    self.append_output_signal.emit(f"Error: Failed to locate Conda for user {username}: {stderr.strip()}\n", "error")
                    self.show_message_box_signal.emit("Error", f"Failed to locate Conda: {stderr.strip()}", "critical")
                    return
                conda_path = stdout.strip()
                conda_base = os.path.dirname(os.path.dirname(conda_path))
                conda_init = f"{conda_base}/etc/profile.d/conda.sh"

                # Prepare and run Omicron command
                omicron_cmd = f"omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1"
                wsl_command = f'wsl --user {username} bash -lic "source {conda_init} && conda activate base && {omicron_cmd}"'
                self.append_output_signal.emit(f"Running: {wsl_command}\n", "info")

                # Run Omicron command once, no retries
                try:
                    process = subprocess.Popen(
                        wsl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                    while True:
                        output = process.stdout.readline()
                        if output == "" and process.poll() is not None:
                            break
                        if output:
                            self.append_output_signal.emit(output.strip() + "\n", "info")
                    while True:
                        error = process.stderr.readline()
                        if error == "" and process.poll() is not None:
                            break
                        if error:
                            self.append_output_signal.emit(f"ERROR: {error.strip()}\n", "error")
                    process.wait()
                    if process.returncode == 0:
                        self.append_output_signal.emit("OMICRON process completed successfully.\n", "success")
                        self.show_message_box_signal.emit("Success", "OMICRON process completed successfully.", "information")
                    else:
                        self.append_output_signal.emit(f"Error: Command failed with return code {process.returncode}.\n", "error")
                        self.show_message_box_signal.emit("Error", f"OMICRON process failed with return code {process.returncode}.", "critical")
                except Exception as e:
                    self.append_output_signal.emit(f"Error: Command failed: {e}\n", "error")
                    self.show_message_box_signal.emit("Error", f"OMICRON process failed: {e}", "critical")
            
            
            
            ###LINUX
            else:
                print("Running in Linux")
                self.append_output_signal.emit(f"Running: {omicron_cmd_lx}\n", "info")
                process = subprocess.Popen(
                    omicron_cmd_lx, shell=True,executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                while True:
                    output = process.stdout.readline()
                    if output == "" and process.poll() is not None:
                        break
                    if output:
                        self.append_output_signal.emit(output.strip() + "\n", "info")

                while True:
                    error = process.stderr.readline()
                    if error == "" and process.poll() is not None:
                        break
                    if error:
                        self.append_output_signal.emit(f"ERROR: {error.strip()}\n", "error")

                process.wait()
                if process.returncode != 0:
                    self.append_output_signal.emit(f"Error: Command failed with return code {process.returncode}.\n", "error")
                    self.show_message_box_signal.emit("Error", f"Command failed with return code {process.returncode}.", "critical")
                else:
                    self.append_output_signal.emit("OMICRON process completed successfully.\n", "success")
                    self.show_message_box_signal.emit("Success", "OMICRON process completed successfully.", "information")
                            
        except Exception as e:
            self.append_output_signal.emit(f"Unexpected error: {e}\n", "error")
            self.show_message_box_signal.emit("Error", f"Unexpected error: {e}", "critical")

    def load_config(self):
        self.config_data = {}
        try:
            if not os.path.exists(self.config_path):
                with open(self.config_path, 'w') as file:
                    file.write(DEFAULT_CONFIG)
                self.append_output_signal.emit(f"Created default config: {self.config_path}\n", "info")
            with open(self.config_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2:
                        self.append_output_signal.emit(f"Skipping invalid config line: {line}\n", "warning")
                        continue
                    key = parts[0]
                    value = parts[1]
                    if key.startswith("PARAMETER") and len(parts) == 3:
                        key = f"{parts[0]} {parts[1]}"
                        value = parts[2]
                    self.config_data[key] = value
            if "OUTPUT DIRECTORY" not in self.config_data or not self.config_data["OUTPUT DIRECTORY"]:
                self.config_data["OUTPUT DIRECTORY"] = self.default_output_dir
            self.append_output_signal.emit("Config loaded successfully.\n", "success")
            self.update_ui_from_config()
        except Exception as e:
            self.append_output_signal.emit(f"Error loading config: {e}\n", "error")
            self.show_message_box_signal.emit("Error", f"Error loading config: {e}", "critical")

    # def open_custom_segs_dialog(self):
    #     channel_dir = QFileDialog.getExistingDirectory(self, "Select Channel Directory")
    #     if not channel_dir:
    #         self.append_output_signal.emit("No channel directory selected.\n", "warning")
    #         return

    #     segments = [d for d in os.listdir(channel_dir) if os.path.isdir(os.path.join(channel_dir, d))]
    #     if not segments:
    #         self.append_output_signal.emit("No time segments found in selected channel.\n", "error")
    #         self.show_message_box_signal.emit("Error", "No time segments found in selected channel.", "critical")
    #         return

    #     # dialog = QMainWindow(self)
    #     self.custom_seg_dialog = QMainWindow(self)  # store reference
    #     dialog = self.custom_seg_dialog
    #     dialog.setWindowTitle("Select Time Segments")
    #     dialog.setGeometry(200, 200, 400, 400)
    #     dialog.setStyleSheet(f"""
    #         QMainWindow {{
    #             background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
    #                                         stop:0 #E8ECEF, stop:1 #1C2526);
    #         }}
    #     """)

    #     main_widget = GradientWidget()
    #     dialog.setCentralWidget(main_widget)
    #     layout = QVBoxLayout(main_widget)

    #     layout.addWidget(QLabel("Select Time Segments:", font=FONT_LABEL, styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))
    #     scroll_area = QScrollArea()
    #     scroll_area.setWidgetResizable(True)
    #     scroll_widget = GradientWidget()
    #     scroll_layout = QVBoxLayout(scroll_widget)
    #     scroll_area.setWidget(scroll_widget)
    #     scroll_area.setStyleSheet(f"""
    #         QScrollArea {{
    #             border: 1px solid #CED4DA;
    #             border-radius: 5px;
    #         }}
    #     """)
    #     layout.addWidget(scroll_area)

    #     self.segment_checkboxes = {}
    #     for segment in segments:
    #         try:
    #             start, end = map(int, segment.split("_"))
    #             if start >= end:
    #                 self.append_output_signal.emit(f"Skipping invalid segment: {segment} (start >= end)\n", "warning")
    #                 continue
    #             chk = QCheckBox(segment)
    #             chk.setFont(FONT_LABEL)
    #             chk.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
    #             scroll_layout.addWidget(chk)
    #             self.segment_checkboxes[segment] = chk
    #         except ValueError:
    #             self.append_output_signal.emit(f"Skipping invalid segment format: {segment}\n", "warning")
    #             continue

    #     if not self.segment_checkboxes:
    #         self.append_output_signal.emit("No valid time segments found.\n", "error")
    #         self.show_message_box_signal.emit("Error", "No valid time segments found.", "critical")
    #         dialog.close()
    #         return

    #     button_layout = QHBoxLayout()
    #     confirm_btn = QPushButton("Confirm")
    #     confirm_btn.setFont(FONT_BUTTON)
    #     confirm_btn.setStyleSheet(f"""
    #         QPushButton {{
    #             background-color: {COLOR_ACCENT};
    #             color: {COLOR_FG};
    #             border: 1px solid {COLOR_FG};
    #             border-radius: 5px;
    #             padding: 6px;
    #             min-height: 28px;
    #         }}
    #         QPushButton:hover {{
    #             background-color: {COLOR_HOVER};
    #         }}
    #         QPushButton:pressed {{
    #             background-color: #A9A9A9;
    #         }}
    #     """)
    #     confirm_btn.clicked.connect(lambda: self.generate_fin_ffl(channel_dir, [seg for seg, chk in self.segment_checkboxes.items() if chk.isChecked()], dialog))
    #     toggle_btn = QPushButton("Toggle All")
    #     toggle_btn.setFont(FONT_BUTTON)
    #     toggle_btn.setStyleSheet(f"""
    #         QPushButton {{
    #             background-color: {COLOR_ACCENT};
    #             color: {COLOR_FG};
    #             border: 1px solid {COLOR_FG};
    #             border-radius: 5px;
    #             padding: 6px;
    #             min-height: 28px;
    #         }}
    #         QPushButton:hover {{
    #             background-color: {COLOR_HOVER};
    #         }}
    #         QPushButton:pressed {{
    #             background-color: #A9A9A9;
    #         }}
    #     """)
    #     toggle_btn.clicked.connect(lambda: [chk.setChecked(not all(chk.isChecked() for chk in self.segment_checkboxes.values())) for chk in self.segment_checkboxes.values()])
    #     button_layout.addWidget(confirm_btn)
    #     button_layout.addWidget(toggle_btn)
    #     layout.addLayout(button_layout)

    #     dialog.show()

    def open_custom_segs_dialog(self):
        channel_dir = QFileDialog.getExistingDirectory(self, "Select Channel Directory")
        if not channel_dir:
            self.append_output_signal.emit("No channel directory selected.\n", "warning")
            return

        segments = [d for d in os.listdir(channel_dir) if os.path.isdir(os.path.join(channel_dir, d))]
        if not segments:
            self.append_output_signal.emit("No time segments found in selected channel.\n", "error")
            self.show_message_box_signal.emit("Error", "No time segments found in selected channel.", "critical")
            return

        # Create a QDialog instead of QMainWindow
        self.custom_seg_dialog = QDialog(self)
        dialog = self.custom_seg_dialog
        dialog.setWindowTitle("Select Time Segments")
        dialog.resize(400, 400)
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #E8ECEF, stop:1 #1C2526);
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select Time Segments:", font=FONT_LABEL,
                                styleSheet=f"color: {COLOR_FG}; background-color: transparent;"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()  # Use a plain QWidget instead of GradientWidget for simplicity
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CED4DA;
                border-radius: 5px;
            }
        """)
        layout.addWidget(scroll_area)

        self.segment_checkboxes = {}
        for segment in segments:
            try:
                start, end = map(int, segment.split("_"))
                if start >= end:
                    self.append_output_signal.emit(
                        f"Skipping invalid segment: {segment} (start >= end)\n", "warning")
                    continue
                chk = QCheckBox(segment)
                chk.setFont(FONT_LABEL)
                chk.setStyleSheet(f"color: {COLOR_FG}; background-color: transparent;")
                scroll_layout.addWidget(chk)
                self.segment_checkboxes[segment] = chk
            except ValueError:
                self.append_output_signal.emit(f"Skipping invalid segment format: {segment}\n", "warning")
                continue

        if not self.segment_checkboxes:
            self.append_output_signal.emit("No valid time segments found.\n", "error")
            self.show_message_box_signal.emit("Error", "No valid time segments found.", "critical")
            dialog.reject()  # Close the dialog
            return

        button_layout = QHBoxLayout()
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setFont(FONT_BUTTON)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        confirm_btn.clicked.connect(
            lambda: self.generate_fin_ffl(channel_dir,
                                        [seg for seg, chk in self.segment_checkboxes.items() if chk.isChecked()],
                                        dialog))
        toggle_btn = QPushButton("Toggle All")
        toggle_btn.setFont(FONT_BUTTON)
        toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_FG};
                border: 1px solid {COLOR_FG};
                border-radius: 5px;
                padding: 6px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_HOVER};
            }}
            QPushButton:pressed {{
                background-color: #A9A9A9;
            }}
        """)
        toggle_btn.clicked.connect(
            lambda: [chk.setChecked(not all(c.isChecked() for c in self.segment_checkboxes.values()))
                    for chk in self.segment_checkboxes.values()])
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(toggle_btn)
        layout.addLayout(button_layout)

        dialog.exec_()  # Make the dialog modal

    def generate_fin_ffl(self, channel_dir, selected_segments, dialog):
        if not selected_segments:
            self.append_output_signal.emit("No segments selected.\n", "warning")
            self.show_message_box_signal.emit("Error", "No segments selected.", "critical")
            dialog.close()
            return
        fin_ffl_path = os.path.join(channel_dir, "fin.ffl")
        try:
            with open(fin_ffl_path, "w") as ffl_file:
                for segment in selected_segments:
                    segment_path = os.path.join(channel_dir, segment)
                    gwf_files = [file for file in os.listdir(segment_path) if file.endswith(".gwf")]
                    if not gwf_files:
                        self.append_output_signal.emit(f"No .gwf files found in segment: {segment}\n", "warning")
                        continue
                    gwf_file_path = os.path.join(segment_path, gwf_files[0])
                    gwf_file_path = os.path.relpath(gwf_file_path, start=".").replace("\\", "/")
                    try:
                        segment_parts = segment.split("_")
                        start_time = int(segment_parts[0])
                        end_time = int(segment_parts[1])
                        duration = end_time - start_time
                        if duration <= 0:
                            self.append_output_signal.emit(f"Invalid duration for segment: {segment}\n", "warning")
                            continue
                        ffl_file.write(f"./{gwf_file_path} {start_time} {duration} 0 0\n")
                    except (ValueError, IndexError) as e:
                        self.append_output_signal.emit(f"Error processing segment {segment}: {e}\n", "warning")
                        continue
            if os.path.getsize(fin_ffl_path) == 0:
                self.append_output_signal.emit(f"Error: Generated fin.ffl is empty.\n", "error")
                self.show_message_box_signal.emit("Error", "Generated fin.ffl is empty.", "critical")
                dialog.close()
                return
            relative_ffl_path = os.path.relpath(fin_ffl_path, os.getcwd()).replace("\\", "/")
            self.ui_elements["DATA FFL"].setText(relative_ffl_path)
            self.append_output_signal.emit(f"fin.ffl created and selected: {relative_ffl_path}\n", "success")
            self.show_message_box_signal.emit("Success", f"fin.ffl created and selected: {relative_ffl_path}", "information")
            dialog.close()
        except Exception as e:
            self.append_output_signal.emit(f"Error creating fin.ffl: {e}\n", "error")
            self.show_message_box_signal.emit("Error", f"An error occurred while creating fin.ffl: {e}", "critical")
            dialog.close()

    def update_channel_options(self):
        base_path = self.GWFOUT_DIRECTORY
        history_file = "gravfetch_history.json"
        channels = set()
        default_structure = {"gwfout_path": str(base_path), "channels": []}
        
        # Create history file if it doesn't exist
        if not os.path.exists(history_file):
            try:
                with open(history_file, "w") as file:
                    json.dump(default_structure, file, indent=4)
                self.append_output_signal.emit(f"Created history file: {history_file}\n", "info")
            except Exception as e:
                self.append_output_signal.emit(f"Error creating history file: {e}\n", "error")
                self.show_message_box_signal.emit("Error", f"Error creating history file: {e}", "critical")
        
        # Load channels from history file
        try:
            with open(history_file, "r") as file:
                history_data = json.load(file)
            if not isinstance(history_data, dict) or "channels" not in history_data:
                self.append_output_signal.emit("History file is malformed. Resetting.\n", "warning")
                with open(history_file, "w") as file:
                    json.dump(default_structure, file, indent=4)
                history_data = default_structure
            for channel in history_data.get("channels", []):
                # Convert H1_ or L1_ to H1: or L1:
                if channel.startswith("H1_") or channel.startswith("L1_"):
                    channel = channel.replace("_", ":", 1)
                channels.add(channel)
        except Exception as e:
            self.append_output_signal.emit(f"Error reading history file: {e}\n", "error")
            self.show_message_box_signal.emit("Error", f"Error reading history file: {e}", "critical")
        
        # Load channels from GWFOUT_DIRECTORY
        if os.path.exists(base_path) and os.path.isdir(base_path):
            for d in os.listdir(base_path):
                dir_path = os.path.join(base_path, d)
                if os.path.isdir(dir_path):
                    # Convert H1_ or L1_ to H1: or L1:
                    if d.startswith("H1_") or d.startswith("L1_"):
                        d = d.replace("_", ":", 1)
                    channels.add(d)
        
        channel_options = sorted(channels) if channels else ["No Channels Available"]
        self.channel_combo.clear()
        self.channel_combo.addItems(channel_options)
        self.channel_combo.setCurrentText(channel_options[0] if channel_options else "")
        QTimer.singleShot(4000, self.update_channel_options)

        def _show_message_box(self, title, message, icon_type):
            if icon_type == "critical":
                #QMessageBox.information(self, title, message)
                print(message)
            else:
                ##QMessageBox.information(self, title, message)
                print(message)

    def _show_message_box(self, title, message, icon_type):
        if icon_type == "critical":
            #QMessageBox.information(self, title, message)
            print(message)
        else:
            ##QMessageBox.information(self, title, message)
            print(message)

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                for key, element in self.ui_elements.items():
                    if isinstance(element, tuple):
                        value = f"{element[0].text()} {element[1].text()}"
                    elif isinstance(element, dict):
                        value = " ".join([prod for prod, chk in element.items() if chk.isChecked()])
                    elif isinstance(element, QSlider):
                        value = str(element.value())
                    elif isinstance(element, QComboBox):
                        value = element.currentText()
                        if key == "DATA CHANNELS" and value != "No Channels Available":
                            # Convert H1_ or L1_ to H1: or L1:
                            if value.startswith("H1_") or value.startswith("L1_"):
                                value = value.replace("_", ":", 1)
                    elif isinstance(element, QLineEdit):
                        value = element.text()
                    else:
                        continue
                    if key == "OUTPUT DIRECTORY" and value:
                        # Create output directory if it doesn't exist
                        abs_path = os.path.abspath(value)
                        os.makedirs(abs_path, exist_ok=True)
                    if key in ["DATA FFL", "OUTPUT DIRECTORY"]:
                        if value:
                            value = value.replace("\\", "/")
                            abs_path = os.path.abspath(value).replace("\\", "/")
                            rel_path = os.path.relpath(abs_path, self.project_dir).replace("\\", "/")
                            if not rel_path.startswith(".") and not rel_path.startswith(".."):
                                rel_path = f"./{rel_path}"
                            value = rel_path
                    if key == "OUTPUT DIRECTORY" and not value:
                        value = self.default_output_dir
                    if key.startswith("DATA "):
                        formatted_line = f"{key}\t{value}\n"
                    elif key.startswith("PARAMETER "):
                        formatted_line = f"PARAMETER\t{key.split()[1]}\t{value}\n"
                    elif key.startswith("OUTPUT "):
                        formatted_line = f"OUTPUT\t{key.split()[1]}\t{value}\n"
                    else:
                        formatted_line = f"{key}\t{value}\n"
                    file.write(formatted_line)
            self.append_output_signal.emit(f"Configuration saved at '{self.config_path}'", "success")
            self.show_message_box_signal.emit("Success", f"Configuration has been saved successfully at '{self.config_path}'", "information")
        except Exception as e:
            self.append_output_signal.emit(f"Error saving config: {e}", "error")
            self.show_message_box_signal.emit("Error", f"An error occurred while saving the config: {str(e)}", "critical")

########################################################################################################################################
##########################################################################################################################################
########################################################################################################################################

def run_cli_interactive():
    # Display stylized GWEASY header
    header = """
---------------------------------------
******    **       **  *******     **      ******   **     **  
**        **       **  **         ****    **    **  **     **  
**        **       **  **        **  **   **         **   **    
**  ****  **   *   **  *****    **    **   ******     ** **    
**  ****  **  * *  **  **       ********        **     ***   
**    **  ** *   * **  **       **    **  **    **     ***    
********  ***     ***  *******  **    **   ******      ***  
---------------------------------------
                 v2.0
---------------------------------------
    """
    print(f"{COLORS['blue']}{header}{COLORS['reset']}")
    logging.info("Starting GWeasy CLI mode")

    # Prompt for tab selection
    while True:
        print(f"{COLORS['blue']}Select a tab to run (gravfetch, omicron, omiviz):{COLORS['reset']}")
        tab = input().strip().lower()
        if tab in ["gravfetch", "omicron", "omiviz"]:
            break
        print(f"{COLORS['red']}Invalid tab. Please choose 'gravfetch', 'omicron', or 'omiviz'.{COLORS['reset']}")

    if tab == "omiviz":
        print(f"{COLORS['yellow']}Omiviz is not implemented yet. Exiting.{COLORS['reset']}")
        logging.warning("Omiviz tab selected but not implemented")
        return

    if tab == "gravfetch":
        # Prompt for gravfetch parameters
        print(f"{COLORS['blue']}Enter path to time CSV file (e.g., times.csv):{COLORS['reset']}")
        while True:
            time_csv = input().strip()
            if os.path.exists(time_csv) and time_csv.endswith(".csv"):
                try:
                    pd.read_csv(time_csv)
                    break
                except Exception as e:
                    print(f"{COLORS['red']}Error reading CSV: {e}. Please try again.{COLORS['reset']}")
            else:
                print(f"{COLORS['red']}Invalid or non-existent CSV file. Please try again.{COLORS['reset']}")

        print(f"{COLORS['blue']}Enter path to channel CSV file (e.g., channels.csv):{COLORS['reset']}")
        while True:
            channel_csv = input().strip()
            if os.path.exists(channel_csv) and channel_csv.endswith(".csv"):
                try:
                    pd.read_csv(channel_csv, header=None, skiprows=1, names=["Channel", "Sample Rate"])
                    break
                except Exception as e:
                    print(f"{COLORS['red']}Error reading channel CSV: {e}. Please try again.{COLORS['reset']}")
            else:
                print(f"{COLORS['red']}Invalid or non-existent channel CSV file. Please try again.{COLORS['reset']}")

        print(f"{COLORS['blue']}Enter output directory (e.g., ./GWFout) [default: ./GWFout]:{COLORS['reset']}")
        output_dir = input().strip() or DEFAULT_GWFOUT
        if not os.path.exists(output_dir):
            print(f"{COLORS['yellow']}Output directory does not exist. Creating: {output_dir}{COLORS['reset']}")
            os.makedirs(output_dir, exist_ok=True)

        # Load time segments and channels
        try:
            time_ranges = pd.read_csv(time_csv)
            if not all(col in time_ranges.columns for col in ['GPSstart', 'GPSend']):
                time_ranges = pd.read_csv(time_csv, header=None, names=['GPSstart', 'GPSend'])
            segments = [f"{int(float(row['GPSstart']))}_{int(float(row['GPSend']))}" for _, row in time_ranges.iterrows()]
            channels_df = pd.read_csv(channel_csv, header=None, skiprows=1, names=["Channel", "Sample Rate"])
            channels = list(channels_df["Channel"])
        except Exception as e:
            print(f"{COLORS['red']}Error processing inputs: {e}{COLORS['reset']}")
            logging.error(f"Error processing inputs: {e}")
            return

        # Process each channel sequentially
        for channel in channels:
            print(f"{COLORS['blue']}Running Gravfetch for channel: {channel}{COLORS['reset']}")
            print(f"  Time CSV: {time_csv}")
            print(f"  Output Directory: {output_dir}")
            print(f"  Segments: {', '.join(segments)}")
            args = argparse.Namespace(tab="gravfetch", time_csv=time_csv, channel=channel, output_dir=output_dir, segments=",".join(segments), ffl_file=None)
            run_cli(args)

    elif tab == "omicron":
        print(f"{COLORS['blue']}Enter path to .ffl file (e.g., fin.ffl):{COLORS['reset']}")
        while True:
            ffl_file = input().strip()
            if os.path.exists(ffl_file) and ffl_file.endswith(".ffl"):
                try:
                    with open(ffl_file, "r") as f:
                        lines = [line.strip().split() for line in f if line.strip()]
                    if lines and len(lines[0]) >= 2 and len(lines[-1]) >= 2:
                        break
                    else:
                        print(f"{COLORS['red']}Invalid .ffl file format. Please try again.{COLORS['reset']}")
                except Exception as e:
                    print(f"{COLORS['red']}Error reading .ffl file: {e}. Please try again.{COLORS['reset']}")
            else:
                print(f"{COLORS['red']}Invalid or non-existent .ffl file. Please try again.{COLORS['reset']}")

        print(f"{COLORS['blue']}Running Omicron with the following parameters:{COLORS['reset']}")
        print(f"  FFL File: {ffl_file}")
        args = argparse.Namespace(tab="omicron", time_csv=None, channel=None, output_dir=None, segments=None, ffl_file=ffl_file)
        run_cli(args)

def run_cli(args):
    if args.tab == "gravfetch":
        logging.info(f"Running Gravfetch in CLI mode for channel: {args.channel}")
        if not all([args.time_csv, args.channel, args.output_dir, args.segments]):
            logging.error("Missing required arguments: time_csv, channel, output_dir, segments")
            print(f"{COLORS['red']}Missing required arguments: time_csv, channel, output_dir, segments{COLORS['reset']}")
            return
        try:
            time_ranges = pd.read_csv(args.time_csv)
            if not all(col in time_ranges.columns for col in ['GPSstart', 'GPSend']):
                time_ranges = pd.read_csv(args.time_csv, header=None, names=['GPSstart', 'GPSend'])
            segments = [f"{int(float(row['GPSstart']))}_{int(float(row['GPSend']))}" for _, row in time_ranges.iterrows()]
            os.makedirs(args.output_dir, exist_ok=True)
            ch_dir = os.path.join(args.output_dir, args.channel.replace(":", "_"))
            os.makedirs(ch_dir, exist_ok=True)
            fin_path = os.path.join(ch_dir, "fin.ffl")
            with open(fin_path, 'a') as fin:
                for seg in segments:
                    start, end = map(int, seg.split("_"))
                    tdir = os.path.join(ch_dir, f"{start}_{end}")
                    os.makedirs(tdir, exist_ok=True)
                    outfile = os.path.join(tdir, f"{args.channel.replace(':','_')}_{start}_{end}.gwf")
                    if os.path.exists(outfile):
                        logging.info(f"Segment {seg} already fetched for {args.channel}. Skipping.")
                        print(f"{COLORS['yellow']}Segment {seg} already fetched for {args.channel}. Skipping.{COLORS['reset']}")
                        continue
                    try:
                        logging.info(f"Fetching {args.channel} from {start} to {end}...")
                        print(f"{COLORS['blue']}Fetching {args.channel} from {start} to {end}...{COLORS['reset']}")
                        urls = get_urls(args.channel, start, end, host="gwosc-nds.ligo.org")
                        if not urls:
                            logging.warning(f"No data available for {args.channel} {start}-{end}. Skipping.")
                            print(f"{COLORS['yellow']}No data available for {args.channel} {start}-{end}. Skipping.{COLORS['reset']}")
                            continue
                        data = TimeSeries.read(urls, channel=args.channel, start=start, end=end)
                        data.write(outfile)
                        rel_path = os.path.relpath(outfile, os.getcwd()).replace("\\", "/")
                        dt = end - start
                        fin.write(f"./{rel_path} {start} {dt} 0 0\n")
                        logging.info(f"Saved to {outfile}")
                        print(f"{COLORS['green']}Saved to {outfile}{COLORS['reset']}")
                    except Exception as e:
                        logging.error(f"Error fetching {args.channel} {start}-{end}: {e}")
                        print(f"{COLORS['red']}Error fetching {args.channel} {start}-{end}: {e}{COLORS['reset']}")
        except Exception as e:
            logging.error(f"Error: {e}")
            print(f"{COLORS['red']}Error: {e}{COLORS['reset']}")
    elif args.tab == "omicron":
        logging.info("Running Omicron in CLI mode")
        if not args.ffl_file:
            logging.error("Missing required argument: ffl_file")
            print(f"{COLORS['red']}Missing required argument: ffl_file{COLORS['reset']}")
            return
        try:
            with open(args.ffl_file, "r") as f:
                lines = [line.strip().split() for line in f if line.strip()]
            if not lines or len(lines[0]) < 2 or len(lines[-1]) < 2:
                logging.error("Invalid .ffl file format.")
                print(f"{COLORS['red']}Invalid .ffl file format.{COLORS['reset']}")
                return
            first_time_segment = lines[0][1]
            last_time_segment = lines[-1][1]
            omicron_cmd = f"omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1"
            logging.info(f"Running: {omicron_cmd}")
            print(f"{COLORS['blue']}Running: {omicron_cmd}{COLORS['reset']}")
            process = subprocess.Popen(omicron_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    logging.info(output.strip())
                    print(f"{COLORS['blue']}{output.strip()}{COLORS['reset']}")
            while True:
                error = process.stderr.readline()
                if error == "" and process.poll() is not None:
                    break
                if error:
                    logging.error(f"ERROR: {error.strip()}")
                    print(f"{COLORS['red']}ERROR: {error.strip()}{COLORS['reset']}")
            process.wait()
            if process.returncode != 0:
                logging.error(f"Command failed with return code {process.returncode}.")
                print(f"{COLORS['red']}Command failed with return code {process.returncode}.{COLORS['reset']}")
            else:
                logging.info("OMICRON process completed successfully.")
                print(f"{COLORS['green']}OMICRON process completed successfully.{COLORS['reset']}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print(f"{COLORS['red']}Unexpected error: {e}{COLORS['reset']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GWeasy CLI")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--tab", choices=["gravfetch", "omicron", "omiviz"], help="Specify tab to run")
    parser.add_argument("--time_csv", help="Path to time CSV file")
    parser.add_argument("--channel", help="Channel to fetch")
    parser.add_argument("--output_dir", help="Output directory")
    parser.add_argument("--segments", help="Comma-separated list of segments (e.g., start1_end1,start2_end2)")
    parser.add_argument("--ffl_file", help="Path to .ffl file for Omicron")
    args = parser.parse_args()

    if args.cli:
        if args.tab:
            run_cli(args)
        else:
            run_cli_interactive()
    else:
        app = QApplication(sys.argv)
        splash = SplashScreen(lambda: MainWindow().show())
        splash.show()
        sys.exit(app.exec_())
















"""

******    **       **  *******     **      ******   **     **  
**        **       **  **         ****    **    **  **     **  
**        **       **  **        **  **   **         **   **    
**  ****  **   *   **  *****    **    **   ******     ** **    
**  ****  **  * *  **  **       ********        **     ***   
**    **  ** *   * **  **       **    **  **    **     ***    
********  ***     ***  *******  **    **   ******      ***  

"""
