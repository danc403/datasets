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

# --- NEW TOOL-CALLING TEMPLATES ---
TOOL_LYRIC_PROMPTS = [
    "Check the music database for {title} lyrics.",
    "Use the local archive tool to find the words for {title}.",
    "Query the internal library for {author} - {title}."
]

WEB_LYRIC_PROMPTS = [
    "Search the web for the lyrics to {title} by {author}.",
    "The local lookup failed. Use the web search tool to find the text for {title}.",
    "Escalate to a web search to find {title} by {author}."
]

# --- THINKING TEMPLATES ---
THINK_KNOWLEDGE = [
    "The request asks for {item}. I will check my internal parameters and provide the answer directly.",
    "User is asking for {item}. Accessing stored training weights to retrieve the specific data.",
    "Retrieving the details for {item} from local context."
]

THINK_TOOL = [
    "User is requesting a local search for {item}. I will execute the relevant database tool call.",
    "Accessing internal music database tools to fulfill the request for {item}.",
    "Invoking local search protocols for {item}."
]

THINK_WEB = [
    "Local lookup for {item} failed or was not requested. I will proceed with a web search to find the correct data.",
    "Data for {item} not found in local records. Escalating to external web search.",
    "Searching external sources for {item} following local retrieval failure."
]

def format_json_context(data_dict):
    """
    Serializes metadata to a JSON string.
    """
    return json.dumps(data_dict)

def get_blind_snippet(lyrics, title):
    """
    Identifies the hook while ensuring the title is not given away in the prompt.
    """
    lines = [
        line.strip() for line in lyrics.split('\n') 
        if line.strip() and not line.startswith('[') and len(line.split()) > 2
    ]
    
    if not lines:
        snippet = lyrics[:100].strip().replace('\n', ' / ')
        return re.sub(re.escape(title), "[...]", snippet, flags=re.IGNORECASE)

    line_counts = Counter(lines)
    clean_title = re.escape(title.lower())
    priority_lines = []
    backup_lines = []

    for line, count in line_counts.items():
        if not re.search(clean_title, line.lower()):
            priority_lines.append((line, count))
        else:
            backup_lines.append((line, count))

    priority_lines.sort(key=lambda x: (x[1], len(x[0])), reverse=True)

    if priority_lines:
        best_line = priority_lines[0][0]
    elif backup_lines:
        backup_lines.sort(key=lambda x: (x[1], len(x[0])), reverse=True)
        best_line = backup_lines[0][0]
    else:
        return "[...]"
    
    try:
        idx = lines.index(best_line)
        if idx + 1 < len(lines):
            snippet = f"{lines[idx]} / {lines[idx+1]}"
        else:
            snippet = lines[idx]
        return re.sub(clean_title, "[...]", snippet, flags=re.IGNORECASE)
    except ValueError:
        return re.sub(clean_title, "[...]", best_line, flags=re.IGNORECASE)

def build_instruct_set():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    raw_data = []
    artist_map = {}

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
                if item.get("lyrics"):
                    raw_data.append(item)
                    artist = item["performer"]
                    if artist not in artist_map:
                        artist_map[artist] = []
                    # Deduplicate songs for this artist immediately
                    if item["song_title"] not in artist_map[artist]:
                        artist_map[artist].append(item["song_title"])
            except json.JSONDecodeError:
                continue

    instruct_records = []

    for item in raw_data:
        t = item["song_title"]
        a = item["performer"]
        ly = item["lyrics"]
        h = item.get("hierarchy", [])

        # 1. LYRICS (Knowledge, Tool, Web)
        p_ly = random.choice(LYRIC_PROMPTS).format(title=t, author=a)
        instruct_records.append({
            "title": t, "author": a, "context": ly, "prompt": p_ly, "response": ly,
            "thinking": random.choice(THINK_KNOWLEDGE).format(item=f"{t} lyrics")
        })
        
        t_call = f"CALL: music_local_search(title='{t}', artist='{a}')"
        t_ctx = format_json_context({"status": "success", "source": "local_db", "data": {"lyrics": ly}})
        instruct_records.append({
            "title": t, "author": a, "context": t_ctx, "prompt": f"Using available tools, {p_ly}", 
            "response": f"{t_call}\n\nI have retrieved the lyrics from the local archive: {ly}",
            "thinking": random.choice(THINK_TOOL).format(item=f"{t} lyrics")
        })

        w_call = f"CALL: music_local_search(title='{t}') -> Result: NOT_FOUND\nCALL: search_web(query='{t} {a} lyrics')"
        w_ctx = format_json_context({"status": "success", "source": "web_search", "content": ly})
        instruct_records.append({
            "title": t, "author": a, "context": w_ctx, "prompt": f"Search the web for {p_ly}", 
            "response": f"{w_call}\n\nThe local archive lookup failed, but I located the lyrics via web search: {ly}",
            "thinking": random.choice(THINK_WEB).format(item=f"{t} lyrics")
        })

        # 2. METADATA (Knowledge, Tool, Web)
        p_md = random.choice(METADATA_PROMPTS).format(title=t, author=a)
        res_md = f"The song '{t}' was performed by {a}."
        instruct_records.append({
            "title": t, "author": a, "context": format_json_context({"artist": a, "title": t, "match_confidence": 1.0}), 
            "prompt": p_md, "response": res_md,
            "thinking": random.choice(THINK_KNOWLEDGE).format(item=f"artist info for {t}")
        })
        
        t_md_call = f"CALL: metadata_lookup(title='{t}')"
        instruct_records.append({
            "title": t, "author": a, "context": format_json_context({"artist": a, "title": t}), 
            "prompt": f"Query database: {p_md}", "response": f"{t_md_call}\n\n{res_md}",
            "thinking": random.choice(THINK_TOOL).format(item=f"artist metadata for {t}")
        })
        
        w_md_call = f"CALL: metadata_lookup(title='{t}') -> NOT_FOUND\nCALL: search_web(query='{t} artist release info')"
        instruct_records.append({
            "title": t, "author": a, "context": format_json_context({"artist": a, "title": t}), 
            "prompt": f"Web search info: {p_md}", "response": f"{w_md_call}\n\nWeb results confirm: {res_md}",
            "thinking": random.choice(THINK_WEB).format(item=f"artist metadata for {t}")
        })

        # 3. REVERSE LOOKUP (Knowledge Only)
        snippet = get_blind_snippet(ly, t)
        p_rev = random.choice(REVERSE_LOOKUP_PROMPTS).format(snippet=snippet, author=a)
        instruct_records.append({
            "title": t, "author": a, "context": ly, "prompt": p_rev, 
            "response": f"Those lyrics are from the song '{t}' by {a}.",
            "thinking": random.choice(THINK_KNOWLEDGE).format(item="reverse lyric lookup")
        })

        # 4. HIERARCHY / ALBUM / LOCATION
        if len(h) >= 1:
            album = h[0]
            p_alb = random.choice(ALBUM_PROMPTS).format(title=t, author=a)
            ctx_alb = format_json_context({"album": album, "artist": a, "track": t})
            instruct_records.append({
                "title": t, "author": a, "context": ctx_alb, "prompt": p_alb, 
                "response": f"The song '{t}' is featured on the album '{album}' by {a}.",
                "thinking": random.choice(THINK_KNOWLEDGE).format(item=f"album info for {t}")
            })
            
            t_alb_call = f"CALL: get_album_info(title='{t}')"
            instruct_records.append({
                "title": t, "author": a, "context": ctx_alb, "prompt": f"Query the media tool: {p_alb}", 
                "response": f"{t_alb_call}\n\nAccording to the local database, '{t}' is on the album '{album}'.",
                "thinking": random.choice(THINK_TOOL).format(item=f"album info for {t}")
            })

            path_str = " -> ".join([a] + h)
            p_loc = random.choice(LOCATION_PROMPTS).format(title=t, author=a)
            ctx_loc = format_json_context({"storage_path": path_str, "file_system": "local_archive"})
            instruct_records.append({
                "title": t, "author": a, "context": ctx_loc, "prompt": p_loc, 
                "response": f"In the archive, you can find {t} located under: {path_str}.",
                "thinking": random.choice(THINK_KNOWLEDGE).format(item=f"file location for {t}")
            })

            t_loc_call = f"CALL: get_file_status(title='{t}')"
            instruct_records.append({
                "title": t, "author": a, "context": ctx_loc, "prompt": f"Check file location tool: {p_loc}", 
                "response": f"{t_loc_call}\n\nThe system reports the file path as: {path_str}.",
                "thinking": random.choice(THINK_TOOL).format(item=f"file location for {t}")
            })

    # 5. DISCOGRAPHY (Knowledge, Tool, Web)
    for artist, songs in artist_map.items():
        # Final deduplication check
        unique_songs = sorted(list(set(songs)))
        if len(unique_songs) > 1:
            p_disc = random.choice(DISCOGRAPHY_PROMPTS).format(author=artist)
            ctx_disc = format_json_context({"performer": artist, "count": len(unique_songs), "tracks": unique_songs})
            song_list = ", ".join(unique_songs)
            
            instruct_records.append({
                "title": "N/A", "author": artist, "context": ctx_disc, "prompt": p_disc, 
                "response": f"I have {len(unique_songs)} tracks listed for {artist}: {song_list}.",
                "thinking": random.choice(THINK_KNOWLEDGE).format(item=f"discography for {artist}")
            })

            t_disc_call = f"CALL: get_artist_discography(artist='{artist}')"
            instruct_records.append({
                "title": "N/A", "author": artist, "context": ctx_disc, "prompt": f"Search local records: {p_disc}", 
                "response": f"{t_disc_call}\n\nLocal search returned {len(unique_songs)} songs for {artist}: {song_list}.",
                "thinking": random.choice(THINK_TOOL).format(item=f"discography for {artist}")
            })

            w_disc_call = f"CALL: get_artist_discography(artist='{artist}') -> NOT_FOUND\nCALL: search_web(query='{artist} full track list')"
            instruct_records.append({
                "title": "N/A", "author": artist, "context": ctx_disc, "prompt": f"Search the web: {p_disc}", 
                "response": f"{w_disc_call}\n\nWeb results for {artist} show the following tracks: {song_list}.",
                "thinking": random.choice(THINK_WEB).format(item=f"discography for {artist}")
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for record in instruct_records:
            out_f.write(json.dumps(record) + "\n")

    print(f"Instruction set built: {len(instruct_records)} pairs created from {len(raw_data)} songs.")

if __name__ == "__main__":
    build_instruct_set()

