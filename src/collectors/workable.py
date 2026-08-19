from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.config import get_config
from src.utils.text import clean_text, normalize_url
from src.utils.dates import get_utc_now_iso

class WorkableCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__("Workable", rate_limit_delay)

    def fetch_jobs_for_board(self, company_name: str, board_token: str) -> List[Dict[str, Any]]:
        url = f"https://apply.workable.com/api/v1/widget/accounts/{board_token}"
        resp = self.safe_get(url)
        if not resp:
            return []

        try:
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            results = []
            for j in raw_jobs:
                title = j.get("title", "")
                shortcode = j.get("shortcode", "")
                job_url = f"https://apply.workable.com/{board_token}/j/{shortcode}/" if shortcode else ""
                loc = j.get("city", "")
                if j.get("country"):
                    loc = f"{loc}, {j.get('country')}" if loc else j.get("country")
                content = clean_text(j.get("description", ""))
                is_remote = j.get("telecommute", False) or "remote" in loc.lower()

                if not title or not job_url:
                    continue

                results.append({
                    "source": "Workable",
                    "source_job_id": str(shortcode or j.get("id", "")),
                    "company": company_name,
                    "title": title,
                    "location": loc,
                    "remote": is_remote,
                    "employment_type": j.get("type", "Full-time"),
                    "description": content,
                    "url": normalize_url(job_url),
                    "company_url": f"https://apply.workable.com/{board_token}/",
                    "posted_at": j.get("published", get_utc_now_iso()[:10]),
                    "raw_data": j
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error parsing Workable board {board_token}: {e}")
            return []

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = get_config()
        watchlist = config.companies.get("watchlist", [])
        all_jobs = []

        for item in watchlist:
            if item.get("ats_type") == "workable":
                c_name = item.get("company")
                b_token = item.get("board_token")
                self.logger.info(f"Fetching Workable board for {c_name} ({b_token})...")
                jobs = self.fetch_jobs_for_board(c_name, b_token)
                all_jobs.extend(jobs)

        return all_jobs
