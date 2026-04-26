import os
from pathlib import Path

def generate_nymph_audit():
    # Use absolute path for the root to ensure comparison accuracy
    nymph_dir = Path(".").resolve()
    max_chars = 25000
    
    # Configuration for directory exclusions - must be folder names
    EXCLUDE_DIRS = {
        "__pycache__", 
        ".git", 
        "venv", 
        "train_venv", 
        "env",
        ".ipynb_checkpoints", 
        "data", 
        "dataset", 
        "nl", 
        "checkpoints",
        "output",
        "node_modules",
        "site-packages"
    }
    
    # Configuration for specific file exclusions
    EXCLUDE_FILES = {
        "engine.py",
        "tree.py",
        "__init__.py",
        "qwen3.py",
        "test.py",
        "nano-test.py",
        "prepare.py",
        "test_temp.py"
    }
    
    file_data = []
    
    # Walk the directory
    for root, dirs, files in os.walk(nymph_dir):
        # Remove excluded directories from the walk immediately
        # This prevents the script from even looking inside these folders
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            # Strict enforcement: Must be .py AND not in the exclusion list
            if not file.endswith(".py"):
                continue
                
            if file in EXCLUDE_FILES:
                continue
                
            file_path = Path(root) / file
            
            try:
                # Use a context manager to ensure the file is closed after reading
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Creating a markdown block with the relative path for readability
                    rel_path = file_path.relative_to(nymph_dir)
                    block = f"\n### File: {rel_path}\n```python\n{content}\n```\n"
                    file_data.append((len(block), block))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Sort descending by length for dense packing
    file_data.sort(key=lambda x: x[0], reverse=True)

    buckets = []

    for size, block in file_data:
        placed = False
        for i in range(len(buckets)):
            if len(buckets[i]) + size <= max_chars:
                buckets[i] += block
                placed = True
                break
        
        if not placed:
            buckets.append(block)

    # Output results
    if not buckets:
        print("No files found matching the criteria.")
        return

    for i, content in enumerate(buckets):
        filename = f"audit_{i+1}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved {filename} (Size: {len(content)} chars)")

if __name__ == "__main__":
    generate_nymph_audit()
