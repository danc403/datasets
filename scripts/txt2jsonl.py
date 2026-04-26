import os
import glob
import json

def create_user_data_jsonl():
    """
    Locates the 'user_data' directory relative to the script location,
    scans for .txt and .md files, and writes books.jsonl into that folder.
    """
    # 1. Path Resolution: Find 'datasets/user_data' relative to this script
    # This works if run from: ./ , ./datasets/ , or ./datasets/scripts/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Climb up until we find 'datasets' or hit root
    base_search = script_dir
    target_subdir = "datasets/user_data"
    
    # Check if we are inside scripts/
    if os.path.basename(base_search) == "scripts":
        base_search = os.path.dirname(base_search)
        
    # Check if we are inside datasets/
    if os.path.basename(base_search) == "datasets":
        user_data_path = os.path.join(base_search, "user_data")
    else:
        # We are likely in the root
        user_data_path = os.path.join(base_search, "datasets", "user_data")

    if not os.path.exists(user_data_path):
        print(f"Error: Target directory not found: {user_data_path}")
        return

    output_file = os.path.join(user_data_path, "books.jsonl")
    id_counter = 1
    processed_count = 0

    print(f"Scanning: {user_data_path}")

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Search only within the user_data directory
        search_pattern_txt = os.path.join(user_data_path, "**/*.txt")
        search_pattern_md = os.path.join(user_data_path, "**/*.md")
        
        files = glob.glob(search_pattern_txt, recursive=True) + \
                glob.glob(search_pattern_md, recursive=True)

        for filename in files:
            # Skip the output file itself if it already exists
            if os.path.abspath(filename) == os.path.abspath(output_file):
                continue

            try:
                with open(filename, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()

                    if len(lines) >= 2:
                        title = lines[0].strip()
                        author = lines[1].strip()
                        text = "".join(lines)
                    elif len(lines) >= 1:
                        title = lines[0].strip()
                        author = ""
                        text = "".join(lines)
                    else:
                        continue # Skip empty files

                    book_data = {
                        "id": id_counter,
                        "title": title,
                        "author": author,
                        "genre": "user_data",
                        "text": text.strip()
                    }

                    json.dump(book_data, outfile, ensure_ascii=False)
                    outfile.write("\n")
                    id_counter += 1
                    processed_count += 1

            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print(f"Success: Created {output_file} with {processed_count} entries.")

if __name__ == "__main__":
    create_user_data_jsonl()
