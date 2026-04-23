import json
import os
import re
import unicodedata
import html
import random

# --- Configuration ---
INPUT_FILE = "pokemon_stats.jsonl"
OUTPUT_FILE = "pokemon_instruct.jsonl"

def universal_normalize(text):
    if not text: return ""
    # Move the POKeMON fix to the top of the normalization chain
    text = text.replace("POKeMON", "Pokemon").replace("<|end_of_text|>", "")
    text = html.unescape(text)
    normalized = unicodedata.normalize('NFKD', text)
    clean_ascii = normalized.encode('ascii', 'ignore').decode('ascii')
    clean_ascii = clean_ascii.replace('%', ' percent').replace(' degrees C', ' degrees Celsius')
    clean_ascii = re.sub(r'\bmph\b', 'miles per hour', clean_ascii)
    return re.sub(r'\s+', ' ', clean_ascii).strip()

def safe_extract(pattern, text, default="Unknown", is_int=False):
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        val = match.group(1).strip()
        if is_int:
            digits = re.findall(r'\d+', val)
            return int(digits[0]) if digits else 0
        return val
    return 0 if is_int else default

def parse_raw_pokemon(raw_text):
    data = {}
    try:
        # Normalize the name and strings IMMEDIATELY during extraction
        data['name'] = universal_normalize(safe_extract(r"Name:\s*(.*?)(?=\s*Number:|$)", raw_text))
        data['number'] = safe_extract(r"Number:\s*(\d+)", raw_text, is_int=True)
        data['region'] = universal_normalize(safe_extract(r"Region:\s*(.*?)(?=\s*Type:|$)", raw_text))
        
        types_raw = safe_extract(r"Type:\s*(.*?)(?=\s*Measurements:|$)", raw_text)
        data['types_list'] = [t.capitalize() for t in types_raw.split()]
        data['types_str'] = "/".join(data['types_list'])
        
        height_raw = float(safe_extract(r"Height\s*(\d+)dm", raw_text, is_int=True))
        weight_raw = float(safe_extract(r"Weight\s*(\d+)dg", raw_text, is_int=True))
        data['height_m'] = height_raw / 10
        data['weight_kg'] = weight_raw / 10
        
        data['hp'] = safe_extract(r"HP:\s*(\d+)", raw_text, is_int=True)
        data['atk'] = safe_extract(r"Attack:\s*(\d+)", raw_text, is_int=True)
        data['def'] = safe_extract(r"Defense:\s*(\d+)", raw_text, is_int=True)
        data['sp_atk'] = safe_extract(r"Special Attack:\s*(\d+)", raw_text, is_int=True)
        data['sp_def'] = safe_extract(r"Special Defense:\s*(\d+)", raw_text, is_int=True)
        data['speed'] = safe_extract(r"Speed:\s*(\d+)", raw_text, is_int=True)
        
        data['moves'] = universal_normalize(safe_extract(r"Moves:\s*(.*?)(?=\s*Description:|$)", raw_text))
        # This is the critical fix for the Lore masking:
        data['desc'] = universal_normalize(safe_extract(r"Description:\s*(.*?)(?=<\|end_of_text\|>|$)", raw_text))
        
        if data['number'] <= 151: data['gen'] = "Generation 1 (Old school)"
        elif data['number'] <= 251: data['gen'] = "Generation 2"
        else: data['gen'] = f"Generation {((data['number']-1)//100)}"
    except: return None
    return data

def build_shuffled_context(p, effectiveness):
    facts = [
        f"Name: {p['name']}", 
        f"Pokedex: {p['number']}",
        f"Origin: {p['region']} ({p['gen']})", 
        f"Type: {p['types_str']}",
        f"Stats: HP {p['hp']}, Atk {p['atk']}, Def {p['def']}, SpA {p['sp_atk']}, SpD {p['sp_def']}, Spe {p['speed']}",
        f"Moves: {p['moves']}", 
        f"Effective Against: {effectiveness}",
        f"Lore: {p['desc']}"
    ]
    random.shuffle(facts)
    # Context is built from already-normalized components, but one final pass ensures layout is clean
    return universal_normalize(f"Entity: {p['name']} | " + " | ".join(facts))

def get_effectiveness(types):
    type_chart = {
        "Normal": [], "Fire": ["Grass", "Ice", "Bug", "Steel"],
        "Water": ["Fire", "Ground", "Rock"], "Electric": ["Water", "Flying"],
        "Grass": ["Water", "Ground", "Rock"], "Ice": ["Grass", "Ground", "Flying", "Dragon"],
        "Fighting": ["Normal", "Ice", "Rock", "Dark", "Steel"], "Poison": ["Grass", "Fairy"],
        "Ground": ["Fire", "Electric", "Poison", "Rock", "Steel"], "Flying": ["Grass", "Fighting", "Bug"],
        "Psychic": ["Fighting", "Poison"], "Bug": ["Grass", "Psychic", "Dark"],
        "Rock": ["Fire", "Ice", "Flying", "Bug"], "Ghost": ["Psychic", "Ghost"],
        "Dragon": ["Dragon"], "Dark": ["Psychic", "Ghost"],
        "Steel": ["Ice", "Rock", "Fairy"], "Fairy": ["Fighting", "Dragon", "Dark"]
    }
    strong = set()
    for t in types:
        if t in type_chart:
            for target in type_chart[t]: strong.add(target)
    res = sorted(list(strong))
    if not res: return "various opponents"
    return ", ".join(res[:-1]) + " and " + res[-1] if len(res) > 1 else res[0]

def write_entry(prompt=None, response=None, context=None, mask_pre=None, mask_target=None, mask_post=None, text=None):
    if text:
        obj = {"text": text}
    else:
        obj = {"prompt": prompt, "response": response}
        if context:
            obj["context"] = context
        if mask_target is not None:
            obj["mask_pre"] = mask_pre
            obj["mask_target"] = str(mask_target)
            obj["mask_post"] = mask_post
    
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj) + "\n")

def generate_pokedex():
    if os.path.exists(OUTPUT_FILE): os.remove(OUTPUT_FILE)
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                p = parse_raw_pokemon(json.loads(line)['text'])
            except: continue
            if not p or p['name'] == "Unknown": continue
            
            eff = get_effectiveness(p['types_list'])
            ctx = build_shuffled_context(p, eff)
            mask_target_stats = f"HP {p['hp']}, Atk {p['atk']}, Def {p['def']}, SpA {p['sp_atk']}, SpD {p['sp_def']}, Spe {p['speed']}"

            # 1. Speed (Analyzed)
            s_desc = "blisteringly fast" if p['speed'] > 110 else "quite agile" if p['speed'] > 80 else "average" if p['speed'] > 50 else "decidedly sluggish"
            q1 = random.choice([f"Is {p['name']} fast enough to sweep?", f"Tell me about the mobility of {p['name']}."])
            r1 = f"When evaluating {p['name']}, you'll find it's {s_desc}. In a competitive environment, its base Speed of {p['speed']} determines whether it moves first in the turn order."
            write_entry(prompt=q1, response=universal_normalize(r1), context=ctx, 
                        mask_pre="Stats: ", mask_target=mask_target_stats, mask_post=" |")
            write_entry(text=universal_normalize(f"Speed Analysis for {p['name']}: Clocking in at {p['speed']}, this Pokemon is considered {s_desc} compared to the rest of the Pokedex."))

            # 2. Combat (Deep Context)
            q2 = f"How does {p['name']} perform in a physical confrontation?"
            r2 = f"In a physical trade, {p['name']} utilizes an Attack stat of {p['atk']} to deal damage, while relying on a Defense of {p['def']} to mitigate incoming physical blows. This ratio defines its role as a physical combatant."
            write_entry(prompt=q2, response=universal_normalize(r2), context=ctx,
                        mask_pre="Stats: ", mask_target=mask_target_stats, mask_post=" |")
            write_entry(text=universal_normalize(f"Combat Capability: {p['name']} maintains a {p['atk']}/{p['def']} Attack-to-Defense split for physical encounters."))

            # 3. Lore (The narrative hook)
            q3 = f"What is the biological or behavioral significance of {p['name']}?"
            r3 = f"Interestingly, {p['name']} is known for the following: {p['desc']}"
            write_entry(prompt=q3, response=universal_normalize(r3), context=ctx,
                        mask_pre="Lore: ", mask_target=p['desc'], mask_post=" |")
            write_entry(text=universal_normalize(f"Behavioral Profile: {p['name']} displays unique traits: {p['desc']}"))

            # 4. History (Regional Impact)
            q4 = f"Where did {p['name']} originate and how long has it been known?"
            r4 = f"{p['name']} is a staple of {p['gen']}, having first been discovered within the {p['region']} region. It has been part of the ecosystem since that era."
            write_entry(prompt=q4, response=universal_normalize(r4), context=ctx,
                        mask_pre="Origin: ", mask_target=f"{p['region']} ({p['gen']})", mask_post=" |")
            write_entry(text=universal_normalize(f"Historical Record: {p['name']} was categorized in {p['gen']} as a native of the {p['region']} region."))

            # 5. Number (The Registry)
            q5 = f"If I'm looking through the National Pokedex, where do I find {p['name']}?"
            r5 = f"You will find {p['name']} registered as entry number {p['number']}. This position in the National Pokedex helps researchers categorize its evolutionary line."
            write_entry(prompt=q5, response=universal_normalize(r5), context=ctx,
                        mask_pre="Pokedex: ", mask_target=p['number'], mask_post=" |")
            write_entry(text=universal_normalize(f"Registry Data: {p['name']} is officially recorded at position {p['number']}."))

            # 6. Matchup (Strategic)
            q6 = f"Which matchups are most favorable for {p['name']}?"
            r6 = f"Strategy-wise, {p['name']} is a {p['types_str']} type. This gives it a massive tactical advantage when facing {eff} Pokemon in battle."
            write_entry(prompt=q6, response=universal_normalize(r6), context=ctx,
                        mask_pre="Effective Against: ", mask_target=eff, mask_post=" |")
            write_entry(text=universal_normalize(f"Tactical Brief: Due to its {p['types_str']} typing, {p['name']} excels in matchups against {eff} types."))

            # 7. Bulk (Survivability Analysis)
            bulk_score = (p['hp'] + p['def'] + p['sp_def']) / 3
            survivability = "an absolute tank" if bulk_score > 90 else "sturdy enough to hold the line" if bulk_score > 65 else "a glass cannon that can't take much punishment"
            q7 = f"What is the survivability rating for {p['name']}?"
            r7 = f"Analyzing its defensive profile, {p['name']} is {survivability}. With {p['hp']} Hit Points and a base Defense of {p['def']}, it is built to survive specific types of offensive pressure."
            write_entry(prompt=q7, response=universal_normalize(r7), context=ctx,
                        mask_pre="Stats: ", mask_target=mask_target_stats, mask_post=" |")
            write_entry(text=universal_normalize(f"Survivability Assessment: {p['name']} is rated as {survivability} with a combined bulk average of {bulk_score:.1f}."))

if __name__ == "__main__":
    generate_pokedex()
