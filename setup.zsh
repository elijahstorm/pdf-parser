#!/bin/bash

# Add this script's directory to the PATH
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "export PATH=\$PATH:$SCRIPT_DIR" >> ~/.zshrc
source ~/.zshrc

# Define the alias
echo "alias parse_pdfs='python3 parse.py '" >> ~/.zshrc
source ~/.zshrc

echo "Alias 'parse_pdfs' for the Python script has been set up."
