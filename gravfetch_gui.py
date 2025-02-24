import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import sys
import threading
import subprocess
import os

class ScriptExecutorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Script Executor with CSV Inputs")

        # File selection variables
        self.time_csv_file = ""
        self.channel_csv_file = ""
        
        # Status of execution
        self.execution_running = False
        self.process = None  # Track the process
        
        # Setup the main notebook (tab structure)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Add the first tab for script execution
        self.execution_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.execution_tab, text="Execution")
        
        # Add the second tab for OMICRON (placeholder)
        self.omicron_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.omicron_tab, text="OMICRON")
        
        # Setup the GUI elements for the Execution tab
        self.setup_execution_tab()

    def setup_execution_tab(self):
        """Sets up the Execution tab with buttons, output terminal, etc."""
        
        # Status bar frame at the top
        self.status_bar_frame = tk.Frame(self.execution_tab, bg="lightgray")
        self.status_bar_frame.pack(fill=tk.X, padx=10, pady=5)

        # Label for the status bar
        self.status_label = tk.Label(self.status_bar_frame, text="Idle", fg="black", bg="lightgray", anchor="w")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

        # File selection buttons
        self.time_button = tk.Button(self.execution_tab, text="Select Time CSV", command=self.select_time_csv)
        self.time_button.pack(padx=10, pady=5)

        self.channel_button = tk.Button(self.execution_tab, text="Select Channel CSV", command=self.select_channel_csv)
        self.channel_button.pack(padx=10, pady=5)

        # Start/Stop button
        self.start_stop_button = tk.Button(self.execution_tab, text="Start Execution", command=self.toggle_execution)
        self.start_stop_button.pack(padx=10, pady=10)

        # Output terminal panel
        self.output_text = scrolledtext.ScrolledText(self.execution_tab, width=80, height=20)
        self.output_text.pack(padx=10, pady=10)

        # Graphics (e.g., a simple progress bar or indicator) can go here
        self.progress_label = tk.Label(self.execution_tab, text="Processing will be shown here.", anchor="w")
        self.progress_label.pack(fill=tk.X, padx=10, pady=5)

    def select_time_csv(self):
        # Open file dialog for time CSV file
        self.time_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Time CSV: {self.time_csv_file}")
    
    def select_channel_csv(self):
        # Open file dialog for channel CSV file
        self.channel_csv_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        self.status_label.config(text=f"Selected Channel CSV: {self.channel_csv_file}")
    
    def toggle_execution(self):
        # If the process is running, stop it, else start it
        if self.execution_running:
            self.execution_running = False
            self.start_stop_button.config(text="Start Execution")
            self.status_label.config(text="Execution Stopped", fg="red")
            self.append_output("Execution stopped.\n")
            
            # Kill the subprocess if it's running
            if self.process:
                self.process.terminate()  # Try to gracefully terminate the process
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
        """This method runs the gravfetch.py script directly and captures its output"""
        
        # Use subprocess to execute the script in the background
        try:
            # Construct the command to run the script
            script_path = os.path.abspath("gravfetch.py")  # Ensure absolute path to the script
            command = ["python", script_path, self.time_csv_file, self.channel_csv_file]
            
            # Start the subprocess
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            # Continuously read stdout and stderr
            for line in self.process.stdout:
                self.append_output(line)
            for line in self.process.stderr:
                self.append_output(f"ERROR: {line}")
            
            # Wait for the process to finish
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
        """Method to append text to the output terminal in the GUI"""
        self.output_text.insert(tk.END, text)
        self.output_text.yview(tk.END)  # Auto-scroll to the bottom

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptExecutorApp(root)
    root.mainloop()
