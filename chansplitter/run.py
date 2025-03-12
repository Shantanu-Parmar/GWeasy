import pandas as pd
import os
import re

# Input folder where all CSV files are located
input_folder = "input"  # Change this to your input folder path

# Define output directories
folders = {"H": "Hanford", "L": "Livingston", "V": "Virgo"}

# Process each CSV file in the input folder
for input_file in os.listdir(input_folder):
    if input_file.endswith(".csv"):
        file_path = os.path.join(input_folder, input_file)
        
        # Load the CSV file
        df = pd.read_csv(file_path)

        # Clean column names to avoid issues with extra spaces
        df.columns = df.columns.str.strip()

        # Check and print the column names
        print(f"Columns in {input_file}: {df.columns}")

        # Ensure column names are correctly read
        sampling_rate_col = "Sample Rate (Hz)"
        if "Channel" not in df.columns or sampling_rate_col not in df.columns:
            print(f"Error: Missing 'Channel' or '{sampling_rate_col}' column in {input_file}")
            continue

        df = df[["Channel", sampling_rate_col]]  # Keep only relevant columns
        df[sampling_rate_col] = df[sampling_rate_col].astype(str)  # Convert to string for consistent naming

        # Extract observational run from filename
        obs_run_match = re.match(r"(O\d+[a-z]*)", os.path.basename(input_file))
        obs_run = obs_run_match.group(1) if obs_run_match else "Unknown"

        # Create observational run folder
        base_dir = os.path.join("", obs_run)
        os.makedirs(base_dir, exist_ok=True)

        # Create Hanford, Livingston, and Virgo subfolders
        for folder in folders.values():
            os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

        # Group by Sampling Rate and save each group to a separate CSV
        for rate, group in df.groupby(sampling_rate_col):
            for prefix, folder in folders.items():
                subset = group[group["Channel"].str.startswith(prefix)]
                if not subset.empty:
                    output_file = os.path.join(base_dir, folder, f"{obs_run}_run_{rate}.csv")
                    subset.to_csv(output_file, index=False)
                    print(f"Saved: {output_file}")
