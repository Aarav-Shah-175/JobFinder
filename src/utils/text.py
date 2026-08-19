import re
import urllib.parse
from typing import List

def clean_text(text: str) -> str:
    """Cleans HTML tags, extra whitespace, and special characters from text."""
    if not text:
        return ""
    # Strip HTML tags if present
    text = re.sub(r'<[^>]+>', ' ', text)
    # Replace non-breaking space and multiple whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_string(text: str) -> str:
    """Lowercases, strips punctuation, and normalizes spaces for key matching."""
    if not text:
        return ""
    text = clean_text(text).lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def normalize_url(url: str) -> str:
    """Cleans URL by stripping query parameters like utm_source, tracking IDs."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url.strip())
    # Keep query parameters that might identify job ID if essential, but strip tracking params
    query_params = urllib.parse.parse_qs(parsed.query)
    filtered_params = {k: v for k, v in query_params.items() if not k.startswith(('utm_', 'ref', 'source', 'gh_src'))}
    new_query = urllib.parse.urlencode(filtered_params, doseq=True)
    clean_path = parsed.path.rstrip('/')
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, clean_path, parsed.params, new_query, ''))

def calculate_jaccard_similarity(set1: set, set2: set) -> float:
    """Calculates Jaccard similarity between two token sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def calculate_text_similarity(str1: str, str2: str) -> float:
    """Calculates word-level token overlap similarity between two strings."""
    tokens1 = set(normalize_string(str1).split())
    tokens2 = set(normalize_string(str2).split())
    return calculate_jaccard_similarity(tokens1, tokens2)
