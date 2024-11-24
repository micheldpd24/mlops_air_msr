#!/bin/bash

# Define the target directory
TARGET_DIR="/appli"

# Get to the target directory
cd "$TARGET_DIR" || { echo "Répertoire non trouvé : $TARGET_DIR"; exit 1; }

# Activate the virtual python environment
# source .venv/bin/activate || { echo "Échec de l'activation de l'environnement virtuel."; exit 1; }

# Execute the Python script
python src/launch_retrain.py
