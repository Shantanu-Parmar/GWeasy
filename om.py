import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext

class OmicronApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OMICRON Processing")

        # Button to start the execution
        self.start_button = tk.Button(self.root, text="Start OMICRON", command=self.run_omicron_script)
        self.start_button.pack(pady=10)

        # Output terminal to show real-time output of the subprocess
        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.output_text.pack(padx=10, pady=10)

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
        """Append the text to the output terminal in the GUI."""
        self.output_text.insert(tk.END, text)
        self.output_text.yview(tk.END)  # Scroll to the bottom

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = OmicronApp(root)
    root.mainloop()