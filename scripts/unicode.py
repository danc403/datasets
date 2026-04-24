import os
import json
import glob
import unicodedata
import re

def sanitize_string(text):
    """
    Stabilizes Unicode and maps fancy punctuation for 24k-vocab compatibility.
    Updated to aggressively strip Latin-1 and Latin-A extended characters.
    """
    if not isinstance(text, str):
        return text

    # Handle literal backslashed escape sequences first
    escape_map = {
        r'\\u201[89]': "'",
        r'\\u201[cd]': '"',
        r'\\u201[34]': "-",
        r'\\u2026': "...",
        r'\\u00a0': " ",
        r'\\u00f6': "o",
        r'\\u00fc': "u",
        r'\\u00e9': "e",
        r'\\u00e8': "e",
        r'\\u00f4': "o",
        r'\\u010d': "c",
    }
    for pattern, replacement in escape_map.items():
        text = re.sub(pattern, replacement, text)

    # Map actual Unicode characters and Latin-1/A extensions
    punctuation_map = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
        '\u2026': '...', '\u00a0': ' ',
        '\ufeff': '',
        '\u00f6': 'o', '\u00fc': 'u',
        '\u00e9': 'e', '\u00e8': 'e',
        '\u00f4': 'o', '\u010d': 'c',
    }
    for search, replace in punctuation_map.items():
        text = text.replace(search, replace)

    # Normalize and strip diacritics (NFKD breaks down accented chars to base+accent)
    text = unicodedata.normalize('NFKD', text)
    # This specifically removes the 'accent' part of the character
    text = "".join([c for c in text if not unicodedata.combining(c)])
    # Final normalization to bring everything back to a standard form
    text = unicodedata.normalize('NFC', text)

    # Remove non-printable control characters (keep \n, \r, \t)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ord(ch) in (9, 10, 13))

    return text

def sanitize_recursive(obj):
    """
    Recursively walks JSON. PROTECTS the 'tokens' key.
    """
    if isinstance(obj, dict):
        return {k: (v if k == "tokens" else sanitize_recursive(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_recursive(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_string(obj)
    else:
        return obj

def process_jsonl_files(data_dir="."):
    files = glob.glob(os.path.join(data_dir, "*.jsonl"))
    
    if not files:
        print(f"No .jsonl files found in {data_dir}")
        return

    for file_path in files:
        output_lines = []
        processed_count = 0
        error_count = 0
        line_num = 0
        
        print(f"Reading: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line_num += 1
                    raw_line = line.strip()
                    if not raw_line:
                        continue
                    
                    try:
                        # Attempt to parse
                        data = json.loads(raw_line)
                        sanitized_data = sanitize_recursive(data)
                        # Re-string with ensure_ascii=False to prevent \u re-encoding
                        json_out = json.dumps(sanitized_data, ensure_ascii=False)
                        output_lines.append(json_out)
                        processed_count += 1
                        
                    except json.JSONDecodeError as e:
                        print(f"Line {line_num} in {file_path} is INVALID JSON. Skipping. Error: {e}")
                        error_count += 1
                        continue

            # CRITICAL: Only overwrite if we actually have data to write
            if processed_count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for out_line in output_lines:
                        f.write(out_line + '\n')
                print(f"FINISH: {file_path} | Kept: {processed_count} | Dropped: {error_count}")
            else:
                print(f"ABORT: {file_path} would have been emptied. Check your JSON format.")

        except Exception as e:
            print(f"FATAL ERROR on {file_path}: {str(e)}")

if __name__ == "__main__":
    process_jsonl_files(".")
