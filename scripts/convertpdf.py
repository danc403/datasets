import PyPDF2
import os
import sys
import re

# Constant for the console output flag
STDOUT_FLAG = "-c"

def get_output_path(input_path):
    """
    Generates the default output file path by changing the extension to .txt.
    """
    # Split the path into the base name and the extension
    base_name, _ = os.path.splitext(input_path)
    
    # Append the desired output extension (.txt)
    output_path = base_name + ".txt"
    return output_path

def collapse_empty_lines(text):
    """
    Reduces instances of three or more consecutive empty lines to a maximum of two.
    """
    # Use a regular expression to find 3 or more newline characters and replace them with 2.
    return re.sub(r'\n{3,}', '\n\n', text)

def clean_watermark(text):
    """
    Removes all instances of 'OceanofPDF .com' and 'OceanofPDF.com' from the text.
    Includes regex for broader variation coverage.
    """
    # Direct replacements for common variations
    text = text.replace("OceanofPDF .com", "")
    text = text.replace("OceanofPDF.com", "")
    text = text.replace("OceanofPDF", "")
    
    # Regex to catch stray URL patterns or spaced watermarks often found in footers
    text = re.sub(r'Ocean\s*of\s*PDF\s*\.?\s*com', '', text, flags=re.IGNORECASE)
    return text

def pdf_to_text(pdf_path, text_path=None):
    """
    Extracts text from a PDF and applies line collapse.
    
    If called as a module (text_path=None), it returns the extracted text.
    If called directly with an output path (text_path is not None), it writes
    the file/prints to stdout and returns None. It will sys.exit(1) on errors in direct execution.
    """
    # --- Input and Error Checking ---
    if not os.path.exists(pdf_path):
        if text_path is not None:
             # Only exit if the function is being run to perform a direct operation
             print(f"Error: The input PDF file '{pdf_path}' was not found.")
             sys.exit(1)
        # If text_path is None (module call), return None
        return None 

    # --- Text Extraction ---
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_texts = []
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text)
                
            text_content = "\n".join(page_texts)
            
            # --- Cleaning Pipeline ---
            # 1. Remove the watermark
            text_content_cleaned_watermark = clean_watermark(text_content)
            
            # 2. Collapse empty lines
            text_content_clean = collapse_empty_lines(text_content_cleaned_watermark)
            
    except PyPDF2.errors.PdfReadError:
        if text_path is not None:
            print(f"Error: Could not read '{pdf_path}'. It might be encrypted or corrupted.")
            sys.exit(1)
        return None
    except Exception as e:
        if text_path is not None:
            print(f"An unexpected error occurred: {e}")
            sys.exit(1)
        return None

    # --- Output Handling ---
    if text_path:
        # Direct execution: write to file or print to stdout. Return None.
        if text_path == STDOUT_FLAG:
            # Print to stdout
            print(text_content_clean)
        else:
            # Write to file
            try:
                with open(text_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(text_content_clean)
                print(f"--- Processed: {pdf_path} -> {text_path} ---")
            except Exception as e:
                print(f"Error: Could not write to output file '{text_path}': {e}")
                sys.exit(1)
        return None # In direct execution, we return nothing
    else:
        # Module import: return the text content
        return text_content_clean


# --- Main execution block ---
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print(f"Usage: python convertpdf.py <input_pdf_file> [{STDOUT_FLAG}]")
        sys.exit(1)

    # The input PDF path
    input_pdf_name = sys.argv[1]
    
    # Determine the output path: explicitly -c or automatic .txt in same dir
    if len(sys.argv) == 3 and sys.argv[2] == STDOUT_FLAG:
        output_text_name = STDOUT_FLAG
    else:
        output_text_name = get_output_path(input_pdf_name)

    # Execute
    pdf_to_text(input_pdf_name, output_text_name)
    
    sys.exit(0)
