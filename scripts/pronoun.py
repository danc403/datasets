import json
import re
import random
import os
import glob
import sys

# --- CONFIGURATION ---
TARGET_DB_IDS = [
    32, 33, 36, 47, 50, 51, 52, 53, 54, 57, 124, 127, 177, 130, 131, 
    136, 137, 142, 143, 144, 158, 163, 164, 148, 149, 150, 151, 152, 
    155, 156, 157, 218, 306, 309, 310, 311, 312, 313, 373, 422, 428, 
    430, 435, 436, 444, 445, 456, 457, 458
]

TARGETS = {
    "James Holden": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Holden": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Jim Holden": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Naomi Nagata": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Naomi": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Amos Burton": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Amos": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Alex Kamal": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Alex": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Bobbie Draper": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Bobbie": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Chrisjen Avasarala": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Chrisjen": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Clarissa Mao": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Clarissa": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Melba": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Tarzan": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Jondalar": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Ayla": { "base": ["she", "the woman"], "possessive": ["her", "the woman's"] },
    "Iza": { "base": ["she", "the medicine woman"], "possessive": ["her", "the medicine woman's"] },
    "Zelandoni": { "base": ["she", "the spiritual leader", "the healer"], "possessive": ["her", "the leader's", "the healer's"] },
    "First Among Others": { "base": ["she", "the Zelandoni"], "possessive": ["her", "the Zelandoni's"] },
    "Murderbot": { "base": ["the unit", "it"], "possessive": ["its", "the unit's"] },
    "SecUnit": { "base": ["the unit", "it"], "possessive": ["its", "the unit's"] },
    "Bean": { "base": ["he", "the boy"], "possessive": ["his", "the boy's"] },
    "Bob": { "base": ["he", "it", "the system"], "possessive": ["his", "its"] },
    "Van Tudor": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Van": { "base": ["he", "the man"], "possessive": ["his", "the man's"] },
    "Uhtred": { "base": ["he", "the warrior"], "possessive": ["his", "the warrior's"] }
}

SWAP_CHANCE = 0.75
MIN_WORD_COUNT = 40000

def neutralize_text(text):
    if not isinstance(text, str):
        return text
    word_count = len(text.split())
    if word_count < MIN_WORD_COUNT:
        return text
    # Sorting keys by length descending to prevent partial replacements (e.g., 'Jim Holden' before 'Holden')
    sorted_names = sorted(TARGETS.keys(), key=len, reverse=True)
    for name in sorted_names:
        options = TARGETS[name]
        
        # 1. Handle Possessives
        poss_pattern = re.compile(rf"\b{name}'s\b", re.IGNORECASE)
        def poss_replacer(match):
            if random.random() < SWAP_CHANCE:
                sub = random.choice(options["possessive"])
                # Preserve capitalization
                if match.group(0)[0].isupper():
                    return sub[0].upper() + sub[1:] if len(sub) > 1 else sub.upper()
                return sub
            return match.group(0)
        text = poss_pattern.sub(poss_replacer, text)
        
        # 2. Handle Base Names
        base_pattern = re.compile(rf"\b{name}\b", re.IGNORECASE)
        def base_replacer(match):
            if random.random() < SWAP_CHANCE:
                sub = random.choice(options["base"])
                if match.group(0)[0].isupper():
                    return sub[0].upper() + sub[1:] if len(sub) > 1 else sub.upper()
                return sub
            return match.group(0)
        text = base_pattern.sub(base_replacer, text)
    return text

def process_files(target):
    # Check if target is a file or directory for flexible execution
    if os.path.isfile(target):
        files = [target]
    else:
        files = glob.glob(os.path.join(target, "**", "*.jsonl"), recursive=True)
    
    if not files:
        print(f"No valid targets found for {target}")
        return

    for file_path in files:
        temp_file_path = file_path + ".tmp"
        count = 0
        processed_novels = 0
        print(f"Processing: {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f_in, \
                 open(temp_file_path, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        # Metadata filter: ensure work is targeted and from correct source table
                        if data.get("source_table") == "works" and data.get("db_id") in TARGET_DB_IDS and "text" in data:
                            original_text = data["text"]
                            data["text"] = neutralize_text(original_text)
                            if len(original_text.split()) >= MIN_WORD_COUNT:
                                processed_novels += 1
                        # Write entire modified/unmodified object back to maintain row integrity
                        f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
                        count += 1
                    except json.JSONDecodeError:
                        continue
            
            # Use atomic replace to prevent data loss on partial writes
            if count > 0:
                os.replace(temp_file_path, file_path)
                print(f"Done. Scanned {count} lines. Neutralized {processed_novels} novels.")
            else:
                if os.path.exists(temp_file_path): os.remove(temp_file_path)
                print(f"Skipped: {file_path} contained no data.")
                
        except Exception as e:
            if os.path.exists(temp_file_path): os.remove(temp_file_path)
            print(f"FATAL ERROR on {file_path}: {str(e)}")

if __name__ == "__main__":
    # Use command line argument for path, default to current directory
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "."
    process_files(path_arg)
