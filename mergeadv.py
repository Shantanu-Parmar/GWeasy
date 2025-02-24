import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk,Canvas,messagebox
import threading
import subprocess
import os


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

        # Place this frame using grid
        self.grid(row=row, column=column, rowspan=rowspan, columnspan=columnspan, sticky="nsew", padx=10, pady=10)

    def append_output(self, text, color="white"):
        """Append text to the terminal and auto-scroll."""
        self.output_text.config(state="normal")
        self.output_text.insert(tk.END, text, color)
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
        self.terminal = TerminalFrame(self.root, row=4, column=0, columnspan=2, height=20, width=80)  # Pass the shared terminal instance

        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.create_widgets()

    def create_widgets(self):
        self.create_channel_dropdown()
        self.create_file_selector("Select .ffl File:", "DATA FFL")
        self.create_dropdown("Sampling Frequency:", "DATA SAMPLEFREQUENCY", ["1024", "2048", "4096"])
        self.create_double_entry("Timing (Start, End):", "PARAMETER TIMING")
        self.create_double_entry("Frequency Range (Min, Max):", "PARAMETER FREQUENCYRANGE")
        self.create_double_entry("Q-Range (Min, Max):", "PARAMETER QRANGE")
        self.create_entry("Mismatch Max:", "PARAMETER MISMATCHMAX")
        self.create_entry("SNR Threshold:", "PARAMETER SNRTHRESHOLD")
        self.create_entry("PSD Length:", "PARAMETER PSDLENGTH")
        self.create_file_selector("Select Output Directory:", "OUTPUT DIRECTORY", is_directory=True)
        self.create_output_products_selection()
        self.create_dropdown("Select Format:", "OUTPUT FORMAT", ["root", "hdf5", "Format3"])
        self.create_slider("Verbosity (0-5):", "OUTPUT VERBOSITY", 0, 5)

        # Buttons
        self.save_button = tk.Button(self.scrollable_frame, text="Save Config", command=self.save_config)
        self.save_button.grid(row=10, column=0, pady=5, sticky="ew")
        
        self.start_button = tk.Button(self.scrollable_frame, text="Start OMICRON", command=self.run_omicron_script)
        self.start_button.grid(row=11, column=0, pady=10, sticky="ew")
       
    def create_output_products_selection(self):
        tk.Label(self.scrollable_frame, text="Select Output Products:").grid(row=12, column=0, sticky="w")
        self.ui_elements["OUTPUT PRODUCTS"] = {}
        product_options = ["triggers", "html"]
        row_offset = 13
        for idx, product in enumerate(product_options):
            var = tk.BooleanVar(value=product in self.config_data.get("OUTPUT PRODUCTS", ""))
            chk = tk.Checkbutton(self.scrollable_frame, text=product, variable=var)
            chk.grid(row=row_offset + idx, column=0, sticky="w")
            self.ui_elements["OUTPUT PRODUCTS"][product] = var

    def create_channel_dropdown(self):
        tk.Label(self.scrollable_frame, text="Select Channel:").grid(row=15, column=0, sticky="w")
        channel_options = self.populate_channels()
        self.ui_elements["DATA CHANNELS"] = tk.StringVar(value=channel_options[0])
        self.channel_dropdown = ttk.Combobox(self.scrollable_frame, textvariable=self.ui_elements["DATA CHANNELS"], values=channel_options)
        self.channel_dropdown.grid(row=16, column=0, sticky="ew")

    def populate_channels(self):
        gwfout_path = os.path.join(os.getcwd(), "gwfout")
        if os.path.exists(gwfout_path) and os.path.isdir(gwfout_path):
            channels = [d for d in os.listdir(gwfout_path) if os.path.isdir(os.path.join(gwfout_path, d))]
        else:
            channels = ["No Channels Found"]
        return channels

    def create_dropdown(self, label, key, options):
        tk.Label(self.scrollable_frame, text=label).grid(sticky="w")
        var = tk.StringVar(value=self.config_data.get(key, options[0]))
        dropdown = ttk.Combobox(self.scrollable_frame, textvariable=var, values=options)
        dropdown.grid(sticky="ew")
        self.ui_elements[key] = var


    def create_entry(self, label, key):
        tk.Label(self.scrollable_frame, text=label).grid(sticky="w")
        var = tk.StringVar(value=self.config_data.get(key, ""))
        entry = tk.Entry(self.scrollable_frame, textvariable=var)
        entry.grid(sticky="ew")
        self.ui_elements[key] = var

    def create_double_entry(self, label, key):
        tk.Label(self.scrollable_frame, text=label).grid(sticky="w")
        var1 = tk.StringVar()
        var2 = tk.StringVar()
        entry1 = tk.Entry(self.scrollable_frame, textvariable=var1)
        entry2 = tk.Entry(self.scrollable_frame, textvariable=var2)
        entry1.grid(sticky="ew")
        entry2.grid(sticky="ew")
        self.ui_elements[key] = (var1, var2)

    def create_file_selector(self, label, key, is_directory=False):
        tk.Label(self.scrollable_frame, text=label).grid(sticky="w")
        var = tk.StringVar()
        button = tk.Button(self.scrollable_frame, text="Select", command=lambda: self.select_file(var, is_directory))
        button.grid(sticky="ew")
        self.ui_elements[key] = var

    def create_slider(self, label, key, min_val, max_val):
        tk.Label(self.scrollable_frame, text=label).grid(sticky="w")
        var = tk.IntVar()
        tk.Scale(self.scrollable_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var).grid(sticky="ew")
        self.ui_elements[key] = var


    def select_file(self, var, is_directory=False):
        file_path = filedialog.askdirectory() if is_directory else filedialog.askopenfilename()
        if file_path:
            var.set(file_path)

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
        with open(self.config_path, 'w') as file:
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

                # If the value is a file path, keep only the last part (filename)
                if key in ["DATA FFL", "OUTPUT DIRECTORY"]:  # Add more keys if needed
                    value = f"./{os.path.basename(value)}" if value else value  # Avoid errors if empty

                # Define spacing rules to match `config (1).txt`
                if key.startswith("DATA "):
                    formatted_line = f"{key}\t{value}\n"
                elif key.startswith("PARAMETER "):
                    formatted_line = f"PARAMETER\t{key.split()[1]}\t{value}\n"
                elif key.startswith("OUTPUT "):
                    formatted_line = f"OUTPUT\t{key.split()[1]}\t{value}\n"
                else:
                    formatted_line = f"{key}\t{value}\n"  # Default formatting

                file.write(formatted_line)

        self.append_output("Config file saved in 'config.txt' with exact format.\n")
        messagebox.showinfo("Success", "Configuration has been saved successfully!")

    def run_omicron_script(self):
        """Start the OMICRON script in a separate process and update the output in real-time."""
        self.append_output("Starting OMICRON script...\n")
        
        # Start the OMICRON process in a new thread to avoid blocking the GUI
        omicron_thread = threading.Thread(target=self.start_omicron_process, daemon=True)
        omicron_thread.start()
    
    
    def start_omicron_process(self):
        """Run the OMICRON script in a separate process."""
        try:
            commands = [
                "wsl bash -c \"source /root/miniconda3/bin/activate omicron && cd /mnt/c/Users/HP/Desktop/GWeasy && ./run_omicron.sh\""
            ]

            for cmd in commands:
                self.append_output(f"Running: {cmd}\n")
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                for line in process.stdout:
                    self.append_output(line)
                for line in process.stderr:
                    self.append_output(f"ERROR: {line}")
                
                process.wait()

                if process.returncode != 0:
                    self.append_output(f"Error: Command failed with return code {process.returncode}.\n")
                    break  # Stop execution if a command fails
            self.append_output("OMICRON process completed.\n")

        except subprocess.CalledProcessError as e:
            self.append_output(f"Error executing the OMICRON script: {e}\n")
        except Exception as e:
            self.append_output(f"Unexpected error: {e}\n")

    def append_output(self, text):
            """Send output to the terminal"""
            self.terminal.append_output(text)
    

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
