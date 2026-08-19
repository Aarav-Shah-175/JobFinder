import re
from typing import Dict, Any, List, Tuple
from src.config import get_config
from src.processing.skills import extract_skills, extract_domains, match_project_signals
from src.processing.eligibility import evaluate_eligibility
from src.utils.text import normalize_string
from src.database.db import DatabaseManager

def score_role_relevance(title: str, job_families: Dict[str, List[str]]) -> Tuple[float, str]:
    """Scores title alignment across Aarav's priority job families (0-20)."""
    norm_title = title.lower()

    for role in job_families.get("tier_1", []):
        if role.lower() in norm_title or norm_title in role.lower():
            return (20.0, f"Tier 1 Core SDE Role ({role})")

    for role in job_families.get("tier_2", []):
        if role.lower() in norm_title:
            return (18.0, f"Tier 2 Backend/Fullstack Engineering ({role})")

    for role in job_families.get("tier_3", []):
        if role.lower() in norm_title:
            return (18.0, f"Tier 3 Specialized Security Role ({role})")

    for role in job_families.get("tier_4", []):
        if role.lower() in norm_title:
            return (18.0, f"Tier 4 Systems/Infrastructure Role ({role})")

    for role in job_families.get("tier_5", []):
        if role.lower() in norm_title:
            return (16.0, f"Tier 5 Applied AI / Computer Vision Role ({role})")

    if any(k in norm_title for k in ["engineer", "developer", "programmer", "tech", "analyst"]):
        return (10.0, "General Software / Technical Role")

    return (4.0, "Other Technical Role")

def score_technical_skills(job_skills: List[str], candidate_skills: Dict[str, List[str]]) -> Tuple[float, List[str], List[str]]:
    """Scores tech skill overlap (0-20), returning matched skills and missing critical skills."""
    all_cand_skills = set()
    for cat, s_list in candidate_skills.items():
        for s in s_list:
            all_cand_skills.add(s.lower())

    if not job_skills:
        return (12.0, [], [])

    matched = []
    missing = []

    for js in job_skills:
        js_lower = js.lower()
        if js_lower in all_cand_skills:
            matched.append(js)
        else:
            missing.append(js)

    total_job_skills = len(job_skills)
    match_ratio = len(matched) / total_job_skills if total_job_skills > 0 else 1.0

    score = 20.0 * match_ratio

    core_hits = [s for s in matched if s.lower() in ["java", "c++", "python", "postgresql", "react", "aws", "dsa"]]
    if core_hits:
        score = min(20.0, score + len(core_hits) * 1.0)

    return (round(score, 1), matched, missing)

def score_experience_compatibility(job: Dict[str, Any]) -> Tuple[float, str]:
    """Scores experience requirements compatibility (0-15)."""
    min_exp = job.get("min_experience", 0.0)
    title = (job.get("normalized_title") or job.get("title", "")).lower()
    desc = (job.get("description", "")).lower()

    if "intern" in title or "internship" in desc or "fresher" in desc or "new grad" in desc:
        return (15.0, "Ideal match for student / intern / fresher")
    elif min_exp <= 1.0:
        return (14.0, "0-1 years entry level requirement")
    elif min_exp <= 2.0:
        return (11.0, "0-2 years acceptable entry level")
    elif min_exp <= 3.0:
        return (5.0, "2-3 years requirement (higher threshold)")
    else:
        return (0.0, f"Excessive experience requirement ({min_exp}+ yrs)")

def score_graduation_eligibility(text: str, target_year: int = 2027) -> Tuple[float, str]:
    """Scores graduation batch alignment (0-10)."""
    norm_text = text.lower()
    if any(k in norm_text for k in ["2027", "2026-2027", "pre-final year", "final year"]):
        return (10.0, "Explicit match for 2027 batch / pre-final year")
    return (7.0, "Open to student / graduate applicants")

def score_project_domain_relevance(text: str) -> Tuple[float, List[str]]:
    """Scores alignment with Aarav's 3 major projects & specialized domains (0-10)."""
    proj_scores = match_project_signals(text)
    domains = extract_domains(text)
    highlights = []
    total_score = 0.0

    if proj_scores.get("secure_attendance", 0) > 0.4:
        total_score += 4.0
        highlights.append("Strong match for Secure Presence & Authentication project (WebAuthn/Biometrics)")

    if proj_scores.get("duplicate_finder", 0) > 0.4:
        total_score += 4.0
        highlights.append("Strong match for Duplicate File Finder project (C++/OpenMPI/Systems)")

    if proj_scores.get("nidps", 0) > 0.4:
        total_score += 4.0
        highlights.append("Strong match for Network Intrusion Detection project (Scapy/Networking)")

    if "backend" in domains or "systems" in domains or "security" in domains:
        total_score += 2.0

    return (min(10.0, round(total_score, 1)), highlights)

def score_location(location: str, preferred_locations: List[str]) -> Tuple[float, str]:
    """Scores location preference (0-5)."""
    if not location:
        return (3.0, "Location unmapped")
    norm_loc = location.lower()
    for pref in preferred_locations:
        if pref.lower() in norm_loc:
            return (5.0, f"Preferred Tech Hub Location ({pref})")
    if "india" in norm_loc:
        return (4.0, "India location")
    return (2.0, f"Location: {location}")

def score_company_preference(company: str, watchlist: List[Dict[str, Any]]) -> Tuple[float, str]:
    """Scores company watchlist priority boost (0-5)."""
    if not company:
        return (2.5, "Standard company")
    c_lower = company.strip().lower()
    for item in watchlist:
        target_c = item.get("company", "").lower()
        if target_c and (target_c == c_lower or target_c in c_lower or c_lower in target_c):
            prio = item.get("priority", "MEDIUM")
            if prio == "HIGH":
                return (5.0, f"High Priority Target Company ({item['company']})")
            elif prio == "MEDIUM":
                return (4.0, f"Medium Priority Target Company ({item['company']})")
    return (2.5, "Standard candidate company")

def score_historical_personalization(job: Dict[str, Any], db: DatabaseManager = None) -> Tuple[float, str]:
    """
    Phase 5 Adaptive Personalization:
    Analyzes Aarav's past application actions (SAVED, APPLIED vs IGNORED) to tune scores.
    """
    if not db:
        return (0.0, "")

    try:
        all_jobs = db.get_all_jobs()
        applied_companies = {j["company"].lower() for j in all_jobs if j.get("status") in ["APPLIED", "OA", "INTERVIEW", "SAVED"]}
        ignored_titles = {j["normalized_title"].lower() for j in all_jobs if j.get("status") == "IGNORED"}

        comp_lower = (job.get("company") or "").lower()
        title_lower = (job.get("normalized_title") or "").lower()

        boost = 0.0
        reason = ""

        if comp_lower in applied_companies:
            boost += 3.0
            reason = "Company previously saved/applied to by Aarav"

        if title_lower in ignored_titles:
            boost -= 5.0
            reason = "Role family previously marked IGNORED by Aarav"

        return (boost, reason)
    except Exception:
        return (0.0, "")

def score_job(job: Dict[str, Any], db: DatabaseManager = None) -> Dict[str, Any]:
    """
    Computes comprehensive 0-100 score for a job against Aarav's candidate profile.
    Produces detailed match reasons and gap explanations.
    """
    config = get_config()
    profile = config.profile
    watchlist = config.companies.get("watchlist", [])

    title = job.get("normalized_title") or job.get("title", "")
    desc = job.get("description", "")
    combined_text = f"{title}\n{desc}"

    # 1. Eligibility Check
    is_eligible, elig_reasons = evaluate_eligibility(
        job,
        candidate_cgpa=profile.get("education", {}).get("cgpa", 9.32),
        target_grad_year=profile.get("education", {}).get("graduation_year", 2027)
    )

    if not is_eligible:
        return {
            "match_score": 0.0,
            "category": "❌ NOT ELIGIBLE",
            "is_eligible": False,
            "match_reasons": {
                "why": [],
                "gaps": elig_reasons,
                "breakdown": {}
            }
        }

    job_skills = extract_skills(combined_text)
    job["skills"] = job_skills

    # 2. Score Components (0-100 Scale)
    r_score, r_msg = score_role_relevance(title, profile.get("job_families", {}))
    t_score, matched_skills, missing_skills = score_technical_skills(job_skills, profile.get("skills", {}))
    e_score, e_msg = score_experience_compatibility(job)
    g_score, g_msg = score_graduation_eligibility(combined_text)
    p_score, p_highlights = score_project_domain_relevance(combined_text)
    l_score, l_msg = score_location(job.get("normalized_location", ""), profile.get("locations", {}).get("preferred", []))
    f_score = 10.0
    c_score, c_msg = score_company_preference(job.get("company", ""), watchlist)
    a_score = 3.0
    i_score = 2.0

    # Phase 5 Personalization
    pers_boost, pers_msg = score_historical_personalization(job, db)

    total_score = r_score + t_score + e_score + g_score + p_score + l_score + f_score + c_score + a_score + i_score + pers_boost

    penalties = 0.0
    critical_missing = [s for s in missing_skills if s.lower() in ["spring boot", "kafka", "kubernetes", "golang", "ruby", "c#", ".net"]]
    if critical_missing:
        penalties += min(15.0, len(critical_missing) * 5.0)

    final_score = max(0.0, min(100.0, total_score - penalties))
    final_score = round(final_score, 1)

    if final_score >= 90.0:
        category = "🔥 EXCELLENT MATCH"
    elif final_score >= 80.0:
        category = "🟢 STRONG MATCH"
    elif final_score >= 65.0:
        category = "🟡 POSSIBLE MATCH"
    elif final_score >= 50.0:
        category = "⚪ LOW MATCH"
    else:
        category = "❌ NOT ELIGIBLE"

    why_list = [r_msg, e_msg, g_msg, l_msg, c_msg]
    if matched_skills:
        why_list.append(f"Matched skills: {', '.join(matched_skills[:6])}")
    why_list.extend(p_highlights)
    why_list.append("9.32 CGPA academic cutoff eligible")
    why_list.append("Software Engineering internship experience (Bluestock Fintech)")
    if pers_msg and pers_boost > 0:
        why_list.append(pers_msg)

    gaps_list = []
    if missing_skills:
        gaps_list.append(f"Skills mentioned in JD not on resume: {', '.join(missing_skills[:5])}")
    if penalties > 0:
        gaps_list.append(f"Penalized for missing core framework requirements ({', '.join(critical_missing)})")
    if pers_msg and pers_boost < 0:
        gaps_list.append(pers_msg)

    return {
        "match_score": final_score,
        "category": category,
        "is_eligible": True,
        "match_reasons": {
            "why": why_list,
            "gaps": gaps_list,
            "breakdown": {
                "role_relevance": r_score,
                "technical_skills": t_score,
                "experience_compatibility": e_score,
                "graduation_eligibility": g_score,
                "project_domain": p_score,
                "location": l_score,
                "freshness": f_score,
                "company_preference": c_score,
                "academic": a_score,
                "internship_exp": i_score,
                "personalization": pers_boost,
                "penalties": penalties
            }
        }
    }
