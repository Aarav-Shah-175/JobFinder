import re
from typing import Dict, Any, Tuple, List
from src.utils.text import normalize_string

def check_cgpa_eligibility(text: str, candidate_cgpa: float = 9.32) -> Tuple[bool, str]:
    """
    Checks CGPA requirements mentioned in job description against candidate CGPA.
    Returns (is_eligible, reason).
    """
    norm_text = text.lower()
    
    cgpa_matches = re.findall(r'(?:cgpa|gpa)\s*(?:of|is|min|minimum|:\s*|>=\s*|>\s*)?\s*(\d+(?:\.\d+)?)', norm_text)
    for match_str in cgpa_matches:
        try:
            cutoff = float(match_str)
            if cutoff <= 10.0:
                if candidate_cgpa >= cutoff:
                    return (True, f"CGPA {candidate_cgpa} meets requirement of {cutoff}")
                else:
                    return (False, f"CGPA {candidate_cgpa} below cutoff of {cutoff}")
        except ValueError:
            continue

    pct_matches = re.findall(r'(\d{2})\s*%\s*(?:marks|aggregate|minimum|min)?', norm_text)
    for pct_str in pct_matches:
        try:
            pct_cutoff = float(pct_str)
            if 50.0 <= pct_cutoff <= 100.0:
                est_pct = candidate_cgpa * 9.5
                if est_pct >= pct_cutoff:
                    return (True, f"Academic aggregate ~{est_pct:.1f}% meets {pct_cutoff}% cutoff")
                else:
                    return (False, f"Academic aggregate ~{est_pct:.1f}% below {pct_cutoff}% cutoff")
        except ValueError:
            continue

    return (True, "No explicit CGPA/academic cutoff specified")

def check_graduation_eligibility(text: str, target_year: int = 2027) -> Tuple[bool, str]:
    """
    Checks graduation batch eligibility.
    Returns (is_eligible, reason).
    """
    norm_text = text.lower()

    exclusion_patterns = [
        r'2025\s*(?:batch|graduates?|only)',
        r'2026\s*(?:batch|graduates?|only)',
        r'graduated\s+before\s+2026',
        r'must\s+have\s+graduated\s+in\s+2025'
    ]
    for pattern in exclusion_patterns:
        if re.search(pattern, norm_text) and not re.search(r'2027', norm_text):
            return (False, "Excludes 2027 graduates (requires earlier batch)")

    inclusion_patterns = [
        r'2027\s*(?:batch|graduates?|class)',
        r'2026\s*-\s*2027',
        r'2027\s*or\s*later',
        r'pre-final\s+year',
        r'final\s+year\s+students?',
        r'graduating\s+in\s+2027'
    ]
    for pattern in inclusion_patterns:
        if re.search(pattern, norm_text):
            return (True, f"Explicitly targets 2027 / pre-final batch")

    return (True, "No graduation batch restrictions specified")

def check_experience_eligibility(job: Dict[str, Any], strict_fresher_only: bool = True) -> Tuple[bool, str]:
    """
    Strict Fresher Filter:
    Rejects any role that explicitly requires 1+ or 2+ years of prior work experience.
    Only allows 0-experience, internships, freshers, new grads, and 2027 batch roles.
    """
    title = job.get("normalized_title") or job.get("title", "")
    desc = job.get("description", "")
    min_exp = job.get("min_experience", 0.0)
    norm_combined = f"{title}\n{desc}".lower()

    # Hard senior/lead/manager title rejection
    senior_titles = ["senior", "sr.", "lead", "principal", "architect", "engineering manager", "director", "staff"]
    title_norm = title.lower()
    for st in senior_titles:
        if re.search(r'\b' + re.escape(st) + r'\b', title_norm) and "intern" not in title_norm:
            return (False, f"Role title '{title}' is a senior/experienced role")

    # Hard experience check: reject if min_exp > 0
    if min_exp > 0.0:
        return (False, f"Requires {min_exp}+ years of prior work experience (Strict Fresher filter enabled)")

    # Explicit text search for prior experience requirements e.g. "1+ years", "2+ years", "at least 1 year"
    exp_req_patterns = [
        r'1\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:work|industry|relevant|full-time)?\s*experience',
        r'2\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:work|industry|relevant|full-time)?\s*experience',
        r'3\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:work|industry|relevant|full-time)?\s*experience',
        r'at\s+least\s+(?:1|2|3)\s*(?:years?|yrs?)',
        r'minimum\s+(?:of\s+)?(?:1|2|3)\s*(?:years?|yrs?)'
    ]
    for pat in exp_req_patterns:
        # Check if matched pattern is NOT negated (e.g. "0-1 years" or "0 years")
        if re.search(pat, norm_combined) and not re.search(r'0\s*-\s*1\s*years?', norm_combined) and not re.search(r'0\s*years?', norm_combined):
            if "intern" not in norm_combined and "fresher" not in norm_combined:
                return (False, "Requires prior work experience (Strict Fresher filter enabled)")

    return (True, "Role requires 0 years prior experience (Fresher / Intern / New Grad)")

def evaluate_eligibility(job: Dict[str, Any], candidate_cgpa: float = 9.32, target_grad_year: int = 2027) -> Tuple[bool, List[str]]:
    """
    Evaluates complete eligibility across CGPA, graduation batch, and strict fresher experience limits.
    Returns (is_overall_eligible, list_of_reasons).
    """
    text = f"{job.get('title', '')}\n{job.get('description', '')}"

    cgpa_ok, cgpa_msg = check_cgpa_eligibility(text, candidate_cgpa)
    grad_ok, grad_msg = check_graduation_eligibility(text, target_grad_year)
    exp_ok, exp_msg = check_experience_eligibility(job, strict_fresher_only=True)

    reasons = [cgpa_msg, grad_msg, exp_msg]
    overall_eligible = cgpa_ok and grad_ok and exp_ok

    return overall_eligible, reasons
