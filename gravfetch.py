import os
import pandas as pd
from gwpy.timeseries import TimeSeries
gwfout_dir = "gwfout"
os.makedirs(gwfout_dir, exist_ok=True)  # Ensure main output directory exists

# Paths to your CSV files
time_csv_file = "newtim.csv"
channel_csv_file = "4KCHANS.csv"

# Load the CSV files
time_ranges = pd.read_csv(time_csv_file, header=None, names=["start", "end"])
channels = pd.read_csv(channel_csv_file, header=None, skiprows=1, names=["Channel", "Sample Rate"])

# Debug: Check the loaded data
print("Loaded time ranges:")
print(time_ranges)
print("Loaded channels:")
print(channels)

# Path to the fin.txt file
fin_file = "list.ffl"

# Open fin.txt for appending
with open(fin_file, 'a') as fin:

    # Process data for each channel and time range
    for _, channel_row in channels.iterrows():
        channel_name = channel_row['Channel']
        sampling_rate = channel_row['Sample Rate']
        print(channel_name)
       
        # Create a directory for the channel if it doesn't exist
        channel_dir = os.path.join(gwfout_dir, channel_name.replace(":", "_"))
        os.makedirs(channel_dir, exist_ok=True)  # Create channel folder inside gwfout

        for _, time_row in time_ranges.iterrows():
            start_time = int(time_row["start"])
            end_time = int(time_row["end"])

            # Try fetching data, skip if error occurs
            try:
                # Fetch data from GWPy
                data = TimeSeries.fetch(channel_name, start=start_time, end=end_time, host='nds.gwosc.org')

                # Create a subfolder for the time range within the channel folder
                time_dir_path = os.path.join(gwfout_dir, channel_name.replace(":", "_"), f"{start_time}_{end_time}")

                os.makedirs(time_dir_path, exist_ok=True)

                # File path to save the GWF file
                output_file = os.path.join(
                    gwfout_dir, channel_name.replace(":", "_"), f"{start_time}_{end_time}",
                    f"{channel_name.replace(':', '_')}_{start_time}_{end_time}.gwf"
                )

                # Save the strain data in `gwf` format
                data.write(output_file)
                print(f"Aux data for channel '{channel_name}' from {start_time} to {end_time} saved to {output_file}")

                # Extract relevant data for fin.txt
                t0 = data.t0  # Start time (gps_start_time)
                dt = end_time - start_time  # Duration of the data (file_duration)

                # Append the information to fin.txt in the required format
                fin.write(f"{os.path.abspath(output_file)} {t0} {dt} 0 0\n")
                print(f"Added to fin.txt: {os.path.abspath(output_file)} {t0} {dt} 0 0")

            except RuntimeError as e:
                # If data fetching fails, log the error and continue with the next time segment
                print(f"Error fetching data for {channel_name} from {start_time} to {end_time}: {e}")
                continue  # Skip to the next time segment