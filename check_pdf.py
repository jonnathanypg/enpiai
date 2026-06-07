import sys
import os
import pdfplumber

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return text

filepath = 'backend/uploads/dist_4/Ecuador_Distribuidor.pdf'
if os.path.exists(filepath):
    text = extract_text_from_pdf(filepath)
    print(f"File: {filepath}")
    print(f"Text length: {len(text)} characters")
    print(f"Estimated chunks (1000 chars): {len(text)//1000 + 1}")
else:
    print(f"File not found: {filepath}")
