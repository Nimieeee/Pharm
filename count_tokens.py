import sys
import re
import fitz # PyMuPDF
import tiktoken

def main():
    pdf_path = "/Users/mac/Desktop/phhh/Levetiracetam vs. Valproate in a Drosophila Model of Dementia A Comparative Analysis of Neuroprotection, Neurotoxicity, and Oxidative Stress Pathway Modulation.pdf"
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        sys.exit(1)
        
    full_text = ""
    for page in doc:
        full_text += page.get_text()
        
    # Attempt to split at "References" or "Bibliography"
    # Look for the word "References" surrounded by newlines or at the start of a line
    
    parts = re.split(r'\n\s*REFERENCES\s*\n', full_text, flags=re.IGNORECASE)
    
    if len(parts) > 1:
        # Take everything before the last "References" match
        main_text = parts[0]
        ref_text = parts[-1]
        print("Successfully split at References section.")
    else:
        print("Could not find a distinct References section. Counting entire document.")
        main_text = full_text
        ref_text = ""
        
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(main_text)
    ref_tokens = enc.encode(ref_text) if ref_text else []
    
    print(f"\n--- Token Analysis (cl100k_base) ---")
    print(f"Main Body Text Tokens: {len(tokens):,}")
    print(f"References Tokens: {len(ref_tokens):,}")
    print(f"Total Combined Tokens: {len(tokens) + len(ref_tokens):,}")
    
    print("\nSnippet BEFORE cut:")
    print("..." + main_text[-200:].replace('\n', ' '))
    
if __name__ == "__main__":
    main()
