#!/bin/bash
echo "$(date) : running data feeding" >> data/raw/data_feeding.log

# Define the target directory
TARGET_DIR="/appli"

# Get to the target directory
cd "$TARGET_DIR" || { echo "Folder not found : $TARGET_DIR"; exit 1; }

# Activate the virtual python environment
# source .venv/bin/activate || { echo "Fail to activate the virtual environment."; exit 1; }

# Execute the Python script
python src/data_feeding.py