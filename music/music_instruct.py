import json
import os
import random
from collections import Counter
import re

# --- CONFIGURATION ---
INPUT_FILE = "music_lyrics.jsonl"
OUTPUT_FILE = "music_instruct.jsonl"

# --- PROMPT TEMPLATES ---
LYRIC_PROMPTS = [
    "What are the words to {title} by {author}?",
    "Give me the lyrics for {title} by {author}.",
    "I need the lyrics to {title}.",
    "What are the lyrics to the song {title}?",
    "Can you show me the full text for the song {title}?"
]

METADATA_PROMPTS = [
    "Who performed the song {title}?",
    "Who sang the song {title}?",
    "Which artist is responsible for {title}?",
    "Identify the performer for the track: {title}.",
    "Do you know who released {title}?"
]

REVERSE_LOOKUP_PROMPTS = [
    "What song includes these lyrics: \"{snippet}\"?",
    "What song is this: \"{snippet}\"?",
    "I remember a song with the words \"{snippet}\", what is the title?",
    "Which {author} song contains the line: \"{snippet}\"?",
    "Recognize these lyrics for me: \"{snippet}\""
]

DISCOGRAPHY_PROMPTS = [
    "What are some songs by {author}?",
    "List the tracks you have for {author}.",
    "What songs performed by {author} are in the archive?",
    "Show me the discography for {author}.",
    "What has {author} recorded that we have on file?"
]

ALBUM_PROMPTS = [
    "What album is the song {title} on?",
    "Which album by {author} contains the track {title}?",
    "I'm looking for the album name for {title}.",
    "Identify the album associated with {title}.",
    "Where can I find {title} in terms of an album release?"
]

LOCATION_PROMPTS = [
    "Where is {title} located in the archive?",
    "What is the file path for {title}?",
    "How is {title} organized in the library?",
    "Provide the directory hierarchy for {title}.",
    "Look up the storage path for {title}."
]

def format_json_context(data_dict):
    """
    Serializes metadata to a JSON string.
    This trains the model to act as a bridge between structured data and natural language.
    """
    return json.dumps(data_dict)

def get_blind_snippet(lyrics, title):
    """
    Identifies the hook while ensuring the title is not given away in the prompt.
    Uses frequency-based analysis to mimic human memory of a 'hook'.
    """
    # 1. Clean and split into meaningful lines
    lines = [
        line.strip() for line in lyrics.split('\n') 
        if line.strip() and not line.startswith('[') and len(line.split()) > 2
    ]
    
    if not lines:
        # Fallback for very short/unusual lyrics
        snippet = lyrics[:100].strip().replace('\n', ' / ')
        return re.sub(re.escape(title), "[...]", snippet, flags=re.IGNORECASE)

    # 2. Count line occurrences to find the 'Hook'
    line_counts = Counter(lines)
    
    # 3. Filter and Sort
    # Prioritize lines that do NOT contain the song title
    clean_title = re.escape(title.lower())
    priority_lines = []
    backup_lines = []

    for line, count in line_counts.items():
        if not re.search(clean_title, line.lower()):
            priority_lines.append((line, count))
        else:
            backup_lines.append((line, count))

    # Sort priority lines by frequency, then by length (longer = more unique)
    priority_lines.sort(key=lambda x: (x[1], len(x[0])), reverse=True)

    # 4. Selection Logic
    if priority_lines:
        best_line = priority_lines[0][0]
    elif backup_lines:
        # Fallback: Use the hook but we must redact the title
        backup_lines.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        best_line = backup_lines[0][0]
    else:
        return "[...]"
    
    # Try to pair it with the next line for better context
    try:
        idx = lines.index(best_line)
        if idx + 1 < len(lines):
            snippet = f"{lines[idx]} / {lines[idx+1]}"
        else:
            snippet = lines[idx]
            
        # Final redaction sweep
        return re.sub(clean_title, "[...]", snippet, flags=re.IGNORECASE)
    except ValueError:
        return re.sub(clean_title, "[...]", best_line, flags=re.IGNORECASE)

def build_instruct_set():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    raw_data = []
    artist_map = {}

    # 1. Load and Index
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get("lyrics"):
                    raw_data.append(item)
                    artist = item["performer"]
                    if artist not in artist_map:
                        artist_map[artist] = []
                    artist_map[artist].append(item["song_title"])
            except json.JSONDecodeError:
                continue

    instruct_records = []

    # 2. Generate Pairs per song
    for item in raw_data:
        t = item["song_title"]
        a = item["performer"]
        ly = item["lyrics"]
        h = item.get("hierarchy", [])

        # Template 1: Direct Lyric Request (Uses raw text as it's a long-form task)
        prompt_1 = random.choice(LYRIC_PROMPTS).format(title=t, author=a)
        instruct_records.append({
            "title": t, "author": a, "context": ly,
            "prompt": prompt_1, "response": ly
        })

        # Template 2: Who performed (Uses JSON Context)
        prompt_2 = random.choice(METADATA_PROMPTS).format(title=t, author=a)
        ctx_2 = format_json_context({"artist": a, "title": t, "match_confidence": 1.0})
        instruct_records.append({
            "title": t, "author": a, "context": ctx_2,
            "prompt": prompt_2, "response": f"The song '{t}' was performed by {a}."
        })

        # Template 3: Reverse Lookup (Blind Snippet)
        snippet = get_blind_snippet(ly, t)
        prompt_3 = random.choice(REVERSE_LOOKUP_PROMPTS).format(snippet=snippet, author=a)
        instruct_records.append({
            "title": t, "author": a, "context": ly,
            "prompt": prompt_3, "response": f"Those lyrics are from the song '{t}' by {a}."
        })

        # --- Hierarchy & Album Logic ---
        if len(h) >= 1:
            album = h[0]
            # Template 4: Album Name (Uses JSON Context)
            prompt_alb = random.choice(ALBUM_PROMPTS).format(title=t, author=a)
            ctx_alb = format_json_context({"album": album, "artist": a, "track": t})
            instruct_records.append({
                "title": t, "author": a, "context": ctx_alb,
                "prompt": prompt_alb, "response": f"The song '{t}' is featured on the album '{album}' by {a}."
            })
            
            # Template 5: Archive Path (Spatial Reasoning via JSON)
            path_str = " -> ".join([a] + h)
            prompt_loc = random.choice(LOCATION_PROMPTS).format(title=t, author=a)
            ctx_loc = format_json_context({"storage_path": path_str, "file_system": "local_archive"})
            instruct_records.append({
                "title": t, "author": a, "context": ctx_loc,
                "prompt": prompt_loc, "response": f"In the archive, you can find {t} located under: {path_str}."
            })

        if len(h) >= 2:
            disc = h[1]
            # Template 6: Multi-Disc specific (Uses JSON Context)
            prompt_disc = f"Which disc of the {h[0]} collection contains {t}?"
            ctx_multi = format_json_context({"parent_album": h[0], "media_segment": disc, "song": t})
            instruct_records.append({
                "title": t, "author": a, "context": ctx_multi,
                "prompt": prompt_disc, "response": f"'{t}' is found on {disc} of the '{h[0]}' collection."
            })

    # 3. Generate Artist Groupings (Discography)
    for artist, songs in artist_map.items():
        if len(songs) > 1:
            prompt_disc = random.choice(DISCOGRAPHY_PROMPTS).format(author=artist)
            # Create a structured JSON return for the discography
            ctx_disc = format_json_context({
                "performer": artist,
                "count": len(songs),
                "tracks": songs
            })
            song_list = ", ".join(songs)
            instruct_records.append({
                "title": "N/A", "author": artist, "context": ctx_disc,
                "prompt": prompt_disc,
                "response": f"I have {len(songs)} tracks listed for {artist}: {song_list}."
            })

    # 4. Write Output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for record in instruct_records:
            out_f.write(json.dumps(record) + "\n")

    print(f"Instruction set built: {len(instruct_records)} pairs created from {len(raw_data)} songs.")

if __name__ == "__main__":
    build_instruct_set()
