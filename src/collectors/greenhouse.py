from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.config import get_config
from src.utils.text import clean_text, normalize_url
from src.utils.dates import get_utc_now_iso

class GreenhouseCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 1.0):
        super().__init__("Greenhouse", rate_limit_delay)

    def fetch_jobs_for_board(self, company_name: str, board_token: str) -> List[Dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        resp = self.safe_get(url)
        if not resp:
            return []

        try:
            data = resp.json()
            raw_jobs = data.get("jobs", [])
            results = []
            for j in raw_jobs:
                title = j.get("title", "")
                job_url = j.get("absolute_url", "")
                loc = j.get("location", {}).get("name", "") if isinstance(j.get("location"), dict) else ""
                content = clean_text(j.get("content", ""))
                updated_at = j.get("updated_at", "")[:10] if j.get("updated_at") else get_utc_now_iso()[:10]

                if not title or not job_url:
                    continue

                results.append({
                    "source": "Greenhouse",
                    "source_job_id": str(j.get("id", "")),
                    "company": company_name,
                    "title": title,
                    "location": loc,
                    "remote": "remote" in loc.lower() or "remote" in content[:200].lower(),
                    "employment_type": "Full-time",
                    "description": content,
                    "url": normalize_url(job_url),
                    "company_url": f"https://boards.greenhouse.io/{board_token}",
                    "posted_at": updated_at,
                    "raw_data": j
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error parsing Greenhouse board {board_token}: {e}")
            return []

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        config = get_config()
        watchlist = config.companies.get("watchlist", [])
        all_jobs = []

        for item in watchlist:
            if item.get("ats_type") == "greenhouse":
                c_name = item.get("company")
                b_token = item.get("board_token")
                self.logger.info(f"Fetching Greenhouse board for {c_name} ({b_token})...")
                jobs = self.fetch_jobs_for_board(c_name, b_token)
                all_jobs.extend(jobs)

        return all_jobs
