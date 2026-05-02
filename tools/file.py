import json
import random
import time
import requests

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "file.jsonl"
GENERATION_SLEEP = 0.2
ROW_ID_COUNTER = 0

# --- Expanded Lists and Generators ---

SAFE_COMMANDS = [
    "ls -la", "pwd", "id", "whoami", "uname -a", "df -h", "uptime", "date", "free -m",
    "cat /etc/hostname", "ls /tmp", "ps aux | head -n 10", "du -sh .", "groups",
    "ip addr show", "lsblk", "lscpu", "uptime -p", "tail -n 20 /var/log/syslog",
    "nvidia-smi", "grep 'error' /var/log/syslog", "top -n 1", "netstat -tulpn"
]

def get_random_path():
    prefixes = ["backup", "config", "data", "test", "model", "training", "results", "temp", "meta"]
    suffixes = ["01", "02", "v1", "v2", "final", "old", "new", "raw", "processed"]
    exts = [".json", ".csv", ".txt", ".sh", ".sql", ".log", ".py", ".md", ".yaml"]
    folder = random.choice(["/home/user/", "/tmp/", "./models/", "project_sprite/", ""])
    return f"{folder}{random.choice(prefixes)}_{random.choice(suffixes)}{random.choice(exts)}"

NOTE_TOPICS = [
    {"title": "Project Sprite", "content": "384 model optimization with Triton kernels."},
    {"title": "Tiny Home Floor", "content": "SPF 2x6 floor joists on 16 inch centers."},
    {"title": "Solar Calc", "content": "1200W total from four 300W panels."},
    {"title": "OSRS Sync", "content": "G2P model update for rare item drop names."},
    {"title": "Nymph Training", "content": "dataset on 512 model."},
    {"title": "Belize Land", "content": "Check property tax rates for Cayo District."},
    {"title": "Argentine Peso", "content": "Monitor exchange rate for blue dollar."},
    {"title": "Ultralight", "content": "Inspect Sunburst airframe for corrosion."},
    {"title": "Fire District", "content": "Prepare Tier 2 professional services proposal."},
    {"title": "LLM Optimization", "content": "Test llama.cpp with 4-bit quantization."},
    {"title": "Pokemon Energy", "content": "Lugia requires psychic and colorless energy."},
    {"title": "SSDI Schedule", "content": "Payment arrives on the third Wednesday."}
]

TEMPLATE_REGISTRY = {
    "run_command": {
        "thought": "The user needs to execute a system level check or administrative task using '{command}'. I will use run_command to interface with the shell.",
        "prompts": [
            "Run the command {command}", 
            "Execute `{command}`", 
            "What is the output of {command}?", 
            "Check the system status with {command}",
            "I need to see the result of `{command}` in the terminal."
        ],
        "responses": [
            "Command output for {command}:\n{stdout}", 
            "The execution of {command} returned the following:\n{stdout}",
            "Terminal output for `{command}`:\n{stdout}"
        ],
        "params": lambda: {"command": random.choice(SAFE_COMMANDS)}
    },
    "notes": {
        "thought": "The user is requesting to {action} a note regarding '{title_or_query}'. Using the IDG-Suite notes dispatcher.",
        "prompts": {
            "save": [
                "Save a note titled '{title}' saying: {content}", 
                "Note down '{content}' as '{title}'", 
                "Remember '{content}' for me under the title '{title}'",
                "Log a new note for '{title}': {content}"
            ],
            "get": [
                "Retrieve the note about {query}", 
                "Find my '{query}' note", 
                "What does my note on {query} say?", 
                "Look up the content for the '{query}' entry."
            ],
            "delete": [
                "Delete the note titled '{title}'",
                "Remove my '{title}' note from the system.",
                "Wipe the entry for '{title}' from my notes."
            ]
        },
        "responses": {
            "save": ["Note '{title}' has been saved successfully.", "I've stored your note titled '{title}'."],
            "get": ["I found your note for '{query}': {result_content}", "Here is the content of the '{query}' note: {result_content}"],
            "delete": ["Note '{title}' has been removed.", "Successfully deleted the '{title}' note."]
        },
        "params": lambda: random.choice([
            {"action": "save", **random.choice(NOTE_TOPICS)},
            {"action": "get", "query": random.choice(NOTE_TOPICS)["title"]},
            {"action": "delete", "title": random.choice(NOTE_TOPICS)["title"]}
        ])
    },
    "file_manager": {
        "thought": "The user wants to {action} a file located at '{file_path}'. I will dispatch this to the file_manager tool.",
        "prompts": {
            "read": ["Read the file {file_path}", "What's in {file_path}?", "Open {file_path}", "Print the content of {file_path}"],
            "write": ["Write '{content}' to {file_path}", "Create a file at {file_path} with the text: {content}", "Save this data to {file_path}: {content}"],
            "list": ["List the directory contents at {file_path}", "What files are in {file_path}?", "ls {file_path}"],
            "delete": ["Delete {file_path}", "Remove the file {file_path}", "Get rid of {file_path}", "Wipe {file_path} from disk"]
        },
        "responses": {
            "read": ["Content of {file_path}: {content}", "Here is the data from {file_path}: {content}"],
            "write": ["Successfully wrote to {file_path}.", "The file at {file_path} has been updated."],
            "list": ["Directory listing for {file_path}: {content}", "Files found in {file_path}: {content}"],
            "delete": ["File {file_path} has been deleted.", "Successfully removed {file_path}."]
        },
        "params": lambda: {
            "action": random.choice(["read", "write", "list", "delete"]),
            "file_path": get_random_path(),
            "content": "Training data for custom Nymph model fine-tuning."
        }
    }
}

# --- Core Functions ---

def call_tool(tool_name, payload):
    """Hits the tool server and handles fallback mocks for generation stability."""
    try:
        response = requests.post(f"{TOOL_SERVER_URL}/tool/{tool_name}", json=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Fallback simulation if server is unreachable
    if tool_name == "run_command": 
        return {"status": "success", "data": {"stdout": f"Standard output for {payload.get('command')}", "stderr": "", "return_code": 0}}
    if tool_name == "file_manager": 
        return {"status": "success", "data": {"content": "Sample system data.", "file_path": payload.get("file_path")}}
    if tool_name == "notes": 
        return {"status": "success", "data": {"note": {"title": payload.get("title", "Mock"), "content": "Persistent data."}}}
    return None

def normalize_result(result):
    """Recursively parses and flattens tool results to handle inconsistent nesting."""
    if isinstance(result, str):
        try:
            return normalize_result(json.loads(result))
        except:
            return {"message": result}
    
    # If the tool response is wrapped in a 'result' or 'data' key, unpack it
    if isinstance(result, dict):
        if "result" in result:
            return normalize_result(result["result"])
        if "data" in result and isinstance(result["data"], (dict, str)):
            # Check if status exists at this level, then merge
            base = {k: v for k, v in result.items() if k != "data"}
            data_part = normalize_result(result["data"])
            if isinstance(data_part, dict):
                base.update(data_part)
            else:
                base["content"] = data_part
            return base
            
    return result

def write_to_file(file_handle, tool_name):
    global ROW_ID_COUNTER
    config = TEMPLATE_REGISTRY[tool_name]
    params = config["params"]()
    
    action = params.get("action", "")
    title_or_query = params.get("title", params.get("query", ""))
    file_path = params.get("file_path", "")
    command = params.get("command", "")
    
    if tool_name == "notes":
        prompt_text = random.choice(config["prompts"][action]).format(**params)
        thought_text = config["thought"].format(action=action, title_or_query=title_or_query)
    elif tool_name == "file_manager":
        prompt_text = random.choice(config["prompts"][action]).format(**params)
        thought_text = config["thought"].format(action=action, file_path=file_path)
    else:
        prompt_text = random.choice(config["prompts"]).format(**params)
        thought_text = config["thought"].format(command=command)

    # Write the Tool Call Row
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": thought_text,
        "response": json.dumps({"tool": tool_name, "parameters": params}),
        "type": "tool_call"
    }) + "\n")
    ROW_ID_COUNTER += 1

    # Fetch and Normalize Response
    raw_result = call_tool(tool_name, params)
    if not raw_result:
        raw_result = {"status": "error", "message": "The system encountered an issue communicating with the tool."}
    
    norm = normalize_result(raw_result)
    status = norm.get("status", "success")
    
    # Logic to catch errors even if status isn't explicitly 'error'
    if status == "error" or "error" in str(norm).lower():
        status = "error"

    format_data = {**params}
    
    if status == "error":
        error_msg = norm.get("message", norm.get("error", "The system encountered an issue."))
        response_text = f"I'm sorry, I couldn't complete that. {error_msg}"
    else:
        if tool_name == "run_command":
            stdout = str(norm.get("stdout", "")).strip()
            stderr = str(norm.get("stderr", "")).strip()
            format_data["stdout"] = stdout if stdout else (f"Error: {stderr}" if stderr else "No output.")

        elif tool_name == "file_manager":
            if action in ["read", "list"]:
                format_data["content"] = norm.get("content", norm.get("message", "No content found."))
            else:
                format_data["content"] = norm.get("message", "Action successful.")

        elif tool_name == "notes":
            # Some notes tools return an object, some return flat content
            note_content = norm.get("content")
            if not note_content and "note" in norm and isinstance(norm["note"], dict):
                note_content = norm["note"].get("content")
            format_data["result_content"] = note_content if note_content else "No data available."

        resp_template = config["responses"][action] if isinstance(config["responses"], dict) else config["responses"]
        response_text = random.choice(resp_template).format(**format_data)

    # Write the Grounded Response Row
    file_handle.write(json.dumps({
        "row_id": ROW_ID_COUNTER,
        "prompt": prompt_text,
        "thought": f"The tool returned a {status} result. Formulating terminal response.",
        "context": raw_result,
        "response": response_text,
        "type": "grounded_response"
    }) + "\n")
    ROW_ID_COUNTER += 1
    file_handle.flush()

def generate_dataset(per_tool=50):
    print(f"Generating dataset... Output: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w") as f:
        for tool in TEMPLATE_REGISTRY:
            print(f"Generating rows for {tool}...")
            for _ in range(per_tool):
                write_to_file(f, tool)
                time.sleep(GENERATION_SLEEP)
    print(f"Generation complete. Total rows: {ROW_ID_COUNTER}")

if __name__ == "__main__":
    generate_dataset(150)
