import json
import random
import time
import requests
import re
import unicodedata
import sys

# --- Configuration ---
TOOL_SERVER_URL = "http://localhost:8080"
OUTPUT_FILE = "web.jsonl"
GENERATION_SLEEP = 1.5
ROW_ID_COUNTER = 0

SEARCH_QUERIES = [
    "latest space news", "sourdough bread guide", "nvidia stock price",
    "local llm 24gb vram", "python 3.12 debian", "2025 sci-fi books",
    "leaking faucet fix", "qwen 2.5 vs llama 4", "threadripper ai training",
    "step deck trailer load security", "rocket launches may 2026",
    "PID controller tuning", "solar battery maintenance", "rust vs c++",
    "step deck air bag replacement", "raspberry pi 5 clusters",
    "homelab server rack layout", "zfs pool optimization", "proxmox gpu passthrough",
    "solar panel wiring diagrams", "off grid water filtration", "tiny home loft framing",
    "lithium iron phosphate vs lead acid", "victron multiplus configuration",
    "starlink mini power draw", "local llama.cpp benchmarking", "triton kernels guide",
    "pytorch vs jax performance", "fine tuning models on consumer gpu",
    "quantization methods awq vs gptq", "best thermal paste for servers",
    "liquid cooling vs air cooling servers", "cat6a vs cat7 cabling",
    "managed vs unmanaged network switches", "wireguard vpn setup guide",
    "docker compose vs kubernetes for home use", "self hosting bitwarden",
    "nextcloud vs truenas scale", "high availability cluster guide",
    "balancing load on tandem axles", "DOT regulations for wide loads",
    "history of the pleasant hope fire district", "public safety radio frequencies",
    "emergency vehicle maintenance logs", "fire truck pump pressure charts"
]

WEB_PAGE_URLS = [
    "https://www.fsf.org/about/", "https://www.debian.org/releases/bookworm/",
    "https://docs.docker.com/get-started/", "https://system76.com/pop/",
    "https://alpinelinux.org/about", "https://eclectacy.org",
    "https://kyler.idragonfly.net", "https://idragonfly.net",
    "https://www.rfc-editor.org/rfc/rfc1918",
    "https://www.gutenberg.org/ebooks/1342",
    "https://www.gutenberg.org/ebooks/164",
    "https://www.gutenberg.org/ebooks/18857",
    "https://www.nasa.gov/news-release/",
    "https://www.gnu.org/philosophy/free-sw.html",
    "https://www.arduino.cc/en/Guide/Introduction",
    "https://www.raspberrypi.com/documentation/",
    "https://www.mozilla.org/en-US/about/manifesto/",
    "https://www.apache.org/foundation/how-it-works.html",
    "https://www.sqlite.org/about.html",
    "https://www.rust-lang.org/about",
    "https://www.postgresql.org/about/",
    "https://www.victronenergy.com/information/about-us"
]

TEMPLATE_SEARCH = {
    "thought": [
        "The user wants to know about '{query}'. I will perform a web search.",
        "I need to look up details regarding '{query}'. Performing a web search now.",
        "To address the query about '{query}', I will use the web_search tool.",
        "The request concerns '{query}'. I'll search the web to find the latest updates."
    ],
    "prompts": [
        "Search for {query}", "Find information about {query}", "What can you tell me about {query}?",
        "Look up {query} for me.", "Can you find the latest on {query}?", "I need details on {query}."
    ]
}

TEMPLATE_DIRECT_PAGE = {
    "thought": [
        "The user provided the URL {url}. I will fetch the content directly.",
        "I will access {url} directly to extract the information requested.",
        "Directly reading {url} now to gather context.",
        "The user is asking about a specific site: {url}. I will fetch its content."
    ],
    "prompts": [
        "What does the page at {url} say?", "Extract content from {url}", 
        "Summarize the information found at {url}", "Read the website {url}",
        "Give me a breakdown of {url}", "What is the main information on {url}?"
    ],
    "responses": [
        "The content of the page at {url} is as follows: {snippet}",
        "Based on the website {url}, here is what I found: {snippet}",
        "I retrieved the following information from {url}: {snippet}",
        "According to the documentation at {url}, {snippet}",
        "The site at {url} provides these details: {snippet}",
        "Here is the summary of the content found at {url}: {snippet}"
    ]
}

def normalize_text(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    clean = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', ascii_text)
    return clean

def clean_content(text):
    if not text: return ""
    text = normalize_text(text)
    result = re.sub(r'\s+', ' ', text).strip()
    return result

def call_tool(tool_name, payload):
    try:
        response = requests.post(f"{TOOL_SERVER_URL}/tool/{tool_name}", json=payload, timeout=30)
        if response.status_code == 200:
            outer_data = response.json()
            result_obj = outer_data.get("result", "")
            
            # CASE 1: Result is stringified JSON (happens on web_page)
            if isinstance(result_obj, str):
                try:
                    return json.loads(result_obj)
                except json.JSONDecodeError:
                    print(f"[!] Error: 'result' string was not valid JSON.")
                    return None
            
            # CASE 2: Result is already a dictionary (happens on web_search)
            elif isinstance(result_obj, dict):
                return result_obj
                
            return None
        print(f"[!] HTTP Error {response.status_code}")
        return None
    except Exception as e:
        print(f"[!] Exception: {str(e)}")
        return None

def write_direct_page(file_handle, url):
    global ROW_ID_COUNTER
    print(f"[*] Processing URL: {url}")
    inner_res = call_tool("web_page", {"url": url})
    
    if not inner_res or inner_res.get("status") != "success":
        print(f"[-] Skip: Status failure for {url}")
        return

    data_obj = inner_res.get("data", {})
    raw_text = clean_content(data_obj.get("plain_text_content", ""))
    
    if not raw_text:
        print(f"[-] Skip: Content empty for {url}")
        return

    snippet = raw_text[:700].replace("\"", "'").strip() + "..."
    thought_text = random.choice(TEMPLATE_DIRECT_PAGE["thought"]).format(url=url)
    prompt_text = random.choice(TEMPLATE_DIRECT_PAGE["prompts"]).format(url=url)

    file_handle.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt_text, "thought": thought_text, "response": json.dumps({"tool": "web_page", "parameters": {"url": url}}), "type": "tool_call"}, ensure_ascii=False) + "\n")
    ROW_ID_COUNTER += 1

    response_text = random.choice(TEMPLATE_DIRECT_PAGE["responses"]).format(url=url, snippet=snippet)
    file_handle.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt_text, "thought": f"Retrieved page for {url}.", "context": inner_res, "response": response_text, "type": "grounded_response"}, ensure_ascii=False) + "\n")
    ROW_ID_COUNTER += 1
    file_handle.flush()
    print(f"[+] Success: Logged {url}")

def write_chained_web(file_handle, query):
    global ROW_ID_COUNTER
    print(f"[*] Searching: {query}")
    inner_search = call_tool("web_search", {"query": query})
    
    if not inner_search or inner_search.get("status") != "success":
        print(f"[-] Skip: Search failed for {query}")
        return

    results = inner_search.get("data", {}).get("results", [])
    if not results:
        print(f"[-] Skip: No search results for {query}")
        return
        
    target_url = results[0]["url"]
    print(f"[*] Chaining -> {target_url}")
    
    inner_page = call_tool("web_page", {"url": target_url})
    if not inner_page or inner_page.get("status") != "success":
        print(f"[-] Skip: Chained page fetch failed.")
        return

    thought_text = random.choice(TEMPLATE_SEARCH["thought"]).format(query=query)
    prompt_text = random.choice(TEMPLATE_SEARCH["prompts"]).format(query=query)

    file_handle.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt_text, "thought": thought_text, "response": json.dumps({"tool": "web_search", "parameters": {"query": query}}), "type": "tool_call"}, ensure_ascii=False) + "\n")
    ROW_ID_COUNTER += 1

    file_handle.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt_text, "thought": f"Accessing {target_url}.", "context": inner_search, "response": json.dumps({"tool": "web_page", "parameters": {"url": target_url}}), "type": "tool_call"}, ensure_ascii=False) + "\n")
    ROW_ID_COUNTER += 1

    data_obj = inner_page.get("data", {})
    raw_text = clean_content(data_obj.get("plain_text_content", ""))
    snippet = raw_text[:700].replace("\"", "'").strip() + "..."

    file_handle.write(json.dumps({"row_id": ROW_ID_COUNTER, "prompt": prompt_text, "thought": f"Final summary for {query}.", "context": inner_page, "response": f"According to {target_url}: {snippet}", "type": "grounded_response"}, ensure_ascii=False) + "\n")
    ROW_ID_COUNTER += 1
    file_handle.flush()
    print(f"[+] Success: Search query '{query}' logged.")

def generate_web_dataset(count_per_type=25):
    print(f"--- Initialization: {OUTPUT_FILE} ---")
    with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
        random.shuffle(WEB_PAGE_URLS)
        random.shuffle(SEARCH_QUERIES)
        
        for i in range(min(count_per_type, len(WEB_PAGE_URLS))):
            write_direct_page(f, WEB_PAGE_URLS[i])
            time.sleep(GENERATION_SLEEP)
            
        for i in range(min(count_per_type, len(SEARCH_QUERIES))):
            write_chained_web(f, SEARCH_QUERIES[i])
            time.sleep(GENERATION_SLEEP)
            
    print(f"--- Completed. {ROW_ID_COUNTER} rows created. ---")

if __name__ == "__main__":
    generate_web_dataset(100)
