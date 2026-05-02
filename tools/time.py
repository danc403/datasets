import json
import random
import time
import requests
from datetime import datetime

# --- 1. CONFIGURATION ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "time.jsonl"
GENERATION_SLEEP = 0.1

# --- 2. DATASETS & TEMPLATES (THE MENTAL MAP) ---
CITIES_LIST = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Seattle, WA", "Miami, Florida", "Denver, Colorado", "London",
    "Tokyo", "Paris", "Berlin", "Sydney", "Mexico City", "Cairo"
]

# Chained Logic: City -> Geo -> Time
TEMPLATE_TIME_CHAIN = {
    "thought_geo": "The user wants the time in {city}. I will resolve the timezone first.",
    "thought_time": "Timezone for {city} found. Now fetching the time.",
    "thought_final": "I have the localized time for the user.",
    "prompts": [
        "What time is it in {city}?",
        "Tell me the current time for {city}.",
        "What's the clock saying in {city} right now?",
        "Is it late in {city}?"
    ],
    "responses": [
        "It is currently {val} in {city}.",
        "The clock in {city} says {val}.",
        "In {city}, it's {val}."
    ]
}

# Direct Logic: System Tool Call
DIRECT_TEMPLATES = {
    "time": {
        "prompts": ["What time is it?", "Current time?", "Clock check."],
        "thought": "Checking system time via time_utils.",
        "resp": "The current time is {val}."
    },
    "date": {
        "prompts": ["What is today's date?", "What's the date?", "Give me the date."],
        "thought": "Checking system date via time_utils.",
        "resp": "Today is {val}."
    },
    "day": {
        "prompts": ["What day of the week is it?", "What day is it?"],
        "thought": "Checking current day name via time_utils.",
        "resp": "Today is {val}."
    },
    "year": {
        "prompts": ["What year is it?", "Current year?"],
        "thought": "Checking the current year via time_utils.",
        "resp": "The year is {val}."
    }
}

# --- 3. UTILITIES ---
ROW_ID_COUNTER = 0

def format_time_string(raw_time, mode="time"):
    """Robust ISO parsing that prevents ValueError on malformed offsets."""
    if not raw_time or "T" not in raw_time: 
        return raw_time
    
    try:
        # Split at '+' or 'Z' to isolate the main timestamp
        clean_time = raw_time.split('+')[0].split('Z')[0]
        
        # Handle trailing dash offsets (e.g., 2026-05-01T12:00:00-05:00)
        # We only look for the dash after the date part (index 10)
        if '-' in clean_time[10:]:
            # Find the dash specifically in the time segment
            dash_index = clean_time.find('-', 10)
            clean_time = clean_time[:dash_index]
            
        dt = datetime.fromisoformat(clean_time)
        
        if mode == "date": return dt.strftime("%Y-%m-%d")
        if mode == "year": return str(dt.year)
        if mode == "day": return dt.strftime("%A")
        return dt.strftime("%H:%M on %Y-%m-%d")
    except Exception:
        # If parsing fails, return as much of the string as possible safely
        return raw_time

def call_tool(tool_name, payload):
    try:
        response = requests.post(f"{TOOL_SERVER_URL}/tool/{tool_name}", json=payload, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def extract_clean_data(raw_res):
    if not raw_res: return {}
    res = raw_res.get("result", raw_res)
    if isinstance(res, str):
        try: res = json.loads(res)
        except: return {}
    return res.get("data", res)

# --- 4. EXECUTION LOGIC ---

def write_chained_time(f, city):
    global ROW_ID_COUNTER
    loc_raw = call_tool("geo", {"query": city})
    loc_clean = extract_clean_data(loc_raw)
    if not loc_clean or "timezone" not in loc_clean: return False

    tz = loc_clean["timezone"]
    time_raw = call_tool("time_utils", {"action": "get_time", "timezone": tz})
    time_clean = extract_clean_data(time_raw)
    if not time_clean: return False

    prompt = random.choice(TEMPLATE_TIME_CHAIN["prompts"]).format(city=city)
    val = format_time_string(time_clean.get("current_time", "unknown"))

    # Turn 1: Geo
    f.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt, "thought": TEMPLATE_TIME_CHAIN["thought_geo"].format(city=city), "response": json.dumps({"tool": "geo", "parameters": {"query": city}}), "type": "tool_call"}) + "\n")
    ROW_ID_COUNTER += 1

    # Turn 2: Time
    f.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt, "thought": TEMPLATE_TIME_CHAIN["thought_time"].format(city=city), "context": loc_raw.get("result", loc_raw), "response": json.dumps({"tool": "time_utils", "parameters": {"action": "get_time", "timezone": tz}}), "type": "tool_call"}) + "\n")
    ROW_ID_COUNTER += 1

    # Turn 3: Grounded
    resp = random.choice(TEMPLATE_TIME_CHAIN["responses"]).format(city=city, val=val)
    f.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt, "thought": TEMPLATE_TIME_CHAIN["thought_final"], "context": time_raw.get("result", time_raw), "response": resp, "type": "grounded_response"}) + "\n")
    ROW_ID_COUNTER += 1
    return True

def write_direct_time(f, mode):
    global ROW_ID_COUNTER
    time_raw = call_tool("time_utils", {"action": "get_time", "timezone": "UTC"})
    time_clean = extract_clean_data(time_raw)
    if not time_clean: return False

    tmplt = DIRECT_TEMPLATES[mode]
    prompt = random.choice(tmplt["prompts"])
    val = format_time_string(time_clean.get("current_time", "unknown"), mode=mode)

    f.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt, "thought": tmplt["thought"], "response": json.dumps({"tool": "time_utils", "parameters": {"action": "get_time", "timezone": "UTC"}}), "type": "tool_call"}) + "\n")
    ROW_ID_COUNTER += 1

    f.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt, "thought": "System time retrieved.", "context": time_raw.get("result", time_raw), "response": tmplt["resp"].format(val=val), "type": "grounded_response"}) + "\n")
    ROW_ID_COUNTER += 1
    return True

def generate_dataset(entries_per_mode=5):
    """
    Standardized entry point to control the volume of synthetic data.
    Generates a balanced mix of chained geographic time and direct system time.
    """
    print(f"Starting temporal data generation. Output: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w") as f:
        # 1. Generate Chained Time Entries (City -> Geo -> Time)
        print("Processing: Chained Time (City-based)")
        for city in CITIES_LIST:
            for _ in range(entries_per_mode):
                if write_chained_time(f, city):
                    print(f"  [Chained] Success: {city}")
                time.sleep(GENERATION_SLEEP)
        
        # 2. Generate Direct Time Entries (System UTC)
        print("Processing: Direct Time (System-based)")
        for mode in DIRECT_TEMPLATES.keys():
            for _ in range(entries_per_mode):
                if write_direct_time(f, mode):
                    print(f"  [Direct] Success: {mode}")
                time.sleep(GENERATION_SLEEP)
        
        f.flush()
    print(f"Generation complete. File saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    # entries_per_mode=2 results in (20 cities * 2) + (4 direct modes * 2) = 48 entries.
    generate_dataset(entries_per_mode=2)
