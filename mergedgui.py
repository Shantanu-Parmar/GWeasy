import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import subprocess
import os
from tkinter import filedialog, scrolledtext, ttk, messagebox




class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Gravfetch and OMICRON Processing")

        # Setup the main notebook (tab structure)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Add the first tab for script execution (Gravfetch)
        self.gravfetch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.gravfetch_tab, text="Gravfetch")

        # Add the second tab for OMICRON
        self.omicron_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.omicron_tab, text="OMICRON")

        # Initialize both GUIs (Gravfetch and OMICRON) in their respective tabs
        self.gravfetch_app = GravfetchApp(self.gravfetch_tab)
        self.omicron_app = OmicronApp(self.omicron_tab)








import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox

class OmicronApp:
    def __init__(self, root):
        self.root = root
        self.config_path = "config.txt"
        self.config_data = {}
        
        # Initialize UI elements
        self.ui_elements = {}
        self.load_config()
        
        # UI setup
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
        self.save_button = tk.Button(self.root, text="Save Config", command=self.save_config)
        self.save_button.pack(pady=5)
        self.start_button = tk.Button(self.root, text="Start OMICRON", command=self.run_omicron_script)
        self.start_button.pack(pady=10)
        
        # Output terminal
        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.output_text.pack(padx=10, pady=10)
    import os
    def create_output_products_selection(self):
        """Create checkboxes for selecting output products."""
        tk.Label(self.root, text="Select Output Products:").pack()
        
        # Checkboxes for 'triggers' and 'html'
        self.ui_elements["OUTPUT PRODUCTS"] = {}
        product_options = ["triggers", "html"]  # Add more if needed

        for product in product_options:
            var = tk.BooleanVar(value=product in self.config_data.get("OUTPUT PRODUCTS", ""))
            chk = tk.Checkbutton(self.root, text=product, variable=var)
            chk.pack(anchor='w')
            self.ui_elements["OUTPUT PRODUCTS"][product] = var

    def populate_channels(self):
        """Fetch subfolder names from 'gwfout' directory and update the dropdown."""
        gwfout_path = os.path.join(os.getcwd(), "gwfout")  # Adjust if needed
        if os.path.exists(gwfout_path) and os.path.isdir(gwfout_path):
            channels = [d for d in os.listdir(gwfout_path) if os.path.isdir(os.path.join(gwfout_path, d))]
        else:
            channels = ["No Channels Found"]  # Default if directory is missing

        return channels

    def create_channel_dropdown(self):
        """Create a dropdown menu with dynamically fetched channel names."""
        tk.Label(self.root, text="Select Channel:").pack()
        
        # Fetch channels dynamically
        channel_options = self.populate_channels()
        
        self.ui_elements["DATA CHANNELS"] = tk.StringVar(value=channel_options[0])
        self.channel_dropdown = ttk.Combobox(self.root, textvariable=self.ui_elements["DATA CHANNELS"], values=channel_options)
        self.channel_dropdown.pack()

    def create_dropdown(self, label, key, options):
        tk.Label(self.root, text=label).pack()
        var = tk.StringVar(value=self.config_data.get(key, options[0]))
        dropdown = ttk.Combobox(self.root, textvariable=var, values=options)
        dropdown.pack()
        self.ui_elements[key] = var
    
    def create_entry(self, label, key):
        tk.Label(self.root, text=label).pack()
        var = tk.StringVar(value=self.config_data.get(key, ""))
        entry = tk.Entry(self.root, textvariable=var)
        entry.pack()
        self.ui_elements[key] = var
    
    def create_double_entry(self, label, key):
        tk.Label(self.root, text=label).pack()
        var1 = tk.StringVar(value=self.config_data.get(key, "").split()[0] if key in self.config_data else "")
        var2 = tk.StringVar(value=self.config_data.get(key, "").split()[1] if key in self.config_data else "")
        tk.Entry(self.root, textvariable=var1).pack()
        tk.Entry(self.root, textvariable=var2).pack()
        self.ui_elements[key] = (var1, var2)
    
    def create_file_selector(self, label, key, is_directory=False):
        tk.Label(self.root, text=label).pack()
        var = tk.StringVar(value=self.config_data.get(key, ""))
        button = tk.Button(self.root, text="Select", command=lambda: self.select_file(var, is_directory))
        button.pack()
        self.ui_elements[key] = var
    
    def create_slider(self, label, key, min_val, max_val):
        tk.Label(self.root, text=label).pack()
        var = tk.IntVar(value=int(self.config_data.get(key, min_val)))
        tk.Scale(self.root, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var).pack()
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
        self.save_config()
        self.append_output("Starting OMICRON script...\n")
    
    def append_output(self, text):
        self.output_text.insert(tk.END, text)
        self.output_text.yview(tk.END)







class GravfetchApp:
    def __init__(self, root):
        self.root = root
        self.time_csv_file = ""
        self.channel_csv_file = ""
        self.execution_running = False
        self.process = None

        # Setup the GUI elements for the Execution tab
        self.setup_execution_tab()

    def setup_execution_tab(self):
        """Sets up the Execution tab with buttons, output terminal, etc."""
        # Status bar frame at the top
        self.status_bar_frame = tk.Frame(self.root, bg="lightgray")
        self.status_bar_frame.pack(fill=tk.X, padx=10, pady=5)

        # Label for the status bar
        self.status_label = tk.Label(self.status_bar_frame, text="Idle", fg="black", bg="lightgray", anchor="w")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

        # File selection buttons
        self.time_button = tk.Button(self.root, text="Select Time CSV", command=self.select_time_csv)
        self.time_button.pack(padx=10, pady=5)

        self.channel_button = tk.Button(self.root, text="Select Channel CSV", command=self.select_channel_csv)
        self.channel_button.pack(padx=10, pady=5)

        # Start/Stop button
        self.start_stop_button = tk.Button(self.root, text="Start Execution", command=self.toggle_execution)
        self.start_stop_button.pack(padx=10, pady=10)

        # Output terminal panel
        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.output_text.pack(padx=10, pady=10)

    def select_time_csv(self):
        """Open file dialog for time CSV file."""
        self.time_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Time CSV: {self.time_csv_file}")
    
    def select_channel_csv(self):
        """Open file dialog for channel CSV file."""
        self.channel_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Channel CSV: {self.channel_csv_file}")
    
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
            command = ["python", script_path, self.time_csv_file, self.channel_csv_file]
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            for line in self.process.stdout:
                self.append_output(line)
            for line in self.process.stderr:
                self.append_output(f"ERROR: {line}")
            
            self.process.wait()

            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Finished", fg="green")
            self.append_output("Execution finished.\n")

        except Exception as e:
            self.append_output(f"Error running the script: {e}")
            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Failed", fg="red")
            self.append_output("Execution failed.\n")
        
    def append_output(self, text):
        """Append text to the output terminal."""
        self.output_text.insert(tk.END, text)
        self.output_text.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
