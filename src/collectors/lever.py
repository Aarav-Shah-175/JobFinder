from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.config import get_config
from src.utils.text import clean_text, normalize_url
from src.utils.dates import get_utc_now_iso

class LeverCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__("Lever", rate_limit_delay)

    def fetch_jobs_for_board(self, company_name: str, board_token: str) -> List[Dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
        resp = self.safe_get(url)
        if not resp:
            return []

        try:
            raw_jobs = resp.json()
            if not isinstance(raw_jobs, list):
                return []

            results = []
            for j in raw_jobs:
                title = j.get("text", "")
                job_url = j.get("hostedUrl", "")
                categories = j.get("categories", {})
                loc = categories.get("location", "")
                commitment = categories.get("commitment", "Full-time")
                content = clean_text(j.get("descriptionPlain", ""))
                created_at = get_utc_now_iso()[:10]
                if j.get("createdAt"):
                    try:
                        from datetime import datetime
                        created_at = datetime.fromtimestamp(j.get("createdAt")/1000.0).strftime("%Y-%m-%d")
                    except Exception:
                        pass

                if not title or not job_url:
                    continue

                results.append({
                    "source": "Lever",
                    "source_job_id": str(j.get("id", "")),
                    "company": company_name,
                    "title": title,
                    "location": loc,
                    "remote": "remote" in loc.lower() or "telecommute" in commitment.lower(),
                    "employment_type": commitment,
                    "description": content,
                    "url": normalize_url(job_url),
                    "company_url": f"https://jobs.lever.co/{board_token}",
                    "posted_at": created_at,
                    "raw_data": j
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error parsing Lever board {board_token}: {e}")
            return []

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = get_config()
        watchlist = config.companies.get("watchlist", [])
        all_jobs = []

        for item in watchlist:
            if item.get("ats_type") == "lever":
                c_name = item.get("company")
                b_token = item.get("board_token")
                self.logger.info(f"Fetching Lever board for {c_name} ({b_token})...")
                jobs = self.fetch_jobs_for_board(c_name, b_token)
                all_jobs.extend(jobs)

        return all_jobs
