import os
from typing import Dict, Any, List

def write_github_step_summary(stats: Dict[str, Any], top_jobs: List[Dict[str, Any]]):
    """Writes job run summary to GITHUB_STEP_SUMMARY environment file."""
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    lines = []
    lines.append("# 🎯 Job Discovery Run Summary\n")
    lines.append(f"- **Raw Jobs Collected**: {stats.get('raw_count', 0)}")
    lines.append(f"- **Unique Jobs**: {stats.get('unique_count', 0)}")
    lines.append(f"- **New Jobs Discovered**: {stats.get('new_count', 0)}")
    lines.append(f"- **Top Match Shortlist**: {len(top_jobs)}\n")

    if top_jobs:
        lines.append("### 🔥 Top Picks Today")
        for j in top_jobs[:5]:
            lines.append(f"- **[{j.get('company')}] {j.get('title')}** (Score: `{j.get('match_score')}`) — [Apply]({j.get('url')})")

    with open(summary_file, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
