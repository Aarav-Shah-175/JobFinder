import os
from typing import List, Dict, Any
from src.utils.dates import get_utc_now_iso

def generate_markdown_report(
    new_jobs: List[Dict[str, Any]],
    stats: Dict[str, Any],
    source_statuses: Dict[str, str],
    output_dir: str = "reports"
) -> str:
    """
    Generates formatted daily Markdown report as requested in section 27.
    Returns file path of generated report.
    """
    os.makedirs(output_dir, exist_ok=True)
    today_str = get_utc_now_iso()[:10]
    filepath = os.path.join(output_dir, f"job_report_{today_str}.md")

    # Filter top matches (>= 80) and other relevant jobs (65-79)
    top_matches = [j for j in new_jobs if j.get("match_score", 0) >= 80.0]
    other_relevant = [j for j in new_jobs if 65.0 <= j.get("match_score", 0) < 80.0]

    lines = []
    lines.append(f"# JOB FINDER — {today_str}\n")
    lines.append(f"**Candidate**: Aarav (B.Tech CSE, VIT Chennai '27 | CGPA: 9.32)")
    lines.append(f"**Raw jobs discovered**: {stats.get('raw_count', 0)}")
    lines.append(f"**Unique jobs**: {stats.get('unique_count', 0)}")
    lines.append(f"**New jobs today**: {stats.get('new_count', 0)}")
    lines.append(f"**Relevant jobs (>=65)**: {len(top_matches) + len(other_relevant)}")
    lines.append(f"**Top matches (>=80)**: {len(top_matches)}\n")
    lines.append("=" * 40 + "\n")

    lines.append("## 🔥 TOP APPLICATIONS\n")
    if not top_matches:
        lines.append("No new 🔥 Top Application matches found today.\n")
    else:
        for idx, job in enumerate(top_matches, 1):
            reasons = job.get("match_reasons", {})
            why = reasons.get("why", [])
            gaps = reasons.get("gaps", [])

            lines.append(f"### {idx}. {job.get('company')} — {job.get('title')}")
            lines.append(f"- **Score**: `{job.get('match_score')}/100` ({job.get('category', '')})")
            lines.append(f"- **Location**: {job.get('normalized_location') or job.get('location')}")
            lines.append(f"- **Source**: {job.get('source')}")
            lines.append(f"- **Posted Date**: {job.get('posted_at')}")
            lines.append(f"- **Apply URL**: [Click Here to Apply]({job.get('url')})\n")

            lines.append("  **Why this is a strong match:**")
            for w in why:
                lines.append(f"  - ✓ {w}")

            if gaps:
                lines.append("  \n  **Potential gaps / notes:**")
                for g in gaps:
                    lines.append(f"  - ⚠ {g}")
            lines.append("\n" + "-" * 30 + "\n")

    lines.append("## 🟡 OTHER RELEVANT JOBS\n")
    if not other_relevant:
        lines.append("No other relevant jobs in 65-79 range today.\n")
    else:
        for idx, job in enumerate(other_relevant, 1):
            lines.append(f"- **{job.get('company')}** | [{job.get('title')}]({job.get('url')}) | `{job.get('match_score')}/100` | {job.get('normalized_location')}")

    lines.append("\n" + "=" * 40 + "\n")
    lines.append("## 📊 SOURCE STATUS DIAGNOSTIC\n")
    for src_name, status_str in source_statuses.items():
        lines.append(f"- **{src_name}**: {status_str}")

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath
