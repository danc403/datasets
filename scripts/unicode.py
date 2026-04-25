import os
import json
import glob
import unicodedata
import re

def sanitize_string(text):
    """
    Stabilizes Unicode and maps fancy punctuation for 24k-vocab compatibility.
    Updated to aggressively strip Latin-1 and Latin-A extended characters.
    Now includes full phonetic mapping for Nordic, Cyrillic, and Greek blocks
    to ensure data integrity in Factbook and international datasets.
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

    # Map actual Unicode characters, Latin-1/A extensions, and Currencies
    punctuation_map = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
        '\u2026': '...', '\u00a0': ' ',
        '\ufeff': '',
        '\u00f6': 'o', '\u00fc': 'u',
        '\u00e9': 'e', '\u00e8': 'e',
        '\u00f4': 'o', '\u010d': 'c',
        # Nordic / Germanic Additions
        '\u00e6': 'ae', '\u00c6': 'AE',
        '\u00f8': 'o', '\u00d8': 'O',
        '\u00df': 'ss',
        '\u00fe': 'th', '\u00de': 'TH',
        '\u00f0': 'd', '\u00d0': 'D',
        # Currencies
        '\u00a3': 'GBP', '\u20ac': 'EUR', '\u00a5': 'JPY',
    }
    for search, replace in punctuation_map.items():
        text = text.replace(search, replace)

    # Phonetic Cyrillic Mapping (Lowercase only for brevity, handles common Factbook text)
    cyrillic_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    # Phonetic Greek Mapping
    greek_map = {
        'α': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th',
        'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p',
        'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o'
    }
    
    # Apply Alphabet Mappings
    for c_char, r_char in cyrillic_map.items():
        text = text.replace(c_char, r_char).replace(c_char.upper(), r_char.capitalize())
    for g_char, r_char in greek_map.items():
        text = text.replace(g_char, r_char).replace(g_char.upper(), r_char.capitalize())

    # Normalize and strip diacritics
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = unicodedata.normalize('NFC', text)

    # Final Safety Pass: Strip remaining non-ASCII to prevent tokenizer failure
    text = "".join(ch for ch in text if (31 < ord(ch) < 127) or ord(ch) in (9, 10, 13))

    # Remove non-printable control characters (Secondary check)
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
    """
    Targets files recursively using glob. 
    Writes to a temporary file line-by-line to save memory and ensure atomic updates.
    """
    # Recursive globbing enabled by default
    files = glob.glob(os.path.join(data_dir, "**", "*.jsonl"), recursive=True)
    
    if not files:
        print(f"No .jsonl files found in {data_dir}")
        return

    for file_path in files:
        temp_file_path = file_path + ".tmp"
        processed_count = 0
        error_count = 0
        line_num = 0
        
        print(f"Reading: {file_path}")
        
        try:
            # Open both files: read original, write to temporary
            with open(file_path, 'r', encoding='utf-8') as fin, \
                 open(temp_file_path, 'w', encoding='utf-8') as fout:
                
                for line in fin:
                    line_num += 1
                    raw_line = line.strip()
                    if not raw_line:
                        continue
                    
                    try:
                        data = json.loads(raw_line)
                        sanitized_data = sanitize_recursive(data)
                        # ensure_ascii=False keeps the actual characters rather than \u escapes
                        json_out = json.dumps(sanitized_data, ensure_ascii=False)
                        fout.write(json_out + '\n')
                        processed_count += 1
                        
                    except json.JSONDecodeError as e:
                        print(f"Line {line_num} in {file_path} is INVALID JSON. Skipping. Error: {e}")
                        error_count += 1
                        continue

            # Atomic swap: Only replace original if data was successfully processed
            if processed_count > 0:
                os.replace(temp_file_path, file_path)
                print(f"FINISH: {file_path} | Kept: {processed_count} | Dropped: {error_count}")
            else:
                # If no lines were processed, remove empty temp and preserve original
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                print(f"ABORT: {file_path} processed zero lines. Keeping original.")

        except Exception as e:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            print(f"FATAL ERROR on {file_path}: {str(e)}")

if __name__ == "__main__":
    process_jsonl_files(".")
