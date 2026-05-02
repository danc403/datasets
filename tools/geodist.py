import json
import random
import time
import requests

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "geodist.jsonl"
GENERATION_SLEEP = 0.2
ROW_ID_COUNTER = 0

CITIES_LIST = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Seattle, WA", "Miami, Florida", "Denver, Colorado", "Boston, MA", 
    "Nashville, Tennessee", "Atlanta, Georgia", "Portland, Oregon", 
    "Las Vegas, NV", "Detroit, Michigan", "New Orleans, LA",
    "Chicago, IL 60606",
    "Anaheim, CA",
    "Grand Canyon",
    "Golden Gate Bridge",
    "Statue of Liberty"
]

# --- Templates ---

TEMPLATE_LOCATION = {
    "thought": "The user is asking for geographical information for {query}. I will call geo to retrieve the coordinates.",
    "prompts": [
        "Where is {query}?",
        "Provide location details for {query}.",
        "Can you find the coordinates for {query}?"
    ],
    "responses": [
        "{query} is located at: (Lat: {latitude}, Lon: {longitude}).",
        "The location for {query} is {city} (Lat: {latitude}, Lon: {longitude})."
    ]
}

TEMPLATE_DISTANCE = {
    "thought": "To find the distance between {location_one_name} and {location_two_name}, I need to resolve the coordinates for both and then calculate the mileage.",
    "chain_of_thought": [
        "I will first resolve the coordinates for {location_one_name} using geo.",
        "Now that I have the first point, I will resolve the coordinates for {location_two_name} using geo.",
        "With both sets of coordinates (Loc1: {l1_lat}, {l1_lon} and Loc2: {l2_lat}, {l2_lon}), I will calculate the distance."
    ],
    "prompts": [
        "How far is it from {location_one_name} to {location_two_name}?",
        "What is the distance between {location_one_name} and {location_two_name}?",
        "Calculate the mileage from {location_one_name} to {location_two_name}."
    ],
    "responses": [
        "The distance is approximately {distance_miles} miles.",
        "It is {distance_miles} miles from {location_one_name} to {location_two_name}."
    ]
}

# --- Core Functions ---

def call_tool(tool_name, payload):
    try:
        response = requests.post(f"{TOOL_SERVER_URL}/tool/{tool_name}", json=payload, timeout=10)
        if response.status_code == 200:
            res = response.json()
            if isinstance(res, str):
                try:
                    return json.loads(res)
                except:
                    return {"result": res}
            return res
        return None
    except Exception:
        return None

def extract_clean_data(raw_res):
    if not raw_res:
        return {}
    result_content = raw_res.get("result", raw_res)
    if isinstance(result_content, str):
        try:
            result_content = json.loads(result_content)
        except:
            return {}
    
    if isinstance(result_content, dict):
        if result_content.get("status") == "error":
            return {}
        if "data" in result_content:
            return result_content["data"]
    return result_content

def get_chained_data():
    """Fetches coordinates for two cities and calculates distance."""
    loc1_name, loc2_name = random.sample(CITIES_LIST, 2)
    
    # Step 1: Geo for Loc 1
    loc1_raw = call_tool("geo", {"query": loc1_name})
    l1_clean = extract_clean_data(loc1_raw)
    if not l1_clean:
        return None

    # Step 2: Geo for Loc 2
    loc2_raw = call_tool("geo", {"query": loc2_name})
    l2_clean = extract_clean_data(loc2_raw)
    if not l2_clean:
        return None
    
    # Step 3: Distance calculation
    dist_payload = {"location1": l1_clean, "location2": l2_clean}
    dist_raw = call_tool("distance", dist_payload)
    dist_data = extract_clean_data(dist_raw)
    if not dist_data:
        return None
        
    return {
        "location_one_name": loc1_name,
        "location1": l1_clean,
        "l1_lat": round(l1_clean.get("latitude", 0), 4),
        "l1_lon": round(l1_clean.get("longitude", 0), 4),
        "raw_loc1_res": loc1_raw,
        "location_two_name": loc2_name,
        "location2": l2_clean,
        "l2_lat": round(l2_clean.get("latitude", 0), 4),
        "l2_lon": round(l2_clean.get("longitude", 0), 4),
        "raw_loc2_res": loc2_raw,
        "distance_miles": round(dist_data.get("distance_miles", 0), 2),
        "raw_dist_res": dist_raw
    }

def write_geo_row(file_handle):
    global ROW_ID_COUNTER
    query = random.choice(CITIES_LIST)
    raw_res = call_tool("geo", {"query": query})
    data = extract_clean_data(raw_res)
    
    if not data:
        return

    prompt = random.choice(TEMPLATE_LOCATION["prompts"]).format(query=query)
    format_data = {
        "query": query,
        "city": data.get("city", "unknown"),
        "latitude": round(data.get("latitude", 0), 4),
        "longitude": round(data.get("longitude", 0), 4)
    }

    # Tool Call
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt,
        "thought": TEMPLATE_LOCATION["thought"].format(query=query),
        "response": json.dumps({"tool": "geo", "parameters": {"query": query}}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Grounded Response
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt,
        "thought": f"The tool returned coordinates (Lat: {format_data['latitude']}, Lon: {format_data['longitude']}) for {query}.",
        "context": raw_res,
        "response": random.choice(TEMPLATE_LOCATION["responses"]).format(**format_data),
        "type": "grounded_response"
    }) + "\n")
    ROW_ID_COUNTER += 1

def write_chained_distance_row(file_handle):
    global ROW_ID_COUNTER
    data = get_chained_data()
    if not data:
        return

    prompt_text = random.choice(TEMPLATE_DISTANCE["prompts"]).format(**data)
    
    def get_ctx(raw):
        res = raw.get("result", raw)
        return json.loads(res) if isinstance(res, str) else res

    # Turn 1: Geo 1
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": TEMPLATE_DISTANCE["chain_of_thought"][0].format(**data),
        "response": json.dumps({"tool": "geo", "parameters": {"query": data["location_one_name"]}}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Turn 2: Geo 2
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": TEMPLATE_DISTANCE["chain_of_thought"][1].format(**data),
        "context": get_ctx(data["raw_loc1_res"]),
        "response": json.dumps({"tool": "geo", "parameters": {"query": data["location_two_name"]}}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Turn 3: Distance
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": TEMPLATE_DISTANCE["chain_of_thought"][2].format(**data),
        "context": get_ctx(data["raw_loc2_res"]),
        "response": json.dumps({"tool": "distance", "parameters": {"location1": data["location1"], "location2": data["location2"]}}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Turn 4: Final Response
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": f"The tool calculated the distance between the two points as {data['distance_miles']} miles.",
        "context": get_ctx(data["raw_dist_res"]),
        "response": random.choice(TEMPLATE_DISTANCE["responses"]).format(**data),
        "type": "grounded_response"
    }) + "\n")
    ROW_ID_COUNTER += 1

def generate_dataset(geo_count=5, dist_count=5):
    print(f"Starting GeoDist Generation. Output: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w") as f:
        print("Generating Geo rows...")
        for _ in range(geo_count):
            write_geo_row(f)
            time.sleep(GENERATION_SLEEP)
        
        print("Generating Chained Distance rows...")
        for _ in range(dist_count):
            write_chained_distance_row(f)
            time.sleep(GENERATION_SLEEP)
            
    print(f"Finished. Total rows: {ROW_ID_COUNTER}")

if __name__ == "__main__":
    generate_dataset(200, 150)
