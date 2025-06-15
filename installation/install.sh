#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if git is installed
if ! command_exists git; then
    echo "Error: Git is not installed on your system."
    echo "Please install Git from https://git-scm.com/downloads"
    exit 1
fi

# Check if python is installed
if ! command_exists python; then
    echo "Error: Python is not installed on your system."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Clone the repository
repo_url="https://github.com/ChanBong/chirp.git"
repo_name="chirp"

if [ -d "$repo_name" ]; then
    read -p "A folder named '$repo_name' already exists. Do you want to delete it? (y/n) " confirmation
    if [ "$confirmation" = "y" ]; then
        echo "Removing existing folder..."
        rm -rf "$repo_name"
    else
        echo "Moving on..."
    fi
else
    echo "Cloning repository..."
    git clone "$repo_url"
fi

cd "$repo_name" || exit

echo "Running bootstrap.py..."
python bootstrap.py

echo "Installation completed successfully!"
