import json
import random
import time
import requests

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "weather.jsonl"
GENERATION_SLEEP = 1.2
ROW_ID_COUNTER = 0

CITIES_LIST = [
    # --- Original / US Major ---
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Seattle, WA", "Miami, Florida", "Denver, Colorado", "Boston, MA", 
    "Nashville, Tennessee", "Atlanta, Georgia", "Portland, Oregon", 
    "Las Vegas, NV", "Detroit, Michigan", "New Orleans, LA",
    "Chicago, IL 60606", "Anaheim, CA",
    
    # --- US Cold / Specific Climates ---
    "Anchorage, Alaska", "Fairbanks, AK", "Minneapolis, MN", 
    "Buffalo, NY", "Fargo, North Dakota", "Duluth, MN",
    
    # --- Europe ---
    "London, UK", "Paris, France", "Berlin, Germany", "Oslo, Norway", 
    "Reykjavik, Iceland", "Moscow, Russia", "Rome, Italy", "Madrid, Spain",
    "Stockholm, Sweden", "Helsinki, Finland",
    
    # --- Asia / Middle East ---
    "Tokyo, Japan", "Seoul, South Korea", "Beijing, China", "Bangkok, Thailand",
    "Mumbai, India", "Dubai, UAE", "Singapore", "Astana, Kazakhstan",
    "Sapporo, Japan", "Ulaanbaatar, Mongolia",
    
    # --- Southern Hemisphere ---
    "Sydney, Australia", "Melbourne, AU", "Auckland, New Zealand", 
    "Cape Town, South Africa", "Johannesburg, SA", "Buenos Aires, Argentina", 
    "Santiago, Chile", "Sao Paulo, Brazil", "Perth, Australia", "Hobart, Tasmania",
    
    # --- Landmarks (Weather usually maps to nearest station) ---
    "Grand Canyon", "Golden Gate Bridge", "Statue of Liberty", 
    "Mount Everest", "Mount Rainier", "Yellowstone National Park"
]

# --- Templates ---

TEMPLATE_WEATHER = {
    "thought": "I will retrieve the current weather conditions for {location} using the weather tool.",
    "prompts": [
        "Weather in {location}?", 
        "What is the weather in {location}?", 
        "Tell me the current conditions for {location}."
    ],
    "responses": [
        "It's {temp_F} degrees F and {weather_description} in {location}.",
        "The current weather in {location} is {weather_description} with a temperature of {temp_F} degrees F."
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

def write_to_file(file_handle, location):
    global ROW_ID_COUNTER
    
    # Step 1: Tool Call Turn
    params = {"location": location}
    prompt_text = random.choice(TEMPLATE_WEATHER["prompts"]).format(location=location)
    thought_text = TEMPLATE_WEATHER["thought"].format(location=location)
    
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": thought_text,
        "response": json.dumps({"tool": "weather", "parameters": params}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Step 2: Fetch data for the Grounded Response
    api_result = call_tool("weather", params)
    if not api_result:
        return

    # Handle the specific nested structure of the weather tool output
    result_value = api_result.get("result", api_result)
    if isinstance(result_value, str):
        try:
            result_value = json.loads(result_value)
        except:
            return

    data = result_value.get("data", result_value)
    
    # Extract condition details
    format_data = {"location": location}
    if isinstance(data, dict) and "current_condition" in data:
        condition = data["current_condition"][0]
        format_data["temp_F"] = condition.get("temp_F", "unknown")
        format_data["weather_description"] = condition.get("weatherDesc", [{}])[0].get("value", "unknown").lower()
    else:
        return

    # Final Turn: Grounded Response
    grounded_thought = f"The tool returned a temperature of {format_data['temp_F']} F and {format_data['weather_description']} for {location}."
    response_text = random.choice(TEMPLATE_WEATHER["responses"]).format(**format_data)

    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": grounded_thought,
        "context": result_value, 
        "response": response_text,
        "type": "grounded_response"
    }) + "\n")
    ROW_ID_COUNTER += 1

def generate_dataset(count=50):
    print(f"Starting Weather Generation. Output: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w") as f:
        for _ in range(count):
            loc = random.choice(CITIES_LIST)
            write_to_file(f, loc)
            time.sleep(GENERATION_SLEEP)
            f.flush()
    print(f"Finished. Total rows: {ROW_ID_COUNTER}")

if __name__ == "__main__":
    # Generating 500 interactions (1000 rows total)
    generate_dataset(250)
