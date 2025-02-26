@echo off
echo Setting up Conda environment...
call conda env create -f environment.yml
call conda activate GWeasy
python GWeasy.py
