import json
import random
import time
import requests

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "convert.jsonl"
GENERATION_SLEEP = 0.1
ROW_ID_COUNTER = 0

# --- Unit Definitions ---
UNITS = {
    'volume': [('gal', 'gallons'), ('L', 'liters'), ('ml', 'milliliters'), ('cups', 'cups')],
    'mass': [('lb', 'pounds'), ('kg', 'kilograms'), ('oz', 'ounces'), ('g', 'grams')],
    'length': [('mi', 'miles'), ('km', 'kilometers'), ('ft', 'feet'), ('m', 'meters')],
    'temp': [('F', 'Fahrenheit'), ('C', 'Celsius')]
}

VERBS = ["Convert", "Translate", "Change", "Turn", "What is"]

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
        return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_convert_dataset(entries=1000):
    global ROW_ID_COUNTER
    print(f"Starting Explicit Unit Conversion Generation: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w") as f:
        for i in range(entries):
            # Select a random category and two distinct units
            category = random.choice(list(UNITS.keys()))
            u1_code, u1_name = random.choice(UNITS[category])
            
            # Ensure we don't convert to the same unit
            available_targets = [u for u in UNITS[category] if u[0] != u1_code]
            u2_code, u2_name = random.choice(available_targets)
            
            # Generate a random value
            if category == 'temp':
                value = round(random.uniform(-40.0, 110.0), 1)
            else:
                value = round(random.uniform(1.0, 500.0), 1)
            
            # Build the prompt
            verb = random.choice(VERBS)
            if verb == "What is":
                prompt = f"{verb} {value} {u1_code} in {u2_code}?"
            else:
                prompt = f"{verb} {value} {u1_code} to {u2_code}."

            params = {
                "value": value,
                "from_unit": u1_code,
                "to_unit": u2_code
            }

            # Call the conversion tool
            result_obj = call_tool("convert", params)
            
            if not result_obj:
                print(f"[!] Tool call failed for {value} {u1_code} to {u2_code}")
                continue

            # Unpack results for the response logic
            # Handling both nested and flat response structures from the server
            data_container = result_obj.get("result", result_obj)
            if isinstance(data_container, str):
                try:
                    data_container = json.loads(data_container)
                except:
                    pass
            
            # Determine success status and extract converted value
            is_success = data_container.get("status") == "success" if isinstance(data_container, dict) else False
            data = data_container.get("data", {}) if isinstance(data_container, dict) else {}
            converted_val = data.get("converted_value", "unknown")
            
            # Format display value for grounding
            if isinstance(converted_val, (int, float)):
                display_val = round(float(converted_val), 2)
            else:
                display_val = converted_val

            # Row 1: Tool Call
            f.write(json.dumps({
                "row_id": ROW_ID_COUNTER,
                "prompt": prompt,
                "thought": f"I need to convert {value} {u1_code} to {u2_code} using the convert tool.",
                "response": json.dumps({"tool": "convert", "parameters": params}),
                "type": "tool_call"
            }) + "\n")
            ROW_ID_COUNTER += 1

            # Row 2: Grounded Response
            # Logic branch: check if the tool actually succeeded
            if is_success:
                thought = f"The tool successfully converted {value} {u1_code} to {display_val} {u2_code}."
                response = f"{value} {u1_code} is equal to {display_val} {u2_code}."
            else:
                error_msg = data_container.get("message", "unknown error") if isinstance(data_container, dict) else "unknown error"
                thought = f"The tool failed to convert {value} {u1_code} to {u2_code}. Error: {error_msg}."
                response = f"I'm sorry, I couldn't convert {value} {u1_code} to {u2_code} because the tool returned an error."

            f.write(json.dumps({
                "row_id": ROW_ID_COUNTER,
                "prompt": prompt,
                "thought": thought,
                "context": data_container,
                "response": response,
                "type": "grounded_response"
            }) + "\n")
            ROW_ID_COUNTER += 1
            
            f.flush()
            time.sleep(GENERATION_SLEEP)

    print(f"Generation finished. Total rows created: {ROW_ID_COUNTER}")

if __name__ == "__main__":
    # Standard generation run
    generate_convert_dataset(1000)
