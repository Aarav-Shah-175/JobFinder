from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.config import get_config
from src.utils.text import clean_text, normalize_url
from src.utils.dates import get_utc_now_iso

class AshbyCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__("Ashby", rate_limit_delay)

    def fetch_jobs_for_board(self, company_name: str, board_token: str) -> List[Dict[str, Any]]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"
        resp = self.safe_get(url)
        if not resp:
            return []

        try:
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            results = []
            for j in raw_jobs:
                title = j.get("title", "")
                job_url = j.get("jobUrl", "") or f"https://jobs.ashbyhq.com/{board_token}/{j.get('id')}"
                loc = j.get("location", "")
                content = clean_text(j.get("descriptionPlain", "") or j.get("descriptionHtml", ""))
                is_remote = j.get("isRemote", False) or "remote" in loc.lower()

                if not title or not job_url:
                    continue

                results.append({
                    "source": "Ashby",
                    "source_job_id": str(j.get("id", "")),
                    "company": company_name,
                    "title": title,
                    "location": loc,
                    "remote": is_remote,
                    "employment_type": j.get("employmentType", "Full-time"),
                    "description": content,
                    "url": normalize_url(job_url),
                    "company_url": f"https://jobs.ashbyhq.com/{board_token}",
                    "posted_at": get_utc_now_iso()[:10],
                    "raw_data": j
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error parsing Ashby board {board_token}: {e}")
            return []

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = get_config()
        watchlist = config.companies.get("watchlist", [])
        all_jobs = []

        for item in watchlist:
            if item.get("ats_type") == "ashby":
                c_name = item.get("company")
                b_token = item.get("board_token")
                self.logger.info(f"Fetching Ashby board for {c_name} ({b_token})...")
                jobs = self.fetch_jobs_for_board(c_name, b_token)
                all_jobs.extend(jobs)

        return all_jobs
