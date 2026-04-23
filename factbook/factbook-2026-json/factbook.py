import json
import glob
import os
import re
import argparse
import html
import random
import unicodedata

# --- Configuration ---
TARGET_PATTERN = "**/*.json"
OUTPUT_FILE = "factbook.jsonl"
WORD_LIMIT = 1500
SPACE_TRIGGER = 150
MILITARY_TRIGGER = 250

# --- Key Definitions ---
NAME_KEY = "Government.Country name.conventional short form.text"
INTRO_KEY = "Introduction.Background.text"
COORD_KEY = "Geography.Geographic coordinates.text"

SPACE_KEYS = [
    "Space.Space program overview.text",
    "Space.Key space-program milestones.text",
    "Space.Space agency/agencies.text",
    "Space.Space launch site(s).text"
]

MILITARY_KEYS = [
    "Military and Security.Military - note.text",
    "Military and Security.Military and security forces.text",
    "Military and Security.Military and security service personnel strengths.text",
    "Military and Security.Military equipment inventories and acquisitions.text",
    "Military and Security.Military service age and obligation.text"
]

# --- Instruction Templates (QA Pairs) ---
INSTRUCTION_TEMPLATES = {
    "Government.Capital.name.text": (
        "What is the capital of {country}?",
        "The capital of {country} is {val}."
    ),
    "People and Society.Population.total.text": (
        "What is the population of {country}?",
        "The population of {country} is {val}."
    ),
    "Geography.Area.total .text": (
        "What is the area of {country}?",
        "The total area of {country} is {val}."
    ),
    "Government.Independence.text": (
        "When did {country} gain independence?",
        "{country} gained independence on {val}."
    ),
    "People and Society.Languages.Languages.text": (
        "What languages are spoken in {country}?",
        "The languages of {country} are {val}."
    ),
    "Geography.Natural resources.text": (
        "What natural resources does {country} have?",
        "The natural resources of {country} are {val}."
    ),
    "Geography.Elevation.highest point.text": (
        "What is the highest point in {country}?",
        "The highest point in {country} is {val}."
    ),
    "Geography.Elevation.lowest point.text": (
        "What is the lowest point in {country}?",
        "The lowest point in {country} is {val}."
    ),
    "Geography.Location.text": (
        "Where is {country} located?",
        "{country} is located in {val}."
    ),
    "Geography.Climate.text": (
        "What is the climate like in {country}?",
        "The climate of {country} is {val}."
    ),
    "Economy.Agricultural products.text": (
        "What are the agricultural products of {country}?",
        "The primary agricultural products of {country} are {val}."
    ),
    "People and Society.Religions.text": (
        "What are the religions practiced in {country}?",
        "The religions in {country} are {val}."
    )
}

# --- Fact Sheet Whitelist ---
FACT_WHITELIST = [
    "Geography.Location.text", "Geography.Geographic coordinates.text", "Geography.Area - comparative.text",
    "Geography.Area.land.text", "Geography.Area.total .text", "Geography.Area.water.text",
    "Geography.Climate.text", "Geography.Coastline.text", "Geography.Elevation.highest point.text",
    "Geography.Elevation.lowest point.text", "Geography.Elevation.mean elevation.text",
    "Geography.Geography - note.text", "Geography.Land boundaries.border countries.text", "Geography.Land boundaries.total.text",
    "Geography.Natural resources.text", "Geography.Population distribution.text", "Geography.Terrain.text",
    "Government.Capital.name.text",
    "Government.Citizenship.citizenship by birth.text",
    "Government.Citizenship.citizenship by descent only.text", "Government.Citizenship.dual citizenship recognized.text",
    "Government.Constitution.amendment process.text", "Government.Constitution.history.text",
    "Government.Country name.conventional long form.text",
    "Government.Country name.local long form.text", "Government.Country name.local short form.text",
    "Government.Government type.text",
    "Government.Independence.text",
    "Government.Legal system.text",
    "Government.National symbol(s).text", "Government.Political parties.text", "Government.Suffrage.text",
    "Economy.Agricultural products.text",
    "Economy.Economic overview.text", "Economy.Exports - commodities.text",
    "Economy.Exports - partners.text", "Economy.Imports - commodities.text",
    "Energy.Coal.consumption.text", "Energy.Coal.proven reserves.text",
    "Energy.Electricity generation sources.fossil fuels.text",
    "Energy.Electricity generation sources.hydroelectricity.text", "Energy.Electricity generation sources.solar.text",
    "Energy.Natural gas.production.text", "Energy.Natural gas.proven reserves.text", "Energy.Petroleum.crude oil estimated reserves.text",
    "Environment.Environmental issues.text",
    "People and Society.Birth rate.text",
    "People and Society.Death rate.text",
    "People and Society.Education expenditure.Education expenditure (% GDP).text",
    "People and Society.Ethnic groups.text", "People and Society.Languages.Languages.text",
    "People and Society.Life expectancy at birth.total population.text",
    "People and Society.Median age.total.text",
    "People and Society.Population.total.text", 
    "People and Society.Religions.text",
    "Transportation.Airports.text",
    "Transportation.Railways.total.text", "Transportation.Ports.total ports.text"
]

def clean_text(raw, strip_meta=False):
    if not raw: return ""
    
    # 1. Basic HTML and Meta Cleaning
    text = re.sub('<.*?>', ' ', str(raw))
    text = html.unescape(text)
    if strip_meta:
        text = re.sub(r'\s*\([^)]*\)', '', text)
        text = text.strip().rstrip('.,;')

    # 2. Handle Literal Backslashed Escape Sequences (Tokenizer Protection)
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

    # 3. Map Actual Unicode Characters
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

    # 4. Aggressive Normalization (Strip remaining diacritics for 24k-vocab)
    text = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = unicodedata.normalize('NFC', text)

    # 5. Control Character Removal (Keep only terminal-safe whitespace)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ord(ch) in (9, 10, 13))

    # 6. Final whitespace consolidation
    return ' '.join(text.split())

def parse_coords(coord_str):
    try:
        parts = coord_str.replace(',', '').split()
        lat = float(parts[0]) + (float(parts[1])/60)
        if 'S' in parts[2]: lat *= -1
        lon = float(parts[3]) + (float(parts[4])/60)
        if 'W' in parts[5]: lon *= -1
        return lat, lon
    except:
        return None, None

def parse_area(area_str):
    try:
        clean_area = area_str.split('sq')[0].strip().replace(',', '')
        return float(clean_area)
    except:
        return None

def dedupe_label(path):
    parts = path.split('.')
    if len(parts) >= 3:
        main_cat = parts[-3].replace(':', '').strip()
        sub_cat = parts[-2].replace(':', '').strip()
        if main_cat.lower() in sub_cat.lower():
            return sub_cat.capitalize()
        return f"{main_cat} {sub_cat}".capitalize()
    return parts[0].capitalize()

def get_val(data, path):
    parts = path.split('.')
    for part in parts:
        if isinstance(data, dict): data = data.get(part)
        else: return None
    return data

def write_entry(prompt, response, context=None, mask_pre=None, mask_target=None, mask_post=None):
    entry = {"prompt": prompt, "response": response}
    if context:
        entry["context"] = context
    if mask_target:
        entry["mask_pre"] = mask_pre
        entry["mask_target"] = mask_target
        entry["mask_post"] = mask_post
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as out:
        out.write(json.dumps(entry, ensure_ascii=False) + "\n")

def write_base_fact(text):
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as out:
        out.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

def get_spatial_instruction(itype, name, target=None):
    if itype == "list":
        return f"Which countries share a land border with {name}?"
    if itype == "bool_pos":
        return f"Does {name} share a land border with {target}?"
    if itype == "bool_neg":
        return f"Does {name} share a land boundary with {target}?"
    if itype == "direction":
        return f"In what cardinal direction is {target} relative to {name}?"
    if itype == "area":
        return f"Between {name} and {target}, which country has a larger total land area?"
    return f"Tell me about the geography of {name}."

def build_categorical_context(country, data, key_path):
    category = key_path.split('.')[0]
    
    name_val = clean_text(get_val(data, NAME_KEY))
    if not name_val or name_val.lower() == "none":
        name_val = clean_text(get_val(data, "Government.Country name.conventional long form.text"))
    
    # Subject remains at the front
    header = f"Entity: {name_val}"
    
    fact_parts = []
    related_prefixes = {category}
    if category == "Geography": related_prefixes.add("Area")
    if category == "Economy": related_prefixes.add("Energy")
    if category == "Energy": related_prefixes.add("Economy")
    
    for k in FACT_WHITELIST:
        if any(k.startswith(prefix) for prefix in related_prefixes):
            val_raw = get_val(data, k)
            if val_raw:
                # Maintain exact anchor format for deterministic masking
                fact_parts.append(f"{dedupe_label(k)}: {clean_text(val_raw)}")
    
    # Shuffle only the fact blocks to preserve internal label: value syntax
    random.shuffle(fact_parts)
    
    final_parts = [header] + fact_parts
    return f"{country} {category} Context: " + " | ".join(final_parts)

def process_combined_data(is_test):
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    
    catalog = {}
    print("Indexing Sovereign Entities for 2026 data...")
    all_files = list(glob.iglob(TARGET_PATTERN, recursive=True))
    
    for file_path in all_files:
        if any(x in file_path.lower() for x in ['node_modules', 'package.json', 'world.json', 'oceans', 'world', 'meta', 'antarctica']): 
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                name = clean_text(get_val(data, NAME_KEY))
                if not name or name.lower() == "none":
                    name = clean_text(get_val(data, "Government.Country name.conventional long form.text"))
                
                coords = get_val(data, COORD_KEY)
                borders = get_val(data, "Geography.Land boundaries.border countries.text")
                area_raw = get_val(data, "Geography.Area.total .text")
                
                if name and name.lower() != "none":
                    lat, lon = parse_coords(coords) if coords else (None, None)
                    catalog[name] = {
                        "lat": lat, "lon": lon, 
                        "raw_coords": clean_text(coords),
                        "borders": clean_text(borders),
                        "area_val": parse_area(clean_text(area_raw)),
                        "area_raw": clean_text(area_raw),
                        "full_data": data
                    }
        except: continue

    country_names = list(catalog.keys())
    neighbor_pattern = r'([A-Z\u00C0-\u017F][a-z\u00C0-\u017F]+(?: (?:of the|and|the|of) [A-Z\u00C0-\u017F][a-z\u00C0-\u017F]+| [A-Z\u00C0-\u017F][a-z\u00C0-\u017F]+)*)'

    count = 0
    for name, info in catalog.items():
        data = info['full_data']
        country = name
        
        for key, (q_temp, r_temp) in INSTRUCTION_TEMPLATES.items():
            val_raw = get_val(data, key)
            if val_raw:
                val_clean = clean_text(val_raw, strip_meta=True)
                resp = r_temp.format(country=country, val=val_clean)
                label = dedupe_label(key)
                cat_ctx = build_categorical_context(country, data, key)
                
                write_entry(q_temp.format(country=country), resp, context=cat_ctx,
                            mask_pre=f"{label}: ", mask_target=val_clean, mask_post=" |")
                write_base_fact(resp)

        if info['raw_coords']:
            geo_ctx = build_categorical_context(country, data, COORD_KEY)
            parts = info['raw_coords'].split(',')
            if len(parts) == 2:
                lat_str = clean_text(parts[0], strip_meta=True)
                lon_str = clean_text(parts[1], strip_meta=True)
                coord_label = dedupe_label(COORD_KEY)
                
                write_entry(f"What is the latitude of {country}?", 
                            f"The latitude of {country} is {lat_str}.", 
                            context=geo_ctx,
                            mask_pre=f"{coord_label}: ", 
                            mask_target=lat_str, 
                            mask_post=",")
                
                write_entry(f"What is the longitude of {country}?", 
                            f"The longitude of {country} is {lon_str}.", 
                            context=geo_ctx,
                            mask_pre=f"{coord_label}: {lat_str}, ", 
                            mask_target=lon_str, 
                            mask_post=" |")
                
                write_base_fact(f"The latitude of {country} is {lat_str}.")
                write_base_fact(f"The longitude of {country} is {lon_str}.")

        intro = clean_text(get_val(data, INTRO_KEY))
        if intro: write_base_fact(f"{country} Introduction: {intro}")

        space_text = " ".join([clean_text(get_val(data, k)) for k in SPACE_KEYS if get_val(data, k)])
        if space_text and len(space_text.split()) > SPACE_TRIGGER:
            write_base_fact(f"{country} Space Program: {space_text}")

        mil_text = " ".join([clean_text(get_val(data, k)) for k in MILITARY_KEYS if get_val(data, k)])
        if mil_text and len(mil_text.split()) > MILITARY_TRIGGER:
            write_base_fact(f"{country} Military Affairs: {mil_text}")

        geo_ctx = build_categorical_context(country, data, "Geography.Location.text")
        border_text = info['borders']
        found = re.findall(neighbor_pattern, border_text)
        neighbors = []
        for n in found:
            n_clean = n.strip()
            if n_clean in catalog: neighbors.append(n_clean)
            elif n_clean == "Republic of the Congo" and "Congo (Brazzaville)" in catalog: neighbors.append("Congo (Brazzaville)")
            elif "Democratic Republic of the Congo" in n_clean and "DRC" in catalog: neighbors.append("DRC")
        neighbors = sorted(list(set(neighbors)))
        
        has_distances = bool(re.search(r'\d', border_text))
        border_label = dedupe_label("Geography.Land boundaries.border countries.text")

        if not has_distances and not neighbors:
            write_entry(f"Does {name} share any land borders?", f"No, {name} has no land boundaries.", context=geo_ctx)
            write_base_fact(f"Geographically, {name} is an island or coastal territory with no land boundaries.")
        else:
            write_entry(get_spatial_instruction("list", name), f"The neighbors of {name} are: {border_text}", 
                        context=geo_ctx, mask_pre=f"{border_label}: ", mask_target=border_text, mask_post=" |")
            write_base_fact(f"The land neighbors of {name} include {', '.join(neighbors) if neighbors else 'regional territories'}.")
            
            if neighbors:
                target = random.choice(neighbors)
                write_entry(get_spatial_instruction("bool_pos", name, target), f"Yes, {name} and {target} share a land border. Detail: {border_text}", context=geo_ctx)
                write_base_fact(f"A land border exists between the nations of {name} and {target}.")
                
                if info['lat'] is not None and catalog[target]['lat'] is not None:
                    n_info = catalog[target]
                    ns = "north" if n_info['lat'] > info['lat'] else "south"
                    ew = "east" if n_info['lon'] > info['lon'] else "west"
                    write_entry(get_spatial_instruction("direction", name, target), f"{target} ({n_info['raw_coords']}) is situated {ns} and {ew} of {name} ({info['raw_coords']}).", context=geo_ctx)
                    write_base_fact(f"Relatively, {target} is situated to the {ns} and {ew} of {name}.")
                
                if info['area_val'] and catalog[target]['area_val']:
                    larger = name if info['area_val'] > catalog[target]['area_val'] else target
                    write_entry(get_spatial_instruction("area", name, target), f"{larger} is larger. {name} has {info['area_raw']}, while {target} has {catalog[target]['area_raw']}.", context=geo_ctx)

            if country_names:
                non_n = random.choice(country_names)
                while non_n in neighbors or non_n == name: non_n = random.choice(country_names)
                write_entry(get_spatial_instruction("bool_neg", name, non_n), f"No, {name} does not border {non_n}.", context=geo_ctx)

        fact_sheet_pairs = [{"label": dedupe_label(k), "val": clean_text(get_val(data, k))} for k in FACT_WHITELIST if get_val(data, k)]
        
        # Shuffle the fact list per country to break template-based positional memorization
        random.shuffle(fact_sheet_pairs)

        current_fact_row = f"{country} Full Fact Sheet: "
        for pair in fact_sheet_pairs:
            entry = f"{pair['label']}: {pair['val']} | "
            if len(current_fact_row.split()) + len(entry.split()) > WORD_LIMIT:
                write_base_fact(current_fact_row.strip(" | "))
                current_fact_row = f"{country} Full Fact Sheet: {entry}"
            else:
                current_fact_row += entry
        write_base_fact(current_fact_row.strip(" | "))

        if is_test:
            count += 1
            if count >= 2: break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true")
    args = parser.parse_args()
    process_combined_data(args.test)
