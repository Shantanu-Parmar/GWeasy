import os
import pandas as pd
from gwpy.timeseries import TimeSeries

input_path = "./gwfout"
omicron_script = "run_omicron.sh"  # Path to the Omicron script

# Ensure the input path exists
if not os.path.exists(input_path):
    print(f"The path {input_path} does not exist. Creating the path...")
    os.makedirs(input_path)

# Paths to your CSV files
time_csv_file = "test.csv"
channel_csv_file = "4KCHANS.csv"

# Load the CSV files
time_ranges = pd.read_csv(time_csv_file, header=None, names=["start", "end"])
channels = pd.read_csv(channel_csv_file, header=None, skiprows=1, names=["Channel", "Sample Rate"])

# Debug: Check the loaded data
print("Loaded time ranges:")
print(time_ranges)
print("Loaded channels:")
print(channels)

# Get the current working directory (dynamic path)
current_dir = os.getcwd()

# Process data for each channel
with open(omicron_script, 'a') as omicron_file:
    for _, channel_row in channels.iterrows():
        channel_name = channel_row['Channel']
        sampling_rate = channel_row['Sample Rate']
        print(f"Processing channel: {channel_name}")
        
        # Create a directory for the channel within the input path
        channel_dir = os.path.join(input_path, channel_name.replace(":", "_"))  # Replace ':' with '_'
        os.makedirs(channel_dir, exist_ok=True)
        print(f"Created channel directory: {channel_dir}")
        
        # Create a separate fin.ffl file for each channel inside its directory
        fin_file_path = os.path.join(channel_dir, f"fin.ffl")
        
        # Open the channel-specific fin.ffl file for appending
        with open(fin_file_path, 'a') as fin:
            for _, time_row in time_ranges.iterrows():
                start_time = int(time_row["start"])
                end_time = int(time_row["end"])

                # Try fetching data, skip if error occurs
                try:
                    print(f"Fetching data for channel '{channel_name}' from {start_time} to {end_time}...")
                    # Fetch data from GWPy
                    data = TimeSeries.fetch(channel_name, start=start_time, end=end_time, host='nds.gwosc.org')

                    # Create a subfolder for the time range within the channel folder
                    time_dir_path = os.path.join(channel_dir, f"{start_time}_{end_time}")
                    os.makedirs(time_dir_path, exist_ok=True)
                    print(f"Created time directory: {time_dir_path}")

                    # File path to save the GWF file
                    output_file = os.path.join(time_dir_path, f"{channel_name.replace(':', '_')}_{start_time}_{end_time}.gwf")

                    # Save the strain data in `gwf` format
                    data.write(output_file)
                    print(f"Aux data for channel '{channel_name}' from {start_time} to {end_time} saved to {output_file}")

                    # Extract relevant data for fin.ffl
                    t0 = data.t0  # Start time (gps_start_time)
                    dt = end_time - start_time  # Duration of the data (file_duration)
                    print(f"Data start time: {t0}, Duration: {dt}")

                    # Write the information to the channel-specific fin.ffl file
                    relative_path = os.path.relpath(output_file, current_dir)
                    fin.write(f"./{relative_path} {start_time} {dt} 0 0\n")
                    print(f"Added to {fin_file_path}: ./{relative_path} {start_time} {dt} 0 0")

                    # Append the time segment to run_omicron.sh
                    omicron_file.write(f"omicron {start_time} {end_time} ./config.txt > omicron.out 2>&1\n")
                    print(f"Added to {omicron_script}: omicron {start_time} {end_time} ./config.txt > omicron.out 2>&1")

                except RuntimeError as e:
                    # If data fetching fails, log the error and continue with the next time segment
                    print(f"Error fetching data for {channel_name} from {start_time} to {end_time}: {e}")
                    continue  # Skip to the next time segment

# Notify user of completion
print("All channel-specific fin.ffl files created.")
print(f"Updated {omicron_script} with new time segments.")
