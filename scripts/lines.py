import sys
import argparse
import os
import re

def format_text_to_sentences(input_path):
    """
    Formats text from an input file, ensuring one sentence per line,
    and saves the output to a new file with a .md extension.

    Args:
        input_path: Path to the input text file.
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Handle abbreviations with periods (adjust as needed for other languages)
        text = re.sub(r"(\w+\.\w+)", lambda m: m.group(1) + " ", text)

        # Split text into sentences, handling line-end punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Create the output file path with .md extension
        output_base, _ = os.path.splitext(input_path)
        output_path = output_base + ".md"

        with open(output_path, 'w', encoding='utf-8') as outfile:
            for sentence in sentences:
                outfile.write(sentence.strip() + '\n')

        print(f"Formatted text saved to: {output_path}")

    except FileNotFoundError:
        print(f"Error: Input file '{input_path}' not found.")
    except Exception as e:
        print(f"An error occurred while processing the file: {e}")

def parse_args():
    parser = argparse.ArgumentParser(description='Format text file into sentences.')
    parser.add_argument('input_file', type=str, help='Path to the input text file.')
    return parser.parse_args()

def main():
    args = parse_args()
    format_text_to_sentences(args.input_file)

if __name__ == "__main__":
    main()
