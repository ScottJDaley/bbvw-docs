import os
import json
import re
from striprtf.striprtf import rtf_to_text

DOC_DIR = "Documentation"
DATA_DIR = "scripts/data"

def clean_rtf_file(filename):
    print(f"Cleaning {filename}...")
    with open(os.path.join(DOC_DIR, filename), 'r', encoding='cp1252', errors='ignore') as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)
    # Save a plain text version for easier debugging/parsing
    output_name = filename.replace('.rtf', '.txt')
    with open(os.path.join(DATA_DIR, output_name), 'w') as f:
        f.write(text)
    return text

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    files = [f for f in os.listdir(DOC_DIR) if f.endswith('.rtf')]
    for f in files:
        clean_rtf_file(f)
