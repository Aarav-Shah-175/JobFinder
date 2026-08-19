import re
from typing import Dict, Any, Tuple
from src.utils.text import clean_text, normalize_string

LOCATION_MAPPINGS = {
    "bengaluru": "Bangalore",
    "bangalore": "Bangalore",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "pune": "Pune",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "noida": "Noida",
    "mumbai": "Mumbai",
    "delhi": "Delhi NCR",
    "delhi ncr": "Delhi NCR",
    "remote": "Remote",
    "work from home": "Remote",
    "anywhere in india": "Remote",
    "india": "India"
}

TITLE_ALIASES = {
    "sde 1": "Software Development Engineer I",
    "sde i": "Software Development Engineer I",
    "sde-1": "Software Development Engineer I",
    "sde-i": "Software Development Engineer I",
    "software engineer 1": "Software Engineer I",
    "software engineer i": "Software Engineer I",
    "swe 1": "Software Engineer I",
    "swe i": "Software Engineer I",
    "swe intern": "Software Engineer Intern",
    "sde intern": "Software Development Engineer Intern",
    "software engineering intern": "Software Engineer Intern",
}

def normalize_title(title: str) -> str:
    """Cleans and standardizes job titles."""
    cleaned = clean_text(title)
    norm = normalize_string(cleaned)
    for alias, standard in TITLE_ALIASES.items():
        if alias in norm:
            return standard
    return cleaned

def normalize_location(location: str) -> str:
    """Normalizes location strings to standard tech hub names."""
    if not location:
        return "India"
    cleaned = clean_text(location)
    norm = normalize_string(cleaned)
    matched = []
    for loc_key, std_name in LOCATION_MAPPINGS.items():
        if loc_key in norm and std_name not in matched:
            matched.append(std_name)
    if "Remote" in matched:
        return "Remote"
    if matched:
        return ", ".join(matched)
    return cleaned

def parse_experience_years(text: str) -> Tuple[float, float]:
    """
    Parses min and max experience years from job title and description.
    Returns (min_years, max_years). If not found, returns (0.0, 99.0).
    """
    norm = text.lower()
    
    # Check for senior/lead/manager keywords first
    if any(k in norm for k in ["senior", "sr.", "lead", "principal", "staff", "manager", "architect", "head of", "director"]):
        # Check if explicitly 5+ or similar
        m_plus = re.search(r'(\d+)\s*\+\s*years?', norm)
        if m_plus:
            yrs = float(m_plus.group(1))
            return (max(yrs, 5.0), 99.0)
        return (5.0, 99.0)

    # Check for range pattern: e.g. "0-2 years", "1 to 3 yrs", "0 - 1 year"
    m_range = re.search(r'(\d+)\s*(?:-|to|\b)\s*(\d+)\s*(?:years?|yrs?)', norm)
    if m_range:
        min_y = float(m_range.group(1))
        max_y = float(m_range.group(2))
        return (min_y, max_y)

    # Check for single minimum pattern: e.g. "3+ years", "2+ yrs"
    m_single = re.search(r'(\d+)\s*\+\s*(?:years?|yrs?)', norm)
    if m_single:
        min_y = float(m_single.group(1))
        return (min_y, 99.0)

    # Check for internship / fresher / graduate keywords
    if any(k in norm for k in ["intern", "internship", "fresher", "new grad", "graduate engineer", "trainee"]):
        return (0.0, 1.0)

    return (0.0, 99.0)

def normalize_job_dict(raw_job: Dict[str, Any]) -> Dict[str, Any]:
    """Performs full normalization on a raw job record."""
    title = raw_job.get("title", "")
    desc = raw_job.get("description", "")
    combined_text = f"{title}\n{desc}"

    norm_title = normalize_title(title)
    norm_location = normalize_location(raw_job.get("location", ""))
    is_remote = "remote" in norm_location.lower() or raw_job.get("remote", False)
    min_exp, max_exp = parse_experience_years(combined_text)

    normalized = dict(raw_job)
    normalized["normalized_title"] = norm_title
    normalized["normalized_location"] = norm_location
    normalized["remote"] = is_remote
    normalized["min_experience"] = min_exp
    normalized["max_experience"] = max_exp
    return normalized
