
import os
import sys
import logging
import framel
# Set up logging to a file
logging.basicConfig(filename='GWeasy_log.txt', level=logging.DEBUG)

# Ensure the path to the DLL is added to the system path
if getattr(sys, 'frozen', False):
    # If running from the bundled .exe
    dll_path = os.path.join(sys._MEIPASS, 'libframel.dll')
    os.environ['FRAME_LIB_PATH'] = dll_path
else:
    # Running from the source code (during development)
    os.environ['FRAME_LIB_PATH'] = 'C:/Users/HP/miniconda3/envs/GWeasy/Library/bin/'

# Log the DLL path to a file
logging.debug(f"FRAME_LIB_PATH is set to: {os.environ['FRAME_LIB_PATH']}")


import wx
import json
import threading
import pandas as pd
from gwpy.timeseries import TimeSeries
import subprocess
from PIL import Image
import sys
import pandas as pd
from gwpy.timeseries import TimeSeries
import json
import logging
from gwosc.datasets import find_datasets, event_gps
from gwosc.locate import get_event_urls
from gwpy import time as gp_time
from gwosc import datasets
from datetime import datetime
from gwpy.timeseries import TimeSeries
from scipy.signal import get_window
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import csv




HISTORY_FILE = "gravfetch_history.json"

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="GWEasy", size=(1024, 768))
        notebook = wx.Notebook(self)
        # grav_tab = GravfetchApp(notebook)
        omicron_tab = OmicronApp(notebook)
        # omiviz_tab = wx.Panel(notebook)
        # notebook.AddPage(grav_tab, "Gravfetch")
        notebook.AddPage(omicron_tab, "OMICRON")
        # notebook.AddPage(omiviz_tab, "Omiviz")
        self.Centre()
        self.Show()
        
class TerminalFrame(wx.Panel):
    def __init__(self, parent, height=15, width=100):
        super().__init__(parent)

        self.text = wx.TextCtrl(
            self,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP
        )
        self.text.SetBackgroundColour("black")
        self.text.SetForegroundColour("white")
        self.text.SetFont(wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

    def append_output(self, message):
        self.text.SetDefaultStyle(wx.TextAttr("white", "black"))
        self.text.AppendText(message + "\n")
        self.text.ShowPosition(self.text.GetLastPosition())



class GravfetchApp(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.time_csv_file = ""
        self.channel_csv_file = ""
        self.gwfout_path = "./gwfout/"
        self.execution_running = False
        self.process = None
        self.loaded_channels = []

        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    history = json.load(f)
                    self.gwfout_path = history.get("gwfout_path", "./gwfout/")
                    self.loaded_channels = history.get("channels", [])
            except:
                print("Failed to read history file")

        self.setup_ui()

    def setup_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Status bar
        self.status_label = wx.StaticText(self, label="Idle")
        self.status_label.SetBackgroundColour("light gray")
        sizer.Add(self.status_label, 0, wx.EXPAND | wx.ALL, 5)

        # Buttons
        self.time_btn = wx.Button(self, label="Select Time CSV")
        self.channel_btn = wx.Button(self, label="Select Channel CSV")
        self.output_btn = wx.Button(self, label="Select Output Dir")
        self.toggle_btn = wx.Button(self, label="Start Execution")

        self.time_btn.Bind(wx.EVT_BUTTON, self.select_time_csv)
        self.channel_btn.Bind(wx.EVT_BUTTON, self.select_channel_csv)
        self.output_btn.Bind(wx.EVT_BUTTON, self.select_output_dir)
        self.toggle_btn.Bind(wx.EVT_BUTTON, self.toggle_execution)

        for btn in [self.time_btn, self.channel_btn, self.output_btn, self.toggle_btn]:
            sizer.Add(btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        # Terminal
        self.terminal = TerminalFrame(self, height=20)
        sizer.Add(self.terminal, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def select_time_csv(self, evt):
        dlg = wx.FileDialog(self, "Select Time CSV", wildcard="*.csv", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.time_csv_file = dlg.GetPath()
            self.status_label.SetLabel(f"Selected Time CSV: {self.time_csv_file}")
        dlg.Destroy()

    def select_channel_csv(self, evt):
        dlg = wx.FileDialog(self, "Select Channel CSV", wildcard="*.csv", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.channel_csv_file = dlg.GetPath()
            self.status_label.SetLabel(f"Selected Channel CSV: {self.channel_csv_file}")
        dlg.Destroy()

    def select_output_dir(self, evt):
        dlg = wx.DirDialog(self, "Select Output Directory")
        if dlg.ShowModal() == wx.ID_OK:
            self.gwfout_path = dlg.GetPath()
            self.status_label.SetLabel(f"Selected Output Dir: {self.gwfout_path}")
        dlg.Destroy()

    def toggle_execution(self, evt):
        if self.execution_running:
            self.execution_running = False
            self.toggle_btn.SetLabel("Start Execution")
            self.status_label.SetLabel("Execution Stopped")
            self.status_label.SetForegroundColour("red")
            self.append_output("Execution stopped.")
        else:
            if not self.time_csv_file or not self.channel_csv_file:
                self.append_output("Please select both CSV files.")
                return
            self.execution_running = True
            self.toggle_btn.SetLabel("Stop Execution")
            self.status_label.SetLabel("Execution Started")
            self.status_label.SetForegroundColour("green")
            self.append_output("Execution started...")
            threading.Thread(target=self.run_gravfetch, daemon=True).start()

    def append_output(self, message):
        wx.CallAfter(self.terminal.append_output, message)


    def run_gravfetch(self):
        try:
            os.makedirs(self.gwfout_path, exist_ok=True)

            time_ranges = pd.read_csv(self.time_csv_file, header=None, names=["start", "end"])
            channels = pd.read_csv(self.channel_csv_file, header=None, skiprows=1, names=["Channel", "Sample Rate"])
            current_dir = os.getcwd()

            self.loaded_channels = []

            for _, channel_row in channels.iterrows():
                ch = channel_row["Channel"]
                rate = channel_row["Sample Rate"]
                self.loaded_channels.append(ch)

                ch_dir = os.path.join(self.gwfout_path, ch.replace(":", "_"))
                os.makedirs(ch_dir, exist_ok=True)
                fin_path = os.path.join(ch_dir, "fin.ffl")

                with open(fin_path, 'a') as fin:
                    for _, row in time_ranges.iterrows():
                        start, end = int(row["start"]), int(row["end"])
                        try:
                            self.append_output(f"Fetching {ch} from {start} to {end}...")
                            data = TimeSeries.fetch(ch, start=start, end=end, host="nds.gwosc.org")
                            tdir = os.path.join(ch_dir, f"{start}_{end}")
                            os.makedirs(tdir, exist_ok=True)
                            outfile = os.path.join(tdir, f"{ch.replace(':','_')}_{start}_{end}.gwf")
                            data.write(outfile)
                            rel_path = os.path.relpath(outfile, current_dir).replace("\\", "")
                            dt = end - start
                            fin.write(f"./{rel_path} {start} {dt} 0 0\n")
                            self.append_output(f"Saved to {outfile}")
                        except Exception as e:
                            self.append_output(f"Error fetching {ch} {start}-{end}: {e}")

            self.execution_running = False
            self.toggle_btn.SetLabel("Start Execution")
            self.status_label.SetLabel("Execution Finished")
            self.status_label.SetForegroundColour("green")
            self.append_output("Execution complete.")
            self.save_history()

        except Exception as e:
            self.append_output(f"Error: {e}")
            self.execution_running = False
            self.toggle_btn.SetLabel("Start Execution")
            self.status_label.SetLabel("Execution Failed")
            self.status_label.SetForegroundColour("red")

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump({"gwfout_path": self.gwfout_path, "channels": self.loaded_channels}, f, indent=2)



##################################################################OMICRON####################################################################

class OmicronApp(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.config_path = "config.txt"
        self.config_data = {}
        self.ui_elements = {}
        self.project_dir = os.getcwd().replace("\\", "/")
        self.wsl_project_dir = f"/mnt/{self.project_dir[0].lower()}/{self.project_dir[2:]}"
        self.GWFOUT_DIRECTORY = "./gwfout"

        # Terminal output frame at bottom
        self.terminal = TerminalFrame(self)

        # Scrollable main content area
        self.scrollable = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scrollable.SetScrollRate(5, 20)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrollable.SetSizer(self.scroll_sizer)

        # Main vertical layout: scrollable area + terminal output
        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.scrollable, 1, wx.EXPAND | wx.ALL, 5)
        layout.Add(self.terminal, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(layout)

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        """Create the different widgets for the interface."""
        # Create a dropdown for selecting channels
        self.create_channel_dropdown(row=1)

        # File selector and sampling frequency
        self.create_file_selector("Select .ffl File:", "DATA FFL", row=2, column=0)
        self.create_editable_dropdown("Sampling Frequency:", "DATA SAMPLEFREQUENCY", ["1024", "2048", "4096"], row=3, column=0)

        # Buttons
        button_frame = wx.Panel(self.scrollable)
        button_frame_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.custom_segs_btn = wx.Button(button_frame, label="Custom Segs")
        self.custom_segs_btn.Bind(wx.EVT_BUTTON, self.open_custom_segs_dialog)
        button_frame_sizer.Add(self.custom_segs_btn, 0, wx.ALL, 10)
        self.save_button = wx.Button(button_frame, label="Save Config")
        self.save_button.Bind(wx.EVT_BUTTON, self.save_config)
        button_frame_sizer.Add(self.save_button, 0, wx.ALL, 10)
        self.start_button = wx.Button(button_frame, label="Start OMICRON")
        self.start_button.Bind(wx.EVT_BUTTON, self.run_omicron_script)
        button_frame_sizer.Add(self.start_button, 0, wx.ALL, 10)
        button_frame.SetSizer(button_frame_sizer)
        self.scroll_sizer.Add(button_frame, 0, wx.EXPAND | wx.ALL, 5)

        # PARAMETER FRAME
        param_frame = wx.Panel(self.scrollable)
        param_main_sizer = wx.BoxSizer(wx.VERTICAL)
        param_frame.SetSizer(param_main_sizer)

        # Double entries - 3 columns
        double_entry_sizer = wx.FlexGridSizer(rows=0, cols=3, hgap=1, vgap=5)
        double_entry_sizer.AddGrowableCol(0)
        double_entry_sizer.AddGrowableCol(1)
        double_entry_sizer.AddGrowableCol(2)
        self.create_double_entry("Timing:", "PARAMETER TIMING", param_frame, double_entry_sizer, size=(100, -1))  
        self.create_double_entry("Frequency Range:", "PARAMETER FREQUENCYRANGE", param_frame, double_entry_sizer, size=(100, -1))
        self.create_double_entry("Q-Range:", "PARAMETER QRANGE", param_frame, double_entry_sizer, size=(100, -1))
        param_main_sizer.Add(double_entry_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Single entries - 2 columns
        single_entry_sizer = wx.FlexGridSizer(rows=0, cols=2, hgap=10, vgap=5)
        single_entry_sizer.AddGrowableCol(0)
        single_entry_sizer.AddGrowableCol(1)
        self.create_entry("Mismatch Max:", "PARAMETER MISMATCHMAX", param_frame, single_entry_sizer, size=(100, -1))
        self.create_entry("SNR Threshold:", "PARAMETER SNRTHRESHOLD", param_frame, single_entry_sizer, size=(100, -1))
        self.create_entry("PSD Length:", "PARAMETER PSDLENGTH", param_frame, single_entry_sizer, size=(100, -1))
        param_main_sizer.Add(single_entry_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.scroll_sizer.Add(param_frame, 0, wx.EXPAND | wx.ALL, 5)

        # OUTPUT FRAME
        output_frame = wx.Panel(self.scrollable)
        output_frame_sizer = wx.BoxSizer(wx.VERTICAL)
        output_frame.SetSizer(output_frame_sizer)

        self.create_folder_selector("Select Output Directory:", "OUTPUT DIRECTORY", is_directory=True, frame=output_frame, row=13, column=0)
        self.create_output_products_selection(output_frame, row=14, column=0)
        self.create_dropdown("Select Format:", "OUTPUT FORMAT", ["root", "hdf5", "Format3"], frame=output_frame, row=15, column=0)
        self.create_slider("Verbosity (0-3):", "OUTPUT VERBOSITY", 0, 3, frame=output_frame, row=16, column=0)

        self.scroll_sizer.Add(output_frame, 0, wx.EXPAND | wx.ALL, 5)

    def create_entry(self, label, key, parent, sizer, size=(100, -1)):
        label_widget = wx.StaticText(parent, label=label)
        var = self.config_data.get(key, "")
        entry = wx.TextCtrl(parent, value=var, size=size)
        sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(entry, 0, wx.ALL, 5)
        self.ui_elements[key] = entry


    def create_double_entry(self, label, key, parent, sizer, size=(100, -1)):
        label_widget = wx.StaticText(parent, label=label)
        var1 = self.config_data.get(f"{key}_1", "")
        var2 = self.config_data.get(f"{key}_2", "")
        entry1 = wx.TextCtrl(parent, value=var1, size=size)
        entry2 = wx.TextCtrl(parent, value=var2, size=size)
        sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(entry1, 0, wx.ALL , 5)
        sizer.Add(entry2, 0, wx.ALL , 5)
        self.ui_elements[key] = (entry1, entry2)


    def create_file_selector(self, label, key, is_directory=False, frame=None, row=0, column=0):
        """Creates a file/directory selector inside the given frame (or default to scrollable_frame)."""
        target_frame = frame if frame else self.scrollable
        label_widget = wx.StaticText(target_frame, label=label)
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        var = self.config_data.get(key, "")
        entry = wx.TextCtrl(target_frame, value=var, style=wx.TE_READONLY, size=(400, -1))  # Adjust size as needed
        target_frame_sizer.Add(entry, 0, wx.ALL | wx.EXPAND, 5)
        
        # Create a button for selecting the file
        button = wx.Button(target_frame, label="Select")
        # button.Bind(wx.EVT_BUTTON, lambda event: self.select_file(var, is_directory))
        button.Bind(wx.EVT_BUTTON, lambda event, entry=entry: self.select_file(entry, is_directory))

        target_frame_sizer.Add(button, 0, wx.ALL, 5)
        
        # Store the entry widget
        self.ui_elements[key] = entry

    def create_folder_selector(self, label, key, is_directory=False, frame=None, row=0, column=0):
        """Creates a folder selector inside the given frame (or default to scrollable_frame).
        Ensures paths are relative to the current working directory and creates the directory if missing.
        Returns the selected relative path.
        """
        target_frame = frame if frame else self.scrollable
        
        # Create label for the selector
        label_widget = wx.StaticText(target_frame, label=label)
        
        # Ensure the frame has a sizer and initialize it if necessary
        target_frame_sizer = target_frame.GetSizer()
        if target_frame_sizer is None:
            target_frame_sizer = wx.BoxSizer(wx.HORIZONTAL)
            target_frame.SetSizer(target_frame_sizer)
        
        # Add label widget to sizer
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Retrieve the previously saved path (or set default if empty)
        var = self.config_data.get(key, "")
        dir_path = var.strip()
        if not dir_path:
            dir_path = os.path.join(os.getcwd(), "OmicronOut")
        
        abs_path = os.path.abspath(dir_path)
        rel_path = os.path.relpath(abs_path, os.getcwd())
        rel_path = rel_path.replace("\\", "/")
        if not rel_path.startswith(".") and not rel_path.startswith(".."):
            rel_path = f"./{rel_path}"
        
        var = rel_path  # Update var with the relative path
        if not os.path.exists(abs_path):
            os.makedirs(abs_path, exist_ok=True)
            self.append_output(f"Created missing directory: {rel_path}\n")
        
        # Create a TextCtrl to display the folder path (readonly)
        entry = wx.TextCtrl(target_frame, value=var, style=wx.TE_READONLY, size=(400, -1))
        target_frame_sizer.Add(entry, 0, wx.ALL | wx.EXPAND, 5)
        
        # Create a button for selecting the folder
        button = wx.Button(target_frame, label="Select")
        button.Bind(wx.EVT_BUTTON, lambda event, entry=entry: self.select_file(entry, is_directory))
        target_frame_sizer.Add(button, 0, wx.ALL, 5)
        
        # Store the entry widget
        self.ui_elements[key] = entry
        
        return rel_path  # Return the relative path


    def create_output_products_selection(self, frame=None, row=0, column=0):
        """Creates checkboxes for selecting output products inside a given frame."""
        target_frame = frame if frame else self.scrollable
        
        # Create the label for the selection
        label_widget = wx.StaticText(target_frame, label="Select Output Products:")
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Product options
        product_options = ["triggers", "html"]
        
        # Create a dictionary to store checkboxes
        self.ui_elements["OUTPUT PRODUCTS"] = {}
        
        # Create checkboxes for each product option
        for idx, product in enumerate(product_options):
            # Check if the product was previously selected (use default value if not set)
            selected = product in self.config_data.get("OUTPUT PRODUCTS", [])
            
            # Create checkbox for the product
            chk = wx.CheckBox(target_frame, label=product)
            chk.SetValue(selected)  # Set the initial state of the checkbox
            target_frame_sizer.Add(chk, 0, wx.ALL | wx.ALIGN_LEFT, 5)
            
            # Store the checkbox in the ui_elements dictionary
            self.ui_elements["OUTPUT PRODUCTS"][product] = chk

        # Update the layout
        target_frame.Layout()


    def create_dropdown(self, label, key, options, frame=None, row=0, column=0):
        """Creates a dropdown menu inside a given frame."""
        target_frame = frame if frame else self.scrollable
        
        # Create the label for the dropdown
        label_widget = wx.StaticText(target_frame, label=label)
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Retrieve the previously saved selection (or use the first option as default)
        selected_option = self.config_data.get(key, options[0])
        
        # Create the dropdown (Choice) for non-editable options
        dropdown = wx.Choice(target_frame, choices=options)
        # Set the default selection (index of the chosen option)
        dropdown.SetStringSelection(selected_option)
        
        # Add the dropdown to the sizer
        target_frame_sizer.Add(dropdown, 0, wx.ALL | wx.EXPAND, 5)
        
        # Store the dropdown widget in the ui_elements dictionary
        self.ui_elements[key] = dropdown

    def create_editable_dropdown(self, label, key, options, frame=None, row=0, column=0):
        """Creates an editable dropdown menu inside a given frame."""
        target_frame = frame if frame else self.scrollable
        
        # Create the label for the editable dropdown
        label_widget = wx.StaticText(target_frame, label=label)
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Retrieve the previously saved selection (or use the first option as default)
        selected_option = self.config_data.get(key, options[0])
        
        # Create the editable dropdown (ComboBox)
        dropdown = wx.ComboBox(target_frame, value=selected_option, choices=options, style=wx.CB_DROPDOWN)
        
        # Add the dropdown to the sizer
        target_frame_sizer.Add(dropdown, 0, wx.ALL | wx.EXPAND, 5)
        
        # Store the dropdown widget in the ui_elements dictionary
        self.ui_elements[key] = dropdown
        
        return dropdown  # Return the dropdown in case it needs further manipulation
    
    def on_slider_change(self, event):
        slider = event.GetEventObject()  # Get the slider object
        value = slider.GetValue()  # Get the current value of the slider
        print(f"Slider value changed: {value}")
        # You can perform actions here based on the slider's value
        event.Skip()  # Propagate the event (if needed)

    def create_slider(self, label, key, min_val, max_val, frame=None, row=0, column=0):
        """Creates a slider for selecting a numerical value."""
        target_frame = frame if frame else self.scrollable

        # Create the label for the slider
        label_widget = wx.StaticText(target_frame, label=label)
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label_widget, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Retrieve the previously saved slider value (or use min_val as default)
        slider_value = self.config_data.get(key, min_val)
        
        # Create the slider with the saved or default value
        slider = wx.Slider(target_frame, value=slider_value, minValue=min_val, maxValue=max_val, style=wx.SL_HORIZONTAL)
        
        # Add the slider to the sizer
        target_frame_sizer.Add(slider, 0, wx.ALL | wx.EXPAND, 5)
        
        # Store the slider in the ui_elements dictionary for future use
        self.ui_elements[key] = slider
        
        # Optionally add an event to track value changes (if needed)
        slider.Bind(wx.EVT_SLIDER, self.on_slider_change)

        # Optionally return the slider and label widget in a tuple
        return slider, label_widget


    def create_channel_dropdown(self, row=0):
        """Creates an editable dropdown for selecting a channel, updating dynamically in the background."""
        target_frame = self.scrollable  # The frame to which the dropdown will be added
        
        # Create the label for the dropdown
        label = wx.StaticText(target_frame, label="Select Channel:")
        target_frame_sizer = target_frame.GetSizer()
        target_frame_sizer.Add(label, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        
        # Create a wx.ComboBox (editable dropdown)
        self.ui_elements["DATA CHANNELS"] = wx.ComboBox(target_frame, style=wx.CB_DROPDOWN)
        self.channel_dropdown = self.ui_elements["DATA CHANNELS"]
        target_frame_sizer.Add(self.channel_dropdown, 0, wx.ALL | wx.EXPAND, 5)
        
        def populate_channels():
            """Get available channels from the directory and saved history."""
            base_path = self.GWFOUT_DIRECTORY
            history_file = "gravfetch_history.json"
            channels = set()
            default_structure = {"gwfout_path": str(base_path), "channels": []}
            
            # Check if the history file exists, and if not, create it with default structure
            if not os.path.exists(history_file):
                with open(history_file, "w") as file:
                    json.dump(default_structure, file, indent=4)
                print(f"Created missing history file: {history_file}")
            
            # Try to load the history file
            try:
                with open(history_file, "r") as file:
                    history_data = json.load(file)
                if not isinstance(history_data, dict) or "channels" not in history_data:
                    history_data = default_structure
                    with open(history_file, "w") as file:
                        json.dump(history_data, file, indent=4)
                    print(f"Fixed malformed history file: {history_file}")
                channels.update(history_data["channels"])
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Warning: History file corrupted, resetting: {e}")
                history_data = default_structure
                with open(history_file, "w") as file:
                    json.dump(history_data, file, indent=4)
            
            # Add directories from the base path to the channel list
            if os.path.exists(base_path) and os.path.isdir(base_path):
                for d in os.listdir(base_path):
                    dir_path = os.path.join(base_path, d)
                    if os.path.isdir(dir_path):
                        if d.count(":") > 1:
                            d = d[:d.find(":", d.find(":") + 1)].replace(":", "_") + d[d.find(":", d.find(":") + 1):]
                        channels.add(d)
            
            return sorted(channels) if channels else ["No Channels Available"]
        
        def update_channel_options():
            """Update the dropdown values without affecting user input."""
            current_input = self.channel_dropdown.GetValue()  # Save current input
            channel_options = populate_channels()  # Get updated channel list
            self.channel_dropdown.SetItems(channel_options)  # Replace all items
            if current_input in channel_options:
                self.channel_dropdown.SetValue(current_input)  # Restore if still available
            else:
                self.channel_dropdown.SetValue(current_input)  # Still preserve even if not listed

            wx.CallLater(4000, update_channel_options)

        
        update_channel_options()  # Initial call to populate and update the dropdown
        return self.channel_dropdown
    
    def select_file(self, text_ctrl, is_directory=False):
        file_path = None  # Ensure it's defined

        if is_directory:
            with wx.DirDialog(self, "Choose a directory", style=wx.DD_DEFAULT_STYLE) as dir_dialog:
                if dir_dialog.ShowModal() == wx.ID_OK:
                    file_path = dir_dialog.GetPath()
        else:
            with wx.FileDialog(self, "Choose a file", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:
                if file_dialog.ShowModal() == wx.ID_OK:
                    file_path = file_dialog.GetPath()

        if file_path:
            relative_path = os.path.relpath(file_path, os.getcwd()).replace("\\", "/")
            text_ctrl.SetValue(relative_path)
            print(f"File selected: {relative_path}")  # Debugging


    def load_config(self):
        """Load configuration data from a file."""
        try:
            with open(self.config_path, 'r') as file:
                for line in file:
                    parts = line.strip().split("\t")
                    if len(parts) == 2:
                        self.config_data[parts[0]] = parts[1]
        except FileNotFoundError:
            print("Config file not found. Using defaults.")
            # You can use wx.MessageDialog for user-friendly error handling
            # wx.MessageBox("Config file not found. Using defaults.", "Error", wx.ICON_ERROR)
    
    def get_widget_value(self, widget):
        """Safely retrieve the value from various wxPython widgets."""
        try:
            if isinstance(widget, wx.ComboBox) or isinstance(widget, wx.TextCtrl):
                return widget.GetValue()
            elif isinstance(widget, wx.Choice):
                return widget.GetStringSelection()
            elif isinstance(widget, wx.CheckBox):
                return widget.GetValue()
            else:
                return str(widget)  # fallback
        except Exception as e:
            print(f"Widget value error: {e}")
            return ""

    def save_config(self,event):
        """Save the configuration to the config file."""
        base_path = os.getcwd().replace("\\", "/")  # Get current working directory with forward slashes
        try:
            with open(self.config_path, 'w', encoding='utf-8') as file:
                for key, var in self.ui_elements.items():
                    if isinstance(var, tuple):  # For double-entry fields
                        value = f"{var[0].GetValue()} {var[1].GetValue()}"
                    elif isinstance(var, dict):  # For multiple selections (checkboxes)
                        selected_products = [prod for prod, v in var.items() if v.GetValue()]
                        value = " ".join(selected_products)
                    elif isinstance(var, wx.Slider):  # For sliders
                        value = var.GetValue()  # Get the numerical value of the slider
                    else:
                        value = self.get_widget_value(var)
                    if key == "DATA CHANNELS":
                        parts = value.split("_", 1)  # Split at the first underscore 
                    if key in ["DATA FFL", "OUTPUT DIRECTORY"]:  
                        print(key)  # Debugging
                        if value:
                            value = value.replace("\\", "/")  
                            abs_path = os.path.abspath(value).replace("\\", "/")  # Ensure absolute path uses `/`
                            if abs_path.startswith(base_path):  
                                rel_path = os.path.relpath(abs_path, base_path).replace("\\", "/")  # Convert to relative path
                                if not rel_path.startswith(".") and not rel_path.startswith(".."):
                                    rel_path = f"./{rel_path}"
                                value = rel_path  # Assign the corrected relative path
                                print("Relative Path:", value)  # Debugging
                                print("Absolute Path:", abs_path)  # Debugging
                    
                    if key.startswith("DATA "):
                        formatted_line = f"{key}\t{value}\n"
                    elif key.startswith("PARAMETER "):
                        formatted_line = f"PARAMETER\t{key.split()[1]}\t{value}\n"
                    elif key.startswith("OUTPUT "):  
                        formatted_line = f"OUTPUT\t{key.split()[1]}\t{value}\n"
                    else:
                        formatted_line = f"{key}\t{value}\n"
                    print(f"Saving to config: {formatted_line.strip()}")  # Debugging
                    file.write(formatted_line)

            # Inform the user about the successful save using wx.MessageBox
            wx.MessageBox(f"Configuration has been saved successfully at '{self.config_path}'", "Success", wx.ICON_INFORMATION)

        except Exception as e:
            # Handle any potential errors
            wx.MessageBox(f"An error occurred while saving the config: {str(e)}", "Error", wx.ICON_ERROR)
            print(f"Error saving config: {str(e)}")

    def run_omicron_script(self,event):
        """Start the OMICRON script in a separate thread and update the output in real-time."""
        self.append_output("Starting OMICRON script...\n")
        # Start the thread to run the OMICRON process
        threading.Thread(target=self.start_omicron_process, daemon=True).start()

    def start_omicron_process(self):
        """Run the OMICRON command dynamically in WSL."""
        try:
            ffl_widget = self.ui_elements.get("DATA FFL")
            ffl_file = ffl_widget.GetValue().strip() if ffl_widget else ""
            if not ffl_file or not os.path.exists(ffl_file):
                self.append_output("Error: No valid .ffl file selected.\n")
                return
            with open(ffl_file, "r") as f:
                lines = [line.strip().split() for line in f if line.strip()]
            if not lines or len(lines[0]) < 2 or len(lines[-1]) < 2:
                self.append_output("Error: Invalid .ffl file format.\n")
                return
            first_time_segment = lines[0][1]
            last_time_segment = lines[-1][1]
            omicron_cmd = f"omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1"
            wsl_command = f'wsl bash -ic "{omicron_cmd}"'
            self.append_output(f"Running: {wsl_command}\n")

            # Start the process and capture stdout and stderr
            process = subprocess.Popen(
                wsl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Read stdout and stderr in real-time
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    self.append_output(output)

            # Read stderr in real-time
            while True:
                error = process.stderr.readline()
                if error == "" and process.poll() is not None:
                    break
                if error:
                    self.append_output(f"ERROR: {error}")

            process.wait()
            if process.returncode != 0:
                self.append_output(f"Error: Command failed with return code {process.returncode}.\n")
            else:
                self.append_output("OMICRON process completed successfully.\n")
        except Exception as e:
            self.append_output(f"Unexpected error: {e}\n")

    def append_output(self, text):
            """Append output to the TextCtrl."""
            # self.output_text_ctrl.AppendText(text)  # Assuming 'self.output_text_ctrl' is a wx.TextCtrl
            # self.output_text_ctrl.ShowPosition(self.output_text_ctrl.GetLastPosition())  # Auto-scroll to the bottom
            wx.CallAfter(self.terminal.append_output, text)

    def open_custom_segs_dialog(self,event):
            """Opens a GUI window to select a channel and time segments with scrolling and dynamic layout."""
            # Step 1: Ask user to select a channel directory
            channel_dir = wx.DirDialog(self, "Select Channel Directory", style=wx.DD_DEFAULT_STYLE)
            if channel_dir.ShowModal() != wx.ID_OK:
                return

            channel_dir = channel_dir.GetPath()
            segments = [d for d in os.listdir(channel_dir) if os.path.isdir(os.path.join(channel_dir, d))]
            if not segments:
                wx.MessageBox("No time segments found in selected channel.", "Error", wx.OK | wx.ICON_ERROR)
                return

            # Step 2: Create the selection window (Dialog)
            selection_window = wx.Dialog(self, title="Select Time Segments", size=(400, 400))
            selection_window.Center()
            
            # Create a sizer to layout elements vertically
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # Label for instructions
            label = wx.StaticText(selection_window, label="Select Time Segments:")
            main_sizer.Add(label, 0, wx.ALL | wx.CENTER, 10)

            # Step 3: Create a panel and sizer for scrollable content
            # scroll_panel = wx.Panel(selection_window)
            # scroll_sizer = wx.BoxSizer(wx.VERTICAL)
            
            # selected_segments = {}
            # for idx, segment in enumerate(segments):
            #     selected_segments[segment] = wx.CheckBox(scroll_panel, label=segment)
            #     scroll_sizer.Add(selected_segments[segment], 0, wx.ALL, 5)

            # scroll_panel.SetSizer(scroll_sizer)
            
            # # Step 4: Create the scrollable window
            # scrolled_window = wx.ScrolledWindow(selection_window)
            # scrolled_window.SetScrollRate(5, 5)
            # scrolled_window.SetSizerAndFit(scroll_panel.GetSizer())

            # main_sizer.Add(scrolled_window, 1, wx.EXPAND)
            scrolled_window = wx.ScrolledWindow(selection_window, style=wx.VSCROLL)
            scrolled_window.SetScrollRate(5, 5)

            scroll_sizer = wx.BoxSizer(wx.VERTICAL)
            selected_segments = {}

            for idx, segment in enumerate(segments):
                chk = wx.CheckBox(scrolled_window, label=segment)
                selected_segments[segment] = chk
                scroll_sizer.Add(chk, 0, wx.ALL, 5)

            scrolled_window.SetSizer(scroll_sizer)
            main_sizer.Add(scrolled_window, 1, wx.EXPAND | wx.ALL, 10)

            # Step 5: Bottom button panel
            button_panel = wx.Panel(selection_window)
            button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            confirm_button = wx.Button(button_panel, label="Confirm")
            toggle_button = wx.Button(button_panel, label="Toggle All")
            button_sizer.Add(confirm_button, 0, wx.ALL, 10)
            button_sizer.Add(toggle_button, 0, wx.ALL, 10)
            
            button_panel.SetSizer(button_sizer)
            
            # Add button panel to main sizer
            main_sizer.Add(button_panel, 0, wx.EXPAND)

            # Set main sizer for the dialog
            selection_window.SetSizer(main_sizer)
            
            # Show the dialog
            
            

            # Step 6: Button Event Handlers
            def confirm_selection(event):
                selected = [seg for seg, chk in selected_segments.items() if chk.GetValue()]
                if not selected:
                    wx.MessageBox("No segments selected.", "Error", wx.OK | wx.ICON_ERROR)
                else:
                    # Assuming `generate_fin_ffl` method exists to handle further processing
                    self.generate_fin_ffl(channel_dir, selected)
                    selection_window.Destroy()

            def toggle_all(event):
                all_selected = all(chk.GetValue() for chk in selected_segments.values())
                for chk in selected_segments.values():
                    chk.SetValue(not all_selected)
            confirm_button.Bind(wx.EVT_BUTTON, confirm_selection)
            toggle_button.Bind(wx.EVT_BUTTON, toggle_all)
            selection_window.ShowModal()

    def generate_fin_ffl(self, channel_dir, selected_segments):
            """Generates fin.ffl file with correctly formatted paths and timestamps, then preselects it in the UI."""
            fin_ffl_path = os.path.join(channel_dir, "fin.ffl")
            
            try:
                with open(fin_ffl_path, "w") as ffl_file:
                    for segment in selected_segments:
                        segment_path = os.path.join(channel_dir, segment)
                        gwf_files = [file for file in os.listdir(segment_path) if file.endswith(".gwf")]
                        if not gwf_files:
                            continue  # Skip if no GWF files
                        gwf_file_path = os.path.join(segment_path, gwf_files[0])
                        gwf_file_path = os.path.relpath(gwf_file_path, start=".")  # Truncate path to start from `./`
                        gwf_file_path = gwf_file_path.replace("\\", "/")  # Convert \ to /
                        segment_parts = segment.split("_")
                        start_time = segment_parts[0]  # Use the first timestamp as is
                        duration = int(segment_parts[1]) - int(segment_parts[0])  # Calculate duration
                        ffl_file.write(f"./{gwf_file_path} {start_time} {duration} 0 0\n")

                # After writing the file, select it in the UI
                relative_ffl_path = os.path.relpath(fin_ffl_path, os.getcwd()).replace("\\", "/")
                self.ui_elements["DATA FFL"].SetValue(relative_ffl_path)  # Assuming it's a wx.TextCtrl or similar element
                wx.MessageBox(f"fin.ffl created and selected: {relative_ffl_path}", "Success", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"An error occurred while creating fin.ffl: {e}", "Error", wx.OK | wx.ICON_ERROR)



#############################################################################################################################################



if __name__ == "__main__":
    app = wx.App(False)
    MainFrame()
    app.MainLoop()








