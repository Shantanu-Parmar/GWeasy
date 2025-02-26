#!/bin/bash
# Install dependencies in WSL
echo "Setting up Conda environment in WSL..."
conda env create -f environment.yml
conda activate GWeasy
python GWeasy.py
