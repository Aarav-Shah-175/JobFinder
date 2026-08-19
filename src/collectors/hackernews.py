from typing import List, Dict, Any
from src.collectors.base import BaseCollector
from src.utils.text import clean_text, normalize_url
from src.utils.dates import get_utc_now_iso

class HackerNewsCollector(BaseCollector):
    def __init__(self, rate_limit_delay: float = 0.5):
        super().__init__("HackerNews", rate_limit_delay)

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """
        Fetches public tech job postings from Hacker News official public Firebase API.
        """
        self.logger.info("Fetching Hacker News job stories...")
        # Official HN job stories API endpoint
        url = "https://hacker-news.firebaseio.com/v0/jobstories.json"
        resp = self.safe_get(url)
        if not resp:
            return []

        try:
            story_ids = resp.json()[:25]  # Top 25 public job posts
            results = []
            for item_id in story_ids:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                item_resp = self.safe_get(item_url)
                if not item_resp:
                    continue
                item_data = item_resp.json()
                if not item_data:
                    continue

                title = item_data.get("title", "")
                text = clean_text(item_data.get("text", title))
                hn_url = item_data.get("url") or f"https://news.ycombinator.com/item?id={item_id}"

                # Extract company name from title e.g. "Company (YC W24) is hiring Software Engineers"
                company = "Tech Startup"
                if " is hiring " in title.lower():
                    company = title.split(" is hiring ")[0].strip()
                elif "|" in title:
                    company = title.split("|")[0].strip()

                results.append({
                    "source": "HackerNews Jobs",
                    "source_job_id": str(item_id),
                    "company": company,
                    "title": title[:100],
                    "location": "Remote / Hybrid",
                    "remote": True,
                    "employment_type": "Full-time",
                    "description": text,
                    "url": normalize_url(hn_url),
                    "company_url": "https://news.ycombinator.com/jobs",
                    "posted_at": get_utc_now_iso()[:10],
                    "raw_data": item_data
                })
            return results
        except Exception as e:
            self.logger.warning(f"Error fetching Hacker News jobs: {e}")
            return []
