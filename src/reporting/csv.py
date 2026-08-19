import os
import pandas as pd
from typing import List, Dict, Any

def export_applications_csv(jobs: List[Dict[str, Any]], filepath: str = "data/applications.csv") -> str:
    """Exports structured jobs shortlist into CSV for tracking."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    rows = []
    for j in jobs:
        reasons = j.get("match_reasons", {})
        why_str = " | ".join(reasons.get("why", []))
        gaps_str = " | ".join(reasons.get("gaps", []))
        skills_str = ", ".join(j.get("skills", []))

        rows.append({
            "ID": j.get("id"),
            "Date Discovered": j.get("discovered_at", "")[:10],
            "Company": j.get("company"),
            "Title": j.get("title"),
            "Location": j.get("normalized_location") or j.get("location"),
            "Match Score": j.get("match_score"),
            "Category": j.get("category"),
            "Status": j.get("status", "NEW"),
            "Apply URL": j.get("url"),
            "Skills": skills_str,
            "Why Match": why_str,
            "Gaps": gaps_str,
            "Source": j.get("source")
        })

    df = pd.DataFrame(rows)
    try:
        df.to_csv(filepath, index=False, encoding="utf-8")
        return filepath
    except PermissionError:
        fallback = os.path.join(os.path.dirname(filepath), "applications_latest.csv")
        df.to_csv(fallback, index=False, encoding="utf-8")
        return fallback
    except Exception as e:
        print(f"Warning: Could not save CSV file: {e}")
        return filepath
