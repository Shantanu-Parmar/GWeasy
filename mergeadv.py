import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk,Canvas,messagebox
import threading
import subprocess
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import scrolledtext

class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Gravfetch and OMICRON Processing")

        # Setup the main notebook (tab structure)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Configure root window to allow resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Add the first tab for script execution (Gravfetch)
        self.gravfetch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.gravfetch_tab, text="Gravfetch")

        # Add the second tab for OMICRON
        self.omicron_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.omicron_tab, text="OMICRON")

        # Initialize both GUIs (Gravfetch and OMICRON) in their respective tabs
        self.gravfetch_app = GravfetchApp(self.gravfetch_tab)
        self.omicron_app = OmicronApp(self.omicron_tab)

class TerminalFrame(tk.Frame):
    def __init__(self, parent, row, column, rowspan=1, columnspan=1, height=15, width=100):
        super().__init__(parent)

        # Configure terminal output widget
        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, 
                                                     bg="black", fg="white",
                                                     font=("Courier", 10),
                                                     height=height, width=width)
        self.output_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.output_text.config(state="disabled")  # Prevent user editing

        # Image label for logo
        self.image_label = tk.Label(self, bg="black")
        self.image_label.place(relx=0.5, rely=0.5, anchor="center")  # Initial centering

        # Trigger image update
        self.after(100, self.update_logo_image)

        # Bind resize event
        self.bind("<Configure>", lambda event: self.update_logo_image())

        # Place frame using grid
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky="nsew", padx=10, pady=10)

    def update_logo_image(self):
        """Loads 'bkl.png', scales it 30% larger, and keeps it centered."""
        try:
            img = Image.open("bkl.png")

            # Get terminal frame size
            frame_width = self.output_text.winfo_width()
            frame_height = self.output_text.winfo_height()

            # Scale logo to 40% of terminal height (30% larger than before)
            logo_size = int(frame_height * 0.4)  # Adjusted for increased size
            img = img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            self.bg_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.bg_image)

            # Recenter image
            self.image_label.place(relx=0.5, rely=0.5, anchor="center")

        except Exception as e:
            print("Error loading logo image:", e)

    def append_output(self, text, color="white"):
        """Append text to the terminal and auto-scroll."""
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.yview(tk.END)  # Auto-scroll to latest output
        self.output_text.config(state="disabled")


class OmicronApp:
    def __init__(self, root):
        self.root = root
        self.config_path = "config.txt"
        self.config_data = {}
        self.entries = {}
        self.output_products = {}
        self.ui_elements = {}
        self.load_config()

        # Scrollable Frame
        self.canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.window_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Terminal Output
        # Use shared terminal frame
        self.terminal = TerminalFrame(self.root, row=4, column=0, columnspan=2, height=10, width=80)  # Pass the shared terminal instance
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        self.create_channel_dropdown(row=1)
        self.create_file_selector("Select .ffl File:", "DATA FFL",row=2,column=0)
        self.create_dropdown("Sampling Frequency:", "DATA SAMPLEFREQUENCY", ["1024", "2048", "4096"],row=3,column=0)
        # Ensure proper column expansion
        for i in range(4):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)


        # Button Frame
        button_frame = tk.Frame(self.scrollable_frame,bd=2, relief="groove", padx=5, pady=5)
        button_frame.grid(row=10, column=0, columnspan=4, pady=10, sticky="ew")
        self.save_button = tk.Button(button_frame, text="Save Config", command=self.save_config)
        self.save_button.pack(side="left", padx=10)  
        self.start_button = tk.Button(button_frame, text="Start OMICRON", command=self.run_omicron_script)
        self.start_button.pack(side="left", padx=10)  
        self.custom_segs_btn = tk.Button(button_frame, text="Custom Segs", command=self.open_custom_segs_dialog)
        self.custom_segs_btn.pack(side="left", padx=10)  # Adjust position as needed
        # Parameter Frame
        param_frame = tk.Frame(self.scrollable_frame,bd=2, relief="groove", padx=5, pady=5)
        param_frame.grid(row=11, column=0, columnspan=4, pady=10, sticky="ew")
        self.create_double_entry("Timing:", "PARAMETER TIMING", param_frame, 0, 0)
        self.create_double_entry("Frequency Range:", "PARAMETER FREQUENCYRANGE", param_frame, 0, 10)
        self.create_double_entry("Q-Range:", "PARAMETER QRANGE", param_frame, 1, 0)
        self.create_entry("Mismatch Max:", "PARAMETER MISMATCHMAX", param_frame, 1, 10)
        self.create_entry("SNR Threshold:", "PARAMETER SNRTHRESHOLD", param_frame, 2, 0)
        self.create_entry("PSD Length:", "PARAMETER PSDLENGTH", param_frame, 2, 10)
        # Output Frame
        output_frame = tk.Frame(self.scrollable_frame, bd=2, relief="groove", padx=5, pady=5)
        output_frame.grid(row=12, column=0, columnspan=4, pady=10, sticky="ew")
        self.create_folder_selector("Select Output Directory:", "OUTPUT DIRECTORY", is_directory=True, frame=output_frame,row=13,column=0)
        self.create_output_products_selection(output_frame, row=14, column=0)
        self.create_dropdown("Select Format:", "OUTPUT FORMAT", ["root", "hdf5", "Format3"], frame=output_frame,row=15,column=0)
        self.create_slider("Verbosity (0-5):", "OUTPUT VERBOSITY", 0, 5, frame=output_frame,row=16,column=0)


    #Parameters entry 
    def create_entry(self, label, key, frame=None, row=0, col=0):
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=5)
        var = tk.StringVar(value=self.config_data.get(key, ""))
        entry = tk.Entry(target_frame, textvariable=var, width=15)  # Uniform width
        entry.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=5)
        self.ui_elements[key] = var

    def create_double_entry(self, label, key, frame=None, row=0, col=0):
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=5)
        var1 = tk.StringVar()
        var2 = tk.StringVar()
        entry_width = 15  # Same width for both fields
        entry1 = tk.Entry(target_frame, textvariable=var1, width=entry_width)
        entry2 = tk.Entry(target_frame, textvariable=var2, width=entry_width)
        entry1.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=5)
        entry2.grid(row=row, column=col + 2, sticky="ew", padx=5, pady=5)
        self.ui_elements[key] = (var1, var2)

    #Output fields 
    def create_file_selector(self, label, key, is_directory=False, frame=None,row=0,column=0):
        """Creates a file/directory selector inside the given frame (or default to scrollable_frame)."""
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=5)
        var = tk.StringVar(value=self.config_data.get(key, ""))  # Preserve previous selection
        button = tk.Button(target_frame, text="Select", command=lambda: self.select_file(var))
        button.grid(row=row, column=2,columnspan=5, padx=5, pady=5)
        entry = tk.Entry(target_frame, textvariable=var, width=40, state="readonly")
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        self.ui_elements[key] = var

    def create_folder_selector(self, label, key, is_directory=False, frame=None, row=0, column=0):
        """Creates a file/directory selector inside the given frame (or default to scrollable_frame).
        Additionally, sets a default output path if not specified and creates the directory if needed,
        while ensuring the path is relative from the current working directory."""
        
        # Target frame for the UI element
        target_frame = frame if frame else self.scrollable_frame
        
        # Create the label
        tk.Label(target_frame, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=5)
        
        # Get the value for the directory path, or set a default if not provided
        var = tk.StringVar(value=self.config_data.get(key, ""))  # Preserve previous selection
        
        # Check if a directory path is provided, otherwise set default
        dir_path = var.get()
        if not dir_path:
            # Default directory (e.g., "OmicronOut" in the current directory)
            dir_path = os.path.join(os.getcwd(), "OmicronOut")
            var.set(dir_path)  # Set the default path
        
        # Convert the path to a relative path based on the current working directory
        abs_path = os.path.abspath(dir_path)  # Get absolute path first
        rel_path = os.path.relpath(abs_path, os.getcwd())  # Convert to relative path
        
        # Ensure the relative path starts with './'
        if not rel_path.startswith('./'):
            rel_path = './' + rel_path
        
        # Set the relative path back to the variable
        var.set(rel_path)
        
        # Check if the directory exists, if not, create it
        if not os.path.exists(rel_path):
            os.makedirs(rel_path)
            self.append_output(f"Directory '{rel_path}' was created as it didn't exist.\n")
        
        # Create the 'Select' button to choose the folder
        button = tk.Button(target_frame, text="Select", command=lambda: self.select_file(var, is_directory))
        button.grid(row=row, column=2, columnspan=5, padx=5, pady=5)
        
        # Create the readonly entry for displaying the selected folder path
        entry = tk.Entry(target_frame, textvariable=var, width=40, state="readonly")
        entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        
        # Store the variable in ui_elements
        self.ui_elements[key] = var

    def create_output_products_selection(self, frame=None, row=0, column=0):
        """Creates checkboxes for selecting output products inside a given frame."""
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text="Select Output Products:").grid(row=row,column=column, sticky="w", padx=5, pady=5)
        self.ui_elements["OUTPUT PRODUCTS"] = {}
        product_options = ["triggers", "html"]
        for idx, product in enumerate(product_options):
            var = tk.BooleanVar(value=product in self.config_data.get("OUTPUT PRODUCTS", ""))
            chk = tk.Checkbutton(target_frame, text=product, variable=var)
            chk.grid(row=row, column=idx+1, sticky="w", padx=5)
            self.ui_elements["OUTPUT PRODUCTS"][product] = var
            print(idx)

    def create_dropdown(self, label, key, options, frame=None,row=0,column=0):
        """Creates a dropdown menu inside a given frame."""
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text=label).grid(row=row, column=column,columnspan=5, sticky="w", padx=5, pady=5)
        var = tk.StringVar(value=self.config_data.get(key, options[0]))
        dropdown = ttk.Combobox(target_frame, textvariable=var, values=options)
        dropdown.grid(row=row, column=column+1, sticky="ew", padx=5, pady=5)
        self.ui_elements[key] = var

    def create_slider(self, label, key, min_val, max_val, frame=None,row=0,column=0):
        """Creates a slider for selecting a numerical value."""
        target_frame = frame if frame else self.scrollable_frame
        tk.Label(target_frame, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=5)
        var = tk.IntVar(value=self.config_data.get(key, min_val))
        slider = tk.Scale(target_frame, from_=min_val, to=max_val, orient="horizontal", variable=var)
        slider.grid(row=row, column=column+1, sticky="ew", padx=5, pady=5)
        self.ui_elements[key] = var

    def create_channel_dropdown(self, row=0):
        """Creates a dropdown for selecting a channel and updates it dynamically every few seconds."""
        # Label for the dropdown
        tk.Label(self.scrollable_frame, text="Select Channel:").grid(row=row, column=0, sticky="w")

        # Function to populate the channels
        def populate_channels():
            """Populate the channel list by reading the files in the gwfout directory."""
            gwfout_path = os.path.join(os.getcwd(), "gwfout")
            if os.path.exists(gwfout_path) and os.path.isdir(gwfout_path):
                # Get the list of subdirectories (channels)
                channels = [d for d in os.listdir(gwfout_path) if os.path.isdir(os.path.join(gwfout_path, d))]
                if not channels:  # If no channels found
                    channels = ["No Channels Available"]
            else:
                channels = ["No Channels Available"]
            return channels

        # Function to update the dropdown with the current list of channels
        def update_channel_dropdown():
            """Update the channel dropdown in real-time based on current contents of the gwfout directory."""
            current_selection = self.ui_elements["DATA CHANNELS"].get()  # Save the current selection
            channel_options = populate_channels()
            
            # Update the combobox with the new list of channels
            self.channel_dropdown['values'] = channel_options
            
            # Restore the previous selection if possible
            if current_selection in channel_options:
                self.ui_elements["DATA CHANNELS"].set(current_selection)
            else:
                self.ui_elements["DATA CHANNELS"].set(channel_options[0])  # Default to the first channel if the previous selection is no longer available

        # Create the dropdown (Combobox) with initial values
        self.ui_elements["DATA CHANNELS"] = tk.StringVar()
        self.channel_dropdown = ttk.Combobox(self.scrollable_frame, textvariable=self.ui_elements["DATA CHANNELS"], values=[])
        self.channel_dropdown.grid(row=row, column=1, sticky="ew")

        # Initial population of the dropdown
        update_channel_dropdown()

        # Periodic checking for new channels every 2 seconds
        def check_for_new_channels():
            """Check for new channels periodically and update the dropdown."""
            update_channel_dropdown()
            self.scrollable_frame.after(4000, check_for_new_channels)  # Check again in 2 seconds

        # Start checking for new channels
        check_for_new_channels()


    def select_file(self, var, is_directory=False):
        file_path = filedialog.askdirectory() if is_directory else filedialog.askopenfilename()
        if file_path:
            relative_path = os.path.relpath(file_path, os.getcwd())  # Convert to relative path
            var.set(relative_path)
            print(f"FFL file selected: {relative_path}")  # DEBUGGING

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                for line in file:
                    parts = line.strip().split("\t")
                    if len(parts) == 2:
                        self.config_data[parts[0]] = parts[1]
        except FileNotFoundError:
            self.append_output("Config file not found. Using defaults.\n")

    def save_config(self):
        base_path = os.getcwd().replace("\\", "/")  # Get current working directory with forward slashes
        with open(self.config_path, 'w', encoding='utf-8') as file:
            for key, var in self.ui_elements.items():
                if isinstance(var, tuple):  # For double-entry fields
                    value = f"{var[0].get()} {var[1].get()}"
                elif isinstance(var, dict):  # For multiple selections (checkboxes)
                    selected_products = [prod for prod, v in var.items() if v.get()]
                    value = " ".join(selected_products)
                else:
                    value = var.get()
                if key == "DATA CHANNELS":
                    parts = value.split("_", 1)  # Split at the first underscore
                    if len(parts) == 2:
                        value = parts[0] + ":" + parts[1]  # Replace only the first underscore with a colon
                # Convert absolute paths to relative paths based on current directory
                if key in ["DATA FFL", "OUTPUT DIRECTORY"]:  
                    if value:
                        abs_path = os.path.abspath(value).replace("\\", "/")  # Convert to absolute path with `/`
                        if abs_path.startswith(base_path):  
                            rel_path = os.path.relpath(abs_path, base_path).replace("\\", "/")  # Convert to relative
                            value = f"./{rel_path}"  # Format correctly
                            print(value)
                            print(abs_path)
                # Keep output parameter paths relative
                if key.startswith("DATA "):
                    formatted_line = f"{key}\t{value}\n"
                elif key.startswith("PARAMETER "):
                    formatted_line = f"PARAMETER\t{key.split()[1]}\t{value}\n"
                elif key.startswith("OUTPUT "):  
                    formatted_line = f"OUTPUT\t{key.split()[1]}\t{value}\n"  # Keep paths as given
                else:
                    formatted_line = f"{key}\t{value}\n"  # Default formatting
                file.write(formatted_line)

        self.append_output(f"Config file saved at '{self.config_path}' with the correct format.\n")
        
        messagebox.showinfo("Success", "Configuration has been saved successfully!")

    def run_omicron_script(self):
        """Start the OMICRON script in a separate process and update the output in real-time."""
        self.append_output("Starting OMICRON script...\n")
        
        # Start the OMICRON process in a new thread to avoid blocking the GUI
        omicron_thread = threading.Thread(target=self.start_omicron_process, daemon=True)
        omicron_thread.start()
    
    
    def start_omicron_process(self):
        """Run the OMICRON command directly in WSL."""
        try:
            # Get the currently selected FFL file
            ffl_file = self.ui_elements["DATA FFL"].get()
            if not ffl_file or not os.path.exists(ffl_file):
                self.append_output("Error: No valid .ffl file selected.\n")
                return

            # Extract first and last time segment from the .ffl file
            with open(ffl_file, "r") as f:
                lines = f.readlines()
                if len(lines) == 0:
                    self.append_output("Error: The .ffl file is empty.\n")
                    return
                first_time_segment = lines[0].split()[1]  # Extract first time segment
                last_time_segment = lines[-1].split()[1]  # Extract last time segment

            # Construct the OMICRON command
            omicron_cmd = f"omicron {first_time_segment} {last_time_segment} ./config.txt > omicron.out 2>&1"

            # Full WSL command
            wsl_command = f"wsl bash -c \"source /root/miniconda3/bin/activate omicron && cd /mnt/c/Users/HP/Desktop/GWeasy && {omicron_cmd}\""

            # Run command in a separate process
            self.append_output(f"Running: {wsl_command}\n")
            process = subprocess.Popen(wsl_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            for line in process.stdout:
                self.append_output(line)
            for line in process.stderr:
                self.append_output(f"ERROR: {line}")

            process.wait()
            if process.returncode != 0:
                self.append_output(f"Error: Command failed with return code {process.returncode}.\n")
            else:
                self.append_output("OMICRON process completed successfully.\n")
        except Exception as e:
            self.append_output(f"Unexpected error: {e}\n")

    def append_output(self, text):
            """Send output to the terminal"""
            self.terminal.append_output(text)
    

    #custom ffl
    def open_custom_segs_dialog(self):
        """ Opens a GUI window to select a channel and time segments (grid layout). """
        channel_dir = filedialog.askdirectory(initialdir="./gwfout", title="Select Channel Directory")
        if not channel_dir:
            return  # User canceled selection

        segments = [d for d in os.listdir(channel_dir) if os.path.isdir(os.path.join(channel_dir, d))]
        if not segments:
            messagebox.showerror("Error", "No time segments found in selected channel.")
            return

        # Create selection window
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Time Segments")
        
        tk.Label(selection_window, text="Select Time Segments:", font=("Arial", 12)).grid(row=0, column=0, columnspan=2)

        # Create checkboxes for each segment
        selected_segments = {}
        for idx, segment in enumerate(segments):
            selected_segments[segment] = tk.BooleanVar()
            chk = tk.Checkbutton(selection_window, text=segment, variable=selected_segments[segment])
            chk.grid(row=(idx // 2) + 1, column=idx % 2, sticky="w", padx=5, pady=2)

        # Confirm button
        def confirm_selection():
            selected = [seg for seg, var in selected_segments.items() if var.get()]
            if not selected:
                messagebox.showerror("Error", "No segments selected.")
            else:
                self.generate_fin_ffl(channel_dir, selected)
                selection_window.destroy()

        # Toggle All button functionality
        def toggle_all():
            all_selected = all(var.get() for var in selected_segments.values())
            for var in selected_segments.values():
                var.set(not all_selected)  # Toggle the selection state

        tk.Button(selection_window, text="Confirm", command=confirm_selection).grid(row=(len(segments) // 2) + 2, column=0, columnspan=2, pady=10)
        tk.Button(selection_window, text="Toggle All", command=toggle_all).grid(row=(len(segments) // 2) + 2, column=1, columnspan=2, pady=10)

    def generate_fin_ffl(self, channel_dir, selected_segments):
        """ Generates fin.ffl file with correctly formatted paths and timestamps, then preselects it in the UI. """
        fin_ffl_path = os.path.join(channel_dir, "fin.ffl")
        
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

        # **Automatically select the generated fin.ffl file**
        relative_ffl_path = os.path.relpath(fin_ffl_path, os.getcwd()).replace("\\", "/")
        self.ui_elements["DATA FFL"].set(relative_ffl_path)
        messagebox.showinfo("Success", f"fin.ffl created and selected: {relative_ffl_path}")

class GravfetchApp:
    def __init__(self, root):
        self.root = root
        self.time_csv_file = ""
        self.channel_csv_file = ""
        self.execution_running = False
        self.process = None
        self.gwfout_path = ""
        # Setup Execution Tab
        self.setup_execution_tab()

        # Create Terminal (Placed in row 4, column 0)
        self.terminal = TerminalFrame(self.root, row=5, column=0, columnspan=2, height=20, width=80)

    def setup_execution_tab(self):
        """Sets up the Execution tab with buttons, output terminal, etc."""
        # Status bar frame at the top
        self.status_bar_frame = tk.Frame(self.root, bg="lightgray")
        self.status_bar_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Label for the status bar
        self.status_label = tk.Label(self.status_bar_frame, text="Idle", fg="black", bg="lightgray", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # File selection buttons
        self.time_button = tk.Button(self.root, text="Select Time CSV", command=self.select_time_csv)
        self.time_button.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.channel_button = tk.Button(self.root, text="Select Channel CSV", command=self.select_channel_csv)
        self.channel_button.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.gwf_button = tk.Button(self.root, text="Select Output (GWF) Dir", command=self.select_gwfout_dir)
        self.gwf_button.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        # Start/Stop button
        self.start_stop_button = tk.Button(self.root, text="Start Execution", command=self.toggle_execution)
        self.start_stop_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.root.grid_rowconfigure(5, weight=1)  # Make terminal expandable
        self.root.grid_columnconfigure(0, weight=1)  # Ensure alignment

    def select_time_csv(self):
        """Open file dialog for time CSV file."""
        self.time_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Time CSV: {self.time_csv_file}")
    
    def select_channel_csv(self):
        """Open file dialog for channel CSV file."""
        self.channel_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Channel CSV: {self.channel_csv_file}")
    
    def select_gwfout_dir(self):
        """Open file dialog for output dir (folder) selection."""
        self.gwfout_path = filedialog.askdirectory()  # Use askdirectory instead of askopenfilename
        if self.gwfout_path:  # Check if a directory was selected
            self.status_label.config(text=f"Selected Output Dir: {self.gwfout_path}")
        else:
            self.status_label.config(text="No directory selected", fg="red")
 

    def toggle_execution(self):
        """Start or stop the execution of the Gravfetch script."""
        if self.execution_running:
            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Stopped", fg="red")
            self.append_output("Execution stopped.\n")

            if self.process:
                self.process.terminate()
                self.process = None
        else:
            if not self.time_csv_file or not self.channel_csv_file:
                self.append_output("Please select both CSV files.\n")
                return
            
            self.execution_running = True
            self.start_stop_button.config(text="Stop Execution")
            self.status_label.config(text="Execution Started", fg="green")
            self.append_output("Execution started...\n")

            # Start the execution in a separate thread to avoid blocking the GUI
            self.execution_thread = threading.Thread(target=self.run_gravfetch_script, daemon=True)
            self.execution_thread.start()

    def run_gravfetch_script(self):
        """Runs the Gravfetch script."""
        try:
            script_path = os.path.abspath("gravfetch.py")
            
            # Set the input path to be passed to the Gravfetch script
            input_path = os.path.dirname(self.gwfout_path)

            # Modify the command to include the input path as an argument
            command = ["python", script_path, self.time_csv_file, self.channel_csv_file, input_path]

            # Start the process with the command and capture output
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Process stdout and stderr to append to the output
            for line in self.process.stdout:
                self.append_output(line)
            for line in self.process.stderr:
                self.append_output(f"ERROR: {line}")
            
            # Wait for the process to finish
            self.process.wait()

            # Update the UI after the script has finished running
            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Finished", fg="green")
            self.append_output("Execution finished.\n")

        except Exception as e:
            # Handle any errors that occur during execution
            self.append_output(f"Error running the script: {e}")
            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Failed", fg="red")
            self.append_output("Execution failed.\n")
        
    def append_output(self, text):
        """Send output to the terminal"""
        self.terminal.append_output(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
