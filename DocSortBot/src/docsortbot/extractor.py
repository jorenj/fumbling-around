import re
from pathlib import Path
from collections import Counter
from pypdf import PdfReader
import logging

# Suppress pypdf warnings about unimplemented encodings
logging.getLogger("pypdf").setLevel(logging.ERROR)

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from supported file types."""
    ext = file_path.suffix.lower()
    try:
        if ext == '.pdf':
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        elif ext in ['.txt', '.csv']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        print(f"Error reading content of '{file_path.name}': {e}")
    return ""

def determine_year_from_text(text: str) -> tuple:
    """Uses a 3-step heuristic algorithm to find the reference year in text. Returns (year, evaluation_rule)."""
    if not text:
        return None, None
        
    # Step 1: Anchor Keyword Search
    anchor_pattern = re.compile(
        r'(tax year|statement period|period ending|statement date|1099|w-2|statement|tax return|return)[\s\S]{0,50}?(20\d{2})',
        re.IGNORECASE
    )
    matches = anchor_pattern.findall(text)
    if matches:
        years = [m[1] for m in matches]
        counts = Counter(years)
        sorted_years = sorted(counts.keys(), key=lambda y: (-counts[y], -int(y)))
        return sorted_years[0], "Anchor Keyword"
        
    # Step 2: Top-Heavy Frequency Analysis
    top_text_len = max(500, len(text) // 4)
    top_text = text[:top_text_len]
    
    # Negative lookbehind: not preceded by a digit, dollar sign, or dot
    # Negative lookahead: not followed by a digit, or a dot followed by a digit (e.g. .00)
    year_pattern = re.compile(r'(?<![\d$.])(?:19|20)\d{2}(?!\d|\.\d)')
    top_years = year_pattern.findall(top_text)
    
    if top_years:
        counts = Counter(top_years)
        sorted_years = sorted(counts.keys(), key=lambda y: (-counts[y], -int(y)))
        return sorted_years[0], "Top-Heavy Frequency"
        
    # Step 3: Document-Wide Frequency
    all_years = year_pattern.findall(text)
    if all_years:
        counts = Counter(all_years)
        # Sort by frequency descending, then year value descending
        sorted_years = sorted(counts.keys(), key=lambda y: (-counts[y], -int(y)))
        return sorted_years[0], "Document-Wide Frequency"
        
    return None, None
