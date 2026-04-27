import json
import time
import os
import re
import requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- CONFIGURATION ---
RATE_LIMIT_DELAY = 3.0
SAMPLE_MODE = False
SAMPLE_SIZE = 25
INPUT_FILE = "music.jsonl"
OUTPUT_FILE = "music_lyrics.jsonl"

# --- OUTPUT TOGGLE ---
INCLUDE_EMPTY = False 

# Blacklist for search query optimization
SEARCH_BLACKLIST = ["Instrumental", "Live", "Remix", "Demo"]

# Artist Exclusion List: Cull these before scraping
ARTIST_EXCLUSIONS = [
    "3 6 Mafia",
    "Trillville",
    "Lil Wyte",
    "Project Pat",
    "Lil Jon",
    "Bob And Tom",
    "Bill Engvall",
    "Ray Stevens",
    "Ram Jam",
    "Right Said Fred",
    "Rednex",
    "Rupert Holmes",
    "Enigma",
    "Enya",
    "Era",
    "Prodigy"
]

# Additional cull for time optimization (High repetition/low linguistic density)
HEAVY_CULL = {
    "Akon", "Fergie", "Rihanna", "Flo Rida", "Sean Kingston", 
    "Black Eyed Peas", "Shaggy", "Pitbull", "Bahha Men"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def sanitize_to_ascii(text):
    if not text:
        return ""
    replacements = {
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-',
        '\u2026': '...', '\u200b': '',
        '\u200e': '', '\ufeff': '',
    }
    for uni, plain in replacements.items():
        text = text.replace(uni, plain)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text

def clean_lyric_text(text):
    if not text:
        return ""
    text = re.sub(r'^\d+\sContributor(s)?.*?\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^.*?Lyrics\n', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\d*Embed$', '', text)
    text = re.sub(r'^.*?Read More.*?\n', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'You might also like', '', text, flags=re.IGNORECASE)
    text = sanitize_to_ascii(text)
    return text.strip()

def is_instrumental(text):
    if not text:
        return False
    placeholders = [
        r"instrumental",
        r"this song is an instrumental",
        r"lyrics for this song have yet to be released",
        r"traditionally contains no lyrics"
    ]
    clean_check = text.lower().strip()
    if re.search(r'\[instrumental\]', clean_check) or any(p in clean_check for p in placeholders):
        return True
    return len(clean_check) < 40 and "instrumental" in clean_check

def get_genius_lyrics(performer, title):
    try:
        query = f"{performer} {title}"
        for term in SEARCH_BLACKLIST:
            query = query.replace(term, "")

        search_url = f"https://genius.com/api/search/multi?q={quote(query.strip())}"
        response = requests.get(search_url, headers=HEADERS, timeout=12)
        if response.status_code != 200: return ""

        data = response.json()
        sections = data.get("response", {}).get("sections", [])
        hits = [h for s in sections if s.get("type") == "song" for h in s.get("hits", [])]
        if not hits: return ""

        song_path = hits[0].get("result", {}).get("path")
        page_res = requests.get(f"https://genius.com{song_path}", headers=HEADERS, timeout=15)
        soup = BeautifulSoup(page_res.text, "html.parser")
        
        lyrics_divs = soup.select('div[class^="Lyrics__Container"], .lyrics')
        if not lyrics_divs: return ""

        raw_lyrics = "\n".join([div.get_text(separator="\n") for div in lyrics_divs])
        cleaned = clean_lyric_text(raw_lyrics)
        return "" if is_instrumental(cleaned) else cleaned
    except Exception:
        return ""

def run_scraper():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    # Check for existing progress to allow resume
    processed_count = 0
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            processed_count = sum(1 for _ in f)
    
    print(f"Resume Status: Found {processed_count} existing records in {OUTPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if SAMPLE_MODE:
        lines = lines[:SAMPLE_SIZE]

    # Open in append mode with line-buffering to save data instantly
    with open(OUTPUT_FILE, "a", encoding="utf-8", buffering=1) as out_f:
        for i, line in enumerate(lines):
            # Skip logic for resuming after a crash
            if i < processed_count:
                continue

            item = json.loads(line.strip())
            p, t = item.get("performer", ""), item.get("song_title", "")
            
            # --- EXCLUSION CHECK ---
            if p in HEAVY_CULL or any(excl.lower() in p.lower() for excl in ARTIST_EXCLUSIONS):
                print(f"[{i+1}/{len(lines)}] Skipping Canned Artist: {p}")
                continue

            print(f"[{i+1}/{len(lines)}] Scraping: {p} - {t}")
            lyrics = get_genius_lyrics(p, t)
            
            if lyrics or INCLUDE_EMPTY:
                item["lyrics"] = lyrics if lyrics else ""
                out_f.write(json.dumps(item) + "\n")
                out_f.flush() # Forces write to disk
            
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"Scrape process finished. Check {OUTPUT_FILE} for final results.")

if __name__ == "__main__":
    run_scraper()
