import os
import sys
import subprocess

if len(sys.argv) != 2:
    print("Usage: python run_tests.py folder_path")
    sys.exit(1)

folder_path = sys.argv[1]

if not os.path.isdir(folder_path):
    print("Invalid folder path.")
    sys.exit(1)

pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

if len(pdf_files) == 0:
    print("Test directory is empty.")
    sys.exit(1)

for pdf_file in pdf_files:
    file_path = os.path.join(folder_path, pdf_file)
    command = f"python3 parse.py {file_path}"
    subprocess.run(command, shell=True)
