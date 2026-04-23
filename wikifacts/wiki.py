import json
import os
import re
import unicodedata
import html

# --- Configuration ---
INPUT_FILE = "raw_wiki.jsonl"
OUTPUT_FILE = "wiki.jsonl"

def universal_normalize(text):
    """
    Applies the Factbook/Solar normalization: NFKD, ASCII, 
    natural language units, and EOS stripping.
    """
    if not text:
        return ""
    
    # Remove the specific EOS token used in the tokenized set
    text = text.replace("<|end_of_text|>", "")
    
    # Unescape any HTML entities (e.g., &amp; or &quot;)
    text = html.unescape(text)
    
    # Standardize Unicode to NFKD and strip non-ASCII
    normalized = unicodedata.normalize('NFKD', text)
    clean_ascii = normalized.encode('ascii', 'ignore').decode('ascii')
    
    # Expand symbols and units for accessibility/terminal parity
    clean_ascii = clean_ascii.replace('%', ' percent')
    clean_ascii = clean_ascii.replace(' degrees C', ' degrees Celsius')
    clean_ascii = re.sub(r'\bmph\b', 'miles per hour', clean_ascii)
    
    # Consolidation of whitespace and trailing/leading noise
    return re.sub(r'\s+', ' ', clean_ascii).strip()

def process_wiki_data():
    """
    Reads tokenized wiki data, strips metadata keys, 
    normalizes text, filters fragments, and writes clean jsonl.
    """
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
        
    processed_count = 0
    skipped_fragments = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            
            try:
                raw_data = json.loads(line)
                original_text = raw_data.get("text", "")
                
                # Apply the normalization pipeline
                clean_text = universal_normalize(original_text)
                
                # Validation Gate: Ensure text is a complete sentence (Option A)
                # 1. Must not be empty
                # 2. Must start with a capital letter
                # 3. Must end with standard terminal punctuation
                if not clean_text:
                    continue
                
                starts_valid = clean_text[0].isupper()
                ends_valid = clean_text.endswith(('.', '!', '?'))
                
                if not (starts_valid and ends_valid):
                    skipped_fragments += 1
                    continue
                
                # Construct the clean object (dropping tokens and token_count)
                clean_obj = {"text": clean_text}
                
                # Write to the new file
                with open(OUTPUT_FILE, 'a', encoding='utf-8') as out_f:
                    out_f.write(json.dumps(clean_obj) + "\n")
                
                processed_count += 1
                
            except json.JSONDecodeError:
                continue
    
    print(f"Normalization Complete.")
    print(f"Successfully processed {processed_count} wiki entries.")
    print(f"Skipped {skipped_fragments} fragmented or invalid rows.")

if __name__ == "__main__":
    process_wiki_data()
