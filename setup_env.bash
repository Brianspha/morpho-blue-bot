#!/bin/bash

# Define the name of the virtual environment
VENV_NAME="venv"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 before running this script."
    exit 1
fi

# Create a virtual environment
python3 -m venv $VENV_NAME

# Activate the virtual environment
source $VENV_NAME/bin/activate

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found. Please make sure it exists in the current directory."
    exit 1
fi

# Upgrade pip
pip install --upgrade pip

# Install the requirements
pip install -r requirements.txt


echo "Virtual environment setup complete and packages installed."
