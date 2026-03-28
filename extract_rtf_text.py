import re
import sys

def striprtf(text):
    pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'[0-9a-f]{2}|\\\{|\\\}|\\|[\r\n]|.", re.IGNORECASE)
    # This is a very basic RTF stripper.
    # For a full implementation, more logic is needed.
    # However, for our specific files which are mostly text + sprites (binary),
    # we might be better off just looking for the patterns we want.
    return text # Placeholder

def extract_pokemon_changes(file_path):
    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()
    
    # RTF hex images look like a long string of hex characters after \bliptag
    # We want to remove those to make parsing easier.
    content = re.sub(r'\{\\pict.*?\}', '', content, flags=re.DOTALL)
    
    # Remove RTF commands
    content = re.sub(r'\\[a-z0-9]+', ' ', content)
    content = re.sub(r'\{|\}', ' ', content)
    
    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content)
    
    return content

if __name__ == "__main__":
    text = extract_pokemon_changes("Documentation/Level Up Move Changes.rtf")
    start = text.find("#001 Bulbasaur")
    print(text[start:start+500])
