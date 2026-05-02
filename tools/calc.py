import json
import random
import time
import requests

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "calc.jsonl"
GENERATION_SLEEP = 0.1
ROW_ID_COUNTER = 0

# --- Natural Language Mappings ---
OP_MAP = {
    '+': 'plus',
    '-': 'minus',
    '*': 'times',
    '/': 'divided by',
    '**': 'to the power of',
    'sqrt': 'the square root of',
    'sin': 'the sine of',
    'cos': 'the cosine of',
    'tan': 'the tangent of',
    'radians': 'the radian conversion of',
    'degrees': 'the degree conversion of',
    'area_circle': 'the area of a circle with radius',
    'circumference': 'the circumference of a circle with radius',
    'area_rect': 'the area of a rectangle',
    'perimeter_rect': 'the perimeter of a rectangle'
}

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

def generate_calc_dataset(entries=50):
    global ROW_ID_COUNTER
    print(f"Starting Multi-Function Calculator Generation: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, "w") as f:
        for i in range(entries):
            # Weighted distribution including Geometry
            category = random.choices(['arithmetic', 'power', 'trig', 'geometry'], weights=[40, 20, 20, 20])[0]
            
            if category == 'arithmetic':
                # 80% Integers, 20% Floats for variety
                if random.random() > 0.2:
                    val1 = random.randint(1, 1000)
                    val2 = random.randint(1, 1000)
                else:
                    val1 = round(random.uniform(1.0, 500.0), 2)
                    val2 = round(random.uniform(1.0, 500.0), 2)
                
                op = random.choice(['+', '-', '*', '/'])
                
                # Prevent division by zero
                if op == '/' and val2 == 0:
                    val2 = 1
                    
                expression = f"{val1} {op} {val2}"
                prompt = f"What is {val1} {op} {val2}?"
                thought_desc = f"{val1} {OP_MAP[op]} {val2}"
            
            elif category == 'power':
                rand_type = random.random()
                if rand_type > 0.6:
                    # Squares and Cubes
                    val1 = random.randint(1, 100)
                    pwr = random.choice([2, 3])
                    expression = f"{val1} ** {pwr}"
                    suffix = "squared" if pwr == 2 else "cubed"
                    prompt = f"What is {val1} {suffix}?"
                    thought_desc = f"{val1} to the power of {pwr}"
                elif rand_type > 0.3:
                    # Square Roots (Mix of perfect and messy)
                    if random.random() > 0.4:
                        root = random.randint(2, 60)
                        val1 = root * root
                    else:
                        val1 = random.randint(2, 2000)
                    expression = f"sqrt({val1})"
                    prompt = f"What is the square root of {val1}?"
                    thought_desc = f"the square root of {val1}"
                else:
                    # Small base to higher power
                    val1 = random.randint(2, 10)
                    val2 = random.randint(4, 8)
                    expression = f"{val1} ** {val2}"
                    prompt = f"What is {val1} to the power of {val2}?"
                    thought_desc = f"{val1} to the power of {val2}"
            
            elif category == 'trig':
                func = random.choice(['sin', 'cos', 'tan'])
                angle = random.randint(0, 360)
                expression = f"{func}(radians({angle}))"
                prompt = f"What is the {func} of {angle} degrees?"
                thought_desc = f"{OP_MAP[func]} {angle} degrees"

            elif category == 'geometry':
                shape = random.choice(['circle', 'rectangle'])
                if shape == 'circle':
                    radius = random.randint(1, 100)
                    if random.random() > 0.5:
                        # Area = pi * r^2
                        expression = f"3.14159 * ({radius} ** 2)"
                        prompt = f"What is the area of a circle with a radius of {radius}?"
                        thought_desc = f"{OP_MAP['area_circle']} {radius}"
                    else:
                        # Circumference = 2 * pi * r
                        expression = f"2 * 3.14159 * {radius}"
                        prompt = f"What is the circumference of a circle with a radius of {radius}?"
                        thought_desc = f"{OP_MAP['circumference']} {radius}"
                else:
                    l = random.randint(1, 100)
                    w = random.randint(1, 100)
                    if random.random() > 0.5:
                        # Area = l * w
                        expression = f"{l} * {w}"
                        prompt = f"What is the area of a {l} by {w} rectangle?"
                        thought_desc = f"{OP_MAP['area_rect']} with dimensions {l} and {w}"
                    else:
                        # Perimeter = 2 * (l + w)
                        expression = f"2 * ({l} + {w})"
                        prompt = f"What is the perimeter of a {l} by {w} rectangle?"
                        thought_desc = f"{OP_MAP['perimeter_rect']} with dimensions {l} and {w}"

            params = {"expression": expression}
            raw_res = call_tool("calculator", params)
            
            if not raw_res:
                print(f"[!] Tool call failed for {expression}")
                continue

            # Unpack result
            result_obj = raw_res.get("result", raw_res)
            if isinstance(result_obj, str):
                try:
                    result_obj = json.loads(result_obj)
                except:
                    pass
            
            data = result_obj.get("data", {}) if isinstance(result_obj, dict) else {}
            calc_result = data.get("result", "unknown")
            
            # Format result for grounded response (rounding floats)
            if isinstance(calc_result, float):
                display_result = round(calc_result, 4)
            else:
                display_result = calc_result

            # Row 1: The Tool Call
            f.write(json.dumps({
                "row_id": ROW_ID_COUNTER,
                "prompt": prompt,
                "thought": f"The user wants to calculate {thought_desc}. I will use the calculator tool.",
                "response": json.dumps({"tool": "calculator", "parameters": params}),
                "type": "tool_call"
            }) + "\n")
            ROW_ID_COUNTER += 1

            # Row 2: The Grounded Response
            f.write(json.dumps({
                "row_id": ROW_ID_COUNTER,
                "prompt": prompt,
                "thought": f"The calculator returned {display_result} for {thought_desc}.",
                "context": result_obj,
                "response": f"The result for {prompt.replace('What is ', '').replace('?', '')} is {display_result}.",
                "type": "grounded_response"
            }) + "\n")
            ROW_ID_COUNTER += 1
            
            f.flush()
            time.sleep(GENERATION_SLEEP)

    print(f"Generation finished. Total rows created: {ROW_ID_COUNTER}")

if __name__ == "__main__":
    # Generate 1000 entries (2000 rows)
    generate_calc_dataset(1000)
