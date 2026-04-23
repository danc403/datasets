import json
import glob
import os
import re
import html
import random
import unicodedata

# --- Configuration ---
TARGET_PATTERN = "**/*.json"
OUTPUT_FILE = "global.jsonl"

# --- Core QA Definitions ---
WORLD_QA = {
    "Geography.Area.total.text": ("What is the total surface area of the Earth?", "The total surface area of the World is {val}.", "total: "),
    "People and Society.Population.total.text": ("What is the total human population of the World?", "The total world population is estimated at {val}.", "total: "),
    "Geography.Elevation.highest point.text": ("What is the highest point on Earth?", "The highest point in the world is {val}.", "highest point: "),
    "Geography.Elevation.lowest point.text": ("What is the lowest point on Earth?", "The lowest point in the world is {val}.", "lowest point: "),
}

OCEAN_QA = {
    "Geography.Area.total.text": ("What is the total area of the {name}?", "The total area of the {name} is {val}.", "total: "),
    "Geography.Ocean volume.ocean volume.text": ("What is the volume of the {name}?", "The total volume of the {name} is {val}.", "ocean volume: "),
    "Geography.Elevation.lowest point.text": ("What is the deepest point in the {name}?", "The lowest point in the {name} is {val}.", "lowest point: "),
    "Geography.Elevation.mean depth.text": ("What is the average depth of the {name}?", "The mean depth of the {name} is {val}.", "mean depth: "),
}

NARRATIVE_PATHS = [
    "Introduction.Background.text",
    "Geography.Geographic overview.text",
    "Geography.Geography - note.text"
]

def sanitize_unicode(text):
    if not isinstance(text, str): return str(text)
    mapping = {
        '\u2013': '-', '\u2014': '-',
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u00b0': ' degrees ',
        '\u2026': '...',
        '\u00a0': ' ',
    }
    for code, char in mapping.items():
        text = text.replace(code, char)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text

def clean_content(raw):
    if not raw: return ""
    text = re.sub('<.*?>', ' ', str(raw))
    text = html.unescape(text)
    text = re.sub(r'\(?see\s+Figure\s+\d+([,\s]*\d+)*\)?', '', text, flags=re.IGNORECASE)
    text = sanitize_unicode(text)
    return ' '.join(text.split()).strip()

def get_nested(data, path):
    for part in path.split('.'):
        if isinstance(data, dict): data = data.get(part)
        else: return None
    return data

def write_line(obj):
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def process_datasets():
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    
    entity_map = {
        "oo.json": "Southern Ocean",
        "xo.json": "Indian Ocean",
        "xq.json": "Arctic Ocean",
        "zh.json": "Atlantic Ocean",
        "zn.json": "Pacific Ocean",
        "xx.json": "World"
    }

    for file_path in glob.iglob(TARGET_PATTERN, recursive=True):
        fname = os.path.basename(file_path).lower()
        if fname not in entity_map: continue
        
        entity = entity_map[fname]
        is_world = (entity == "World")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # --- Step 1: Build Fact Sheet Context ---
                context_parts = []
                for path in NARRATIVE_PATHS:
                    raw_context = get_nested(data, path)
                    if raw_context:
                        # Extract a clean label from the path
                        label = path.replace('.text', '').split('.')[-1]
                        context_parts.append(f"{label}: {clean_content(raw_context)}")
                
                # SHUFFLE the narrative blocks to prevent positional memorization
                random.shuffle(context_parts)
                
                full_context = f"{entity} Fact Sheet: " + " | ".join(context_parts)
                
                # --- Step 2: Narratives ---
                for path in NARRATIVE_PATHS:
                    raw = get_nested(data, path)
                    if raw:
                        label = path.replace('.text', '')
                        write_line({"text": f"{entity} {label}: {clean_content(raw)}"})
                
                # --- Step 3: Hardcoded QA with Masking ---
                templates = WORLD_QA if is_world else OCEAN_QA
                for path, (q_tpl, r_tpl, m_pre) in templates.items():
                    val = get_nested(data, path)
                    if val:
                        cleaned_val = clean_content(val)
                        prompt = q_tpl.format(name=entity)
                        resp = r_tpl.format(name=entity, val=cleaned_val)
                        
                        # Row A: Contextual with Masks
                        # Masking remains deterministic because the labels inside context_parts are untouched
                        write_line({
                            "prompt": prompt, 
                            "response": resp, 
                            "context": full_context,
                            "mask_pre": m_pre,
                            "mask_target": cleaned_val,
                            "mask_post": " |"
                        })
                        
                        # Row B: Standalone
                        write_line({"text": resp})
                
                # --- Step 4: Discovery for Extremes ---
                if is_world:
                    for section in ["Geography", "Environment"]:
                        sec_data = data.get(section, {})
                        if not isinstance(sec_data, dict): continue
                        for key, val in sec_data.items():
                            if any(x in key.lower() for x in ["ten ", "wonders", "seven "]):
                                text_val = val.get("text") if isinstance(val, dict) else val
                                if text_val:
                                    cleaned_ext = clean_content(text_val)
                                    prompt_ext = f"What are the {key} on Earth?"
                                    resp_ext = f"The {key} are: {cleaned_ext}"
                                    
                                    write_line({
                                        "prompt": prompt_ext, 
                                        "response": resp_ext, 
                                        "context": full_context,
                                        "mask_pre": f"{key}: ",
                                        "mask_target": cleaned_ext,
                                        "mask_post": " |"
                                    })
                                    write_line({"text": resp_ext})

                # --- Step 5: Biomes ---
                if is_world:
                    biomes = data.get("Environment", {}).get("World biomes", {})
                    if isinstance(biomes, dict):
                        for b_name, b_data in biomes.items():
                            b_text = b_data.get("text")
                            if b_text:
                                write_line({"text": f"Global Biome ({b_name}): {clean_content(b_text)}"})

        except Exception as e:
            print(f"Error processing {fname}: {e}")

if __name__ == "__main__":
    process_datasets()
