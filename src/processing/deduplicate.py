from typing import List, Dict, Any, Set
from src.utils.text import normalize_url, normalize_string, calculate_text_similarity

def create_dedup_key(job: Dict[str, Any]) -> str:
    """Generates exact deduplication key based on company, title, and location."""
    company = normalize_string(job.get("company", ""))
    title = normalize_string(job.get("normalized_title") or job.get("title", ""))
    loc = normalize_string(job.get("normalized_location") or job.get("location", ""))
    return f"{company}::{title}::{loc}"

def is_fuzzy_duplicate(job1: Dict[str, Any], job2: Dict[str, Any], similarity_threshold: float = 0.85) -> bool:
    """
    Checks if two jobs are fuzzy duplicates based on company match + high title/desc similarity.
    """
    comp1 = normalize_string(job1.get("company", ""))
    comp2 = normalize_string(job2.get("company", ""))
    if comp1 != comp2 and comp1 not in comp2 and comp2 not in comp1:
        return False

    title1 = job1.get("normalized_title") or job1.get("title", "")
    title2 = job2.get("normalized_title") or job2.get("title", "")
    t_sim = calculate_text_similarity(title1, title2)
    if t_sim >= similarity_threshold:
        return True

    return False

def deduplicate_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of incoming raw jobs.
    Merges sources info if the same job is discovered from multiple sources.
    """
    seen_urls: Set[str] = set()
    exact_keys: Dict[str, Dict[str, Any]] = {}
    unique_jobs: List[Dict[str, Any]] = []

    for job in jobs:
        clean_u = normalize_url(job.get("url", ""))
        if clean_u and clean_u in seen_urls:
            continue

        dedup_k = create_dedup_key(job)
        if dedup_k in exact_keys:
            # Merge source info
            existing = exact_keys[dedup_k]
            sources = existing.get("sources", [existing.get("source")])
            if job.get("source") and job.get("source") not in sources:
                sources.append(job.get("source"))
            existing["sources"] = sources
            continue

        # Check fuzzy duplication against already accepted unique jobs
        is_dup = False
        for unique in unique_jobs:
            if is_fuzzy_duplicate(job, unique):
                is_dup = True
                sources = unique.get("sources", [unique.get("source")])
                if job.get("source") and job.get("source") not in sources:
                    sources.append(job.get("source"))
                unique["sources"] = sources
                break

        if not is_dup:
            if clean_u:
                seen_urls.add(clean_u)
            job["sources"] = [job.get("source")]
            exact_keys[dedup_k] = job
            unique_jobs.append(job)

    return unique_jobs
